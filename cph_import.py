"""
cph-by-chenkx - 从文件导入测试数据

支持四种来源:
1. in/out 文件对 (自动探测同名 .out/.ans 或 out.txt 等)
2. 单个文件 (内含 output 分隔行, 自动切分输入/输出)
3. cph-ng 风格 (同目录 in.txt / input.txt + 对应输出)
4. 文件夹批量导入 (所有 .in/.out 文件对)

注意: 所有命令通过 cph_view_tester 走正常 Run 流程刷新测评视图,
绝不直接对源代码视图调用 make_opd(load_session=True)。
"""

import sublime
import sublime_plugin
import os
import re
import glob

from .core.cph_settings import save_tests, load_all_tests
from .core.cph_i18n import t


class CphImportTestsCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        window = self.view.window()
        if not window:
            return

        options = [
            [t('import_from_pair'), t('import_from_pair_desc')],
            [t('import_from_single'), t('import_from_single_desc')],
            [t('import_from_cphng'), t('import_from_cphng_desc')],
            [t('import_from_folder'), t('import_from_folder_desc')],
        ]

        def on_select(idx):
            if idx == 0:
                self._import_from_pair(window)
            elif idx == 1:
                self._import_from_single(window)
            elif idx == 2:
                self._import_from_cphng(window)
            elif idx == 3:
                self._import_from_folder(window)

        window.show_quick_panel(options, on_select)

    # ---------- 1. in/out pair ----------

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
                self._import_input_only(input_path)
                return

            if len(candidates) == 1:
                self._do_import(input_path, candidates[0], append=True)
            else:
                window.show_quick_panel(
                    [[os.path.basename(c)] for c in candidates],
                    lambda idx: idx >= 0 and self._do_import(input_path, candidates[idx], append=True)
                )

        existing_in = self._find_cphng_input(src_dir)
        if existing_in:
            window.show_quick_panel(
                [[os.path.basename(existing_in), t('use_existing_in_cphng')],
                 [t('choose_other_file')]],
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

    def _import_input_only(self, input_path):
        try:
            with open(input_path, 'r', encoding='utf-8') as f:
                content = f.read()
            tests = [{'test': content, 'correct_answers': []}]
            self._save_and_show(tests, input_path, append=True)
        except Exception as e:
            sublime.error_message(t('import_failed', error=str(e)))

    def _do_import(self, input_path, output_path, append=False):
        try:
            with open(input_path, 'r', encoding='utf-8') as f:
                inp = f.read()
            out = ''
            if output_path:
                with open(output_path, 'r', encoding='utf-8') as f:
                    out = f.read()
            tests = [{'test': inp, 'correct_answers': [out.strip()] if out.strip() else []}]
            self._save_and_show(tests, input_path, append=append)
        except Exception as e:
            sublime.error_message(t('import_failed', error=str(e)))

    # ---------- 2. single file with separator ----------

    def _import_from_single(self, window):
        src_file = self.view.file_name()
        if not src_file:
            sublime.status_message(t('save_file_first'))
            return

        window.show_input_panel(
            t('import_file_path') + ':', '',
            lambda s: self._do_import_single(s.strip() or None),
            None, None
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
                tests = [{'test': inp + '\n', 'correct_answers': [out] if out else []}]
                self._save_and_show(tests, file_path, append=True)
                return

        tests = [{'test': content, 'correct_answers': []}]
        self._save_and_show(tests, file_path, append=True)

    # ---------- 3. cph-ng style ----------

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
            self._import_input_only(in_path)
            return

        if len(candidates) == 1:
            self._do_import(in_path, candidates[0], append=True)
        else:
            window.show_quick_panel(
                [[os.path.basename(c)] for c in candidates],
                lambda idx: idx >= 0 and self._do_import(in_path, candidates[idx], append=True)
            )

    # ---------- 4. folder batch import ----------

    def _import_from_folder(self, window):
        src_file = self.view.file_name()
        if not src_file:
            sublime.status_message(t('save_file_first'))
            return

        src_dir = os.path.dirname(src_file)
        window.show_input_panel(
            t('import_folder_path') + ':', src_dir,
            lambda s: self._do_import_from_folder(s.strip(), window),
            None, None
        )

    def _do_import_from_folder(self, selected_path, window):
        """Import all .in/.out pairs from a folder; merges (dedup) with existing tests."""
        if not selected_path or not os.path.isdir(selected_path):
            sublime.status_message(t('file_not_found'))
            return

        in_files = []
        for pattern in ['*.in', '*.in.txt']:
            in_files.extend(glob.glob(os.path.join(selected_path, pattern)))

        if not in_files:
            sublime.status_message(t('no_test_files_in_dir'))
            return

        in_files.sort()

        new_tests = []
        for in_file in in_files:
            base_file = os.path.splitext(in_file)[0]
            out_file = None
            for out_ext in ['.out', '.ans', '.out.txt']:
                candidate = base_file + out_ext
                if os.path.exists(candidate):
                    out_file = candidate
                    break

            try:
                with open(in_file, 'r', encoding='utf-8') as f:
                    inp = f.read()
                out = ''
                if out_file:
                    with open(out_file, 'r', encoding='utf-8') as f:
                        out = f.read().strip()

                new_tests.append({'test': inp, 'correct_answers': [out] if out else []})
            except Exception as e:
                print('[cph-by-chenkx] Failed to import %s: %s' % (in_file, e))

        if new_tests:
            self._save_and_show(new_tests, selected_path, append=True)
        else:
            sublime.error_message(t('import_save_failed'))

    # ---------- shared ----------

    def _save_and_show(self, tests, source_path, append=False):
        src_file = self.view.file_name()
        if not src_file:
            return

        if append:
            existing_tests = load_all_tests(src_file)
            seen = set()
            merged = []
            for item in existing_tests + tests:
                key = (item.get('test', ''), tuple(sorted(item.get('correct_answers', []))))
                if key not in seen:
                    seen.add(key)
                    merged.append(item)
            tests = merged

        if save_tests(src_file, tests):
            sublime.status_message(t('imported_tests', count=len(tests),
                                     source=os.path.basename(source_path)))
            # 正常 Run 流程: 复用/创建 -run 视图并从磁盘重新加载样例
            self.view.run_command('cph_view_tester', {'action': 'make_opd'})
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
            out = ''
            if candidates:
                with open(candidates[0], 'r', encoding='utf-8') as f:
                    out = f.read().strip()
            tests = [{'test': inp, 'correct_answers': [out] if out else []}]
            # append/merge with existing tests instead of overwriting them
            existing = load_all_tests(src_file)
            seen = set()
            merged = []
            for item in existing + tests:
                key = (item.get('test', ''), tuple(sorted(item.get('correct_answers', []))))
                if key not in seen:
                    seen.add(key)
                    merged.append(item)
            if save_tests(src_file, merged):
                sublime.status_message(t('imported_tests', count=len(merged),
                                         source=os.path.basename(file_path)))
                self.view.run_command('cph_view_tester', {'action': 'make_opd'})
            else:
                sublime.error_message(t('import_save_failed'))
        except Exception as e:
            sublime.error_message(t('import_failed', error=str(e)))
