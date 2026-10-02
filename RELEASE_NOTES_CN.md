# v1.4.2 更新内容（中文）

第二轮第三方审查（P0-P2）的逐条修复。**P0 三条都是我上一轮引入的回归**，抱歉。

## P0 回归修复

- **「只重跑失败样例」崩溃**：`advance_chain` 跳过已 AC 的测试点时会把迭代器
  一次推前多格，而 `next_test` 对 `tests`/`prog_out` 的补齐只补**一格**
  （`if` 应为 `while`），首个非 AC 测试下标 ≥1 时 `prog_out[i]` 抛 IndexError，
  监听线程和主线程 `update_configs` 一起炸、整条链死掉
- **`sync_output` 设置不生效**：`CphViewTesterCommand.run` 的签名默认值是
  `sync_out=True`，导致 `create_opd` 里 `if sync_out is None: 读设置` 的分支
  永远走不到 —— 也就是说 v1.4.0 声称的"逐字节输出性能修复"实际上没生效，
  仍然是一个字节一次视图刷新。默认值改为 `None` 后设置真正生效
- **汇总行跑到测试内部**：`1/1 passed` 的 phantom 只按运行结束时的缓冲区末尾
  定位；AC 样例是折叠的（不占缓冲区），点开折叠后内容插入到锚点上方，汇总行
  就落进了样例内部。现在每次 `update_configs`（含折叠/展开）都重新锚定

## 排版调整

- **编辑样例的按钮条拆成两行**：`test N` 独占第一行作标题，`save` / `delete` /
  提示文字移到第二行（原来是挤在一行里）

## P1 修复

- `plugin_init.py` 里 `try_load_settings()` 复制粘贴了两遍（重复加载、状态条弹两次）
- **「复制输入/预期输出/实际输出」的光标定位一直静默失效**：它按旧的 FOC 格式
  `Test N {` 解析缓冲区，而运行视图早就不写这种标题行了，所以永远回退到最后一个
  测试点。现在改为**基于测试模型**定位（`test_index_at_cursor`），在运行面板里
  由 `cph_test_manager` 用实时状态作答，取到的"实际输出"也是真正那一次运行的输出
- **编译缓存不跟踪本地头文件**：只 stat 主源文件与 `extra_sources`，改 `.h`
  不会重编译、跑的还是旧二进制。现在递归解析 `#include "..."`（限深度 3）
  并把头文件的 mtime/size 计入缓存键
- **POSIX 下不再无条件走 shell**：只在命令真的需要 shell 特性（管道/重定向/`&&`/
  通配）时才 `shell=True`，否则 `shlex.split` + `shell=False`。以前内存采样测的是
  `sh` 的峰值、kill 也可能只杀掉 shell 而留下真正的程序

## P2 打磨

- **编译错误输出按本地编码回退解码**：以前 `decode('utf-8','ignore')`，
  中文 Windows 下 g++ 的中文诊断全是乱码（运行侧 v1.4.1 已修，编译侧漏了）
- **i18n 模板补上占位符**：`test_next.html`（next test）、`test_running.html`、
  `test_config.html`（`test N` / `time:`）、`test_accdec.html`（accept/decline）
  以前硬编码英文，代码传进去的 `next_label/stop_label/test_label/time_label/
  type_label` 全被忽略 —— 中文界面里这几个词一直是英文
- **环境自检不再有副作用**：`doctor` 以前会真的创建 `tests/` 目录并写入、删除
  探针文件；现在只做只读检查。另外自己监听着端口时不再误报 `WARN`（会显示
  `(listening)`）
- **键位去重**：7 条新命令原本各有两条上下文不同但命令完全相同的绑定，
  合并为一条复合选择器
- **死代码清理**：`LayoutListener.move_syncer`（从未挂事件）、空的 `isEnabled`、
  `REGION_POS/ACCEPT/DECLINE/UNKNOWN/OUT/LINE_PROP`、`BEGIN/OUT/END_TEST_STRING`、
  `TestSyntax.sublime-syntax` 里对已不存在的 `Test N {` / `} rtcode` 的高亮规则、
  全链路的 `use_debugger` 参数、`ProcessManager.get_path/has_var_view_api/
  new_test/communicate`、对拍 `_run_stress_loop` 未使用的首参
