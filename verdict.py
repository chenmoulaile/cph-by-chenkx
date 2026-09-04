"""
cph-by-chenkx - Verdict system (similar to cph-ng)
"""

VERDICT_NAME = {
    'unknown_error': 'UKE',
    'accepted': 'AC',
    'partially_correct': 'PC',
    'presentation_error': 'PE',
    'wrong_answer': 'WA',
    'time_limit_exceed': 'TLE',
    'memory_limit_exceed': 'MLE',
    'output_limit_exceed': 'OLE',
    'runtime_error': 'RE',
    'restricted_function': 'RF',
    'compilation_error': 'CE',
    'system_error': 'SE',
    'waiting': 'WT',
    'compiling': 'CP',
    'compiled': 'CPD',
    'judging': 'JG',
    'judged': 'JGD',
    'comparing': 'CMP',
    'skipped': 'SK',
    'rejected': 'RJ',
}

VERDICT_TYPE = {
    'running': 'RUNNING',
    'passed': 'PASSED',
    'failed': 'FAILED',
}

VERDICTS = {
    'unknown_error': {
        'name': VERDICT_NAME['unknown_error'],
        'full_name_en': 'Unknown Error',
        'full_name_zh': '未知错误',
        'color': '#0000ff',
        'type': VERDICT_TYPE['failed'],
    },
    'accepted': {
        'name': VERDICT_NAME['accepted'],
        'full_name_en': 'Accepted',
        'full_name_zh': '通过',
        'color': '#49cd32',
        'type': VERDICT_TYPE['passed'],
    },
    'partially_correct': {
        'name': VERDICT_NAME['partially_correct'],
        'full_name_en': 'Partially Correct',
        'full_name_zh': '部分正确',
        'color': '#ed9813',
        'type': VERDICT_TYPE['failed'],
    },
    'presentation_error': {
        'name': VERDICT_NAME['presentation_error'],
        'full_name_en': 'Presentation Error',
        'full_name_zh': '格式错误',
        'color': '#ff778e',
        'type': VERDICT_TYPE['failed'],
    },
    'wrong_answer': {
        'name': VERDICT_NAME['wrong_answer'],
        'full_name_en': 'Wrong Answer',
        'full_name_zh': '答案错误',
        'color': '#d3140d',
        'type': VERDICT_TYPE['failed'],
    },
    'time_limit_exceed': {
        'name': VERDICT_NAME['time_limit_exceed'],
        'full_name_en': 'Time Limit Exceeded',
        'full_name_zh': '超出时间限制',
        'color': '#0c0066',
        'type': VERDICT_TYPE['failed'],
    },
    'memory_limit_exceed': {
        'name': VERDICT_NAME['memory_limit_exceed'],
        'full_name_en': 'Memory Limit Exceeded',
        'full_name_zh': '超出内存限制',
        'color': '#5300a7',
        'type': VERDICT_TYPE['failed'],
    },
    'output_limit_exceed': {
        'name': VERDICT_NAME['output_limit_exceed'],
        'full_name_en': 'Output Limit Exceeded',
        'full_name_zh': '超出输出限制',
        'color': '#8300a7',
        'type': VERDICT_TYPE['failed'],
    },
    'runtime_error': {
        'name': VERDICT_NAME['runtime_error'],
        'full_name_en': 'Runtime Error',
        'full_name_zh': '运行时错误',
        'color': '#1a26c8',
        'type': VERDICT_TYPE['failed'],
    },
    'restricted_function': {
        'name': VERDICT_NAME['restricted_function'],
        'full_name_en': 'Restricted Function',
        'full_name_zh': '禁止调用函数',
        'color': '#008f81',
        'type': VERDICT_TYPE['failed'],
    },
    'compilation_error': {
        'name': VERDICT_NAME['compilation_error'],
        'full_name_en': 'Compilation Error',
        'full_name_zh': '编译错误',
        'color': '#8b7400',
        'type': VERDICT_TYPE['failed'],
    },
    'system_error': {
        'name': VERDICT_NAME['system_error'],
        'full_name_en': 'System Error',
        'full_name_zh': '系统错误',
        'color': '#000000',
        'type': VERDICT_TYPE['failed'],
    },
    'waiting': {
        'name': VERDICT_NAME['waiting'],
        'full_name_en': 'Waiting',
        'full_name_zh': '等待',
        'color': '#4100d9',
        'type': VERDICT_TYPE['running'],
    },
    'compiling': {
        'name': VERDICT_NAME['compiling'],
        'full_name_en': 'Compiling',
        'full_name_zh': '编译中',
        'color': '#5e19ff',
        'type': VERDICT_TYPE['running'],
    },
    'compiled': {
        'name': VERDICT_NAME['compiled'],
        'full_name_en': 'Compiled',
        'full_name_zh': '编译完成',
        'color': '#7340ff',
        'type': VERDICT_TYPE['running'],
    },
    'judging': {
        'name': VERDICT_NAME['judging'],
        'full_name_en': 'Judging',
        'full_name_zh': '评判中',
        'color': '#844fff',
        'type': VERDICT_TYPE['running'],
    },
    'judged': {
        'name': VERDICT_NAME['judged'],
        'full_name_en': 'Judged',
        'full_name_zh': '评判完成',
        'color': '#967fff',
        'type': VERDICT_TYPE['running'],
    },
    'comparing': {
        'name': VERDICT_NAME['comparing'],
        'full_name_en': 'Comparing',
        'full_name_zh': '比较中',
        'color': '#a87dff',
        'type': VERDICT_TYPE['running'],
    },
    'skipped': {
        'name': VERDICT_NAME['skipped'],
        'full_name_en': 'Skipped',
        'full_name_zh': '已跳过',
        'color': '#4b4b4b',
        'type': VERDICT_TYPE['passed'],
    },
    'rejected': {
        'name': VERDICT_NAME['rejected'],
        'full_name_en': 'Rejected',
        'full_name_zh': '已拒绝',
        'color': '#4e0000',
        'type': VERDICT_TYPE['passed'],
    },
}


