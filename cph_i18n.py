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