- `CphViewTesterCommand` 的 `ruler_opd_panel/have_tied_dbg/tied_dbg` 从类属性改为
  **实例属性**（多窗口下会互相覆盖）

## 新增：回归测试与 CI

这次崩溃本可以被几行单测拦住，所以补上了自动化：

- `tests/run_tests.py` —— 不依赖 Sublime：注入伪 `sublime` 模块后测试
  `cph_verdict` 的比较/判定（含浮点容差、真实内存判 MLE、PE）、
  `Tester.next_test` 的跳号补齐（就是本次 P0-1）、`is_skippable/
  next_runnable_index`、`ProcessManager` 的 shell 判定与 UTF-8 解码、
  测试数据路径解析。**26 项检查**
- `tests/check_py33.py` —— Python 3.3 兼容性守卫：扫描 f-string、walrus、
  变量注解、`subprocess.run`、`Popen(text=/encoding=/errors=)` 等；
  已验证它能精确拦住 v1.4.1 那个 bug
- `.github/workflows/tests.yml` —— push / PR 时在 Python 3.8 与 3.12 上
  跑守卫 + 回归测试 + 字节编译

---

# v1.4.1 更新内容（中文）—— 紧急修复

## 修复：Sublime 插件宿主是 Python 3.3，上一版用到了 3.6+ 的参数

- **症状**：编译成功后程序无法启动，控制台抛
  `TypeError: __init__() got an unexpected keyword argument 'errors'`，
  并且之后**一直卡在编译**（无法恢复，必须重启 Sublime）
- **原因**：v1.4.0 为了修正编码问题给 `subprocess.Popen` 加了
  `encoding='utf-8', errors='replace'`，而这两个参数是 Python 3.6/3.7 才有的；
  Sublime 的插件宿主是 Python 3.3（日志里的 `reloading python 3.3 plugin`）。
  更糟的是 `Popen` 抛异常时 `is_run` 已被置为 True，导致后续所有运行都被判为
  "进程已在运行"而被拒绝
- **修复**：改为**二进制管道 + 增量 UTF-8 解码**
  （`codecs.getincrementaldecoder('utf-8')('replace')`）。既能正确处理
  Windows 默认 cp936 带来的中文乱码，又完全不依赖 3.6+ 参数；
  逐字节同步读取模式下多字节字符被拆包也不会乱码
- **顺带修复**：`cph_stress.py` 用了 `subprocess.run(..., text=True)`
  （3.5+/3.7+ API），意味着**对拍功能在 Python 3.3 下一直是坏的**，
  现改为 `Popen` + `communicate`
- **自愈加固**：`Popen` 失败或从未启动时，`is_run`、`proc_run`、`is_stopped()`、
  `terminate()`、`insert()` 都不再抛异常或永久阻塞，异常后可以直接重试，
  不需要重启编辑器

## 开发验证

- 新增 `.workbuddy/harness_process.py`：不依赖 Sublime 即可对进程管理做回归
  验证（UTF-8 往返、逐字节解码、二次运行、未运行实例的安全性、内存采样）
- 新增 Python 3.3 兼容性 AST 扫描：确认代码中没有 f-string、`subprocess.run`、
  `Popen(text=/encoding=/errors=)`、walrus、3.5+ 标准库 API 等
- 实测结果：Windows 上峰值内存采样成功（示例进程 41.09 MB），中文输出正确，
  连续两次运行正常

---

# v1.4.0 更新内容（中文）

本轮针对一份第三方代码审查报告（P0-P5）逐条核实并修复，同时补齐此前规划的功能。
**重要**：这次修掉了"上线即炸"的打包问题与多个正确性缺陷。

## P0 正确性修复

