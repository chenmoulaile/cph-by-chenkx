"""
cph-by-chenkx - 对拍 (Stress Test) 功能
"""

import sublime
import sublime_plugin
import os
import random
import shlex
import shutil
import subprocess
import tempfile
import threading
import time

from .core.cph_settings import get_settings, load_all_tests, save_tests
from .core.cph_tests_merge import merge_tests
from .core.cph_state import set_stress_running
from .core.cph_target import context_menu_enabled, visible as context_menu_visible
from .core.cph_i18n import t
from .core.cph_verdict import normalize_lines, outputs_equal
from .core import cph_checker
from .Modules.ProcessManager import _LenientFormat
from .Modules.build_artifact import (output_path_from_compile_cmd,
                                     isolate_output, resolve_artifact,
                                     retarget_path, print_safe)


class _Aborted(Exception):
    """Raised when the user stops a stress test mid-round."""


_stress_state = {
    'running': False,
    'stop_requested': False,
    'std_file': None,
    'generator_file': None,
    'user_file': None,
    'time_limit': 2,
    'max_rounds': 1000,
    'current_round': 0,
    'last_diff': None,
    # The program running right now, so Stop can kill it instead of waiting
    # out its time limit.
    'current_proc': None,
    # Scratch directory the stress binaries are built into.
    'build_root': None,
    'build_seq': 0,
}


#: Hints for the two programs a stress test needs, matched against the stem
#: of every source file next to the file under test.
_STD_HINTS = ('std', 'brute', 'bf', 'baoli', 'sol', 'standard', 'correct',
              'right', '暴力')
_GEN_HINTS = ('gen', 'data', 'maker', 'make', 'rand', 'random', 'generator',
              'shuju', '生成', '数据')

_FALLBACK_EXTS = ('cpp', 'cc', 'cxx', 'c', 'py', 'java', 'js', 'mjs', 'pas',
                  'go', 'rs')


def _source_extensions():
    """Every source extension the package knows how to run."""
    exts = set(_FALLBACK_EXTS)
    try:
        for entry in (get_settings().get('run_settings') or []):
            for ext in (entry.get('extensions') or []):
                exts.add(str(ext).lower().lstrip('.'))
    except Exception:
        pass
    return exts


def _candidate_files(directory, kind, exclude=()):
    """Files in `directory` that look like the std / generator program.

    Typing the path of std.cpp and gen.cpp by hand for every run was the
    slowest part of setting a stress test up, and both files almost always
    sit right next to the file under test.
    """
    hints = _STD_HINTS if kind == 'std' else _GEN_HINTS
    exts = _source_extensions()
    skip = set()
    for item in (exclude or ()):
        if item:
            skip.add(os.path.normcase(os.path.abspath(item)))
    hits = []
    try:
        names = sorted(os.listdir(directory))
    except Exception:
        return hits
    for name in names:
        full = os.path.join(directory, name)
        if not os.path.isfile(full):
            continue
        if os.path.splitext(name)[1].lower().lstrip('.') not in exts:
            continue
        if os.path.normcase(os.path.abspath(full)) in skip:
            continue
        stem = os.path.splitext(name)[0].lower()
        for hint in hints:
            if hint in stem:
                hits.append(full)
                break
    # `std.cpp` before `std_old.cpp`: the shortest matching name is the one
    # that was meant.
    hits.sort(key=lambda p: (len(os.path.basename(p)),
                             os.path.basename(p).lower()))
    return hits


def _remembered_file(settings, key):
    """A path from an earlier run, when it still exists."""
    path = settings.get(key) or ''
    if path and os.path.exists(path):
        return [path]
    return []


_PS_OPEN_FILE = """
$ErrorActionPreference = 'SilentlyContinue'
Add-Type -AssemblyName System.Windows.Forms
$dir = [System.Text.Encoding]::UTF8.GetString(
    [System.Convert]::FromBase64String('{dir}'))
$title = [System.Text.Encoding]::UTF8.GetString(
    [System.Convert]::FromBase64String('{title}'))
$dlg = New-Object System.Windows.Forms.OpenFileDialog
if ($dir) {{ $dlg.InitialDirectory = $dir }}
$dlg.Title = $title
$dlg.CheckFileExists = $true
$dlg.Filter = 'Source files (*.cpp;*.cc;*.cxx;*.c;*.py;*.java;*.js)|*.cpp;*.cc;*.cxx;*.c;*.py;*.java;*.js|All files (*.*)|*.*'
$owner = New-Object System.Windows.Forms.Form
$owner.TopMost = $true
$owner.WindowState = 'Minimized'
$owner.ShowInTaskbar = $false
$owner.Show()
$res = $dlg.ShowDialog($owner)
$owner.Dispose()
if ($res -eq [System.Windows.Forms.DialogResult]::OK) {{
    [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
    Write-Output $dlg.FileName
}}
"""


def _native_pick(window, start_dir, title, on_done, on_fallback):
    """The system file dialog, opened in the source file's directory.

    Runs on a worker thread: the dialog can stay open for as long as the user
    likes, and Sublime must not freeze while it does.
    """
    if sublime.platform() != 'windows':
        return False
    import base64
    try:
        script = _PS_OPEN_FILE.format(
            dir=base64.b64encode(start_dir.encode('utf-8')).decode('ascii'),
            title=base64.b64encode(title.encode('utf-8')).decode('ascii'))
        encoded = base64.b64encode(script.encode('utf-16-le')).decode('ascii')
    except Exception:
        return False
    argv = ['powershell', '-NoProfile', '-STA', '-EncodedCommand', encoded]

    def worker():
        picked = ''
        try:
            proc = subprocess.Popen(argv, stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE,
                                    startupinfo=_hidden_startupinfo())
            out, _err = proc.communicate()
            text = (out or b'').decode('utf-8', 'replace').strip()
            if text:
                picked = text.splitlines()[0].strip()
        except Exception:
            picked = ''

        def finish():
            if picked and os.path.exists(picked):
                on_done(picked)
            else:
                on_fallback()
        sublime.set_timeout(finish, 0)

    thread = threading.Thread(target=worker)
    thread.daemon = True
    thread.start()
    return True


