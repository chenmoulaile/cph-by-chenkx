"""cph-by-chenkx regression tests.

Runs with plain CPython - no Sublime Text, no third party packages:

    python tests/run_tests.py

A fake `sublime` module is injected so the plugin modules can be imported.
The cases below cover the bugs that actually shipped and had to be hot-fixed:
the multi-sample chain crash, the memory-limit verdict never firing, the
Python 3.3 subprocess arguments and the float comparison.

Exit code 0 = all good, 1 = failures (used by .github/workflows/tests.yml).
"""

import importlib
import importlib.util
import io
import json
import os
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