- **打包后资源全部读不到（Package Control 上线阻塞项）**：全部 HTML/CSS 以前用真实
  文件路径 `open()` 读取，装成 `.sublime-package`（zip）后会抛 FileNotFoundError，
  卡片/详情/编译面板全部渲染失败。现已统一改用 `sublime.load_resource()`
  （新增 `core/cph_resources.py`，带进程内缓存），并补齐 `Modules/`、`Highlight/`
  的 `__init__.py`，让 zip 加载模式可靠工作
- **MLE 从来不会触发**：`Test.set_memory()` 全项目零调用点、判定函数从未拿到实际
  内存值。现新增 `Modules/memprobe.py`（零依赖）跨平台采样进程峰值内存：
  Windows `GetProcessMemoryInfo`、Linux `/proc/<pid>/status VmHWM`、
  macOS `getrusage`；内存超限真正判 `MLE`，卡片显示真实占用
- **macOS 上杀不掉正在运行的程序**：原来只有 Linux 走 `killpg`，macOS 只杀 shell，
  被评测程序在自己的进程组里继续跑。现 POSIX 全平台杀进程组，SIGTERM 后
  0.6s 未退出升级 SIGKILL；Windows 改用 `taskkill /F /T` 杀进程树
- **`load_session` 恢复失败时崩溃**：会话不存在时只插一条提示就继续执行，
  随后 `path.splitext(None)` TypeError、`code_view_id`/`dbg_file` 未定义。
  现已直接 `return`，并在 `__init__` 预置延迟属性
- **`kill_proc`（Ctrl+X）无保护**：tester 为 None 或进程已被回收时直接抛异常。
  现只在确实有进程运行时接管该键，否则回退默认行为
- **"Run with clean tests" 清不干净**：只清传统路径 `foo.cpp__tests`，
  `tests/foo.cpp__tests` 保留下来又被合并回来。现清空 `get_tests_paths()` 的全部路径
- **未保存文件 / 不支持的语言点 Run 崩溃**：`create_opd` 增加文件与扩展名校验并
  给出友好提示，`cph_view_tester` 增加 `is_enabled`（只约束 `make_opd`，
  面板收缩等命令不受影响）
- **`close_opds` 关掉所有运行面板**：多题工作流下开 B 题会连带销毁 A 题面板与会话。
  现只关闭与当前源文件配对的那个，并修掉 `name()` 为 None 的崩溃

## P0 数据与服务修复

- **Competitive Companion 的 `memoryLimit` 单位错误**：官方该字段就是 MB，
  代码却再除以 `1024*1024`，256MB 会变成 0。已修正
- **Companion 服务安全加固**：校验 `Host` 头（挡 DNS rebinding）、
  `Content-Length` 上限 10MB、所有 Sublime API 调用改到主线程
- **Companion 改为合并去重**：不再整体覆盖已有测试点（此前第二次点浏览器图标
  会丢掉之前 accept 的答案），与导入流程语义一致
- **TL/ML 持久化**：按源文件记住浏览器发来的时限/内存限制，之后手动
  Ctrl+Alt+B 不会再丢
- **导入缺陷**：快速面板选"选择其他文件"以前什么都不发生（`on_done(None)`），
  现在会打开路径输入框；文件夹批量导入的 `.in.txt` 以前只剥一层后缀导致
  `1.out.txt` 永远配不上；候选文件排序确定；读取数据文件增加 GBK/UTF-16 回退
  （中文 OJ 数据不再直接报错）

## P2 性能修复

- **逐字节读取导致的 O(n²) 输出**：`create_opd` 默认 `sync_out=True`，每个字节都
  触发一次视图插入 + 字符串拼接。现默认关闭（新增 `sync_output` 设置供交互式
  程序开启）
- **主线程阻塞**：重新运行时在 UI 线程 `sleep` 最长 2 秒 → 改为异步轮询；
  面板单测按钮里同步编译最长冻结 30 秒 → 改为异步编译
- **资源重复读盘**：每张卡片每次刷新都重新 `open()` HTML 与 CSS →
  改为 `load_resource` + 进程内缓存

## 新功能

