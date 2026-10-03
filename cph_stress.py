"""
cph-by-chenkx - 对拍 (Stress Test) 功能
"""

import sublime
import sublime_plugin
import os
import re
import shlex
import subprocess
import threading
import time
from os import path

from .core.cph_settings import base_name, get_settings, root_dir, load_all_tests, save_tests
from .core.cph_tests_merge import merge_tests
from .core.cph_state import set_stress_running
from .core.cph_i18n import t
from .core.cph_verdict import normalize_lines
from .Highlight.test_interface import get_test_styles


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
}


class CphStartStressTestCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        user_file = self.view.file_name()
        if not user_file:
            sublime.error_message(t('save_file_first'))
            return

        settings = sublime.load_settings('cph-by-chenkx.sublime-settings')
        saved_std = settings.get('stress_std_file', '')
        saved_gen = settings.get('stress_generator_file', '')

        # Re-entrancy guard: a second Start used to silently overwrite the
        # state of the loop that is still running.
        if _stress_state.get('running'):
            sublime.status_message('cph-by-chenkx: ' + t('stress_already_running'))
            return

        src_dir = os.path.dirname(user_file)
        default_std = saved_std if saved_std and os.path.exists(saved_std) else \
                      os.path.join(src_dir, 'std.cpp')
        default_gen = saved_gen if saved_gen and os.path.exists(saved_gen) else \
                      os.path.join(src_dir, 'gen.cpp')

        window = self.view.window()
        window.show_input_panel(
            t('choose_std_file') + ' (default: ' + os.path.basename(default_std) + '):',
            default_std,
            lambda s: self._on_std(s.strip(), default_gen, user_file, window),
            None, None
        )

    def _on_std(self, std_file, default_gen, user_file, window):
        if not std_file:
            std_file = os.path.join(os.path.dirname(user_file), 'std.cpp')
        if not os.path.exists(std_file):
            sublime.error_message(t('file_not_found') + ': ' + std_file)
            return
        window.show_input_panel(
            t('choose_generator_file') + ' (default: ' + os.path.basename(default_gen) + '):',
            default_gen,
            lambda s: self._on_gen(s.strip(), default_gen, user_file, std_file, window),
            None, None
        )

    def _on_gen(self, gen_file, default_gen, user_file, std_file, window):
        if not gen_file:
            gen_file = default_gen
        if not os.path.exists(gen_file):
            sublime.error_message(t('file_not_found') + ': ' + gen_file)
            return

        settings = sublime.load_settings('cph-by-chenkx.sublime-settings')
        settings.set('stress_std_file', std_file)
        settings.set('stress_generator_file', gen_file)
        sublime.save_settings('cph-by-chenkx.sublime-settings')

        window.show_input_panel(
            t('stress_time_limit') + ' (seconds):',
            str(get_settings().get('stress_time_limit_seconds', 2)),
            lambda s: self._on_time(s.strip(), user_file, std_file, gen_file, window),
            None, None
        )

    def _on_time(self, time_str, user_file, std_file, gen_file, window):
        try:
            time_limit = float(time_str)
        except ValueError:
            time_limit = 2.0

        window.show_input_panel(
            t('stress_max_rounds') + ':',
            '1000',
            lambda s: self._start(s.strip(), user_file, std_file, gen_file, time_limit),
            None, None
        )

    def _start(self, rounds_str, user_file, std_file, gen_file, time_limit):
        try:
            max_rounds = int(rounds_str)
        except ValueError:
            max_rounds = 1000

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
        self._open_stress_view()

        t_thread = threading.Thread(
            target=_run_stress_loop,
            args=(user_file, std_file, gen_file, time_limit, max_rounds)
        )
        t_thread.daemon = True
        t_thread.start()

    def _open_stress_view(self):
        window = self.view.window()
        stress_view = None
        for v in window.views():
            if v.name() and v.name().endswith(' -stress'):
                stress_view = v
                break

        if stress_view is None:
            stress_view = window.new_file()
            stress_view.set_name(os.path.basename(self.view.file_name() or 'stress') + ' -stress')
            stress_view.set_scratch(True)
            stress_view.run_command('set_setting', {'setting': 'word_wrap', 'value': True})
            stress_view.run_command('set_setting', {'setting': 'fold_buttons', 'value': False})
            stress_view.run_command('set_setting', {'setting': 'line_numbers', 'value': False})

        window.focus_view(stress_view)
        stress_view.run_command('select_all')
        stress_view.run_command('left_delete')
        _stress_state['stress_view_id'] = stress_view.id()


class CphStopStressTestCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        if _stress_state['running']:
            _stress_state['stop_requested'] = True
            sublime.status_message('cph-by-chenkx: ' + t('process_terminated'))
        else:
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
    return cmd.format(source_file=file, source_file_dir=src_dir, file_name=base, args='')


def _compile_program(file, time_limit=30):
    """Build a stress-test program using the SAME config as the main flow.

    Previously this was hardcoded to `g++ -std=c++11 -O2`, so the stress
    binary could differ from what the judge-like runner actually builds.
    """
    entry = _lang_entry(file)
    if entry is None:
        print('[cph-by-chenkx] stress: no run_settings entry for %s' % file)
        return False, None

    src_dir = os.path.dirname(file)
    base = os.path.splitext(os.path.basename(file))[0]
    template = entry.get('compile_cmd')
    if not template:
        # interpreted language (python/java handled by its own run_cmd)
        return True, file

    cmd = _format_cmd(template, file)
    m = re.search(r'-o\s+"?([^"\s]+)"?', cmd)
    if m:
        out_name = m.group(1)
        exe_path = out_name if os.path.isabs(out_name) else os.path.join(src_dir, out_name)
    else:
        exe_path = os.path.join(
            src_dir, base + ('.exe' if sublime.platform() == 'windows' else ''))

    try:
        rc, out, err = _popen_capture(cmd, src_dir, shell=True, timeout=time_limit)
        if rc != 0:
            print('[cph-by-chenkx] Compile error in %s:\n%s' % (file, err))
            return False, None
        return True, exe_path
    except Exception as e:
        print('[cph-by-chenkx] Compile error: %s' % str(e))
        return False, None


def _popen_capture(cmd, cwd, input_text=None, shell=False, timeout=30):
    """Run a command and capture its output as text.

    Uses Popen instead of subprocess.run: Sublime's plugin host is Python
    3.3, which has no subprocess.run (3.5+) and no text/encoding arguments
    (3.6/3.7+). Raises subprocess.TimeoutExpired on timeout.
    """
    proc = subprocess.Popen(
        cmd,
        cwd=cwd,
        shell=shell,
        stdin=subprocess.PIPE if input_text is not None else None,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        startupinfo=_hidden_startupinfo()
    )
    data = input_text.encode('utf-8', 'replace') if isinstance(input_text, str) else input_text
    try:
        out, err = proc.communicate(input=data, timeout=timeout)
    except subprocess.TimeoutExpired:
        try:
            proc.kill()
            proc.communicate()
        except Exception:
            pass
        raise
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
    return parts


def _run_program(program, input_data, cwd=None, time_limit=2.0):
    """Run a program with the run_settings command; program is a source file."""
    argv = _program_argv(program) if not isinstance(program, list) else program
    if not argv:
        return (-1, '', 'no run command configured', False)
    if cwd is None:
        cwd = os.path.dirname(program if isinstance(program, str) else argv[0])
    try:
        rc, out, err = _popen_capture(argv, cwd, input_text=input_data,
                                     timeout=time_limit)
        return (rc, out, err, False)
    except subprocess.TimeoutExpired:
        return (-1, '', '', True)
    except Exception as e:
        return (-1, '', str(e), False)