def _browse_panel(window, directory, title, on_done):
    """Walk the file system with a quick panel, starting at `directory`."""
    exts = _source_extensions()

    def show(path):
        dirs = []
        files = []
        try:
            names = sorted(os.listdir(path))
        except Exception:
            names = []
        for name in names:
            full = os.path.join(path, name)
            if os.path.isdir(full):
                dirs.append(full)
            elif os.path.splitext(name)[1].lower().lstrip('.') in exts:
                files.append(full)
        entries = list(dirs) + list(files)
        items = [t('stress_browse_up')]
        items += [os.path.basename(d) + '/' for d in dirs]
        items += [os.path.basename(f) for f in files]
        mapping = [None] + entries

        def on_select(index):
            if index < 0 or index >= len(mapping):
                return
            target = mapping[index]
            if target is None:
                parent = os.path.dirname(path.rstrip(os.sep))
                show(parent or path)
            elif os.path.isdir(target):
                show(target)
            else:
                on_done(target)

        window.show_quick_panel(items, on_select)

    show(directory)


def _open_file_dialog(window, start_dir, title, on_done):
    """Pick a file: the system dialog where there is one, a panel otherwise."""
    mode = str(get_settings().get('stress_file_picker', 'auto') or 'auto').lower()

    def fallback():
        _browse_panel(window, start_dir, title, on_done)

    if mode in ('auto', 'native'):
        if _native_pick(window, start_dir, title, on_done, fallback):
            return
    fallback()


def _pick_file(window, start_dir, title, candidates, on_done):
    """One file: an exact hit is used silently, otherwise ask."""
    if len(candidates) == 1:
        on_done(candidates[0])
        return
    if candidates:
        items = [os.path.basename(c) for c in candidates]
        items.append(t('stress_browse_more'))

        def on_select(index):
            if index < 0:
                return
            if index < len(candidates):
                on_done(candidates[index])
            else:
                _open_file_dialog(window, start_dir, title, on_done)
        window.show_quick_panel(items, on_select)
        return
    _open_file_dialog(window, start_dir, title, on_done)


def _open_stress_view(view):
    window = view.window()
    stress_view = None
    for v in window.views():
        if v.name() and v.name().endswith(' -stress'):
            stress_view = v
            break

    if stress_view is None:
        stress_view = window.new_file()
        stress_view.set_name(os.path.basename(view.file_name() or 'stress') + ' -stress')
        stress_view.set_scratch(True)
        stress_view.run_command('set_setting', {'setting': 'word_wrap', 'value': True})
        stress_view.run_command('set_setting', {'setting': 'fold_buttons', 'value': False})
        stress_view.run_command('set_setting', {'setting': 'line_numbers', 'value': False})

    window.focus_view(stress_view)
    stress_view.run_command('select_all')
    stress_view.run_command('left_delete')
    _stress_state['stress_view_id'] = stress_view.id()


def _launch(view, user_file, std_file, gen_file, time_limit, max_rounds):
    _stress_state['running'] = True
    _stress_state['stop_requested'] = False
    set_stress_running(True)
    _stress_state['std_file'] = std_file
    _stress_state['generator_file'] = gen_file
    _stress_state['user_file'] = user_file
    _stress_state['time_limit'] = time_limit
    _stress_state['max_rounds'] = max_rounds
    _stress_state['current_round'] = 0
    _stress_state['last_diff'] = None

    sublime.status_message(t('stress_running'))
    _open_stress_view(view)

    worker = threading.Thread(
        target=_run_stress_loop,
        args=(user_file, std_file, gen_file, time_limit, max_rounds)
    )
    worker.daemon = True
    worker.start()


class CphStartStressTestCommand(sublime_plugin.TextCommand):
    def is_visible(self, event=None, **kwargs):
        """Context menu: only offered where stress testing makes sense."""
        return context_menu_visible(self.view, event)

    def run(self, edit, choose=False):
        _start_flow(self.view, choose)


class CphStressWithOptionsCommand(sublime_plugin.TextCommand):
    """Stress test with the files and the limits chosen by hand.

    The plain command picks std/gen next to the file under test and uses the
    configured limits; this one always asks, for the times the guess is wrong
    or the round count has to change.
    """

    def is_visible(self, event=None, **kwargs):
        if event is not None and not context_menu_enabled():
            return False
        return True

    def run(self, edit):
        _start_flow(self.view, True)