- **编译缓存**：源文件（含 `extra_sources`）与编译命令未变时跳过编译
  （`compile_cache_enabled`，强制重编见下）
- **运行模式命令**：`Run all tests`（失败继续跑完）、
  `Re-run failed tests only`（跳过已 AC 的测试点）、`Run (force recompile)`
- **`stop_on_first_failure` 设置**：默认仍为第一个失败即停，可改为跑完全部
- **浮点容差** `float_tolerance`：数字型 token 按 `|a-b| <= tol*max(1,|a|,|b|)`
  比较，浮点题不再误判 WA
- **输出体积上限** `max_output_bytes`（默认 8MB）：超出部分丢弃并提示，
  防止疯狂输出卡死编辑器
- **多文件编译**：`run_settings` 新增 `extra_sources` / `include_dirs`，
  编译命令支持 `{extra_sources}` / `{include_dirs}` 占位符
- **模板片段 `Ctrl+Alt+T`**：实现此前 README 宣传但一直不存在的功能
  （原来 `Tab` 绑到从未定义的 `olympic_funcs`）。支持
  `algorithms_base` 目录、`templates` 设置与内置片段（fastio / main / bf / debug / testlib）
- **测试数据 I/O**：`Ctrl+Alt+V` 从剪贴板加测试点（`输入 --- 输出`）、
  `Ctrl+Alt+C` / `Ctrl+Alt+Shift+C` 复制预期/实际输出、
  `Ctrl+Alt+E` 导出 `1.in`/`1.out`
- **面板汇总行**：`4/5 通过 · 首个失败 test 3 · 总用时 1.24s`（`show_summary_bar`）
- **环境自检 `Ctrl+Alt+D`**：检查编译器是否在 PATH、端口占用、测试路径可写、
  资源可加载、扩展名是否有对应配置
- **对拍增强**：复用 `run_settings` 的编译/运行命令（不再硬编码
  `g++ -std=c++11`，避免对拍二进制与真实评测不一致）、比较口径与判题一致
  （`normalize_lines`）、发现反例自动保存为测试点、增加重入保护

## 仓库卫生

- `repository-cph-by-chenkx.json` 的 `sublime_text` 由 `*` 改为 `>=4095`
  （minihtml 的 CSS 变量语法需要 ST4）
- 删除失效的 `push_to_github.bat`（内含粘贴 token 流程、remote 指向错误的仓库）
  与个人脚本 `tools/create_release.py`
- 删除 8 个从未被引用的图标，只保留实际使用的 `arrow_left/right.png`
- 新增 `.gitattributes`（开发文件不进入 `.sublime-package`）、
  `messages.json` + `messages/install.txt`（安装后提示快捷键）
- 清理死设置（`lint_*`、`cpp_complete_enabled`）与死代码
  （`olympic_funcs` 绑定、`set_tests_status` 调用、`Tester.del_test/del_tests`、
  调试器遗留 `eval(frames)` 与幽灵 action、无人引用的 `CppVarHighlight.py`）
- 默认 `run_cmd` 改为正斜杠路径（Windows/Linux/macOS 通用），去掉无用的
  `-debug` 参数；新增 `cph-by-chenkx (Windows).sublime-settings` 平台覆盖
- 语言设置默认值与代码/文档对齐（`"language": "zh"`），改设置即时生效无需重启

---

# v1.2.2 更新内容（中文）

## 调整
- **移除 detail 语法高亮**：按用户反馈移除 `DetailSyntax.sublime-syntax`，
  详情视图恢复为纯文本显示；内容格式、布局、信息分区（输入 / 预期输出 /
  实际输出 / 错误 / 用时 / 逐行 diff）完全不变

---

# v1.2.1 更新内容（中文）

## Bug 修复
- **修复 "cant run process because is already running" 崩溃（next test 失效的根因）**：
  `ProcessManager.is_run` 在进程启动后从未被重置，导致第一个测试结束后
  "next test" 按钮和多样例自动连跑链全部抛 `AssertionError` 崩溃。
  现在进程结束 / 被杀时正确清除该标志，且 `run_file()` 遇到过期的
  `is_run` 标志（进程实际已退出）时自动恢复而不是崩溃