def _run_stress_loop(user_file, std_file, gen_file, time_limit, max_rounds):
    try:
        sublime.set_timeout(
            lambda: _append_stress('[cph-by-chenkx] Compiling programs...\n'), 0)

        ok1, user_exe = _compile_program(user_file)
        if not ok1:
            sublime.set_timeout(
                lambda: _append_stress('[cph-by-chenkx] Failed to compile user program: ' + user_file + '\n'), 0)
            _stop_stress()
            return

        ok2, std_exe = _compile_program(std_file)
        if not ok2:
            sublime.set_timeout(
                lambda: _append_stress('[cph-by-chenkx] Failed to compile std: ' + std_file + '\n'), 0)
            _stop_stress()
            return

        ok3, gen_exe = _compile_program(gen_file)
        if not ok3:
            sublime.set_timeout(
                lambda: _append_stress('[cph-by-chenkx] Failed to compile generator: ' + gen_file + '\n'), 0)
            _stop_stress()
            return

        sublime.set_timeout(
            lambda: _append_stress(
                '[cph-by-chenkx] Stress test started\n'
                '  user: %s\n  std:  %s\n  gen:  %s\n'
                '  time limit: %ss/round, max rounds: %d\n\n'
                % (os.path.basename(user_file), os.path.basename(std_file),
                   os.path.basename(gen_file), time_limit, max_rounds)
            ), 0)

        round_count = 0
        compared = 0
        for round_count in range(1, max_rounds + 1):
            if _stress_state['stop_requested']:
                sublime.set_timeout(
                    lambda: _append_stress('\n[cph-by-chenkx] ' + t('process_terminated') + ' at round %d\n' % round_count), 0)
                break

            _stress_state['current_round'] = round_count

            ret, inp, _, _ = _run_program(gen_file, '', time_limit=time_limit)
            if ret != 0:
                sublime.set_timeout(
                    lambda r=round_count: _append_stress(
                        '[cph-by-chenkx] Generator failed at round %d\n' % r), 0)
                break

            ret1, user_out, _, tle1 = _run_program(user_file, inp, time_limit=time_limit)
            if tle1:
                sublime.set_timeout(
                    lambda r=round_count: _append_stress(
                        '[cph-by-chenkx] Round %d: user program TLE\n' % r), 0)
                continue

            ret2, std_out, _, tle2 = _run_program(std_file, inp, time_limit=time_limit)
            if tle2:
                sublime.set_timeout(
                    lambda r=round_count: _append_stress(
                        '[cph-by-chenkx] Round %d: std program TLE\n' % r), 0)
                continue

            compared += 1
            # Same comparison rules as the judge-like runner (ignore trailing
            # whitespace per line and trailing blank lines).
            is_diff = normalize_lines(user_out) != normalize_lines(std_out)

            if is_diff:
                _stress_state['last_diff'] = {
                    'round': round_count,
                    'input': inp,
                    'user_output': user_out,
                    'std_output': std_out,
                }
                sublime.set_timeout(
                    lambda: _on_stress_failed(round_count, inp, user_out, std_out), 0)
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
    except Exception as e:
        # Bind `e` as a default argument: Python deletes the except-variable
        # when the block ends, so a bare `lambda: ... % e` raised NameError
        # by the time the deferred callback actually ran (the message never
        # appeared and the real error was swallowed).
        sublime.set_timeout(
            lambda e=e: _append_stress('[cph-by-chenkx] Error: %s\n' % str(e)), 0)
    finally:
        _stop_stress()


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


def _on_stress_failed(round_count, inp, user_out, std_out):
    text = '\n' + '=' * 60 + '\n'
    text += '[cph-by-chenkx] ' + t('stress_failed', round=round_count) + '\n'
    text += '=' * 60 + '\n\n'
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
                    'correct_answers': [answer] if answer else []}])
                if save_tests(user_file, merged):
                    text += '\n[cph-by-chenkx] ' + \
                        t('stress_counterexample_added', total=len(merged)) + '\n'
    except Exception as e:
        print('[cph-by-chenkx] failed to save counterexample: %s' % e)

    _append_stress(text)
    _stop_stress()
