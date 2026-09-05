"""
cph-by-chenkx - 评判系统 (类似 cph-ng)
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
        'color': '#0000ff',
        'type': VERDICT_TYPE['failed'],
    },
    'accepted': {
        'name': VERDICT_NAME['accepted'],
        'color': '#49cd32',
        'type': VERDICT_TYPE['passed'],
    },
    'partially_correct': {
        'name': VERDICT_NAME['partially_correct'],
        'color': '#ed9813',
        'type': VERDICT_TYPE['failed'],
    },
    'presentation_error': {
        'name': VERDICT_NAME['presentation_error'],
        'color': '#ff778e',
        'type': VERDICT_TYPE['failed'],
    },
    'wrong_answer': {
        'name': VERDICT_NAME['wrong_answer'],
        'color': '#d3140d',
        'type': VERDICT_TYPE['failed'],
    },
    'time_limit_exceed': {
        'name': VERDICT_NAME['time_limit_exceed'],
        'color': '#0c0066',
        'type': VERDICT_TYPE['failed'],
    },
    'memory_limit_exceed': {
        'name': VERDICT_NAME['memory_limit_exceed'],
        'color': '#5300a7',
        'type': VERDICT_TYPE['failed'],
    },
    'output_limit_exceed': {
        'name': VERDICT_NAME['output_limit_exceed'],
        'color': '#8300a7',
        'type': VERDICT_TYPE['failed'],
    },
    'runtime_error': {
        'name': VERDICT_NAME['runtime_error'],
        'color': '#1a26c8',
        'type': VERDICT_TYPE['failed'],
    },
    'restricted_function': {
        'name': VERDICT_NAME['restricted_function'],
        'color': '#008f81',
        'type': VERDICT_TYPE['failed'],
    },
    'compilation_error': {
        'name': VERDICT_NAME['compilation_error'],
        'color': '#8b7400',
        'type': VERDICT_TYPE['failed'],
    },
    'system_error': {
        'name': VERDICT_NAME['system_error'],
        'color': '#000000',
        'type': VERDICT_TYPE['failed'],
    },
    'waiting': {
        'name': VERDICT_NAME['waiting'],
        'color': '#4100d9',
        'type': VERDICT_TYPE['running'],
    },
    'compiling': {
        'name': VERDICT_NAME['compiling'],
        'color': '#5e19ff',
        'type': VERDICT_TYPE['running'],
    },
    'judging': {
        'name': VERDICT_NAME['judging'],
        'color': '#844fff',
        'type': VERDICT_TYPE['running'],
    },
}


def get_verdict(name):
    return VERDICTS.get(name, VERDICTS['unknown_error'])


def get_verdict_by_code(rtcode, runtime, time_limit_ms, memory_limit_mb,
                        stderr, stdout, expected_output,
                        ignore_error=True, ole_size=None, regard_pe_as_ac=False):
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

    if not expected_output or not expected_output.strip():
        # 没有设置正确答案时,不能判定为 AC,返回未评判
        return get_verdict('unknown_error')

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
