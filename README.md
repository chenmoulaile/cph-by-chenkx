# cph-by-chenkx

**Sublime Text 上更「能打」的算法竞赛测评插件** —— 一个测试点卡片 + 彩色 verdict + 逐行 diff 详情 + 真实内存/超时判定的完整闭环。

> **基于什么开发**：本插件是 **[FastOlympicCoding](https://github.com/Jatana/FastOlympicCoding)**（Jatana）的深度二次开发版本，
> 参考 VSCode 的 **[cph-ng](https://github.com/langningchen/cph-ng)** 重做了判题结果显示（彩色 verdict、详情面板、逐行 diff），
> 并借鉴 **[FastOlympicCodingHook](https://github.com/DrSchwad/FastOlympicCodingHook)** 集成了 [Competitive Companion](https://github.com/jmerle/competitive-companion) 浏览器插件支持。

---

## 相比原版 FastOlympicCoding，多了什么

| 能力 | FastOlympicCoding | cph-by-chenkx |
| --- | --- | --- |
| 彩色 verdict 徽章（AC/WA/TLE/MLE/RE/PE/CE…） | ❌ 只有纯文本 | ✅ 类 cph-ng 的徽章样式 |
| **真实内存判定（MLE）** | ❌ 内存是死配置 | ✅ 跨平台采样进程峰值内存，超限真判 MLE |
| **超时硬杀（TLE）** | ❌ 死循环杀不掉 | ✅ 看门狗到点终止整个进程树 |
| **运行错误定位（RE 位置）** | ❌ | ✅ 从程序输出解析 `文件:行号`（Python 回溯 / Java 栈 / `-fsanitize` 诊断） |
| 详情视图 + **逐行 diff** | ❌ | ✅ 独立标签页，可选中可复制 |
| **编译缓存** | ❌ 每次都重编 | ✅ 源文件/命令未变则跳过编译 |
| 只重跑失败 / 跑完全部 / 强制重编 | ❌ | ✅ 三个命令 + 快捷键 |
| **浮点容差**（`float_tolerance`） | ❌ | ✅ 浮点题不再因 `0.1+0.2 != 0.3` 误判 |
| 输出体积上限（防卡死） | ❌ | ✅ `max_output_bytes` |
| 多文件编译（`extra_sources` / `include_dirs`） | ❌ | ✅ |
| 环境自检 doctor | ❌ | ✅ 一条命令排查 + 可粘贴的 Markdown 报告 |
| 纯键盘操作（选测试点→操作） | ❌ | ✅ `Ctrl+Alt+M` |
| 对拍反例自动入库 | ❌ | ✅ |
| Competitive Companion 持久监听 | ⚠️ 需 Hook | ✅ 内建、可反复点击 |
| 中英文双语界面 | ❌ | ✅ |
| 测试面板自适应宽度 | ❌ | ✅ 卡片放不下时自动加宽 |

工程上还有：**Python 3.3 兼容**（Sublime 插件宿主）、四平台 CI（Linux 3.8/3.12 + Windows + macOS）、**80+ 项回归测试**。

---

## 主要功能

### 1. 类 cph-ng 的测评结果显示

每个测试点显示：

- **彩色 verdict 徽章**：`AC`（绿）、`WA`（红）、`TLE`（黄）、`MLE`（紫）、`RE`（蓝）、`PE`（粉）、`CE`（黄）等
- **运行时间**：毫秒级，超过 5 秒自动换算成秒
- **内存占用**：MB / GB（**跨平台真实采样进程峰值内存**：Windows 用 `GetProcessMemoryInfo`、Linux 读 `/proc/<pid>/status` 的 `VmHWM`、macOS 用 `libproc.proc_pid_rusage`），超限会真的判 `MLE`
- **超时硬杀**：超过时间限制会被自动终止并判 `TLE`，不会出现死循环杀不掉；手动停止的测试显示 `SK`
- **运行错误定位**：程序崩溃（`RE`）时，若输出里有位置信息（Python 回溯、Java 栈、`-fsanitize` 诊断），卡片详情会显示 `运行错误 (RE) 位置: main.py:12`，状态栏同时提示
- **三个按钮**：`编辑`、`运行`、`详情`

> **C++ 想拿到 RE 行号？** 普通的段错误不带行号。把编译命令加上
> `-fsanitize=address,undefined -g -fno-omit-frame-pointer`（在 `run_settings` 里自定义
> `compile_cmd`），崩溃时就会输出 `main.cpp:12:5: runtime error: ...`，插件会自动解析出行号。

### 2. 详情视图（detail）+ 逐行 diff

点击 `详情` 打开一个真实的编辑器标签页（`xxx - test N detail`），文字**可选中、可复制**：

- **预期输出** / **实际输出** / **错误输出 (stderr)**
- **Diff**：预期与实际**逐行对比**（忽略行末空格与末尾换行），只列出有差异的行
- 顶部显示 verdict + 运行时间 + 内存占用

运行结束后再次点击 `详情` 会自动刷新。

### 3. 正确/错误答案快捷标记

运行结束后输出下方出现 `accept` / `decline`：`accept` 把当前输出记为正确答案，`decline` 记为错误答案。

### 4. 集成 Competitive Companion 浏览器插件

1. 在 Sublime Text 中打开要做题的代码文件
2. 右键选择 `cph-by-chenkx: Listen to Competitive Companion`
3. 浏览器打开题目页，点 Competitive Companion 扩展的绿色 `+`
4. 样例与时间/内存限制自动发送到 Sublime Text、存进测试文件并自动运行

监听器是**持久**的（cph-ng 风格）：启动一次后可**反复点击**发送不同题目，不会端口冲突或报 "Can't restore session"；在另一个文件上再次执行该命令 = 切换监听目标；`Stop Competitive Companion listener` 随时停止。

**注意**：需要在 Competitive Companion 扩展的端口列表里加入 `12345`（可用设置项 `companion_port` 修改）。

### 5. 国际化 (i18n)

默认中文，可切换：

- **菜单**：`Tools` → `cph-by-chenkx` → `Switch language (中/EN)`
- **命令面板**：`cph-by-chenkx: Switch to English` / `切换为中文`
- **右键菜单**：`Switch language (中/EN)`
- **设置**：`"language": "en"` 或 `"zh"`

### 6. 运行模式与效率

- **编译缓存**：源文件（含多文件依赖）与编译命令没变时跳过编译；需要时 `Ctrl+Alt+Shift+R` 强制重编
- **只重跑失败 / 跑完全部**：`Ctrl+Alt+R` 只重跑没 AC 的点，`Ctrl+Alt+Shift+B` 跑完全部（默认第一个失败即停，可用 `stop_on_first_failure` 改）
- **浮点容差**：设置 `float_tolerance`（如 `1e-6`），数字型输出按相对/绝对误差比较
- **输出上限**：`max_output_bytes`（默认 8MB）防止疯狂输出卡死编辑器，超出部分会被截断并给出提示
- **多文件编译**：`run_settings` 里用 `extra_sources`（glob）与 `include_dirs`，编译命令中用 `{extra_sources}` / `{include_dirs}` 占位符
- **面板汇总行**：底部显示 `4/5 通过 · 首个失败 test 3 · 总用时 1.24s`
- **环境自检**：`Ctrl+Alt+D` 检查编译器是否在 PATH、端口占用、测试路径可写、资源可加载，并给出一段可粘贴到 issue 的 Markdown 报告
- **纯键盘流**：`Ctrl+Alt+M` 选测试点 → 运行 / 详情 / 编辑 / 接受 / 拒绝 / 删除
- **对拍反例入库**：对拍发现反例自动保存为正式测试点（可用 `stress_save_counterexample` 关闭）
- **统一合并策略**：导入文件 / 剪贴板 / 浏览器 / 对拍反例四条路径共用「按输入去重、答案只补不覆盖」，重发样例不会顶掉你手动标记的答案

### 7. 测试面板自适应宽度

右侧运行面板默认只占窗口 32%；卡片按钮放不下时，插件会在每次刷新后自动加宽，直到最宽的卡片能一行放下：

- **只在需要时加宽**，从不自动收窄
- **上限为半个窗口**（可配置）

```json
{
	"auto_fit_panel_width": true,
	"max_panel_width_ratio": 0.5
}
```

## 安装

1. 克隆或下载本仓库
2. 把 `cph-by-chenkx` 文件夹复制到 Sublime Text 的 `Packages` 目录
3. 重启 Sublime Text

## 使用方法

1. 打开 C++ 源文件
2. 按 `Ctrl+Alt+B`（Mac：`Cmd+Alt+B`）启动测评
3. 右侧打开测试运行窗口，可输入/编辑测试数据
4. 测评结束后每个测试点显示 verdict 徽章
5. 点 `详情` 看带逐行 diff 的详情页；点 `编辑` 打开输入（`test N -edit`）与标准答案（`test N -answer`）两个标签页，在答案页填好预期输出后 `save` 即可自动重新评判

> **关于默认运行命令**：默认 `run_cmd` 用正斜杠路径，Windows / Linux / macOS 通用。想换成自己的写法，把 `run_settings` 复制到 User 设置里覆盖即可。

## 已知限制

- **macOS 内存占用**是单进程实时采样（`libproc.proc_pid_rusage`）的峰值，不是内核严格意义上的峰值 RSS，可能比 Activity Monitor 略低；已不再使用 `RUSAGE_CHILDREN`（所有子进程累计峰值）那种错误口径。
- **裸段错误（C++）不带行号**：RE 位置只在程序输出包含位置信息时才有（Python 回溯 / Java 栈 / `-fsanitize` 诊断）；纯 C++ 段错误需要自行加 `-fsanitize` 编译。
- **`sync_output`（逐字符同步输出）默认关闭**：开启后一个字符刷新一次视图，只适合交互式程序。
- **`PE`（Presentation Error）**：只有「token 完全相同但空白/换行不同」才算 PE，默认与 WA 分别显示；若你的 OJ 把 PE 也算通过，把 `regard_pe_as_ac` 设为 `true`。
- 输出超过 `max_output_bytes`（默认 8MB）时超出部分会被丢弃，并插入一行截断提示。
- **非 ASCII 文件名靠自动识别**：Windows 上编译器按 ANSI 代码页写出的 `中文.exe`
  在磁盘上会变成另一个名字（GBK 字节被当成 latin-1 读），插件编译后会核对产物、
  按真实的文件名去运行，并在控制台说明（`the binary is ... on disk, not ...`）。
  如果你的编译命令把 `-o` 写到别处，请保证输出名用引号包起来。

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

对拍 = 用随机数据生成器不停测试你的程序和标准程序 (std)，一旦输出不一致就停下，把出错的输入和两边输出展示给你。适合排查 WA 的边界情况。

### 1. 准备三个文件（放在同一目录）

- **你的程序**：当前打开的文件，如 `main.cpp`
- **标准程序 std**：保证正确的写法（暴力 / 题解做法），默认 `std.cpp`
- **数据生成器 gen**：往 stdout 打印一组随机数据，默认 `gen.cpp`

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

在**你的程序**的编辑视图里任选一种：

- 菜单：`View` → `cph-by-chenkx` → `Start stress test`
- 命令面板：`cph-by-chenkx: Start stress test`
- 快捷键：`Ctrl+Alt+S` (Mac: `Cmd+Alt+S`)

然后依次确认（直接回车用默认值）：std 文件路径（默认 `std.cpp`）→ 生成器路径（默认 `gen.cpp`）→ 每轮时间限制秒数（默认 2）→ 最大轮数（默认 1000）。选过的路径会被记住。

### 3. 查看结果

会打开 `xxx -stress` 输出窗口：

- 每轮通过滚动显示 `第 N 轮 ... OK`
- **发现不一致**时立即停止，展示：输入数据、你的输出、std 输出、逐行差异（`user:` vs `std:`）
- 跑满最大轮数全部一致则显示对拍通过；全部轮次超时会明确提示「未比较任何输出」
- 中途可用 `Stop stress test`（`Ctrl+Alt+Shift+S`）停止

### 4. 注意事项

- 三个程序都从 stdin 读、往 stdout 写，调试信息请用 `cerr`（配合 `"ignore_stderr": true`）
- Python 文件也可以直接作为你的程序 / std / gen 参与对拍
- 对拍会使用 `run_settings` 里的编译命令；失败的反例可自动存为正式测试点
- **生成器有独立的时间上限**：`stress_generator_time_limit_seconds`（默认 10 秒）。
  造数据通常比解题慢，用程序本身的时限（`stress_time_limit_seconds`）卡生成器会把
  「生成器超时」误判成「生成器失败」。生成器超时会跳过该轮，连续 3 次才停止并提示。
- **`-DLOCAL` + 循环里的 `debug()` 会让本地运行超时**：`std::cerr` 默认不缓冲，把整个
  数组丢给 `cerr` 的调试语句放在主循环里时，输出量是 O(n²)，本地 n=2000 就要 20 秒以上
  （实测同一份代码不加 `-DLOCAL` 只要 0.02 秒）。提交前记得删掉这类调试输出，或把编译
  命令里的 `-DLOCAL` 去掉。

## 致谢

本插件基于以下开源项目：

- [FastOlympicCoding](https://github.com/Jatana/FastOlympicCoding) —— **基础框架（本插件由其二次开发而来）**
- [cph-ng](https://github.com/langningchen/cph-ng) —— verdict 颜色与详情面板设计灵感
- [FastOlympicCodingHook](https://github.com/DrSchwad/FastOlympicCodingHook) —— Competitive Companion 集成思路

## 设置示例

在 `cph-by-chenkx.sublime-settings` 中：

```json
{
	"language": "zh",
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

> 想要 C++ 崩溃时给出**行号**，把 `compile_cmd` 改成：
> `g++ "{source_file}" -std=c++11 -g -fsanitize=address,undefined -fno-omit-frame-pointer -o "{file_name}"`
