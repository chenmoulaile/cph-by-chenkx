"""
Algorithm Competition Assistant - 国际化 / Internationalization
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
    'compile_warning': {
        'zh': '编译警告',
        'en': 'Compilation Warning',
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
    'test_gone': {
        'zh': '该测试点已被删除，编辑内容未保存',
        'en': 'that test no longer exists, nothing was saved',
    },
    'panel_not_ready': {
        'zh': '测试面板还没准备好（编译失败或尚未编译）',
        'en': 'the test panel is not ready yet (nothing compiled)',
    },
    # ---- 机器速度校准 ----
    'calibrate_write_failed': {
        'zh': '写基准程序失败：{error}',
        'en': 'could not write the benchmark: {error}',
    },
    'calibrate_compile_failed': {
        'zh': '基准程序编译失败（{compiler} 是否在 PATH？）：{error}',
        'en': 'benchmark failed to compile (is {compiler} on PATH?): {error}',
    },
    'calibrate_run_failed': {
        'zh': '基准程序运行失败：{error}',
        'en': 'benchmark failed to run: {error}',
    },
    'calibrate_report': {
        'zh': '本机速度系数 {factor}×（{score} ops/s，耗时 {seconds}s）。'
              '系数 >1 表示本机比参考评测机快：本地 {factor} 毫秒只相当于评测机 1 毫秒。',
        'en': 'machine factor {factor}x ({score} ops/s, {seconds}s). A factor '
              'above 1 means this machine is faster than the reference judge.',
    },
    'calibrate_label': {
        'zh': '本机 {factor}× ≈ OJ {ms}ms',
        'en': 'local {factor}x ~ OJ {ms}ms',
    },
    'calibrate_factor': {
        'zh': '本机 {factor}×',
        'en': 'local {factor}x',
    },
    # ---- 抓题 ----
    'fetch_bad_url': {
        'zh': '不是合法的 http(s) 链接：{url}',
        'en': 'not a valid http(s) URL: {url}',
    },
    'fetch_http_error': {
        'zh': '抓取失败：HTTP {code}（{url}）',
        'en': 'fetch failed: HTTP {code} ({url})',
    },
    'fetch_failed': {
        'zh': '抓取失败：{error}（{url}）',
        'en': 'fetch failed: {error} ({url})',
    },
    'fetch_no_samples': {
        'zh': '页面上没找到样例（可能需要在浏览器里登录，或该站结构不同）',
        'en': 'no sample found on the page (it may need a login, or the site '
              'uses a different structure)',
    },
    'fetch_found_samples': {
        'zh': '找到 {n} 组样例',
        'en': 'found {n} sample(s)',
    },
    'fetch_added': {
        'zh': '已加入 {n} 个测试点，共 {total} 个',
        'en': 'added {n} test(s), {total} in total',
    },
    'fetch_enter_url': {
        'zh': '题目链接',
        'en': 'problem URL',
    },
    'statement_source': {
        'zh': '> 来源：{url}',
        'en': '> Source: {url}',
    },
    'statement_empty': {
        'zh': '题面解析为空（可能需要在浏览器里登录）',
        'en': 'the statement parsed as empty (it may need a login)',
    },
    # ---- 比赛计时 ----
    'contest_enter_minutes': {
        'zh': '比赛时长（分钟）',
        'en': 'contest length (minutes)',
    },
    'contest_started': {
        'zh': '比赛计时开始：{minutes} 分钟',
        'en': 'contest timer started: {minutes} minutes',
    },
    'contest_stopped': {
        'zh': '比赛计时已停止',
        'en': 'contest timer stopped',
    },
    'contest_remaining': {
        'zh': '剩余 {time}',
        'en': '{time} left',
    },
    'contest_finished': {
        'zh': '比赛时间到！',
        'en': 'time is up!',
    },
    'contest_warning': {
        'zh': '还剩 {minutes} 分钟',
        'en': '{minutes} minutes left',
    },
    # ---- Benchmark ----
    'benchmark_no_test': {
        'zh': '先跑一次测试点再做 benchmark',
        'en': 'run a test first, then benchmark it',
    },
    'benchmark_running': {
        'zh': 'benchmark：跑 {n} 次…',
        'en': 'benchmark: running {n} times...',
    },
    'benchmark_done': {
        'zh': 'benchmark（{n} 次）：最快 {best}ms / 平均 {avg}ms / 最慢 {worst}ms',
        'en': 'benchmark ({n} runs): best {best}ms / avg {avg}ms / worst {worst}ms',
    },
    # ---- 练习统计 ----
    'stats_empty': {
        'zh': '还没有练习记录',
        'en': 'no practice history yet',
    },
    'stats_reset_done': {
        'zh': '练习统计已清空',
        'en': 'practice statistics cleared',
    },
    'stats_title': {
        'zh': '练习统计（最近 {days} 天）',
        'en': 'practice statistics (last {days} days)',
    },
    'stress_seed': {
        'zh': '本轮随机种子 seed = {seed}（生成器可通过环境变量 CPH_SEED 复现）',
        'en': 'round seed = {seed} (the generator can read it from CPH_SEED)',
    },
    'stress_replaying': {
        'zh': '用 seed = {seed} 重放上一个反例…',
        'en': 'replaying the last counterexample with seed = {seed}...',
    },
    'stress_no_counterexample': {
        'zh': '还没有记录到反例（或该轮没有种子）',
        'en': 'no counterexample recorded yet (or it has no seed)',
    },
    'stress_replay_same': {
        'zh': '重放结果一致：这轮的差异可能是环境/时序导致的',
        'en': 'replay matched: the earlier difference may have been timing',
    },
    'stress_replay_tle': {
        'zh': '重放时用户程序超时',
        'en': 'the user program timed out during the replay',
    },
    'interactor_missing': {
        'zh': '找不到 interactor 文件：{path}（{error}）',
        'en': 'interactor file not found: {path} ({error})',
    },
    'interactor_compile_failed': {
        'zh': 'interactor 编译失败：{cmd}\n{error}',
        'en': 'interactor failed to compile: {cmd}\n{error}',
    },
    'interactive_running': {
        'zh': '交互题：正在与 interactor 交互（{done}/{total}）',
        'en': 'interactive: talking to the interactor ({done}/{total})',
    },
    'interactor_label': {
        'zh': 'interactor 对话',
        'en': 'interactor dialogue',
    },
    'checker_missing': {
        'zh': '找不到 checker 文件：{path}（{error}）',
        'en': 'checker file not found: {path} ({error})',
    },
    'checker_compile_failed': {
        'zh': 'checker 编译失败：{cmd}\n{error}',
        'en': 'checker failed to compile: {cmd}\n{error}',
    },
    'checker_run_failed': {
        'zh': 'checker 运行失败：{error}',
        'en': 'checker failed to run: {error}',
    },
    'checker_judged': {
        'zh': 'SPJ 判定：{verdict}',
        'en': 'judged by the checker: {verdict}',
    },
    'checker_label': {
        'zh': 'checker 输出',
        'en': 'checker output',
    },
    'checker_disabled': {
        'zh': '该语言没有配置 checker（run_settings 里的 "checker"），仍按逐 token 比较',
        'en': 'no checker configured for this language (run_settings "checker"); '
              'falling back to token comparison',
    },
    'checker_ok': {
        'zh': 'checker 可用：{path}',
        'en': 'checker ready: {path}',
    },
    'parallel_running': {
        'zh': '并行运行测试点：{done}/{total}',
        'en': 'running tests in parallel: {done}/{total}',
    },
    'parallel_done': {
        'zh': '并行运行完成：{total} 个测试点',
        'en': 'parallel run finished: {total} tests',
    },
    'tle_debug_build': {
        'zh': '编译命令里有 -DLOCAL/-DDEBUG：调试宏通常会把 debug() 输出打到不缓冲的 '
              'stderr，循环里调用时输出量是 O(n²)，本地会比评测机慢几十倍——'
              '代码正确也可能被判 TLE。计时时建议去掉该宏，并确认编译命令带 -O2。',
        'en': 'the compile command has -DLOCAL/-DDEBUG: the debug macro usually '
              'writes debug() to unbuffered stderr, which is O(n^2) output '
              'inside a loop, so a local run can be orders of magnitude slower '
              'than the judge and a correct program is reported TLE. Drop the '
              'macro for timing runs, and make sure the command uses -O2.',
    },
    'tle_no_output': {
        'zh': '超时被终止，且完全没有输出：程序很可能在等待输入（样例是否完整？）'
              '或者死循环。若终端里能正常跑出结果，先确认样例是否粘贴完整。',
        'en': 'killed at the time limit with no output at all: the program is '
              'most likely waiting for input (is the sample complete?) or '
              'looping forever. If it works in a terminal, check that the '
              'whole sample was pasted.',
    },
    # ---- sanitizer 回退 ----
    'sanitizer_fallback': {
        'zh': '本机工具链缺少 sanitizer 运行库 (ld: cannot find -lubsan/-lasan), '
              '已自动去掉 -fsanitize 参数重新编译一次; debug 模式的 -D_GLIBCXX_ASSERTIONS '
              '不依赖该运行库, 越界等未定义行为仍会中止并判 RE',
        'en': 'The local toolchain lacks the sanitizer runtime '
              '(ld: cannot find -lubsan/-lasan). The -fsanitize flags were '
              'dropped and the build was retried once. debug mode still passes '
              '-D_GLIBCXX_ASSERTIONS, which needs no such runtime: '
              'out-of-bounds and other undefined behaviour still abort and '
              'are judged RE',
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
        'zh': 'Algorithm Competition Assistant 监听已启动，等待 Competitive Companion 发送数据...',
        'en': 'Algorithm Competition Assistant listener started, waiting for Competitive Companion...',
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
        'zh': 'Algorithm Competition Assistant: 会话已保存',
        'en': 'Algorithm Competition Assistant: session saved',
    },
    'settings_loaded': {
        'zh': 'Algorithm Competition Assistant: 设置已加载',
        'en': 'Algorithm Competition Assistant: settings loaded',
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
    'stress_checker_message': {
        'zh': 'checker 判定: {message}',
        'en': 'Checker verdict: {message}',
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
    'stress_finished': {
        'zh': '对拍结束，用时 {seconds} 秒',
        'en': 'stress test finished in {seconds}s',
    },
    'stress_wall_limit': {
        'zh': '已达总时长上限 {limit} 秒，已停止（可调大 stress_max_wall_seconds）',
        'en': 'reached the overall limit of {limit}s and stopped'
              ' (raise stress_max_wall_seconds)',
    },
    'stress_browse_up': {
        'zh': '..（上一层目录）',
        'en': '.. (parent directory)',
    },
    'stress_browse_more': {
        'zh': '浏览其它文件…',
        'en': 'Browse for another file...',
    },
    'stress_type_path': {
        'zh': '输入路径…（已预填源文件所在目录，补个文件名即可）',
        'en': 'Type a path... (pre-filled with the source directory)',
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
    'stress_counterexample_too_big': {
        'zh': '反例输入 {size} 字节，超过 stress_max_insert_bytes={limit}，'
              '未写入 __tests（完整输入已在上方展示；调大该设置或设为 -1 可照常保存）',
        'en': 'the counterexample input is {size} bytes, above '
              'stress_max_insert_bytes={limit} - not written to __tests '
              '(the full input is printed above; raise the setting or use -1 '
              'to save it anyway)',
    },
    'doctor_title': {
        'zh': 'Algorithm Competition Assistant 环境自检',
        'en': 'Algorithm Competition Assistant environment check',
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
    'stress_multi_running': {
        'zh': '有 %d 个对拍正在进行，请切换到对应的对拍页再停止',
        'en': '%d stress tests are running - focus one of the stress pages to stop it',
    },
    'stress_none_running': {
        'zh': '当前没有正在运行的对拍',
        'en': 'no stress test running',
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
