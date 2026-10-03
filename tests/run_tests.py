"""cph-by-chenkx regression tests.

Runs with plain CPython - no Sublime Text, no third party packages:

    python tests/run_tests.py

A fake `sublime` module is injected so the plugin modules can be imported.
The cases below cover the bugs that actually shipped and had to be hot-fixed:
the multi-sample chain crash, the memory-limit verdict never firing, the
Python 3.3 subprocess arguments and the float comparison.

Exit code 0 = all good, 1 = failures (used by .github/workflows/tests.yml).
"""

import ast
import contextlib
import importlib
import importlib.util
import io
import json
import os
import re
import shutil
import sys
import tempfile
import types

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# --------------------------------------------------------------- fake sublime
def _install_fake_sublime():
    sublime = types.ModuleType('sublime')

    class Region(object):
        def __init__(self, a=0, b=None):
            self.a = a
            self.b = a if b is None else b

        def begin(self):
            return min(self.a, self.b)

        def end(self):
            return max(self.a, self.b)

        def empty(self):
            return self.a == self.b

        def __eq__(self, other):
            return isinstance(other, Region) and (self.a, self.b) == (other.a, other.b)

    class Settings(object):
        def __init__(self, data=None):
            self._data = dict(data or {})

        def get(self, key, default=None):
            return self._data.get(key, default)

        def set(self, key, value):
            self._data[key] = value

        def add_on_change(self, *args):
            pass

    class Phantom(object):
        def __init__(self, region, content, layout=None, on_navigate=None):
            self.region = region
            self.content = content

    class PhantomSet(object):
        def __init__(self, view, key):
            self.view = view
            self.key = key
            self.phantoms = []

        def update(self, phantoms):
            self.phantoms = list(phantoms)

    class View(object):
        def __init__(self, file_name=None, settings=None, size=0):
            self._file_name = file_name
            self._settings = Settings(settings)
            self._size = size
            self._status = {}

        def file_name(self):
            return self._file_name

        def name(self):
            return ''

        def settings(self):
            return self._settings

        def size(self):
            return self._size

        def get_status(self, key):
            return self._status.get(key)

        def set_status(self, key, value):
            self._status[key] = value

        def set_name(self, name):
            self._name = name

        def set_scratch(self, scratch):
            self._scratch = scratch

        def execute_command(self, *args, **kwargs):
            pass

        def run_command(self, *args, **kwargs):
            pass

        def sel(self):
            return [Region(0)]

        def window(self):
            return Window()

    class Window(object):
        """Minimal stand-in so doctor.run() can open its report view."""

        def __init__(self):
            self._views = []

        def new_file(self):
            view = View()
            self._views.append(view)
            return view

        def focus_view(self, view):
            pass

        def active_view(self):
            return self._views[-1] if self._views else None

        def run_command(self, *args, **kwargs):
            pass

        def status_message(self, *args, **kwargs):
            pass

    sublime.Region = Region
    sublime.Phantom = Phantom
    sublime.PhantomSet = PhantomSet
    sublime.Settings = Settings
    sublime.View = View
    sublime.LAYOUT_BLOCK = 1
    sublime.LAYOUT_INLINE = 2
    sublime.HIDDEN = 0
    sublime.DRAW_NO_FILL = 0
    sublime.DRAW_NO_OUTLINE = 0
    sublime.DRAW_STIPPLED_UNDERLINE = 0
    sublime.DRAW_EMPTY_AS_OVERWRITE = 0

    sublime.platform = lambda: 'linux'
    sublime.status_message = lambda *a, **k: None
    sublime.error_message = lambda *a, **k: None
    sublime.ok_cancel_dialog = lambda *a, **k: True
    sublime.message_dialog = lambda *a, **k: None
    sublime.set_timeout = lambda fn, delay=0: None          # never run the chain
    sublime.set_timeout_async = lambda fn, delay=0: None
    sublime.windows = lambda: []
    sublime.active_window = lambda: None
    sublime.get_clipboard = lambda: ''
    sublime.set_clipboard = lambda text: None
    sublime.load_settings = lambda name: Settings({})
    sublime.save_settings = lambda name: None
    sublime.load_resource = lambda path: '<div class="panel"></div>'
    sublime.decode_value = json.loads
    sublime.encode_value = json.dumps
    sublime.expand_variables = lambda s, v: s
    sublime.version = lambda: '4213'
    sys.modules['sublime'] = sublime

    sublime_plugin = types.ModuleType('sublime_plugin')

    class _Command(object):
        def __init__(self, view=None):
            self.view = view

        def is_enabled(self, *a, **k):
            return True

        def is_visible(self, *a, **k):
            return True

    sublime_plugin.TextCommand = _Command
    sublime_plugin.WindowCommand = _Command
    sublime_plugin.ApplicationCommand = _Command
    sublime_plugin.EventListener = object
    sys.modules['sublime_plugin'] = sublime_plugin


def _load_package():
    """Import the plugin package despite the hyphen in its folder name."""
    name = 'cphpkg'
    spec = importlib.util.spec_from_file_location(
        name, os.path.join(ROOT, '__init__.py'),
        submodule_search_locations=[ROOT])
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return name



# --------------------------------------------------- static analysis helpers
SKIP_DIRS = {'.git', '__pycache__', '.workbuddy', 'tests'}
ST_PROVIDED = {'view', 'window', 'run', 'is_enabled', 'is_visible', 'is_checked',
               'description', 'want_event', 'settings', 'on_navigate',
               'send_response', 'send_header', 'end_headers', 'log_message',
               'handle_one_request', 'wfile', 'rfile', 'headers',
               'protocol_version'}


def _plugin_py_files():
    out = []
    for base, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for f in files:
            if f.endswith('.py'):
                out.append(os.path.relpath(os.path.join(base, f), ROOT).replace(os.sep, '/'))
    return sorted(out)