def _start_flow(view, choose=False):
    user_file = view.file_name()
    if not user_file:
        # The stress panel is a scratch view and it takes focus when a
        # run starts, so pressing the key again used to answer "save the
        # file first" instead of restarting the test.
        last = _stress_state.get('user_file')
        if last and os.path.exists(last):
            user_file = last
    if not user_file:
        sublime.error_message(t('save_file_first'))
        return

    # Re-entrancy guard: a second Start used to silently overwrite the
    # state of the loop that is still running.
    if _stress_state.get('running'):
        sublime.status_message('cph-by-chenkx: ' + t('stress_already_running'))
        return

    window = view.window()
    if window is None:
        return
    settings = sublime.load_settings('cph-by-chenkx.sublime-settings')
    src_dir = os.path.dirname(user_file)

    # Look next to the file under test first: that is where the std and the
    # generator of *this* problem live. Only then fall back to what was used
    # last time, which may belong to a completely different problem.
    std_hits = _candidate_files(src_dir, 'std', exclude=[user_file])
    if not std_hits:
        std_hits = _remembered_file(settings, 'stress_std_file')
    gen_hits = _candidate_files(src_dir, 'gen', exclude=[user_file] + std_hits)
    if not gen_hits:
        gen_hits = _remembered_file(settings, 'stress_generator_file')

    def begin(std_file, gen_file):
        if not std_file or not os.path.exists(std_file):
            sublime.error_message(t('file_not_found') + ': ' + str(std_file))
            return
        if not gen_file or not os.path.exists(gen_file):
            sublime.error_message(t('file_not_found') + ': ' + str(gen_file))
            return
        settings.set('stress_std_file', std_file)
        settings.set('stress_generator_file', gen_file)
        sublime.save_settings('cph-by-chenkx.sublime-settings')

        try:
            time_limit = float(get_settings().get('stress_time_limit_seconds', 2) or 2)
        except (TypeError, ValueError):
            time_limit = 2.0
        try:
            max_rounds = int(get_settings().get('stress_max_rounds', 1000) or 1000)
        except (TypeError, ValueError):
            max_rounds = 1000

        if choose:
            ask_limits(window, user_file, std_file, gen_file, time_limit,
                       max_rounds, view)
            return
        sublime.status_message('cph-by-chenkx: %s / %s'
                               % (os.path.basename(std_file),
                                  os.path.basename(gen_file)))
        _launch(view, user_file, std_file, gen_file, time_limit, max_rounds)

    if choose or len(std_hits) != 1 or len(gen_hits) != 1:
        def pick_gen(std_file):
            _pick_file(window, src_dir, t('choose_generator_file'),
                       [g for g in gen_hits
                        if os.path.normcase(g) != os.path.normcase(std_file)],
                       lambda gen_file: begin(std_file, gen_file))

        _pick_file(window, src_dir, t('choose_std_file'), std_hits, pick_gen)
        return

    begin(std_hits[0], gen_hits[0])


def _to_number(text, kind, default):
    try:
        return kind(text)
    except (TypeError, ValueError):
        return default


def ask_limits(window, user_file, std_file, gen_file, time_limit, max_rounds,
               view):
    def on_rounds(value):
        rounds = _to_number((value or '').strip(), int, max_rounds)
        _launch(view, user_file, std_file, gen_file, time_limit, rounds)

    def on_limit(value):
        limit = _to_number((value or '').strip(), float, time_limit)
        if limit <= 0:
            limit = time_limit
        window.show_input_panel(t('stress_max_rounds') + ':', str(max_rounds),
                                on_rounds, None, None)

    window.show_input_panel(t('stress_time_limit') + ' (seconds):',
                            str(time_limit), on_limit, None, None)


class CphStopStressTestCommand(sublime_plugin.TextCommand):
    def is_visible(self, event=None, **kwargs):
        """Only offer 'Stop stress test' while a stress test is running.

        This one is a state gate rather than a file-context gate, so it stays
        correctly hidden in the View menu and the command palette too.
        """
        if event is not None and not context_menu_enabled():
            return False
        return bool(_stress_state.get('running'))

    def run(self, edit):
        if _stress_state['running']:
            _stress_state['stop_requested'] = True
            proc = _stress_state.get('current_proc')
            if proc is not None:
                # Kill the program that is running right now instead of
                # waiting for the round's time limit to expire: with a 10s
                # generator limit, "stop" looked like it did nothing.
                killer = threading.Thread(target=_kill_tree, args=(proc,))
                killer.daemon = True
                killer.start()
            sublime.status_message('cph-by-chenkx: ' + t('process_terminated'))
        else:
            # Nothing is running, but if a panel or the running flag was left
            # behind by an earlier run, clear it so starting works again.
            _finish_stress()
            sublime.status_message('cph-by-chenkx: no stress test running')


def _hidden_startupinfo():
    if sublime.platform() != 'windows':
        return None
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    return startupinfo


def _lang_entry(file):
    """run_settings entry matching this file, or None."""
    run_settings = sublime.load_settings('cph-by-chenkx.sublime-settings') \
        .get('run_settings') or []
    ext = os.path.splitext(file)[1][1:]
    for entry in run_settings:
        if ext in (entry.get('extensions') or []):
            return entry
    return None


def _format_cmd(template, file, drop_args=True):
    src_dir = os.path.dirname(file)
    base = os.path.splitext(os.path.basename(file))[0]
    cmd = template or ''
    # optional multi-file placeholders are meaningless for stress programs
    cmd = cmd.replace('{extra_sources}', '').replace('{include_dirs}', '')
    if drop_args:
        cmd = cmd.replace('{args}', '')
    # Exactly the placeholders ProcessManager.format_command() knows, and
    # just as lenient. {file} is a documented placeholder, and the main Run
    # path accepts it, while stress used to abort with KeyError: 'file'; a
    # misspelled name must only warn (doctor reports it) instead of killing
    # the run.
    values = _LenientFormat({
        'file': os.path.basename(file),
        'source_file': file,
        'source_file_dir': src_dir,
        'file_name': base,
        'args': '',
    })
    return cmd.format_map(values)


