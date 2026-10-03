"""
cph-by-chenkx - 国际化 / Internationalization
默认中文 (可切换为英文)
Default Chinese, switchable to English
"""

LANG_ZH = 'zh'
LANG_EN = 'en'

_current_lang = LANG_ZH  # default is Chinese

STRINGS = {
    'edit': {
        'zh': '编辑',
        'en': 'edit',
    },
    'run': {
        'zh': '运行',
        'en': 'run',
    },
    'stop': {
        'zh': '停止',
        'en': 'stop',
    },
    'detail': {
        'zh': '详情',
        'en': 'detail',
    },
    'time': {
        'zh': '时间',
        'en': 'time',
    },
    'memory': {
        'zh': '内存',
        'en': 'mem',
    },
    'close': {
        'zh': '关闭',
        'en': 'close',
    },
    'accept': {
        'zh': '接受',
        'en': 'accept',
    },
    'has_stderr': {
        'zh': '有 stderr',
        'en': 'stderr',
    },
    'decline': {
        'zh': '拒绝',
        'en': 'decline',
    },
    'test_label': {
        'zh': '测试',
        'en': 'test',
    },
    'compiling': {
        'zh': '编译中...',
        'en': 'Compiling...',
    },
    'compilation_error': {
        'zh': '编译错误',
        'en': 'Compilation Error',
    },
    'input': {
        'zh': '输入',
        'en': 'Input',
    },
    'expected_output': {
        'zh': '预期输出',
        'en': 'Expected Output',
    },
    'actual_output': {
        'zh': '实际输出',
        'en': 'Actual Output',
    },
    'error_output': {
        'zh': '标准错误输出 (stderr)',
        'en': 'Standard Error (stderr)',
    },
    'message': {
        'zh': '信息',
        'en': 'Message',
    },
    'correct_answer': {
        'zh': '正确答案',
        'en': 'Correct Answer',
    },
    'edit_answer_hint': {
        'zh': '标准答案',
        'en': 'expected answer',
    },
    'edit_input_hint': {
        'zh': '保存输入和答案',
        'en': 'saves input + answer',
    },
    'diff': {
        'zh': '差异',
        'en': 'Diff',
    },
    'cannot_action_while_running': {
        'zh': '运行中无法{action}',
        'en': 'can not {action} while process running',
    },
    'listen_companion': {
        'zh': '监听 Competitive Companion',
        'en': 'Listen to Competitive Companion',
    },
    'server_started': {
        'zh': 'cph-by-chenkx 监听已启动，等待 Competitive Companion 发送数据...',
        'en': 'cph-by-chenkx listener started, waiting for Competitive Companion...',
    },
    'tests_loaded': {
        'zh': '已加载 {count} 个测试用例',
        'en': 'Loaded {count} test cases',
    },
    'tests_loaded_with_limits': {
        'zh': '已加载 {count} 个测试用例（时间限制: {time}ms, 内存限制: {memory}MB）',
        'en': 'Loaded {count} test cases (Time limit: {time}ms, Memory limit: {memory}MB)',
    },
    'process_terminated': {
        'zh': '进程已终止',
        'en': 'Process terminated',
    },
    'stop_before_delete': {
        'zh': '请先停止运行再删除',
        'en': 'stop process before delete action',
    },
    'deleted_tests': {
        'zh': '已删除测试: {ids}',
        'en': 'deleted tests: {ids}',
    },
    'process_already_running': {
        'zh': '进程已在运行',
        'en': 'process already running',
    },
    'no_more_tests': {
        'zh': '已是最后一个测试',
        'en': 'no more tests',
    },
    'cant_restore_session': {
        'zh': '无法恢复会话',
        'en': 'Can\'t restore session',
    },
    'session_saved': {
        'zh': 'cph-by-chenkx: 会话已保存',
        'en': 'cph-by-chenkx: session saved',
    },
    'settings_loaded': {
        'zh': 'cph-by-chenkx: 设置已加载',
        'en': 'cph-by-chenkx: settings loaded',
    },
    'next_test': {
        'zh': '下一个测试',
        'en': 'next test',
    },
    'error_handling_post': {
        'zh': '处理 POST 请求出错 - {error}',
        'en': 'Error handling POST - {error}',
    },
    'error_starting_thread': {
        'zh': '错误: 无法启动线程 - {error}',
        'en': 'Error: unable to start thread - {error}',
    },
    'new_test_file_path': {
        'zh': '测试用例文件路径: {path}',
        'en': 'New test case path: {path}',
    },
    'compile_error': {
        'zh': '编译错误',
        'en': 'compilation error',
    },
    'hide_phantoms': {
        'zh': '隐藏面板',
        'en': 'hide phantoms',
    },
    'save': {
        'zh': '保存',
        'en': 'save',
    },
    'delete': {
        'zh': '删除',
        'en': 'delete',
    },
    'show_phantoms': {
        'zh': '显示面板',
        'en': 'show phantoms',
    },
    'debugger_enabled': {
        'zh': '调试器已启用',
        'en': 'debugger enabled',
    },
    'debugger_disabled': {
        'zh': '调试器已禁用',
        'en': 'debugger disabled',
    },
    'no_input_provided': {
        'zh': '请输入测试数据',
        'en': 'No input provided',
    },
    'expand_test': {
        'zh': '展开测试',
        'en': 'expand test',
    },
    'fold_test': {
        'zh': '折叠测试',
        'en': 'fold test',
    },
    'import_from_pair': {
        'zh': '从 in/out 文件对导入 (cph-ng 风格)',
        'en': 'Import from in/out file pair (cph-ng style)',
    },
    'import_from_pair_desc': {
        'zh': '导入与输出文件配对的输入文件',
        'en': 'Import an input file paired with an output file',
    },
    'import_from_single': {
        'zh': '从单个文件导入 (含分隔符)',
        'en': 'Import from a single file (with separator)',
    },
    'import_from_single_desc': {
        'zh': '导入同时包含输入和输出的单个文件',
        'en': 'Import a single file containing both input and output',
    },
    'import_from_cphng': {
        'zh': '从 cph-ng 文件夹导入',
        'en': 'Import from cph-ng folder (in.txt/out.txt)',
    },
    'import_from_cphng_desc': {
        'zh': '自动查找同目录下的 in.txt 和 out.txt',
        'en': 'Auto-detect in.txt and out.txt in the same folder',
    },
    'import_file_path': {
        'zh': '测试文件路径',
        'en': 'Test file path',
    },
    'input_file_path': {
        'zh': '输入文件路径',
        'en': 'Input file path',
    },
    'output_file_not_found': {
        'zh': '未找到对应的输出文件,只导入输入',
        'en': 'Output file not found, importing input only',
    },
    'imported_tests': {
        'zh': '已导入 {count} 个测试 (来源: {source})',
        'en': 'Imported {count} test(s) from {source}',
    },
    'import_save_failed': {
        'zh': '导入失败: 无法保存测试数据',
        'en': 'Import failed: cannot save test data',
    },
    'import_failed': {
        'zh': '导入失败: {error}',
        'en': 'Import failed: {error}',
    },
    'read_failed': {
        'zh': '读取文件失败: {error}',
        'en': 'Failed to read file: {error}',
    },
    'file_not_found': {
        'zh': '文件不存在',
        'en': 'File not found',
    },
    'no_cphng_files_found': {
        'zh': '未找到 cph-ng 样例文件 (in.txt / input.txt)',
        'en': 'No cph-ng sample files found (in.txt / input.txt)',
    },
    'no_test_files_in_dir': {
        'zh': '当前目录未找到测试文件',
        'en': 'No test files found in current directory',
    },
    'use_existing_in_cphng': {
        'zh': '(已找到 cph-ng 文件)',
        'en': '(existing cph-ng file found)',
    },
    'save_file_first': {
        'zh': '请先保存当前文件',
        'en': 'Please save the current file first',
    },
    'stress_test': {
        'zh': '对拍',
        'en': 'Stress Test',
    },
    'stress_test_desc': {
        'zh': '使用 std 与用户程序对拍 (生成随机数据, 比较输出)',
        'en': 'Stress test against standard solution with random data',
    },
    'stress_running': {
        'zh': '对拍进行中...',
        'en': 'Stress testing...',
    },
    'stress_round': {
        'zh': '第 {round} 轮',
        'en': 'Round {round}',
    },
    'stress_passed': {
        'zh': '对拍通过: {rounds} 轮全部一致',
        'en': 'Stress test passed: {rounds} rounds all consistent',
    },
    'runtime_error_at': {
        'zh': '运行错误 (RE) 位置: {location}',
        'en': 'runtime error (RE) at {location}',
    },
    'stress_all_timeout': {
        'zh': '对拍结束: 所有轮次都超时, 未比较任何输出',
        'en': 'stress test ended: every round timed out, nothing compared',
    },
    'stress_failed': {
        'zh': '对拍失败: 第 {round} 轮输出不一致',
        'en': 'Stress test failed: mismatch at round {round}',
    },
    'stress_diff': {
        'zh': '差异:',
        'en': 'Diff:',
    },
    'stress_input': {
        'zh': '输入',
        'en': 'Input',
    },
    'stress_user_output': {
        'zh': '用户输出',
        'en': 'User Output',
    },
    'stress_std_output': {
        'zh': '标准输出',
        'en': 'Standard Output',
    },
    'stress_generator_tle': {
        'zh': '生成器超时（第 {round} 轮，上限 {limit}s），跳过该轮',
        'en': 'generator timed out at round {round} (limit {limit}s), round skipped',
    },
    'stress_generator_limit_hint': {
        'zh': '生成器连续超时，已停止；可调大 stress_generator_time_limit_seconds'
              '（当前 {limit}s）或让 gen.cpp 更快',
        'en': 'the generator keeps timing out, stopped; raise'
              ' stress_generator_time_limit_seconds (now {limit}s) or make gen.cpp faster',
    },
    'stress_generator_failed': {
        'zh': '生成器运行失败（第 {round} 轮，退出码 {code}）',
        'en': 'generator failed at round {round} (exit code {code})',
    },
    'stress_cannot_run': {
        'zh': '无法运行 {program}: {reason}',
        'en': 'cannot run {program}: {reason}',
    },
    'stress_tle_hint': {
        'zh': '提示: 若编译命令里定义了 LOCAL 之类的调试宏，程序里留在循环内的'
              'debug 输出会非常慢（stderr 不缓冲），本地很容易超时；'
              '去掉该行或删掉编译命令里的 -DLOCAL 再试',
        'en': 'hint: if the compile command defines a debug macro such as LOCAL,'
              ' a debug() call left inside a loop is extremely slow (stderr is'
              ' unbuffered) and times out locally; remove it or drop -DLOCAL',
    },
    'stress_choose_std': {
        'zh': '请先选择 std 文件',
        'en': 'Please choose the standard (std) file first',
    },
    'stress_choose_generator': {
        'zh': '请先选择数据生成器文件',
        'en': 'Please choose the data generator file first',
    },
    'choose_std_file': {
        'zh': '选择 std (标准) 文件',
        'en': 'Choose std (standard) file',
    },
    'choose_generator_file': {
        'zh': '选择数据生成器文件',
        'en': 'Choose data generator file',
    },
    'generator_hint': {
        'zh': '提示: 数据生成器应输出随机测试数据到 stdout',
        'en': 'Hint: generator should output random test data to stdout',
    },
    'stress_time_limit': {
        'zh': '对拍时间限制(秒)',
        'en': 'Stress test time limit (seconds)',
    },
    'stress_max_rounds': {
        'zh': '对拍最大轮数',
        'en': 'Stress test max rounds',
    },
    'choose_stress_files': {
        'zh': '选择对拍文件',
        'en': 'Choose stress test files',
    },
    'stress_files_needed': {
        'zh': '需要 std 文件和 generator 文件',
        'en': 'Need both std file and generator file',
    },
    # ---- Competitive Companion persistent listener ----
    'listener_started': {
        'zh': 'Competitive Companion 监听已启动 (端口 {port}，目标: {file})，浏览器扩展可反复点击发送',
        'en': 'Competitive Companion listener started (port {port}, target: {file})',
    },
    'listener_retarget': {
        'zh': '监听运行中，目标已切换为: {file}',
        'en': 'Listener running, target switched to: {file}',
    },
    'listener_stopped': {
        'zh': 'Competitive Companion 监听已停止',
        'en': 'Competitive Companion listener stopped',
    },
    'listener_not_running': {
        'zh': '监听未在运行',
        'en': 'Listener is not running',
    },
    'listener_need_save': {
        'zh': '请先保存当前文件再开启监听',
        'en': 'Save the current file before listening',
    },
    'listener_no_target': {
        'zh': '监听目标文件不存在或未保存',
        'en': 'Listener target missing or unsaved',
    },
    'listener_port_error': {
        'zh': '监听启动失败 (端口 {port}): {error}',
        'en': 'Failed to start listener on port {port}: {error}',
    },
    'tests_received': {
        'zh': '已接收题目 "{name}": {count} 个样例 (时间限制 {time}ms, 内存限制 {memory}MB)',
        'en': 'Received "{name}": {count} test(s) (TL {time}ms, ML {memory}MB)',
    },
    # ---- detail view ----
    'detail_no_result': {
        'zh': '请先运行测试再查看详情',
        'en': 'Run the test first to see details',
    },
    'detail_empty': {
        'zh': '(空)',
        'en': '(empty)',
    },
    'diff_ignore_trailing': {
        'zh': '逐行对比，忽略行末空格与末尾换行',
        'en': 'line-by-line, ignoring trailing spaces',
    },
    'diff_all_match': {
        'zh': '全部 {n} 行一致',
        'en': 'all {n} lines match',
    },
    'diff_lines_differ': {
        'zh': '{n} 处不同 (共 {total} 行)',
        'en': '{n} difference(s) over {total} lines',
    },
    'diff_no_expected': {
        'zh': '未设置标准答案，无法对比。可在 "test N -answer" 标签页设置后再运行',
        'en': 'No expected answer set. Fill it in the "test N -answer" tab and re-run',
    },
    'expected_short': {
        'zh': '预期',
        'en': 'expected',
    },
    'actual_short': {
        'zh': '实际',
        'en': 'actual',
    },
    'expected_only': {
        'zh': '仅预期输出有',
        'en': 'expected only',
    },
    'actual_only': {
        'zh': '仅实际输出有',
        'en': 'actual only',
    },
    # ---- import ----
    'import_from_folder': {
        'zh': '从文件夹批量导入 (.in/.out 文件对)',
        'en': 'Batch import from folder (.in/.out pairs)',
    },
    'import_from_folder_desc': {
        'zh': '输入一个文件夹路径, 导入其中所有 .in/.out 文件对',
        'en': 'Enter a folder path to import all .in/.out pairs inside',
    },
    'import_folder_path': {
        'zh': '文件夹路径 (包含 .in/.out 文件对)',
        'en': 'Folder path containing .in/.out pairs',
    },
    'choose_other_file': {
        'zh': '选择其他文件...',
        'en': 'Choose another file...',
    },

    'compile_cached': {
        'zh': '编译缓存命中，已跳过编译',
        'en': 'compile skipped (cache hit)',
    },
    'output_truncated_warn': {
        'zh': '输出过大，已截断显示',
        'en': 'output too large, truncated',
    },
    'summary_passed': {
        'zh': '{passed}/{total} 通过',
        'en': '{passed}/{total} passed',
    },
    'summary_first_fail': {
        'zh': '首个失败 test {id}',
        'en': 'first failure: test {id}',
    },
    'summary_total_time': {
        'zh': '总用时 {time}s',
        'en': 'total {time}s',
    },
    'no_running_process': {
        'zh': '当前没有正在运行的程序',
        'en': 'no running process',
    },
    'unsupported_language': {
        'zh': '没有为 .{ext} 配置运行方式（见 run_settings）',
        'en': 'no run_settings entry for .{ext}',
    },
    'template_no_keyword': {
        'zh': '请把光标放在关键字后（如 fastio）再按快捷键',
        'en': 'put the cursor after a keyword (e.g. fastio)',
    },
    'template_not_found': {
        'zh': '没有名为 {name} 的模板（可用 algorithms_base 或 templates 设置）',
        'en': 'no template named {name} (see algorithms_base / templates)',
    },
    'clipboard_empty': {
        'zh': '剪贴板为空',
        'en': 'clipboard is empty',
    },
    'clipboard_test_added': {
        'zh': '已从剪贴板新增测试点，共 {total} 个',
        'en': 'added test from clipboard, {total} total',
    },
    'no_tests': {
        'zh': '当前没有测试数据',
        'en': 'no test data',
    },
    'nothing_to_copy': {
        'zh': '这一项是空的，没有内容可复制',
        'en': 'nothing to copy',
    },
    'copied_test_part': {
        'zh': '已复制 test {id} 的内容到剪贴板',
        'en': 'copied test {id} to clipboard',
    },
    'export_to_dir': {
        'zh': '导出目录',
        'en': 'export folder',
    },
    'export_done': {
        'zh': '已导出 {count} 个测试点到 {dir}',
        'en': 'exported {count} tests to {dir}',
    },
    'stress_counterexample_added': {
        'zh': '已把对拍反例保存为测试点（共 {total} 个）',
        'en': 'saved the counterexample as a test ({total} total)',
    },
    'doctor_title': {
        'zh': 'cph-by-chenkx 环境自检',
        'en': 'cph-by-chenkx environment check',
    },
    'doctor_no_run_settings': {
        'zh': 'run_settings 为空，先去设置里配置语言',
        'en': 'run_settings is empty - configure a language first',
    },
    'doctor_languages': {
        'zh': '语言配置',
        'en': 'language entry',
    },
    'doctor_compile': {
        'zh': '编译命令',
        'en': 'compile',
    },
    'doctor_run': {
        'zh': '运行命令',
        'en': 'run',
    },
    'doctor_fix_path': {
        'zh': '找不到 {name}，请确认它在 PATH 中或改用绝对路径',
        'en': '{name} not found - add it to PATH or use an absolute path',
    },
    'doctor_port': {
        'zh': 'Companion 端口',
        'en': 'Companion port',
    },
    'doctor_port_busy': {
        'zh': '端口被占用：监听器可能已在运行，或换 companion_port 设置',
        'en': 'port busy: a listener may already be running, or change companion_port',
    },
    'doctor_tests_path': {
        'zh': '测试数据路径',
        'en': 'tests path',
    },
    'doctor_extension': {
        'zh': '当前文件扩展名',
        'en': 'current file extension',
    },
    'doctor_no_file': {
        'zh': '当前视图没有文件（无法检查测试路径）',
        'en': 'current view has no file (tests path not checked)',
    },
    'doctor_resources': {
        'zh': 'HTML/CSS 资源加载',
        'en': 'HTML/CSS resources',
    },
    'doctor_settings': {
        'zh': '设置文件可解析',
        'en': 'settings file readable',
    },
    'answer_conflict_kept': {
        'zh': '答案冲突：已保留原有的答案',
        'en': 'answer conflict: the existing answer was kept',
    },
    'process_already_exited': {
        'zh': '程序已退出，输入被丢弃',
        'en': 'the program exited, input dropped',
    },
    'stress_already_running': {
        'zh': '对拍已经在运行中',
        'en': 'a stress test is already running',
    },
    'doctor_placeholder_unknown': {
        'zh': '命令里有不认识的占位符（会被当成空字符串）：{names}',
        'en': 'unknown placeholder(s) in the command (substituted with ""): {names}',
    },
    'doctor_markdown_hint': {
        'zh': '把下面这段贴到 issue 里（已包含环境与命令）：',
        'en': 'paste this block into an issue (environment and commands included):',
    },
    'doctor_footer': {
        'zh': '提示：把结果贴到 issue 里可以更快定位问题。',
        'en': 'tip: paste this report into an issue to speed up diagnosis.',
    },
}


def set_lang(lang):
    global _current_lang
    if lang in (LANG_ZH, LANG_EN):
        _current_lang = lang


def get_lang():
    return _current_lang


def add_strings(new_strings):
    for key, trans in new_strings.items():
        if key in STRINGS:
            for lang, val in trans.items():
                STRINGS[key][lang] = val
        else:
            STRINGS[key] = trans


def t(key, **kwargs):
    if key not in STRINGS:
        return key
    s = STRINGS[key].get(_current_lang, STRINGS[key].get(LANG_EN, key))
    if kwargs:
        try:
            return s.format(**kwargs)
        except (KeyError, IndexError):
            return s
    return s
