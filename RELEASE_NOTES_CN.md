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