def _compile_program(file, time_limit=30):
    """Build a stress-test program using the SAME config as the main flow.

    Previously this was hardcoded to `g++ -std=c++11 -O2`, so the stress
    binary could differ from what the judge-like runner actually builds.

    Returns (ok, path, reason): `reason` is a short explanation for the
    panel when the build failed, instead of a bare "failed to compile".
    """
    entry = _lang_entry(file)
    if entry is None:
        print_safe('[cph-by-chenkx] stress: no run_settings entry for %s' % file)
        return False, None, 'no run_settings entry for this file type'

    if not os.path.exists(file):
        # The compiler only says "No such file or directory" for this, which
        # looks like a broken path rather than an unsaved buffer.
        return False, None, 'the file is not on disk (save it first)'

    src_dir = os.path.dirname(file)
    base = os.path.splitext(os.path.basename(file))[0]
    template = entry.get('compile_cmd')
    if not template:
        # interpreted language (python/java handled by its own run_cmd)
        return True, file, ''

    cmd = _format_cmd(template, file)
    # Build into a scratch directory: the same .exe is the one the user
    # rebuilds by hand, and running it for thousands of rounds made that
    # rebuild fail with "Permission denied" until the run was over.
    out_dir = _build_dir()
    exe_path = None
    if out_dir:
        cmd, exe_path = isolate_output(cmd, out_dir)
    if not exe_path:
        exe_path = output_path_from_compile_cmd(cmd)
        if exe_path and not os.path.isabs(exe_path):
            exe_path = os.path.join(src_dir, exe_path)
    if not exe_path:
        exe_path = os.path.join(
            src_dir, base + ('.exe' if sublime.platform() == 'windows' else ''))
    artifact_dir = os.path.dirname(exe_path) or src_dir

    started_at = time.time()
    try:
        rc, out, err = _popen_capture(cmd, src_dir, shell=True, timeout=time_limit,
                                      abort=_stress_abort)
        if rc != 0:
            print_safe('[cph-by-chenkx] Compile error in %s:\n%s' % (file, err))
            detail = (err or out or '').strip().splitlines()
            return False, None, ('compiler exit code %s%s'
                                 % (rc, (': ' + detail[0][:200]) if detail else ''))
        # A successful compile that wrote nothing (or wrote a different name
        # than the one asked for) used to fail later as "cannot run"; check
        # now so the message points at the real problem.
        real = resolve_artifact(exe_path, artifact_dir, started_at)
        if real is None:
            print_safe('[cph-by-chenkx] stress: %s compiled but %r is missing'
                       % (file, os.path.basename(exe_path)))
            return False, None, ('the compiler produced no %s'
                                 % os.path.basename(exe_path))
        if real != exe_path:
            print_safe('[cph-by-chenkx] stress: binary of %s is %r on disk'
                       % (base, os.path.basename(real)))
        return True, real, ''
    except _Aborted:
        # Stopped while the compiler was running: say the run was stopped,
        # not that the program failed to build.
        raise
    except Exception as e:
        print_safe('[cph-by-chenkx] Compile error: %s' % str(e))
        return False, None, str(e)[:200]


def _kill_tree(proc):
    """Kill a program and everything it started.

    With `shell=True` the direct child is cmd.exe, so a plain kill leaves the
    compiler running; it then keeps holding the .exe it was writing, which is
    what made a rebuild fail with "Permission denied" afterwards.
    """
    try:
        pid = proc.pid
    except Exception:
        return
    if pid is None:
        return
    if sublime.platform() == 'windows':
        try:
            killer = subprocess.Popen(
                ['taskkill', '/F', '/T', '/PID', str(pid)],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                startupinfo=_hidden_startupinfo())
            killer.wait(timeout=3)
            return
        except Exception:
            pass
    try:
        proc.kill()
    except Exception:
        pass


def _drain(stream, sink):
    try:
        while True:
            chunk = stream.read(8192)
            if not chunk:
                break
            sink.append(chunk)
    except Exception:
        pass


def _feed(proc, data):
    try:
        proc.stdin.write(data)
        proc.stdin.flush()
    except Exception:
        pass
    finally:
        try:
            proc.stdin.close()
        except Exception:
            pass


def _communicate_abortable(proc, data, timeout, abort):
    """Read a program's output while staying able to kill it early.

    Popen.communicate(timeout) cannot do this: it kills the process itself as
    soon as the timeout expires and cannot be resumed, so pressing Stop had
    to wait out the whole time limit of the round that was running. Draining
    the pipes on reader threads and polling the process keeps the decision
    here. Raises subprocess.TimeoutExpired / _Aborted.
    """
    out_parts = []
    err_parts = []
    threads = []
    if proc.stdout is not None:
        th = threading.Thread(target=_drain, args=(proc.stdout, out_parts))
        th.daemon = True
        th.start()
        threads.append(th)
    if proc.stderr is not None:
        th = threading.Thread(target=_drain, args=(proc.stderr, err_parts))
        th.daemon = True
        th.start()
        threads.append(th)
    feeder = None
    if data is not None and proc.stdin is not None:
        feeder = threading.Thread(target=_feed, args=(proc, data))
        feeder.daemon = True
        feeder.start()

    deadline = (time.time() + timeout) if timeout and timeout > 0 else None
    timed_out = False
    aborted = False
    while proc.poll() is None:
        if abort is not None and abort():
            aborted = True
            _kill_tree(proc)
            break
        if deadline is not None and time.time() >= deadline:
            timed_out = True
            _kill_tree(proc)
            break
        time.sleep(0.02)
    try:
        proc.wait()
    except Exception:
        pass
    for th in threads:
        th.join(timeout=2)
    if feeder is not None:
        feeder.join(timeout=2)
    if timed_out:
        raise subprocess.TimeoutExpired(getattr(proc, 'args', ''), timeout)
    if aborted:
        raise _Aborted()
    return b''.join(out_parts), b''.join(err_parts)


