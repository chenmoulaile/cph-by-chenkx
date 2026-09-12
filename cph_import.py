"""
cph-by-chenkx - 从文件导入测试数据
"""

import sublime
import sublime_plugin
import os
import re
from os import path

from .cph_settings import base_name, get_settings, root_dir, save_tests
from .cph_i18n import t


class CphImportTestsCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        window = self.view.window()
        if not window:
            return

        options = [
            [t('import_from_pair'), t('import_from_pair_desc')],
            [t('import_from_single'), t('import_from_single_desc')],
            [t('import_from_cphng'), t('import_from_cphng_desc')],
        ]

        def on_select(idx):
            if idx == 0:
                self._import_from_pair(window)
            elif idx == 1:
                self._import_from_single(window)
            elif idx == 2:
                self._import_from_cphng(window)

        window.show_quick_panel(options, on_select)

    def _import_from_pair(self, window):
        src_file = self.view.file_name()
        if not src_file:
            sublime.status_message(t('save_file_first'))
            return

        src_dir = os.path.dirname(src_file)

        def on_done(input_path):
            if not input_path:
                return
            candidates = self._find_output_for_input(input_path)
            if not candidates:
                sublime.status_message(t('output_file_not_found'))
                self._import_input_only(input_path, None)
                return

            if len(candidates) == 1:
                self._do_import(input_path, candidates[0])
            else:
                window.show_quick_panel(
                    [[os.path.basename(c)] for c in candidates],
                    lambda idx: idx >= 0 and self._do_import(input_path, candidates[idx])
                )

        existing_in = self._find_cphng_input(src_dir)
        if existing_in:
            window.show_quick_panel(
                [[os.path.basename(existing_in), t('use_existing_in_cphng')]] +
                [[t('choose_other_file')]],
                lambda idx: on_done(existing_in if idx == 0 else None)
            )
        else:
            window.show_input_panel(
                t('input_file_path') + ':', '',
                lambda s: on_done(s.strip() or None),
                None, None
            )

    def _find_cphng_input(self, src_dir):
        candidates = ['in.txt', 'input.txt', 'stdin.txt']
        for c in candidates:
            p = os.path.join(src_dir, c)
            if os.path.exists(p):
                return p
        return None

    def _find_output_for_input(self, input_path):
        candidates = []
        base, ext = os.path.splitext(input_path)
        for new_ext in ['.out', '.ans', '.txt']:
            p = base + new_ext
            if os.path.exists(p) and p != input_path:
                candidates.append(p)
        for new_name in ['out.txt', 'output.txt', 'stdout.txt', 'ans.txt']:
            p = os.path.join(os.path.dirname(input_path), new_name)
            if os.path.exists(p) and p != input_path:
                candidates.append(p)
        return list(set(candidates))

    def _import_input_only(self, input_path, output_path):
        try:
            with open(input_path, 'r', encoding='utf-8') as f:
                content = f.read()
            tests = [{'test': content, 'correct_answers': []}]
            self._save_and_show(tests, input_path)
        except Exception as e:
            sublime.error_message(t('import_failed', error=str(e)))

    def _do_import(self, input_path, output_path):
        try:
            with open(input_path, 'r', encoding='utf-8') as f:
                inp = f.read()
            out = ''
            if output_path:
                with open(output_path, 'r', encoding='utf-8') as f:
                    out = f.read()
            tests = [{'test': inp, 'correct_answers': [out.strip()] if out else []}]
            self._save_and_show(tests, input_path)
        except Exception as e:
            sublime.error_message(t('import_failed', error=str(e)))

    def _import_from_single(self, window):
        src_file = self.view.file_name()
        if not src_file:
            sublime.status_message(t('save_file_first'))
            return

        sublime.set_timeout(
            lambda: window.show_input_panel(
                t('import_file_path') + ':', '',
                lambda s: self._do_import_single(s.strip() or None),
                None, None
            ), 100
        )

    def _do_import_single(self, file_path):
        if not file_path or not os.path.exists(file_path):
            sublime.status_message(t('file_not_found'))
            return

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            sublime.error_message(t('read_failed', error=str(e)))
            return

        sep_patterns = [
            (r'\n[-=]{3,}\s*output\s*[-=]{0,}\n', 'output'),
            (r'\n#{1,3}\s*output\s*#{0,}\n', 'output'),
            (r'\n-{3,}\s*OUT(?:PUT)?\s*-{0,}\n', 'OUT'),
            (r'\noutput\s*:\s*\n', 'output:'),
        ]

        for pattern, _ in sep_patterns:
            match = re.split(pattern, content, maxsplit=1, flags=re.IGNORECASE)
            if len(match) == 2:
                inp, out = match[0].strip(), match[1].strip()
                tests = [{'test': inp + '\n', 'correct_answers': [out]}]
                self._save_and_show(tests, file_path)
                return

        tests = [{'test': content, 'correct_answers': []}]
        self._save_and_show(tests, file_path)

    def _import_from_cphng(self, window):
        src_file = self.view.file_name()
        if not src_file:
            sublime.status_message(t('save_file_first'))
            return

        src_dir = os.path.dirname(src_file)

        in_path = self._find_cphng_input(src_dir)
        if not in_path:
            sublime.error_message(t('no_cphng_files_found'))
            return

        candidates = self._find_output_for_input(in_path)
        if not candidates:
            self._import_input_only(in_path, None)
            return

        if len(candidates) == 1:
            self._do_import(in_path, candidates[0])
        else:
            window.show_quick_panel(
                [[os.path.basename(c)] for c in candidates],
                lambda idx: idx >= 0 and self._do_import(in_path, candidates[idx])
            )

    def _save_and_show(self, tests, source_path):
        src_file = self.view.file_name()
        if not src_file:
            return

        if save_tests(src_file, tests):
            count = len(tests)
            sublime.status_message(t('imported_tests', count=count, source=os.path.basename(source_path)))
            self.view.run_command('view_tester', {'action': 'make_opd', 'load_session': True})
        else:
            sublime.error_message(t('import_save_failed'))


class CphPickImportFileCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        window = self.view.window()
        if not window:
            return

        src_file = self.view.file_name()
        if not src_file:
            sublime.status_message(t('save_file_first'))
            return

        src_dir = os.path.dirname(src_file)

        candidates = []
        for f in sorted(os.listdir(src_dir)):
            full = os.path.join(src_dir, f)
            if os.path.isfile(full) and (f.endswith('.in') or f.endswith('.out') or
                                         f.endswith('.in.txt') or f.endswith('.out.txt') or
                                         f.endswith('.ans') or f == 'in.txt' or
                                         f == 'input.txt' or f == 'out.txt' or
                                         f == 'output.txt' or f == 'sample.txt' or
                                         (f.endswith('.txt') and not f.endswith('__tests'))):
                candidates.append([f, full])

        if not candidates:
            sublime.status_message(t('no_test_files_in_dir'))
            return

        def on_select(idx):
            if idx < 0 or idx >= len(candidates):
                return
            _, file_path = candidates[idx]
            self.view.run_command('cph_import_tests_file', {'file_path': file_path})

        window.show_quick_panel(candidates, on_select)


class CphImportTestsFileCommand(sublime_plugin.TextCommand):
    def run(self, edit, file_path=None):
        if not file_path:
            return

        src_file = self.view.file_name()
        if not src_file:
            sublime.status_message(t('save_file_first'))
            return

        candidates = []
        base, ext = os.path.splitext(file_path)
        for new_ext in ['.out', '.ans']:
            p = base + new_ext
            if os.path.exists(p):
                candidates.append(p)
        if ext in ('.in', '.in.txt', '.txt') and 'in' in os.path.basename(file_path).lower():
            for new_name in ['out.txt', 'output.txt', 'stdout.txt', 'ans.txt']:
                p = os.path.join(os.path.dirname(file_path), new_name)
                if os.path.exists(p):
                    candidates.append(p)

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                inp = f.read()
            if candidates:
                with open(candidates[0], 'r', encoding='utf-8') as f:
                    out = f.read()
                out = out.strip()
            else:
                out = ''
            tests = [{'test': inp, 'correct_answers': [out] if out else []}]
            if save_tests(src_file, tests):
                sublime.status_message(t('imported_tests', count=1, source=os.path.basename(file_path)))
                self.view.run_command('view_tester', {'action': 'make_opd', 'load_session': True})
            else:
                sublime.error_message(t('import_save_failed'))
        except Exception as e:
            sublime.error_message(t('import_failed', error=str(e)))