def _self_calls_without_definition(rel_path):
    """[(class, line, method)] where self.method() is not defined in the class.

    Nested classes are handled: their methods belong to them, not to the
    enclosing class, and a class may use methods of our own mixins.
    """
    tree = ast.parse(open(os.path.join(ROOT, rel_path), encoding='utf-8').read())
    own = {}

    def collect(node):
        for item in ast.iter_child_nodes(node):
            if isinstance(item, ast.ClassDef):
                names = set()
                for sub in item.body:
                    if isinstance(sub, (ast.FunctionDef, ast.ClassDef)):
                        names.add(sub.name)
                own[item.name] = names
                collect(item)
    collect(tree)

    found = []

    def check_class(node):
        defined = set()
        assigned = set()
        inherited = set()
        for base in node.bases:
            bname = getattr(base, 'id', getattr(base, 'attr', ''))
            inherited |= own.get(bname, set())
        calls = []

        def scan_method(fn):
            for sub in ast.walk(fn):
                if isinstance(sub, ast.Assign):
                    for t in sub.targets:
                        if (isinstance(t, ast.Attribute)
                                and getattr(t.value, 'id', '') == 'self'):
                            assigned.add(t.attr)
                if isinstance(sub, ast.Call):
                    fn2 = sub.func
                    if (isinstance(fn2, ast.Attribute)
                            and isinstance(fn2.value, ast.Name)
                            and fn2.value.id == 'self'):
                        calls.append((sub.lineno, fn2.attr))

        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                defined.add(item.name)
                scan_method(item)
            elif isinstance(item, ast.ClassDef):
                defined.add(item.name)
                check_class(item)
            elif isinstance(item, ast.Assign):
                for t in item.targets:
                    if isinstance(t, ast.Attribute) and getattr(t.value, 'id', '') == 'self':
                        assigned.add(t.attr)

        resolved = defined | assigned | inherited | ST_PROVIDED
        for line, name in calls:
            if name in resolved or name.startswith('__'):
                continue
            found.append((node.name, line, name))

    for item in ast.iter_child_nodes(tree):
        if isinstance(item, ast.ClassDef):
            check_class(item)
    return found


def _lambdas_leaking_except_var(rel_path):
    """[(line, name)] where a lambda inside `except ... as NAME` reads NAME
    without binding it.

    Python deletes the exception variable when the except block ends, so a
    deferred callback such as `set_timeout(lambda: ... % e)` raised NameError
    by the time it ran (the error message was swallowed).
    """
    tree = ast.parse(open(os.path.join(ROOT, rel_path), encoding='utf-8').read())
    found = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.ExceptHandler) or not node.name:
            continue
        for sub in ast.walk(node):
            if not isinstance(sub, ast.Lambda):
                continue
            bound = {a.arg for a in sub.args.args}
            bound |= {a.arg for a in sub.args.kwonlyargs}
            for default in list(sub.args.defaults) + [d for d in sub.args.kw_defaults if d]:
                if isinstance(default, ast.Name):
                    bound.add(default.id)
            if node.name in bound:
                continue
            for inner in ast.walk(sub.body):
                if (isinstance(inner, ast.Name) and inner.id == node.name
                        and isinstance(inner.ctx, ast.Load)):
                    found.append((sub.lineno, node.name))
                    break
    return found

# ------------------------------------------------------------------ test rig
FAILURES = []
CHECKS = [0]


def check(label, condition, detail=''):
    CHECKS[0] += 1
    if condition:
        print('  ok   %s' % label)
    else:
        print('  FAIL %s %s' % (label, detail))
        FAILURES.append(label)