def _stress_abort():
    return bool(_stress_state.get('stop_requested'))


def _popen_capture(cmd, cwd, input_text=None, shell=False, timeout=30, env=None,
                   abort=None):
    """Run a command and capture its output as text.

    Uses Popen instead of subprocess.run: Sublime's plugin host is Python
    3.3, which has no subprocess.run (3.5+) and no text/encoding arguments
    (3.6/3.7+). Raises subprocess.TimeoutExpired on timeout, _Aborted when
    `abort()` turns true while the command is still running.
    """
    if env:
        # Extra variables (the stress seed) on top of the inherited ones.
        merged = dict(os.environ)
        merged.update(env)
    else:
        merged = None
    proc = subprocess.Popen(
        cmd,
        cwd=cwd,
        shell=shell,
        env=merged,
        stdin=subprocess.PIPE if input_text is not None else None,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        startupinfo=_hidden_startupinfo()
    )
    _stress_state['current_proc'] = proc
    data = input_text.encode('utf-8', 'replace') if isinstance(input_text, str) else input_text
    try:
        out, err = _communicate_abortable(proc, data, timeout, abort)
    finally:
        _stress_state['current_proc'] = None
    return (proc.returncode,
            (out or b'').decode('utf-8', 'replace'),
            (err or b'').decode('utf-8', 'replace'))


def _program_argv(file):
    """Command line to run a program, taken from run_settings.run_cmd."""
    entry = _lang_entry(file)
    if entry is None:
        return None
    run_cmd = entry.get('run_cmd')
    if not run_cmd:
        return None
    cmd = _format_cmd(run_cmd, file)
    windows = (sublime.platform() == 'windows')
    try:
        parts = shlex.split(cmd, posix=not windows)
    except Exception:
        return [cmd]
    if windows:
        # posix=False keeps the surrounding quotes: strip them, otherwise
        # the path would be passed to CreateProcess with literal quotes.
        cleaned = []
        for p in parts:
            if len(p) > 1 and p[0] == '"' and p[-1] == '"':
                p = p[1:-1]
            cleaned.append(p)
        parts = cleaned
    if parts:
        # The compiler may have written the binary under a different name
        # (non-ASCII -o names go through the ANSI codepage on Windows), which
        # used to make every round fail with "cannot run".
        parts[0] = retarget_path(parts[0], os.path.dirname(file))
    return parts


def _run_program(program, input_data, cwd=None, time_limit=2.0, env=None):
    """Run a program with the run_settings command; program is a source file."""
    argv = _program_argv(program) if not isinstance(program, list) else program
    if not argv:
        return (-1, '', 'no run command configured', False)
    if cwd is None:
        cwd = os.path.dirname(program if isinstance(program, str) else argv[0])
    try:
        rc, out, err = _popen_capture(argv, cwd, input_text=input_data,
                                     timeout=time_limit, env=env,
                                     abort=_stress_abort)
        return (rc, out, err, False)
    except subprocess.TimeoutExpired:
        return (-1, '', '', True)
    except _Aborted:
        # Stop was pressed: let the loop wind down instead of reporting this
        # round as a timeout.
        raise
    except Exception as e:
        return (-1, '', str(e), False)


def _build_dir():
    """A fresh scratch directory for one stress binary."""
    root = _stress_state.get('build_root')
    if not root:
        return None
    seq = _stress_state.get('build_seq', 0) + 1
    _stress_state['build_seq'] = seq
    path = os.path.join(root, str(seq))
    try:
        os.makedirs(path)
        return path
    except Exception:
        return None


def _program_command(exe, source_file):
    """argv for one stress program, or None to go through run_cmd.

    Compiled languages run the binary that was just built; interpreted ones
    (Python) have no binary and keep using their run command.
    """
    if exe and os.path.normcase(exe) != os.path.normcase(source_file):
        return [exe]
    return None


def _finish_stress():
    """Release everything a run owned, whether it ended or was stopped."""
    root = _stress_state.get('build_root')
    if root:
        try:
            shutil.rmtree(root, ignore_errors=True)
        except Exception:
            pass
    _stress_state['build_root'] = None
    _stress_state['build_seq'] = 0
    _stress_state['current_proc'] = None
    _stress_state['current_round'] = 0
    _stop_stress()