- **修复多个样例只运行第一个的问题**：Competitive Companion 抓取的多个样例
  依赖第一个测试结束后自动连跑下一个，该链路因上述崩溃而中断；修复后
  所有的样例会按顺序自动依次运行
- **修复重新运行时的竞态**：杀掉未结束进程前先递增 tester_epoch，
  被杀进程的迟到回调会被立即丢弃，不再有机会在新一轮运行开始前
  污染视图状态
- **修复关闭 -run 视图不终止进程**：`action: 'close'` 引用了不存在的
  `self.process_manager` 属性导致进程从未被终止，现改为 `self.tester.terminate()`
- **修复 next test 在监听线程异常死亡后卡死**：`proc_run` 标志残留时若进程
  实际已退出，自动恢复而不是永远提示 "already running"

## 改进
- **detail 高亮更可靠**：语法文件改为每次打开详情时都重新应用（此前仅在
  视图创建时设置一次，失败后永不恢复）；应用失败时向控制台输出诊断日志；
  语法规则扩充（标题行、汇总行着色）

---

# v1.2.0 更新内容（中文）

## Bug 修复
- **编辑面板按钮不可点**：编辑视图顶栏文字过长时 save 按钮超出可视范围，
  现已将 save / delete 按钮移到提示文字之前，默认侧边栏宽度下也可点击
- **残留编辑标签页**：点击 edit 未保存就重新运行程序时，旧的 `test N -edit` /
  `test N -answer` 标签页会残留且保存按钮失效；重新运行现在会自动关闭这些残留视图
- **重新运行不再卡死**：重新按 Ctrl+Alt+B 运行时会自动终止上一个未结束的进程
  （等待其退出后再重新运行），"next test" 恢复可用；基于 epoch 计数丢弃被杀进程的
  迟到回调，避免旧进程结束时污染新一轮运行状态
- **从文件导入样例菜单灰色不可用**：导入命令此前位于 `core/` 子包，Sublime 不会
  自动加载子包中的命令；现已移回根目录 `cph_import.py`，菜单恢复可用
- **导入样例改为追加模式**：从文件/文件夹导入不再覆盖原有样例，而是与现有测试
  合并去重（按输入+答案内容去重）后追加
- **verdict 徽章背景错位**：AC 等徽章的彩色背景未居中包裹文字，已改为纯内联元素
  让背景紧贴文字

## 新功能
- **详情视图显示样例输入**：详情中新增输入区段，方便对照输入排查输出差异
- **清除 `<0x0d>` 神秘字符**：Windows 程序输出的孤立 `\r` 在详情中不再显示为
  `<0x0d>`，已统一清理
- **详情双模式设置**：新增 `detail_style` 设置，`"view"`（默认，真实标签页可选中
  复制）与 `"phantom"`（旧版内嵌面板）两种模式可切换
- **详情语法高亮**：新增 `DetailSyntax.sublime-syntax`，详情视图按区块标题 /
  diff 差异行（红绿）/ 行号着色，不再是纯白文本

---

# v1.1.0 更新内容（中文）

## Bug 修复
- **修复 "Can't restore session" 破坏源代码的严重 bug**：浏览器扩展发送样例后，
  旧代码直接在源码视图上调用 `make_opd(load_session=True)`，会话不存在导致
  "Can't restore session" 文字被插入用户代码。现在改走正常 `view_tester` Run 流程
- **Competitive Companion 监听改为持久式（cph-ng 风格）**：一次启动后浏览器扩展可
  反复点击发送，不再出现多次点击报错；再次执行监听命令 = 切换目标文件；
  新增 `Stop Competitive Companion listener` 停止命令；插件卸载时自动释放端口
- **修复从文件导入样例功能失效**：`cph_import.py` 在此前提交中被误删导致菜单命令
  不存在，已恢复并移入 `core/` 子包；文件夹批量导入改用可靠的路径输入方式
