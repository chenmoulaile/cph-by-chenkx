# cph-by-chenkx

cph-by-chenkx 是基于 [FastOlympicCoding](https://github.com/Jatana/FastOlympicCoding) 的 Sublime Text 插件，
参考 VSCode 的 [cph-ng](https://github.com/langningchen/cph-ng) 实现了更加友好的 C++ 测评结果显示，
并集成 [Competitive Companion](https://github.com/jmerle/competitive-companion) 浏览器插件支持。

## 主要功能

### 1. 类似 cph-ng 的测评结果显示

每个测试点会显示：
- **彩色 verdict 徽章**：`AC`（绿）、`WA`（红）、`TLE`（深蓝）、`MLE`（紫）、`RE`（蓝）、`PE`（粉）、`CE`（黄）等
- **运行时间**：毫秒级显示，超过 5 秒自动转换为秒
- **内存占用**：MB / GB 显示（跨平台真实采样进程峰值内存，Windows 用 `GetProcessMemoryInfo`、Linux 读 `/proc/<pid>/status VmHWM`、macOS 用 `getrusage`），超限会真的判 `MLE`
- **超时硬杀**：程序超过时间限制会被自动终止并判 `TLE`（cph-ng 行为），
  不会再出现死循环杀不掉的问题；手动停止的测试显示 `SK`
- **三个按钮**：`编辑`、`运行`、`详情`

### 2. 详情视图（detail）+ 逐行 diff

点击每个测试点的 `详情` 按钮，会打开一个真实的编辑器标签页
（`xxx - test N detail`），文字**可选中、可复制**，方便对比：

- **预期输出** (Expected Output)
- **实际输出** (Actual Output)
- **Diff**：预期输出与实际输出**逐行对比**（忽略行末空格与末尾换行），
  不同的行会标出 `expected` / `actual`，只列出有差异的行
- **错误输出** (Error Output / stderr)
- 顶部显示 verdict + 运行时间 + 内存占用

运行结束后再次点击 `详情` 会自动刷新内容。

### 3. 正确/错误答案快捷标记

测试运行结束后，会在输出下方出现 `accept` / `decline` 按钮：
- 点击 `accept` - 把当前输出标记为正确答案
- 点击 `decline` - 把当前输出标记为错误答案

### 4. 集成 Competitive Companion 浏览器插件

参考 [FastOlympicCodingHook](https://github.com/DrSchwad/FastOlympicCodingHook) 实现了 Competitive Companion 支持：

1. 在 Sublime Text 中打开你要做题的代码文件
2. 右键点击文件，选择 `cph-by-chenkx: Listen to Competitive Companion`
3. 在浏览器中打开题目页面，点击 Competitive Companion 扩展的绿色 + 图标
4. 题目样例和时间/内存限制会自动发送到 Sublime Text，保存到测试文件中并自动运行

监听器是**持久**的（cph-ng 风格）：
- 启动一次后浏览器扩展可以**反复点击**发送不同题目，不会出现端口冲突
  或 "Can't restore session" 之类的错误
- 在另一个代码文件上再次执行该命令 = 把监听目标切换到那个文件
- `Stop Competitive Companion listener` 可随时停止监听

**注意**：需要在 Competitive Companion 浏览器扩展的端口列表中添加 `12345`
（可用 `cph-by-chenkx.sublime-settings` 的 `companion_port` 修改）。

### 5. 国际化 (i18n)

默认使用中文显示，可以通过以下方式切换语言：

- **菜单**：`Tools` -> `cph-by-chenkx` -> `Switch language (中/EN)`
- **命令面板**：`cph-by-chenkx: Switch to English` / `切换为中文`
- **右键菜单**：`Switch language (中/EN)`
- **快捷方式**：在 `cph-by-chenkx.sublime-settings` 中设置 `"language": "en"` 或 `"language": "zh"`

### 6. 测试面板自适应宽度

右侧运行面板默认只占窗口的 32%，窗口较窄或字体较大时，测试卡片的按钮
（`edit` / `run` / `detail` / `time` ...）会因宽度不够而换行堆叠。

插件会在每次刷新测试卡片后自动加宽右侧面板，直到最宽的卡片能在一行内
放下为止，并且：

- **只在需要时加宽**：卡片放得下就保持原样，从不自动收窄
- **上限为半个窗口**：最多加宽到窗口布局的 50%（可配置）
- 可通过 `cph-by-chenkx.sublime-settings` 关闭或调整上限：

```json
{
	"auto_fit_panel_width": true,
	"max_panel_width_ratio": 0.5
}
```

## 安装

1. 克隆或下载本仓库
2. 将 `cph-by-chenkx` 文件夹复制到 Sublime Text 的 `Packages` 目录
3. 重启 Sublime Text

## 使用方法

1. 打开 C++ 源文件
2. 按 `Ctrl+Alt+B` (Mac: `Cmd+Alt+B`) 启动测评
3. 右侧会打开一个测试运行窗口，可以输入/编辑测试数据
4. 测评结束后，每个测试点会显示 verdict 徽章
5. 点击 `详情` 打开带逐行 diff 的详情标签页；点击 `编辑` 会打开
   输入 (`test N -edit`) 与标准答案 (`test N -answer`) 两个标签页，
   在答案页填入预期输出后 `save`，即可自动重新评判

### 6. 运行模式与效率

- **编译缓存**：源文件（含多文件）与编译命令没变时跳过编译直接跑，
  改样例反复调试时不再每次等编译；需要时用 `Ctrl+Alt+Shift+R` 强制重编
- **只重跑失败 / 跑完全部**：`Ctrl+Alt+R` 只重跑没 AC 的测试点，
  `Ctrl+Alt+Shift+B` 跑完全部（默认第一个失败即停，可用
  `stop_on_first_failure` 改默认行为）
- **浮点容差**：设置 `float_tolerance`（如 `1e-6`）后，数字型输出按
  相对/绝对误差比较，浮点题不再因为 `0.1+0.2 != 0.3` 误判 `WA`
- **输出上限**：`max_output_bytes`（默认 8MB）防止程序在时限内疯狂输出卡死编辑器
- **多文件编译**：在 `run_settings` 里用 `extra_sources`（glob）与
  `include_dirs`，编译命令中用 `{extra_sources}` / `{include_dirs}` 占位符
- **面板汇总行**：运行面板底部显示 `4/5 通过 · 首个失败 test 3 · 总用时 1.24s`
- **环境自检**：`Ctrl+Alt+D` 一条命令检查编译器是否在 PATH、端口占用、
  测试路径可写、资源可加载，排查问题先跑它
- **对拍反例入库**：对拍发现反例会自动保存成一个正式测试点（可用
  `stress_save_counterexample` 关闭）


> **关于默认运行命令**：默认 `run_cmd` 使用正斜杠路径，Windows / Linux / macOS
> 通用（Windows 也接受反斜杠）。想换成自己的写法，把 `run_settings` 复制到
> User 设置里覆盖即可。

## 已知限制

- **macOS 的内存占用**是单进程实时采样（`libproc.proc_pid_rusage`）的峰值，
  不是内核严格意义上的峰值 RSS，因此显示的数值可能比 Activity Monitor 略低；
  它已经不会再用 `RUSAGE_CHILDREN` 那种「所有子进程累计峰值」的错误口径。
- **`sync_output`（逐字符同步输出）默认关闭**：开启后输出会一个字符一次刷新视图，
  只适合交互式程序；普通题目保持关闭，输出量大时才不会卡。
- **`PE`（Presentation Error）判定**：只有「token 完全相同但空白/换行不同」才算 PE。
  默认与 WA 分别显示；若你的 OJ 把 PE 也算通过，把 `regard_pe_as_ac` 设为 `true` 即可。
- 判定使用首个测试点的答案文件时，若程序输出超过 `max_output_bytes`（默认 8MB），
  超出部分会被丢弃，输出里会插入一行截断提示。

## 快捷键

| 按键 | 功能 |
| --- | --- |
| `Ctrl+Alt+B` (Mac: `Cmd+Alt+B`) | 运行测试 |
| `Ctrl+Alt+I` (Mac: `Cmd+Alt+I`) | 从文件导入测试 |
| `Ctrl+Alt+S` / `Ctrl+Alt+Shift+S` (Mac: `Cmd+Alt+S` / `Cmd+Alt+Shift+S`) | 开始 / 停止对拍 |
| `Ctrl+Alt+L` / `Ctrl+Alt+Shift+L` (Mac: `Cmd+Alt+L` / `Cmd+Alt+Shift+L`) | 开启 / 停止 Competitive Companion 监听 |
| `Ctrl+Alt+P` 或 `Ctrl+K, Ctrl+P` (Mac: `Cmd+Alt+P` 或 `Cmd+K, Cmd+P`) | 收缩 / 恢复右侧测试面板 |
| `Ctrl+Alt+T` (Mac: `Cmd+Alt+T`) | 展开模板片段（光标停在关键字后，如 `fastio`） |
| `Ctrl+Alt+V` (Mac: `Cmd+Alt+V`) | 用剪贴板内容新增测试点（`输入 --- 输出` 可同时带答案） |
| `Ctrl+Alt+C` / `Ctrl+Alt+Shift+C` | 复制当前测试的 预期输出 / 实际输出 |
| `Ctrl+Alt+E` (Mac: `Cmd+Alt+E`) | 把全部测试导出成 `1.in` / `1.out` 文件对 |
| `Ctrl+Alt+R` (Mac: `Cmd+Alt+R`) | 只重跑失败的测试点（已 AC 的自动跳过） |
| `Ctrl+Alt+Shift+B` | 跑完全部测试点（不因失败中断） |
| `Ctrl+Alt+Shift+R` | 强制重新编译后运行（忽略编译缓存） |
| `Ctrl+Alt+D` (Mac: `Cmd+Alt+D`) | 环境自检（编译器 / 端口 / 路径 / 资源） |
| `Ctrl+Alt+M` (Mac: `Cmd+Alt+M`) | 键盘选择测试点并运行 / 详情 / 编辑（不用鼠标） |
| `Enter` (在 TestSyntax 中) | 插入行 |
| `Ctrl+Enter` (在 TestSyntax 中) | 新建测试 |
| `Ctrl+V` / `Cmd+V` (在 TestSyntax 中) | 粘贴 |
| `Ctrl+X` / `Cmd+X` (在 TestSyntax 中) | 终止进程 |
| `Ctrl+D` / `Cmd+D` (在 TestSyntax 中) | 删除测试 |
| `Ctrl+Shift+Up/Down` (在 TestSyntax 中) | 交换测试顺序 |

## 对拍 (Stress Test) 教程

对拍 = 用随机数据生成器不停地测试你的程序和标准程序 (std)，一旦两者输出不一致就停下来，把出错的输入和两边输出展示给你。适合排查 WA 的边界情况。

### 1. 准备三个文件（放在同一目录）

- **你的程序**：当前打开的文件，比如 `main.cpp`
- **标准程序 std**：保证正确的写法（暴力 / 题解做法），默认文件名 `std.cpp`
- **数据生成器 gen**：往标准输出 (stdout) 打印一组随机测试数据，默认文件名 `gen.cpp`

`gen.cpp` 示例（随机生成两个 1~10 的数）：

```cpp
#include <bits/stdc++.h>
using namespace std;
int main() {
    srand(time(0) + rand());
    int a = rand() % 10 + 1, b = rand() % 10 + 1;
    printf("%d %d\n", a, b);
    return 0;
}
```

### 2. 启动对拍

在**你的程序**的编辑视图里，任选一种方式：

- 菜单: `View -> cph-by-chenkx -> Start stress test`
- 命令面板: `cph-by-chenkx: Start stress test`
- 快捷键: `Ctrl+Alt+S` (Mac: `Cmd+Alt+S`)

然后依次确认（直接回车就用默认值）：

1. std 文件路径（默认 `std.cpp`）
2. 生成器文件路径（默认 `gen.cpp`）
3. 每轮时间限制秒数（默认 2）
4. 最大对拍轮数（默认 1000）

选过的 std / gen 路径会被记住，下次直接回车即可。

### 3. 查看结果

会打开一个 `xxx -stress` 输出窗口：

- 每轮通过会滚动显示 `第 N 轮 ... OK`
- **发现不一致**时立即停止，展示：输入数据、你的输出、std 输出、以及逐行差异 (`user:` vs `std:`)，拿着这个输入去调试即可
- 跑满最大轮数全部一致则显示对拍通过
- 中途可随时用 `Stop stress test`（或 `Ctrl+Alt+Shift+S`）停止

### 4. 注意事项

- 三个程序都从 stdout 读入/输出，不要把调试信息打到 stdout（可用 `cerr`，配合 `"ignore_stderr": true` 设置）
- Python 文件也可以直接作为你的程序 / std / gen 参与对拍
- 对拍用 `g++ -std=c++11 -O2` 独立编译，不影响正常测评的编译命令

## 致谢

本插件基于以下开源项目：

- [FastOlympicCoding](https://github.com/Jatana/FastOlympicCoding) - 基础框架
- [cph-ng](https://github.com/langningchen/cph-ng) - verdict 颜色和详情面板设计灵感
- [FastOlympicCodingHook](https://github.com/DrSchwad/FastOlympicCodingHook) - Competitive Companion 集成代码

## 设置示例

在 `cph-by-chenkx.sublime-settings` 中：

```json
{
	"language": "zh",  // "zh" 中文 (默认) 或 "en" 英文
	"run_settings": [
		{
			"name": "C++",
			"extensions": ["cpp"],
			"compile_cmd": "g++ \"{source_file}\" -std=c++11 -o \"{file_name}\"",
			"run_cmd": "\"{source_file_dir}\\{file_name}.exe\" {args} -debug",
			"time_limit_ms": 2000,
			"memory_limit_mb": 256
		}
	],
	"tests_relative_dir": ""
}
```