def _run_stress_loop(user_file, std_file, gen_file, time_limit, max_rounds):
    wall_start = time.time()
    _stress_state['build_seq'] = 0
    _stress_state['build_root'] = None
    try:
        # Every stress binary gets its own scratch directory, so the .exe in
        # the source directory stays free for the user to rebuild.
        _stress_state['build_root'] = tempfile.mkdtemp(prefix='cph-stress-')
    except Exception:
        _stress_state['build_root'] = None
    try:
        sublime.set_timeout(
            lambda: _append_stress('[cph-by-chenkx] Compiling programs...\n'), 0)

        ok1, user_exe, why1 = _compile_program(user_file)
        if not ok1:
            sublime.set_timeout(
                lambda w=why1: _append_stress(
                    '[cph-by-chenkx] Failed to compile user program: '
                    + os.path.basename(user_file) + (': ' + w if w else '') + '\n'), 0)
            _stop_stress()
            return

        ok2, std_exe, why2 = _compile_program(std_file)
        if not ok2:
            sublime.set_timeout(
                lambda w=why2: _append_stress(
                    '[cph-by-chenkx] Failed to compile std: '
                    + os.path.basename(std_file) + (': ' + w if w else '') + '\n'), 0)
            _stop_stress()
            return

        ok3, gen_exe, why3 = _compile_program(gen_file)
        if not ok3:
            sublime.set_timeout(
                lambda w=why3: _append_stress(
                    '[cph-by-chenkx] Failed to compile generator: '
                    + os.path.basename(gen_file) + (': ' + w if w else '') + '\n'), 0)
            _stop_stress()
            return

        # Run the binaries that were just built instead of looking the run
        # command up again every round, and keep the working directory of the
        # source file (programs often read files next to it).
        user_argv = _program_command(user_exe, user_file)
        std_argv = _program_command(std_exe, std_file)
        gen_argv = _program_command(gen_exe, gen_file)
        user_cwd = os.path.dirname(user_file) or None
        std_cwd = os.path.dirname(std_file) or None
        gen_cwd = os.path.dirname(gen_file) or None

        # The generator is allowed to take longer than the program under
        # test: producing a large sample is not the same as solving it.
        try:
            generator_limit = float(
                get_settings().get('stress_generator_time_limit_seconds', 10) or 10)
        except (TypeError, ValueError):
            generator_limit = 10.0
        if generator_limit <= 0:
            generator_limit = 10.0

        # Multi-solution problems: comparing the two outputs line by line
        # reports a difference on almost every round even though both are
        # valid. When a checker is configured it decides instead.
        checker_cfg = cph_checker.config(
            (get_settings().get('run_settings') or []), user_file, get_settings())
        checker_exe = None
        if checker_cfg is not None:
            exe, why = cph_checker.executable(checker_cfg)
            if not exe:
                sublime.set_timeout(
                    lambda w=why: _append_stress(
                        '[cph-by-chenkx] Failed to build checker: %s\n' % w), 0)
                _stop_stress()
                return
            checker_exe = exe

        try:
            float_tol = float(get_settings().get('float_tolerance', 0) or 0)
        except (TypeError, ValueError):
            float_tol = 0.0

        started_extra = ''
        if checker_exe is not None:
            started_extra += '  checker: %s (%s)\n' % (
                os.path.basename(str(checker_cfg.get('path') or '')),
                checker_cfg.get('style') or 'testlib')
        elif float_tol > 0:
            started_extra += '  float tolerance: %g\n' % float_tol

        sublime.set_timeout(
            lambda: _append_stress(
                '[cph-by-chenkx] Stress test started\n'
                '  user: %s\n  std:  %s\n  gen:  %s\n'
                '  time limit: %ss/round, generator limit: %ss, max rounds: %d\n'
                '%s\n'
                % (os.path.basename(user_file), os.path.basename(std_file),
                   os.path.basename(gen_file), time_limit, generator_limit,
                   max_rounds, started_extra)
            ), 0)

        try:
            wall_limit = float(get_settings().get('stress_max_wall_seconds', 0) or 0)
        except (TypeError, ValueError):
            wall_limit = 0.0

        round_count = 0
        compared = 0
        gen_timeouts = 0
        tle_hint_shown = False
        for round_count in range(1, max_rounds + 1):
            if _stress_state['stop_requested']:
                sublime.set_timeout(
                    lambda: _append_stress('\n[cph-by-chenkx] ' + t('process_terminated') + ' at round %d\n' % round_count), 0)
                break
            if wall_limit > 0 and time.time() - wall_start >= wall_limit:
                # A run that is still going after this long is not going to
                # finish any time soon; say so instead of hanging.
                sublime.set_timeout(
                    lambda l=wall_limit: _append_stress(
                        '\n[cph-by-chenkx] ' + t('stress_wall_limit', limit=l) + '\n'), 0)
                break
            if round_count == 1 or round_count % 10 == 0:
                # Without this there is no way to tell a slow run from a hung
                # one, which is what "it never ends" looked like.
                sublime.set_timeout(
                    lambda r=round_count: sublime.status_message(
                        'cph-by-chenkx: ' + t('stress_round', round=r)
                        + ' / %d' % max_rounds), 0)

            _stress_state['current_round'] = round_count
            # A fresh seed per round, handed to the generator through the
            # environment (CPH_SEED) so a counterexample can be replayed:
            # "found a counterexample" is only actionable when you can make
            # the generator produce exactly that test again.
            seed = random.randrange(1, 2147483647)
            _stress_state['current_seed'] = seed

            # The generator gets its own, larger budget. Generating the test
            # is legitimately slower than solving it, and measuring it with
            # the program's limit made a correct setup stop at
            # "Generator failed at round 1" (a timeout was reported as a
            # failure because the TLE flag was dropped here).
            ret, inp, gen_err, gen_tle = _run_program(
                gen_argv or gen_file, '', cwd=gen_cwd,
                time_limit=generator_limit,
                env={'CPH_SEED': str(seed)})
            if gen_tle:
                gen_timeouts += 1
                sublime.set_timeout(
                    lambda r=round_count, l=generator_limit: _append_stress(
                        '[cph-by-chenkx] ' + t('stress_generator_tle', round=r, limit=l) + '\n'), 0)
                if gen_timeouts >= 3:
                    sublime.set_timeout(
                        lambda l=generator_limit: _append_stress(
                            '[cph-by-chenkx] ' + t('stress_generator_limit_hint', limit=l) + '\n'), 0)
                    break
                continue
            if ret != 0:
                # Say *why*: exit code plus whatever the generator printed.
                sublime.set_timeout(
                    lambda r=round_count, rc=ret, e=gen_err: _append_stress(
                        '[cph-by-chenkx] ' + t('stress_generator_failed', round=r, code=rc)
                        + ('\n  ' + e.strip()[:500] if e.strip() else '') + '\n'), 0)
                break

            ret1, user_out, user_err, tle1 = _run_program(
                user_argv or user_file, inp, cwd=user_cwd, time_limit=time_limit)
            if tle1:
                sublime.set_timeout(
                    lambda r=round_count: _append_stress(
                        '[cph-by-chenkx] Round %d: user program TLE\n' % r), 0)
                if not tle_hint_shown:
                    # By far the most common cause on a correct solution: the
                    # compile command defines LOCAL, so a debug macro left
                    # inside the main loop prints O(n^2) of stderr. Saying it
                    # once saves a long hunt (and a stderr dump would be huge).
                    tle_hint_shown = True
                    sublime.set_timeout(
                        lambda: _append_stress(
                            '[cph-by-chenkx] ' + t('stress_tle_hint') + '\n'), 0)
                continue
            if ret1 < 0 and user_err:
                # The program never started (missing binary, bad command):
                # comparing its empty output as a wrong answer hid this.
                sublime.set_timeout(
                    lambda e=user_err: _append_stress(
                        '[cph-by-chenkx] ' + t('stress_cannot_run',
                                               program=os.path.basename(user_file),
                                               reason=e.strip()[:300]) + '\n'), 0)
                break

            ret2, std_out, std_err, tle2 = _run_program(
                std_argv or std_file, inp, cwd=std_cwd, time_limit=time_limit)
            if tle2:
                sublime.set_timeout(
                    lambda r=round_count: _append_stress(
                        '[cph-by-chenkx] Round %d: std program TLE\n' % r), 0)
                continue
            if ret2 < 0 and std_err:
                sublime.set_timeout(
                    lambda e=std_err: _append_stress(
                        '[cph-by-chenkx] ' + t('stress_cannot_run',
                                               program=os.path.basename(std_file),
                                               reason=e.strip()[:300]) + '\n'), 0)
                break

            compared += 1
            checker_msg = ''
            if checker_exe is not None:
                # Both answers can be valid: let the checker decide.
                res = cph_checker.judge(checker_cfg, checker_exe, inp,
                                        user_out, std_out)
                is_diff = not res.get('ok')
                checker_msg = (res.get('message') or '').strip()
            else:
                # Same comparison rules as the judge-like runner (whitespace
                # insensitive) plus the configured float tolerance, so a
                # floating point problem no longer "fails" on the last digit.
                is_diff = not outputs_equal(user_out, std_out, float_tol)

            if is_diff:
                _stress_state['last_diff'] = {
                    'round': round_count,
                    'input': inp,
                    'user_output': user_out,
                    'std_output': std_out,
                    'checker_message': checker_msg,
                }
                sublime.set_timeout(
                    lambda m=checker_msg: _on_stress_failed(
                        round_count, inp, user_out, std_out, m), 0)
                break

            if round_count <= 10 or round_count % 10 == 0:
                sublime.set_timeout(
                    lambda r=round_count: _append_stress(
                        t('stress_round', round=r) + ' ... OK\n'
                    ), 0)

        else:
            if compared:
                sublime.set_timeout(
                    lambda: _append_stress(
                        '\n[cph-by-chenkx] ' + t('stress_passed', rounds=round_count) + '\n'
                    ), 0)
            else:
                # Every round hit `continue` (TLE), so nothing was ever
                # compared: the for/else used to still announce "passed".
                sublime.set_timeout(
                    lambda: _append_stress(
                        '\n[cph-by-chenkx] ' + t('stress_all_timeout') + '\n'
                    ), 0)
        # Always say the run is over: a panel that just stopped growing is
        # what "it never ends" looked like.
        elapsed = time.time() - wall_start
        sublime.set_timeout(
            lambda e=elapsed: _append_stress(
                '\n[cph-by-chenkx] ' + t('stress_finished', seconds='%.1f' % e) + '\n'
            ), 0)
        sublime.set_timeout(
            lambda e=elapsed: sublime.status_message(
                'cph-by-chenkx: ' + t('stress_finished', seconds='%.1f' % e)), 0)
    except _Aborted:
        sublime.set_timeout(
            lambda: _append_stress('\n[cph-by-chenkx] ' + t('process_terminated') + '\n'), 0)
    except Exception as e:
        # Bind `e` as a default argument: Python deletes the except-variable
        # when the block ends, so a bare `lambda: ... % e` raised NameError
        # by the time the deferred callback actually ran (the message never
        # appeared and the real error was swallowed).
        sublime.set_timeout(
            lambda e=e: _append_stress('[cph-by-chenkx] Error: %s\n' % str(e)), 0)
    finally:
        _finish_stress()


