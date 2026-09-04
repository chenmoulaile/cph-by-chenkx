"""
cph-by-chenkx - 国际化 / Internationalization
默认中文，可设置切换为英文
Default Chinese, can be switched to English
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
        'zh': '错误输出',
        'en': 'Error Output',
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
}


def set_lang(lang):
    global _current_lang
    if lang in (LANG_ZH, LANG_EN):
        _current_lang = lang


def get_lang():
    return _current_lang


def t(key, **kwargs):
    """Translate a key"""
    if key not in STRINGS:
        return key
    s = STRINGS[key].get(_current_lang, STRINGS[key].get(LANG_EN, key))
    if kwargs:
        try:
            return s.format(**kwargs)
        except (KeyError, IndexError):
            return s
    return s
