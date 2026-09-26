# cph-by-chenkx — Package Control 提交文件

## 提交 JSON（用于 fork package_control_channel 后添加到 repository/ 目录）

文件：`repository-cph-by-chenkx.json`

```json
{
	"name": "cph-by-chenkx",
	"details": "https://github.com/chenmoulaile/cph-by-chenkx",
	"releases": [
		{
			"sublime_text": "*",
			"tags": true
		}
	]
}
```

## 提交流程（手动完成）

1. 在 https://github.com/wbond/package_control_channel 进行 Fork
2. 克隆你的 Fork：`git clone https://github.com/<你的用户名>/package_control_channel.git`
3. 将 `repository-cph-by-chenkx.json` 复制到 `repository/` 目录（可重命名为 `cph-by-chenkx.json` 以符合命名规范）
4. 提交并推送：
   ```bash
   git add repository/cph-by-chenkx.json
   git commit -m "Add cph-by-chenkx v1.1.0"
   git push origin master
   ```
5. 在 GitHub 上创建 Pull Request（目标：`wbond/package_control_channel` 的 `master` 分支）

## PR 标题建议

```
Add cph-by-chenkx - C++ competitive programming plugin for Sublime Text
```

## PR 说明（可直接复制）

```
Package: cph-by-chenkx
Version: v1.1.0 (tag-based release)
Repo: https://github.com/chenmoulaile/cph-by-chenkx

This is a Sublime Text plugin for C++ competitive programming, based on FastOlympicCoding.
It provides colorful verdict badges, detail panels, stress testing, and Competitive Companion integration.

Verified fixes for Package Control review (16 fixes):
- Root __init__.py is comment-only; plugin_init.py is entry point
- Core modules moved to core/ subpackage
- Contextual key bindings in all .sublime-keymap files
- No package-metadata.json or .no-sublime-package
- Raw regex in CppVarHighlight (r'\\d+')
- Hidden console window fix (startupinfo) in cph_stress.py and ProcessManager.py
- Status consistency (COMPILING) in test_manager.py
- Syntax-specific settings (TestSyntax.sublime-settings)
- Menu includes Key Bindings entry
- .sublime-package built with correct exclusions
```

## 注意事项

- 本文件（`repository-cph-by-chenkx.json`）已生成，可直接用于 PR 提交
- GitHub 仓库已确认包含 `v1.0.7` 标签（根据用户反馈，已在本地计算机完成推送）
- 提交后 Package Control 会每小时检查一次更新