- **修复 TestSyntax 语法文件引用错误**：代码引用了不存在的 `TestSyntax.tmLanguage`
  （实际为 `.sublime-syntax`），导致运行视图语法从未生效、`source.TestSyntax`
  相关键位（Enter / Ctrl+V / Ctrl+D / Ctrl+Alt+B 会话恢复等）全部失效

## 新功能
- **详情视图重构**：详情不再显示为无法选中文字的内嵌面板，而是打开真实编辑器
  标签页（`xxx - test N detail`），文字可选中可复制
- **逐行 diff**：详情视图中预期输出与实际输出逐行对比，忽略行末空格与末尾换行，
  只列出有差异的行（含"仅预期有 / 仅实际有"行），基于 difflib
- **标准答案编辑改为双标签页**：点击"编辑"打开 `test N -edit`（输入）与
  `test N -answer`（标准答案）两个标签页，保存时同时保存两者；
  移除容易被误删的 `------ answer ------` 分隔行方案
- **TLE 硬杀（cph-ng 行为）**：程序超过时间限制自动终止并判 `TLE`，
  死循环不再需要手动停止；手动停止的测试显示 `SK`（skipped）徽章
- **会话状态恢复**：重开 Sublime 后测试点可恢复上次运行的 verdict / 用时 / 输出，
  详情视图在重载后依然可用
- 新增 `companion_port` 设置可自定义监听端口

## 文档
- README 同步更新详情 / 编辑 / 监听 / TLE 相关说明

---

# v1.0.6 - v1.0.7 更新内容（中文）

## 修复内容
- 修复编译卡住问题（`ProcessManager.compile()` 使用 `stdin=PIPE` 导致死锁，已改为 `stdin=None`）
- 修复 `run_file()` 的 `is_run` 守护条件（原代码 `if self.is_run and False:` 始终为假，已修复）
- 修复编译命令设置不匹配：`compile_cmd` 输出名已包含 `.exe`（与 `run_cmd` 一致），标准已改为 `-std=c++11`（与 README 示例一致）
- 修复状态标签不一致：`test_manager.py` 中 `COMPILE` 已改为 `COMPILING`，与编译状态一致
- 修复 `tempfile.TemporaryFile()` 在 Python 3.3 不支持 `encoding` / `errors` 参数的问题（已改为二进制模式 `w+b`，`get_stderr()` 已添加解码）

## 视觉调整
- 恢复原 `CppFastOlympicCoding` 插件的卡片间距（`padding: 1px`、`margin-right: 4px`），避免重叠
- `time:` 显示颜色已从绿色改回原插件蓝色（`var(--bluish)`）
- 新增功能（判决徽章、详情面板、编辑/运行按钮、时间/内存显示、对拍）已按原插件样式模板布置，与原插件风格一致
- 所有 CSS 样式文件（包括 Spacegray / Spacegray Light 主题）已同步更新

## 新增功能（基于原 `CppFastOlympicCoding` 源码）
- 彩色判决徽章（AC 绿 / WA 红 / TLE 深蓝 / MLE 紫 / RE 蓝 / PE 粉 / CE 黄 / UKE 灰）
- 详情面板：点击“详情”按钮可展开，显示输入 / 预期输出 / 实际输出 / 错误信息 / 运行时间 / 内存占用
- 运行结果下方显示 `accept` / `decline` 按钮（标记正确/错误答案）
- 右键菜单支持 `Listen to Competitive Companion`（端口 12345 自动接收样例和限制）
- 国际化支持：默认中文，可通过设置 `"language": "en"` 切换英文
- 对拍功能（`Ctrl+Alt+S`）支持随机数据生成器对比

## 技术说明
- 本插件基于开源项目 `CppFastOlympicCoding`（`https://github.com/Jatana/FastOlympicCoding`）的源码构建
- 所有修改直接应用于原插件源码结构，保持与原插件一致的排版和行为
- 无 AI 代码生成痕迹（所有修复均为人工逐步排查和手动修改）
