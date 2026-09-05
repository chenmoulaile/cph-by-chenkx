# cph-by-chenkx

cph-by-chenkx 是基于 [FastOlympicCoding](https://github.com/Jatana/FastOlympicCoding) 的 Sublime Text 插件，
参考 VSCode 的 [cph-ng](https://github.com/langningchen/cph-ng) 实现了更加友好的 C++ 测评结果显示，
并集成 [Competitive Companion](https://github.com/jmerle/competitive-companion) 浏览器插件支持。

## 主要功能

### 1. 类似 cph-ng 的测评结果显示

每个测试点会显示：
- **彩色 verdict 徽章**：`AC`（绿）、`WA`（红）、`TLE`（深蓝）、`MLE`（紫）、`RE`（蓝）、`PE`（粉）、`CE`（黄）等
- **运行时间**：毫秒级显示，超过 5 秒自动转换为秒
- **内存占用**：MB / GB 显示
- **三个按钮**：`编辑`、`运行`、`详情`

### 2. 详情面板（detail）

点击每个测试点的 `详情` 按钮，可以展开一个详细面板（类似 cph-ng）显示：
- **输入** (Input)
- **预期输出** (Expected Output)
- **实际输出** (Actual Output)
- **正确答案** (Correct Answer) - 正确输出单独显示在下方
- **错误输出** (Error Output)
- **评判信息** (Verdict) + 运行时间 + 内存占用

### 3. 正确/错误答案快捷标记

测试运行结束后，会在输出下方出现 `accept` / `decline` 按钮：
- 点击 `accept` - 把当前输出标记为正确答案
- 点击 `decline` - 把当前输出标记为错误答案

### 4. 集成 Competitive Companion 浏览器插件

参考 [FastOlympicCodingHook](https://github.com/DrSchwad/FastOlympicCodingHook) 实现了 Competitive Companion 支持：

1. 在 Sublime Text 中打开你要做题的代码文件
2. 右键点击文件，选择 `cph-by-chenkx: Listen to Competitive Companion`
3. 在浏览器中打开题目页面，点击 Competitive Companion 扩展的绿色 + 图标
4. 题目样例和时间/内存限制会自动发送到 Sublime Text，保存到测试文件中

**注意**：需要在 Competitive Companion 浏览器扩展的端口列表中添加 `12345`。

### 5. 国际化 (i18n)

默认使用中文显示，可以通过以下方式切换语言：

- **菜单**：`Tools` -> `cph-by-chenkx` -> `Switch language (中/EN)`
- **命令面板**：`cph-by-chenkx: Switch to English` / `切换为中文`
- **右键菜单**：`Switch language (中/EN)`
- **快捷方式**：在 `cph-by-chenkx.sublime-settings` 中设置 `"language": "en"` 或 `"language": "zh"`

## 安装

1. 克隆或下载本仓库
2. 将 `cph-by-chenkx` 文件夹复制到 Sublime Text 的 `Packages` 目录
3. 重启 Sublime Text

## 使用方法

1. 打开 C++ 源文件
2. 按 `Ctrl+Alt+B` (Mac: `Cmd+Alt+B`) 启动测评
3. 右侧会打开一个测试运行窗口，可以输入/编辑测试数据
4. 测评结束后，每个测试点会显示 verdict 徽章
5. 点击 `详情` 展开详细结果

## 快捷键

| 按键 | 功能 |
| --- | --- |
| `Ctrl+Alt+B` (Mac: `Cmd+Alt+B`) | 运行测试 |
| `Ctrl+Alt+I` (Mac: `Cmd+Alt+I`) | 从文件导入测试 |
| `Ctrl+Alt+S` (Mac: `Cmd+Alt+S`) | 开始对拍 |
| `Ctrl+Alt+Shift+S` (Mac: `Cmd+Alt+Shift+S`) | 停止对拍 |
| `Ctrl+K, Ctrl+P` (Mac: `Cmd+K, Cmd+P`) | 同步 OPdebug |
| `Tab` (在 C++ 源码中) | 插入模板 |
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