def _stop_stress():
    _stress_state['running'] = False
    _stress_state['stop_requested'] = False
    set_stress_running(False)


def _append_stress(text):
    if 'stress_view_id' not in _stress_state:
        return
    for window in sublime.windows():
        for v in window.views():
            if v.id() == _stress_state.get('stress_view_id'):
                v.run_command('append', {'characters': text})
                v.show(v.size())
                return


def _on_stress_failed(round_count, inp, user_out, std_out, checker_message=''):
    # Keep everything needed to reproduce this counterexample later
    # ('Stress: replay last counterexample').
    _stress_state['last_counterexample'] = {
        'seed': _stress_state.get('current_seed'),
        'input': inp,
        'user_out': user_out,
        'std_out': std_out,
        'round': round_count,
    }

    text = '\n' + '=' * 60 + '\n'
    text += '[cph-by-chenkx] ' + t('stress_failed', round=round_count) + '\n'
    text += '=' * 60 + '\n\n'
    seed = _stress_state.get('current_seed')
    if seed is not None:
        # Without the seed the counterexample cannot be regenerated; say it
        # out loud so it can be replayed (or set CPH_SEED by hand).
        text += '[cph-by-chenkx] ' + t('stress_seed', seed=seed) + '\n\n'
    if checker_message:
        # testlib's quitf message: the only explanation of *why* the two
        # outputs are not both valid.
        text += '[cph-by-chenkx] ' + t('stress_checker_message',
                                       message=checker_message[:500]) + '\n\n'
    text += '[' + t('stress_input') + ']\n'
    text += inp + '\n'
    text += '\n[' + t('stress_user_output') + ']\n'
    text += user_out + '\n'
    text += '\n[' + t('stress_std_output') + ']\n'
    text += std_out + '\n'
    text += '\n[' + t('stress_diff') + ']\n'
    user_lines = user_out.splitlines()
    std_lines = std_out.splitlines()
    max_lines = max(len(user_lines), len(std_lines))
    for i in range(max_lines):
        u = user_lines[i] if i < len(user_lines) else ''
        s = std_lines[i] if i < len(std_lines) else ''
        if u != s:
            text += 'Line %d:\n' % (i + 1)
            text += '  user: %s\n' % u
            text += '  std:  %s\n' % s

    # Save the counterexample as a permanent test case: finding a
    # counterexample is only useful if it comes back as a regression test.
    try:
        if get_settings().get('stress_save_counterexample', True):
            user_file = _stress_state.get('user_file')
            if user_file:
                answer = std_out.strip()
                merged, _conflicts = merge_tests(load_all_tests(user_file), [{
                    'test': inp,
                    'correct_answers': [answer] if answer else [],
                    # Keep the generator seed with the counterexample so
                    # 'Stress: replay last seed' can reproduce it exactly.
                    'seed': _stress_state.get('current_seed')}])
                if save_tests(user_file, merged):
                    text += '\n[cph-by-chenkx] ' + \
                        t('stress_counterexample_added', total=len(merged)) + '\n'
    except Exception as e:
        print_safe('[cph-by-chenkx] failed to save counterexample: %s' % e)

    _append_stress(text)
    _stop_stress()