def get_verdict(name):
    return VERDICTS.get(name, VERDICTS['unknown_error'])


def get_verdict_by_code(rtcode, runtime, time_limit_ms, memory_limit_mb,
                        stderr, stdout, expected_output,
                        ignore_error=True, ole_size=None, regard_pe_as_ac=False):
    """
    Determine verdict based on execution result and output comparison.
    Similar to cph-ng Grader.
    """
    if rtcode is None:
        return get_verdict('unknown_error')

    if rtcode < 0:
        return get_verdict('runtime_error')

    if rtcode != 0:
        if rtcode == 137 or rtcode == 9:
            return get_verdict('memory_limit_exceed')
        elif rtcode == 124 or rtcode == 142:
            return get_verdict('time_limit_exceed')
        return get_verdict('runtime_error')

    if time_limit_ms and runtime and runtime > time_limit_ms:
        return get_verdict('time_limit_exceed')

    if not expected_output:
        return get_verdict('accepted')

    if not ignore_error and stderr and stderr.strip():
        return get_verdict('runtime_error')

    def fix(s):
        if not s:
            return ''
        return '\n'.join(line.rstrip() for line in s.rstrip().split('\n'))

    fixed_actual = fix(stdout)
    fixed_expected = fix(expected_output)

    if ole_size and fixed_actual and fixed_expected and len(fixed_actual) > len(fixed_expected) * ole_size:
        return get_verdict('output_limit_exceed')

    def compress(s):
        if not s:
            return ''
        return ''.join(s.split())

    if compress(stdout) != compress(expected_output):
        return get_verdict('wrong_answer')

    if fixed_actual != fixed_expected and not regard_pe_as_ac:
        return get_verdict('presentation_error')

    return get_verdict('accepted')