def main():
    _install_fake_sublime()
    pkg = _load_package()

    print('== cph_verdict: comparison and verdicts ==')
    verdict = importlib.import_module(pkg + '.core.cph_verdict')

    check('exact token match', verdict.outputs_equal('1 2 3', '1 2 3', 0))
    check('whitespace insensitive', verdict.outputs_equal('1  2\n3\n', '1 2 3', 0))
    check('mismatch detected', not verdict.outputs_equal('1 2', '1 3', 0))
    check('float tolerance accepts rounding',
          verdict.outputs_equal('0.30000000000000004', '0.3', 1e-6))
    check('float tolerance rejects real error',
          not verdict.outputs_equal('0.31', '0.3', 1e-6))
    check('token count mismatch rejected',
          not verdict.outputs_equal('1 2', '1', 1e-6))
    check('non numeric tokens stay exact',
          not verdict.outputs_equal('abc', 'abd', 1e-6))

    ac = verdict.get_verdict_by_code(
        rtcode=0, runtime=10, time_limit_ms=1000, memory_limit_mb=256,
        stderr='', stdout='42\n', expected_output='42')
    check('plain AC', ac['name'] == 'AC', ac['name'])

    mle = verdict.get_verdict_by_code(
        rtcode=0, runtime=10, time_limit_ms=1000, memory_limit_mb=256,
        stderr='', stdout='42\n', expected_output='42', memory_used_mb=300)
    check('MLE fires on measured memory', mle['name'] == 'MLE', mle['name'])

    tle = verdict.get_verdict_by_code(
        rtcode=0, runtime=1500, time_limit_ms=1000, memory_limit_mb=256,
        stderr='', stdout='42\n', expected_output='42')
    check('TLE on runtime', tle['name'] == 'TLE', tle['name'])

    pe = verdict.get_verdict_by_code(
        rtcode=0, runtime=10, time_limit_ms=1000, memory_limit_mb=256,
        stderr='', stdout='1  2', expected_output='1 2')
    check('PE on formatting only', pe['name'] == 'PE', pe['name'])

    diff, total = verdict.build_line_diff('a\nb\nc', 'a\nX\nc')
    check('line diff finds the changed line',
          diff is not None and any(op[0] == '!=' and op[1] == 2 for op in diff),
          str(diff))

    print('== runtime error: detected and located ==')
    for label, rtcode in (('segfault (139)', 139), ('abort (exit 3)', 3),
                          ('signal (-11)', -11)):
        got = verdict.get_verdict_by_code(
            rtcode=rtcode, runtime=10, time_limit_ms=1000, memory_limit_mb=256,
            stderr='', stdout='', expected_output='1')['name']
        check('%s is a runtime error' % label, got == 'RE', got)

    py_tb = ('Traceback (most recent call last):\n'
             '  File "/tmp/main.py", line 12, in <module>\n'
             '    print(1 / 0)\nZeroDivisionError: division by zero\n')
    check('python traceback is located',
          verdict.find_crash_location(py_tb, '/tmp/main.py') == ('/tmp/main.py', 12),
          repr(verdict.find_crash_location(py_tb, '/tmp/main.py')))
    java_tb = ('Exception in thread "main" java.lang.ArithmeticException: / by zero\n'
               '\tat Main.main(Main.java:5)\n')
    check('java stack trace is located',
          verdict.find_crash_location(java_tb, 'Main.java') == ('Main.java', 5),
          repr(verdict.find_crash_location(java_tb, 'Main.java')))
    san = "main.cpp:7:5: runtime error: load of null pointer of type 'int'\n"
    check('sanitizer diagnostic is located',
          verdict.find_crash_location(san, 'main.cpp') == ('main.cpp', 7),
          repr(verdict.find_crash_location(san, 'main.cpp')))
    check('no location for a bare segfault',
          verdict.find_crash_location('', 'main.cpp') is None)
    check('ordinary output yields no location',
          verdict.find_crash_location('3\n', 'main.cpp') is None)

    print('== Tester: the multi-sample chain crash ==')
    tm = importlib.import_module(pkg + '.test_manager')

    class FakeProcess(object):
        """Stands in for ProcessManager (no real process in unit tests)."""

        is_run = False

        def set_calls(self, *args):
            pass

        def run(self, *args, **kwargs):
            pass

        def write(self, s):
            pass

        def is_stopped(self):
            return 0

        def get_time_limit_ms(self):
            return 1000

        def get_memory_limit_mb(self):
            return 256

    def make_tester(tests):
        return tm.CphTestManagerCommand.Tester(
            FakeProcess(), lambda *a: None, lambda *a: None,
            lambda *a: None, lambda *a: None,
            sync_out=False, tests=tests, epoch=1)

    cmd = tm.CphTestManagerCommand.__new__(tm.CphTestManagerCommand)
    cmd.view = sys.modules['sublime'].View()

    # 'Run failed tests' jumps past accepted tests: index 3 with only 2 tests
    tester = make_tester([tm.CphTestManagerCommand.Test('a'),
                          tm.CphTestManagerCommand.Test('b')])
    tester.proc_run = False
    tester.test_iter = 3
    cmd.tester = tester
    try:
        tester.next_test(0, lambda: None)
        ok = len(tester.tests) >= 4 and len(tester.prog_out) >= 4
        check('next_test pads tests/prog_out up to the jump target', ok,
              'tests=%d prog_out=%d' % (len(tester.tests), len(tester.prog_out)))
    except Exception as e:
        check('next_test pads tests/prog_out up to the jump target', False,
              '%s: %s' % (type(e).__name__, e))

    # a folded (skipped) test must not be re-run and must fold itself
    tester2 = make_tester([tm.CphTestManagerCommand.Test('a'),
                           tm.CphTestManagerCommand.Test('b')])
    tester2.tests[0].verdict = verdict.get_verdict('accepted')
    tester2.run_failed = True
    cmd.tester = tester2
    check('is_skippable marks AC tests', cmd.is_skippable(0) is True)
    check('is_skippable leaves failures alone', cmd.is_skippable(1) is False)
    check('next_runnable_index skips the AC test', cmd.next_runnable_index() == 1,
          str(cmd.next_runnable_index()))

    print('== ProcessManager: python 3.3 safe subprocess handling ==')
    pm_mod = importlib.import_module(pkg + '.Modules.ProcessManager')

    check('quoted path needs no shell',
          pm_mod._needs_shell('"/opt/my prog/app"') is False)
    check('pipes need a shell', pm_mod._needs_shell('a | b') is True)
    check('&& needs a shell', pm_mod._needs_shell('a && b') is True)
    check('plain command needs no shell',
          pm_mod._needs_shell('g++ "x.cpp" -o x') is False)

    check('utf-8 output decodes',
          pm_mod._decode_output('中文'.encode('utf-8')) == '中文')
    check('garbage bytes do not raise',
          isinstance(pm_mod._decode_output(b'\xff\xfe\x00abc'), str))
    check('decoded output drops CR',
          pm_mod._decode_output(b'1\r\n2\r\n') == '1\n2\n',
          repr(pm_mod._decode_output(b'1\r\n2\r\n')))

    # Windows programs emit CRLF; a raw CR renders as '<0x0d>' in the panel
    pm_obj = pm_mod.ProcessManager.__new__(pm_mod.ProcessManager)
    pm_obj._pending_cr = False
    norm = pm_obj._normalize_newlines
    check('CRLF becomes LF', norm('a\r\nb') == 'a\nb', repr(norm('a\r\nb')))
    check('lone CR becomes LF', norm('a\rb') == 'a\nb', repr(norm('a\rb')))
    check('plain LF untouched', norm('a\nb') == 'a\nb', repr(norm('a\nb')))

    pm_obj._pending_cr = False
    split = norm('a\r') + norm('\nb')
    check('CRLF split across two chunks keeps exactly one newline',
          split == 'a\nb', repr(split))

    pm_obj._pending_cr = False
    split2 = norm('a\r') + norm('b')
    check('lone CR split across chunks becomes one newline',
          split2 == 'a\nb', repr(split2))

    pm_obj._pending_cr = False
    at_eof = norm('x\r') + norm('', final=True)
    check('trailing CR at EOF is flushed', at_eof == 'x\n', repr(at_eof))

    # byte-at-a-time (sync) mode must behave the same
    pm_obj._pending_cr = False
    pm_obj._out_decoder = None
    bytewise = ''
    for ch in 'a\r\nb\r\n':
        bytewise += norm(ch)
    check('byte-at-a-time CRLF handling', bytewise == 'a\nb\n', repr(bytewise))

    print('== stored test data: no stray CR ==')
    crlf_test = tm.CphTestManagerCommand.Test(
        {'test': '1\r\n2\r\n', 'correct_answers': ['3\r\n4\r\n']})
    check('test input CR normalized',
          crlf_test.test_string == '1\n2\n', repr(crlf_test.test_string))
    check('stored answer normalized (CR folded + trimmed)',
          list(crlf_test.correct_answers) == ['3\n4'],
          repr(crlf_test.correct_answers))

    # the exact regression: Popen must not receive 3.6+ only keywords
    import inspect
    try:
        src = inspect.getsource(pm_mod)
        forbidden = [w for w in ('encoding=', 'errors=', 'text=True', 'capture_output=')
                     if w in src.split('def run_file')[1].split('def ')[0]]
        check('run_file avoids 3.6+ Popen keywords', not forbidden, str(forbidden))
    except Exception as e:
        check('run_file avoids 3.6+ Popen keywords', False, str(e))

    # insert() calls the i18n helper on a broken stdin pipe; the import was
    # missing, so that "drop the input gracefully" path raised NameError.
    check('ProcessManager can resolve t() used by insert()',
          callable(getattr(pm_mod, 't', None)))

    # cph_run_modes sends these flags to cph_view_tester.run(); before the
    # fix they were rejected with TypeError, so "Run all / Run failed /
    # Force recompile" did nothing when invoked outside the -run panel.
    params = inspect.signature(tm.CphViewTesterCommand.run).parameters
    missing = [k for k in ('run_all', 'run_failed', 'force_compile') if k not in params]
    check('cph_view_tester.run accepts the run-mode flags', not missing, str(missing))

    print('== cph_settings: test file path resolution ==')
    settings = importlib.import_module(pkg + '.core.cph_settings')
    paths = settings.get_tests_paths(os.path.join('tmp', 'foo.cpp'))
    check('three candidate paths are probed', len(paths) == 3, str(paths))
    check('traditional path first', paths[0].endswith('foo.cpp__tests'), paths[0])
    check('cph-ng folder path present',
          any(p.endswith(os.path.join('tests', 'foo.cpp__tests')) for p in paths),
          str(paths))

    # tests_relative_dir is honoured by save_tests(); if it is not probed on
    # load, the saved data becomes invisible (and "clear tests" misses it).
    _real_rel_dir = settings.get_tests_relative_dir
    settings.get_tests_relative_dir = lambda: 'rel'
    try:
        rel_paths = settings.get_tests_paths(os.path.join('tmp', 'foo.cpp'))
        check('tests_relative_dir is probed first',
              len(rel_paths) == 4
              and rel_paths[0].endswith(os.path.join('rel', 'foo.cpp__tests')),
              str(rel_paths))
    finally:
        settings.get_tests_relative_dir = _real_rel_dir

    # Import must detect a UTF-16 BOM; otherwise the bytes decode as UTF-8
    # mojibake / fall through to gb18030 and the utf-16 branch is dead code.
    import tempfile
    importer = importlib.import_module(pkg + '.cph_import')
    fh = tempfile.NamedTemporaryFile(suffix='.in', delete=False)
    fh.write('1 2 3\n'.encode('utf-16'))
    fh.close()
    try:
        check('utf-16 test data decodes (BOM detected)',
              importer._read_text(fh.name).strip() == '1 2 3',
              repr(importer._read_text(fh.name)))
    finally:
        os.unlink(fh.name)

    print('== shipped settings: every command must be formattable ==')
    # This is the P0 that shipped in v1.4.0-v1.4.4: the default C++ compile_cmd
    # contains {extra_sources} / {include_dirs}, which are NOT format keys, so
    # str.format() raised KeyError on the very first run of a fresh install.
    import tempfile
    raw = open(os.path.join(ROOT, 'cph-by-chenkx.sublime-settings'), encoding='utf-8').read()
    raw = re.sub(r'//[^\n]*', '', raw)
    shipped = json.loads(raw)
    tmpdir = tempfile.mkdtemp()
    file_names = {'cpp': 'main.cpp', 'py': 'main.py', 'java': 'Main.java'}
    for entry in shipped.get('run_settings', []):
        for ext in entry.get('extensions', []):
            target = os.path.join(tmpdir, file_names.get(ext, 'prog.' + ext))
            with open(target, 'w'):
                pass
            mgr = pm_mod.ProcessManager(target, 'source.' + ext,
                                        run_settings=shipped['run_settings'])
            for label, getter in (('compile_cmd', lambda m=mgr: m.get_compile_cmd()),
                                  ('run_cmd', lambda m=mgr: m.get_run_cmd(''))):
                name = '%s %s formats' % (entry.get('name', '?'), label)
                try:
                    getter()
                    check(name, True)
                except Exception as e:
                    check(name, False, '%s: %s' % (type(e).__name__, e))

    print('== Test model: attributes used by rendering ==')
    fresh = tm.CphTestManagerCommand.Test({'test': '1\n'})
    check('rtcode is initialized (expanding a skipped card)',
          getattr(fresh, 'rtcode', None) == '0', repr(getattr(fresh, 'rtcode', None)))

    print('== second round: card CSS, output bounds, stderr chip, sampler ==')
    # The card's status class must exist in the shipped CSS themes, or the
    # green/red tint is silently dead ('test-AC' / 'test-wrong-answer' matched
    # no rule at all).
    css_text = ''
    for css_name in ('test_styles.css', 'test_styles_spacegray.css',
                     'test_styles_spacegraylight.css'):
        with open(os.path.join(ROOT, 'Highlight', css_name), encoding='utf-8') as f:
            css_text += f.read()
    for vname, expected in (('AC', 'test-accept'), ('WA', 'test-decline')):
        card = tm.CphTestManagerCommand.Test({'test': '1\n'})
        card.verdict = verdict.get_verdict_by_name(vname)
        got = card.get_test_class()
        check('card class for %s is defined in CSS' % vname,
              got == expected and ('.' + got) in css_text, '%s -> %s' % (vname, got))

    # every verdict the plugin can render (incl. one restored from a session)
    # needs a badge rule, or the badge silently falls back to the base style
    missing_css = sorted(n for n in set(verdict.VERDICT_NAME.values())
                         if ('.verdict-' + n) not in css_text)
    check('every verdict badge class is defined in CSS', not missing_css,
          ', '.join(missing_css))

    # prog_out can legitimately be shorter than the test list (session-restored
    # tests, or the test menu acting on an un-materialised one).
    tester = make_tester([tm.CphTestManagerCommand.Test('a')])
    tester.prog_out = []
    check('output_at() is safe for an un-materialised test', tester.output_at(3) == '')
    tester.prog_out = ['abc']
    check('output_at() returns the stored output',
          tester.output_at(0) == 'abc' and tester.output_at(9) == '')

    # the card template must actually surface a captured stderr
    with open(os.path.join(ROOT, 'Highlight', 'test_config.html'), encoding='utf-8') as f:
        card_tpl = f.read()
    check('card template surfaces captured stderr',
          '{stderr_display}' in card_tpl and '{stderr_label}' in card_tpl)

    # A leaked MemorySampler used to poll a dead pid for the whole session.
    # Use an impossible pid plus a tiny interval and a hard cap on how long a
    # single sample may take, so the check cannot depend on runner speed (a
    # fixed sleep here was too tight on a loaded macOS runner).
    mp = importlib.import_module(pkg + '.Modules.memprobe')
    sampler = mp.MemorySampler(99999999, interval=0.001, max_silence=1.0)
    sampler.start()
    sampler._thread.join(timeout=10.0)
    still_alive = sampler._thread.is_alive()
    sampler.stop()
    check('memory sampler stops polling a dead pid', not still_alive)

    print('== doctor: template commands are not a failure ==')
    doc = importlib.import_module(pkg + '.cph_doctor')
    ok, detail = doc._check_command('"{source_file_dir}/{file_name}.exe" {args}')
    check('run_cmd template is not reported as missing', ok is True, detail)
    ok2, _ = doc._check_command('g++ -O2 -o x')
    check('plain compiler command is looked up', ok2 is not None)

    # v1.4.6 shipped doctor without `import re`: the first language entry made
    # _unknown_placeholders raise NameError and the report view was never
    # created - doctor was unusable, not merely wrong. Pin both the helper and
    # the whole run() path so this class of "feature totally dead" regression
    # cannot slip through again.
    check('known placeholders are accepted',
          doc._unknown_placeholders('g++ {file} -o {file_name}') == [],
          repr(doc._unknown_placeholders('g++ {file} -o {file_name}')))
    check('a typo in a placeholder is flagged',
          doc._unknown_placeholders('g++ {file_nmae}') == ['file_nmae'],
          repr(doc._unknown_placeholders('g++ {file_nmae}')))
    check('an empty command has no placeholders',
          doc._unknown_placeholders('') == [])

    real_get_settings = doc.get_settings
    doc.get_settings = lambda: {'run_settings': [
        {'name': 'C++', 'extensions': ['cpp'],
         'compile_cmd': 'g++ {file_nmae} -o x', 'run_cmd': 'x'}]}
    try:
        cmd = doc.CphDoctorCommand(sys.modules['sublime'].View())
        # doctor also prints the report to the console; capture it so the
        # check does not depend on the console encoding (a cp1252 Windows
        # console cannot encode the Chinese report text and raised
        # UnicodeEncodeError, which is a test-host artefact - inside Sublime
        # the console is UTF-8 and the report view is created before the print).
        with contextlib.redirect_stdout(io.StringIO()):
            cmd.run(None)
        check('doctor run() survives a language entry', True)
    except Exception as e:
        check('doctor run() survives a language entry', False,
              '%s: %s' % (type(e).__name__, e))
    finally:
        doc.get_settings = real_get_settings

    print('== companion: merge keyed by input ==')
    comp = importlib.import_module(pkg + '.cph_companion')
    comp.load_all_tests = lambda f: [{'test': '1 2\n', 'correct_answers': []}]
    merged = comp.merge_tests('x.cpp', [{'test': '1 2\n', 'correct_answers': ['3\n']}])
    check('resending the same input updates the answer instead of duplicating',
          len(merged) == 1 and merged[0]['correct_answers'] == ['3\n'], repr(merged))
    merged2 = comp.merge_tests('x.cpp', [{'test': '9\n', 'correct_answers': []}])
    check('a genuinely new input is appended', len(merged2) == 2, repr(merged2))

    print('== static checks: the regressions that unit tests cannot reach ==')
    # 1. Every self.X() call must resolve inside its own class. This is the
    #    v1.4.5 bug: a helper was defined on CphViewTesterCommand but called
    #    from CphTestManagerCommand, so make_opd raised AttributeError right
    #    after creating the -run view and the panel stayed empty.
    problems = []
    for path in _plugin_py_files():
        for cname, line, name in _self_calls_without_definition(path):
            problems.append('%s:%d %s.self.%s()' % (path, line, cname, name))
    check('every self.<method>() is defined in its class', not problems,
          '; '.join(problems[:5]))

    # 2. The run panel is identified by a view setting now; comparing the old
    #    'opd_info' status value is exactly how _refresh_panel silently broke.
    stale = []
    for path in _plugin_py_files():
        with open(path, encoding='utf-8') as f:
            for i, line in enumerate(f, 1):
                if "get_status('opd_info') ==" in line:
                    stale.append('%s:%d' % (path, i))
    check('no stale opd_info marker comparisons', not stale, ', '.join(stale))

    # 3. A lambda inside an except block must not read the exception variable
    #    without binding it (Python deletes it when the block ends).
    leaked = []
    for path in _plugin_py_files():
        for line, name in _lambdas_leaking_except_var(path):
            leaked.append('%s:%d lambda reads except-var %s' % (path, line, name))
    check('no lambda leaks an except variable', not leaked, '; '.join(leaked[:5]))

    print('== merge policy (shared by import / clipboard / companion) ==')
    merge = importlib.import_module(pkg + '.core.cph_tests_merge')

    merged, conflicts = merge.merge_tests(
        [{'test': '1\n', 'correct_answers': []}],
        [{'test': '1\n', 'correct_answers': ['7\n']}])
    check('answer is filled in when none was stored',
          len(merged) == 1 and merged[0]['correct_answers'] == ['7\n'] and not conflicts,
          repr((merged, conflicts)))

    merged, conflicts = merge.merge_tests(
        [{'test': '1\n', 'correct_answers': ['user\n']}],
        [{'test': '1\n', 'correct_answers': ['sample\n']}])
    check('a stored answer is never overwritten by a re-sent sample',
          merged[0]['correct_answers'] == ['user\n'], repr(merged))
    check('the conflict is reported to the caller', len(conflicts) == 1, repr(conflicts))

    merged, _ = merge.merge_tests([{'test': '1\n', 'correct_answers': []}],
                                  [{'test': '2\n', 'correct_answers': []}])
    check('a different input is appended', len(merged) == 2, repr(merged))

    print('== regard_pe_as_ac is wired to the setting ==')
    pe_strict = verdict.get_verdict_by_code(
        rtcode=0, runtime=10, time_limit_ms=1000, memory_limit_mb=256,
        stderr='', stdout='1  2', expected_output='1 2')
    pe_lenient = verdict.get_verdict_by_code(
        rtcode=0, runtime=10, time_limit_ms=1000, memory_limit_mb=256,
        stderr='', stdout='1  2', expected_output='1 2', regard_pe_as_ac=True)
    check('PE stays PE by default', pe_strict['name'] == 'PE', pe_strict['name'])
    check('regard_pe_as_ac=true turns PE into AC',
          pe_lenient['name'] == 'AC', pe_lenient['name'])
    with open(os.path.join(ROOT, 'cph-by-chenkx.sublime-settings'), encoding='utf-8') as f:
        settings_text = f.read()
    check('the setting is documented in the default settings',
          '"regard_pe_as_ac"' in settings_text)
    check('it defaults to false (strict)',
          '"regard_pe_as_ac": false' in settings_text)

    print('== Package Control review rules ==')
    DEFAULTS = ('Default (Windows).sublime-keymap', 'Default (Linux).sublime-keymap',
                'Default (OSX).sublime-keymap')
    EXAMPLES = ('Example (Windows).sublime-keymap', 'Example (Linux).sublime-keymap',
                'Example (OSX).sublime-keymap')

    # 1. A package should not claim keys while the user is editing their own
    #    code (Package Control: "we strongly advice against adding keybindings
    #    by default"). Our shipped defaults may only fire inside the package's
    #    own syntax or behind a custom state key.
    claims = []
    every_binding_scoped = True
    for name in DEFAULTS:
        with open(os.path.join(ROOT, name), encoding='utf-8') as f:
            for entry in json.load(f):
                contexts = entry.get('context') or []
                if not contexts:
                    every_binding_scoped = False
                    claims.append('%s %s (no context)' % (name, entry.get('keys')))
                    continue
                own_view = any(
                    item.get('key') == 'selector' and item.get('operator') == 'equal'
                    and str(item.get('operand', '')).strip() == 'source.TestSyntax'
                    for item in contexts)
                stateful = any(str(item.get('key', '')).startswith('cph_')
                               for item in contexts)
                if not (own_view or stateful):
                    claims.append('%s %s' % (name, '+'.join(entry.get('keys') or [])))
    check('shipped bindings never claim keys while editing code', not claims,
          '; '.join(claims))
    check('every shipped binding still carries a context', every_binding_scoped)

    # 2. The suggestions users copy must be valid JSON and scoped as well.
    suggestion_problems = []
    suggestion_count = 0
    for name in EXAMPLES:
        path = os.path.join(ROOT, name)
        if not os.path.isfile(path):
            suggestion_problems.append('%s missing' % name)
            continue
        with open(path, encoding='utf-8') as f:
            entries = json.load(f)
        suggestion_count += len(entries)
        for entry in entries:
            if not entry.get('context'):
                suggestion_problems.append('%s %s' % (name, entry.get('keys')))
    check('per-platform example keymaps exist and are scoped',
          not suggestion_problems and suggestion_count > 0,
          '; '.join(suggestion_problems) or 'no suggestions')
    check('no active key binding ships by default',
          not os.path.isfile(os.path.join(ROOT, 'Example.sublime-keymap')),
          'the old single Example.sublime-keymap is back')

    # 3. Custom context keys used anywhere must be answered by the listener.
    with open(os.path.join(ROOT, 'cph_context.py'), encoding='utf-8') as f:
        ctx_src = f.read()
    used_keys = set()
    for name in DEFAULTS + EXAMPLES:
        with open(os.path.join(ROOT, name), encoding='utf-8') as f:
            for entry in json.load(f):
                for item in entry.get('context') or []:
                    key = item.get('key', '')
                    if key.startswith('cph_'):
                        used_keys.add(key)
    unanswered = [k for k in sorted(used_keys) if ("'%s'" % k) not in ctx_src]
    check('custom context keys are answered by cph_context', not unanswered,
          '; '.join(unanswered))
    check('at least one custom context key is exercised', bool(used_keys),
          'none found')

    # 4. Context menu entries: .sublime-menu has no `context` key, so the
    #    command's is_visible() is the only way to make an entry conditional.
    #    Every command we put in that menu must implement it.
    def class_defines(pkg_rel_dir, class_name, method):
        for rel in _plugin_py_files():
            if pkg_rel_dir and not rel.startswith(pkg_rel_dir):
                continue
            with open(os.path.join(ROOT, rel), encoding='utf-8') as f:
                tree = ast.parse(f.read())
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef) and node.name == class_name:
                    return any(isinstance(b, ast.FunctionDef) and b.name == method
                               for b in node.body)
        return False

    def command_class(command):
        return ''.join(part.capitalize() for part in command.split('_')) + 'Command'

    with open(os.path.join(ROOT, 'Context.sublime-menu'), encoding='utf-8') as f:
        menu = json.load(f)
    unconditional = [item['command'] for item in menu
                     if not class_defines('', command_class(item['command']), 'is_visible')]
    check('every context menu command implements is_visible()', not unconditional,
          '; '.join(unconditional))
    menu_bare_context = [item['command'] for item in menu if 'context' in item]
    check('context menu items do not fake an unsupported context key',
          not menu_bare_context, '; '.join(menu_bare_context))

    # 5. Settings and key bindings must open in split view: `edit_settings`,
    #    not `open_file`.
    with open(os.path.join(ROOT, 'Main.sublime-menu'), encoding='utf-8') as f:
        main_menu = json.load(f)
    wrong = []

    def walk_menu(items):
        for item in items:
            caption = str(item.get('caption') or '')
            if item.get('command') == 'open_file' and (
                    'settings' in caption.lower() or 'key binding' in caption.lower()
                    or '.sublime-keymap' in str(item.get('args'))):
                wrong.append(caption)
            for child in item.get('children') or []:
                walk_menu([child])

    walk_menu(main_menu)
    check('settings/keybindings use edit_settings (split view)', not wrong,
          '; '.join(wrong))

    # 6. The context menu switch is documented in the shipped settings.
    with open(os.path.join(ROOT, 'cph-by-chenkx.sublime-settings'), encoding='utf-8') as f:
        settings_text = f.read()
    check('context_menu setting is shipped',
          '"context_menu"' in settings_text)

    # 3. Root level plugin modules must not be imported from each other
    #    (Sublime loads every root level .py as an independent plugin).
    root_modules = set()
    for name in os.listdir(ROOT):
        if name.endswith('.py') and os.path.isfile(os.path.join(ROOT, name)):
            root_modules.add(name[:-3])
    violations = []
    for rel in _plugin_py_files():
        if '/' in rel:          # only root level files matter
            continue
        with open(os.path.join(ROOT, rel), encoding='utf-8') as f:
            for i, line in enumerate(f, 1):
                stripped = line.strip()
                if not stripped.startswith('from .'):
                    continue
                # 'from .cph_companion import x' -> '.cph_companion' -> 'cph_companion'
                target = stripped.split()[1].lstrip('.').split('.')[0]
                if target in root_modules - {'__init__'}:
                    violations.append('%s:%d %s' % (rel, i, stripped))
    check('no root-level plugin module imports', not violations,
          '; '.join(violations[:3]))

    # 4. Platform specific settings variants must be named after the package
    #    or a syntax we ship - we ship none, so the base file must stay neutral.
    stray = [f for f in os.listdir(ROOT) if ' (' in f and f.endswith('.sublime-settings')]
    check('no stray platform settings variants', not stray, '; '.join(stray))

    print('== build artifacts: the compiler does not always use the -o name ==')
    artifacts = importlib.import_module(pkg + '.Modules.build_artifact')

    check('quoted -o with spaces is parsed',
          artifacts.output_path_from_compile_cmd(
              'g++ "a b.cpp" -o "A  中文.exe" -DLOCAL') == 'A  中文.exe')
    check('unquoted -o is parsed',
          artifacts.output_path_from_compile_cmd('g++ x.cpp -o out.exe') == 'out.exe')
    check('a command without -o yields nothing',
          artifacts.output_path_from_compile_cmd('javac -d . A.java') is None)

    # A Chinese name written through GBK and read back as latin-1.
    mangled = '中文.exe'.encode('cp936').decode('latin-1')
    check('mangled name is recognised', artifacts.names_match(mangled, '中文.exe'),
          repr(mangled))
    check('unrelated names do not match', not artifacts.names_match('a.exe', 'b.exe'))

    tmp = tempfile.mkdtemp(prefix='cph_artifact_')
    try:
        wanted = os.path.join(tmp, 'A  中文.exe')
        real = os.path.join(tmp, 'A  ' + mangled)
        open(real, 'w').close()

        check('the missing -o name resolves to the mangled file',
              artifacts.resolve_artifact(wanted, tmp) == real)
        check('an existing file is returned untouched',
              artifacts.resolve_artifact(real, tmp) == real)
        check('retarget_command points at the real binary',
              artifacts.retarget_command(
                  '"%s" -x' % wanted, tmp) == '"%s" -x' % real)
        check('retarget_command leaves an existing path alone',
              artifacts.retarget_command('"%s" ' % real, tmp) == '"%s" ' % real)
        check('retarget_command leaves PATH commands alone',
              artifacts.retarget_command('python "x.py"', tmp) == 'python "x.py"')
        check('retarget_path points at the real binary',
              artifacts.retarget_path(wanted, tmp) == real)
        check('retarget_path leaves a foreign missing file alone',
              artifacts.retarget_path(os.path.join(tmp, 'nope.py'), tmp)
              == os.path.join(tmp, 'nope.py'))

        os.remove(real)
        check('nothing is invented when the binary is really gone',
              artifacts.resolve_artifact(wanted, tmp) is None)
        other = os.path.join(tmp, 'weird.exe')
        open(other, 'w').close()
        check('the newest file wins as a last resort',
              artifacts.resolve_artifact(wanted, tmp, started_at=0) == other)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    # print() must survive a narrow console: the Windows CI runner is cp1252
    # and printing a mangled non-ASCII binary name there raised
    # UnicodeEncodeError and failed the whole job.
    class _NarrowStdout(object):
        def write(self, text):
            text.encode('cp1252')
            return len(text)

        def flush(self):
            pass

    try:
        with contextlib.redirect_stdout(_NarrowStdout()):
            # '中文' and the mangled latin-1 lookalike are both unprintable
            # on cp1252; this is the exact message that broke the CI job.
            artifacts.print_safe(
                '[cph-by-chenkx] the binary is %r on disk, not %r'
                % ('ÖÐÎÄ.exe', '中文.exe'))
        narrow_ok = True
    except Exception as e:
        narrow_ok = '%s: %s' % (type(e).__name__, e)
    check('console output survives a cp1252 stdout', narrow_ok is True, narrow_ok)

    print('== the run command follows the real binary ==')
    pm_mod = importlib.import_module(pkg + '.Modules.ProcessManager')
    tmp2 = tempfile.mkdtemp(prefix='cph_run_')
    try:
        source = os.path.join(tmp2, '中文.cpp')
        open(source, 'w').close()
        exe_real = os.path.join(tmp2, mangled)
        exe_wanted = os.path.join(tmp2, '中文.exe')
        run_settings = [{
            'name': 'C++', 'extensions': ['cpp'],
            'compile_cmd': 'g++ "{source_file}" -o "{file_name}.exe"',
            'run_cmd': '"{source_file_dir}/{file_name}.exe" {args}',
        }]
        manager = pm_mod.ProcessManager(source, 'source.c++',
                                        run_settings=run_settings)
        open(exe_real, 'w').close()
        cmd = manager.get_run_cmd('')
        check('get_run_cmd retargets a missing non-ASCII binary',
              exe_real in cmd, cmd)
        os.remove(exe_real)
        open(exe_wanted, 'w').close()
        cmd = manager.get_run_cmd('')
        check('get_run_cmd keeps the command when the binary is there',
              '中文.exe' in cmd and mangled not in cmd, cmd)
    finally:
        shutil.rmtree(tmp2, ignore_errors=True)

    print('== stress loop: a timeout is not a failure ==')
    i18n = importlib.import_module(pkg + '.core.cph_i18n')
    stress = importlib.import_module(pkg + '.cph_stress')
    fake_sublime = sys.modules['sublime']
    chunks = []
    saved = (fake_sublime.set_timeout, stress._append_stress,
             stress._compile_program, stress._run_program, i18n.get_lang())
    try:
        fake_sublime.set_timeout = lambda fn, delay=0: fn()
        stress._append_stress = lambda text: chunks.append(text)
        stress._compile_program = lambda f, time_limit=30: (True, f, '')
        i18n.set_lang('en')

        def run_as(gen, user):
            del chunks[:]
            stress._stress_state['stop_requested'] = False
            stress._stress_state['running'] = True

            def fake_run(program, data, cwd=None, time_limit=2.0):
                return gen if program.endswith('gen.cpp') else user

            stress._run_program = fake_run
            stress._run_stress_loop('u.cpp', 's.cpp', 'gen.cpp', 2.0, 3)
            return ''.join(chunks)

        text = run_as((-1, '', '', True), (0, '1', '', False))
        check('a generator timeout is reported as a timeout',
              'timed out' in text and 'Generator failed' not in text,
              text.replace('\n', ' | ')[:200])
        check('the generator timeout names the setting to change',
              'stress_generator_time_limit_seconds' in text)

        text = run_as((3, '', 'boom', False), (0, '1', '', False))
        check('a generator crash shows the exit code and its stderr',
              'exit code 3' in text and 'boom' in text,
              text.replace('\n', ' | ')[:200])

        text = run_as((0, '1', '', False), (-1, '', 'FileNotFoundError: nose.exe', False))
        check('a program that cannot start is reported, not compared',
              'cannot run' in text and 'mismatch' not in text,
              text.replace('\n', ' | ')[:200])

        text = run_as((0, '1', '', False), (-1, '', '', True))
        check('a user TLE adds the debug-output hint',
              'hint' in text and 'mismatch' not in text,
              text.replace('\n', ' | ')[:200])
    finally:
        fake_sublime.set_timeout, stress._append_stress, \
            stress._compile_program, stress._run_program = saved[:4]
        i18n.set_lang(saved[4])
        stress._stop_stress()

    print('')
    print('%d checks, %d failures' % (CHECKS[0], len(FAILURES)))
    if FAILURES:
        print('failed:')
        for f in FAILURES:
            print('  - %s' % f)
        return 1
    print('ALL TESTS PASSED')
    return 0


if __name__ == '__main__':
    sys.exit(main())
