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
import importlib
import importlib.util
import io
import json
import os
import re
import sys
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

        def execute_command(self, *args, **kwargs):
            pass

        def run_command(self, *args, **kwargs):
            pass

        def sel(self):
            return [Region(0)]

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
    check('stored answer CR normalized',
          list(crlf_test.correct_answers) == ['3\n4\n'],
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

    print('== cph_settings: test file path resolution ==')
    settings = importlib.import_module(pkg + '.core.cph_settings')
    paths = settings.get_tests_paths(os.path.join('tmp', 'foo.cpp'))
    check('three candidate paths are probed', len(paths) == 3, str(paths))
    check('traditional path first', paths[0].endswith('foo.cpp__tests'), paths[0])
    check('cph-ng folder path present',
          any(p.endswith(os.path.join('tests', 'foo.cpp__tests')) for p in paths),
          str(paths))

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

    print('== doctor: template commands are not a failure ==')
    doc = importlib.import_module(pkg + '.cph_doctor')
    ok, detail = doc._check_command('"{source_file_dir}/{file_name}.exe" {args}')
    check('run_cmd template is not reported as missing', ok is True, detail)
    ok2, _ = doc._check_command('g++ -O2 -o x')
    check('plain compiler command is looked up', ok2 is not None)

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
