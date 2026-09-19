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