class CphStressReplayCommand(sublime_plugin.TextCommand):
	"""Re-run the last counterexample from its recorded generator seed.

	The stress loop hands the generator a fresh seed every round (CPH_SEED) and
	stores it with the counterexample, so the exact failing test can be
	reproduced instead of hoping the random search hits it again.
	"""

	def run(self, edit):
		state = _stress_state.get('last_counterexample')
		if not state or state.get('seed') is None:
			sublime.status_message('[cph-by-chenkx] ' + t('stress_no_counterexample'))
			return
		gen_file = get_settings().get('stress_generator_file') or _stress_state.get('gen_file')
		user_file = _stress_state.get('user_file')
		std_file = get_settings().get('stress_std_file') or _stress_state.get('std_file')
		if not (gen_file and user_file and std_file):
			sublime.status_message('[cph-by-chenkx] ' + t('stress_no_counterexample'))
			return

		seed = state['seed']
		_append_stress('\n[cph-by-chenkx] ' + t('stress_replaying', seed=seed) + '\n')

		def worker():
			try:
				ok, gen_exe, why = _compile_program(gen_file)
				if not ok:
					_append_stress('[cph-by-chenkx] generator: %s\n' % (why or 'failed'))
					return
				rc, inp, err, tle = _run_program(
					gen_exe, '', time_limit=float(
						get_settings().get('stress_generator_time_limit_seconds', 10) or 10),
					env={'CPH_SEED': str(seed)})
				if rc != 0 or tle:
					_append_stress('[cph-by-chenkx] generator failed: rc=%s %s\n'
								   % (rc, err[:200]))
					return
				_append_stress('[cph-by-chenkx] regenerated %d bytes\n' % len(inp))
				ok1, user_exe, why1 = _compile_program(user_file)
				ok2, std_exe, why2 = _compile_program(std_file)
				if not (ok1 and ok2):
					_append_stress('[cph-by-chenkx] compile failed: %s%s\n'
								   % (why1 or '', why2 or ''))
					return
				limit = float(get_settings().get('stress_time_limit_seconds', 2) or 2)
				_rc1, user_out, _e1, tle1 = _run_program(user_exe, inp, time_limit=limit)
				_rc2, std_out, _e2, _tle2 = _run_program(std_exe, inp, time_limit=limit)
				if tle1:
					_append_stress('[cph-by-chenkx] ' + t('stress_replay_tle') + '\n')
					return
				if normalize_lines(user_out) == normalize_lines(std_out):
					_append_stress('[cph-by-chenkx] ' + t('stress_replay_same') + '\n')
				else:
					_on_stress_failed(state.get('round') or 0, inp, user_out, std_out)
			except Exception as e:
				_append_stress('[cph-by-chenkx] replay error: %s\n' % e)

		thread = threading.Thread(target=worker)
		thread.daemon = True
		thread.start()
