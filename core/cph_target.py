"""cph-by-chenkx - 本插件适用于哪些视图

Package Control 的审查要求：

- **右键菜单**里的项必须"只在相关上下文出现、并且条件化"。
  ``.sublime-menu`` 的菜单项**没有** ``context`` 字段（见官方 Menus 参考），
  让菜单项按上下文显隐的唯一办法是命令的 ``is_visible()``——ST 自带的
  ``open_context_url`` 就是这么做的。
- 菜单项显隐还要"最好是可配置的"，所以这里同时读取 ``context_menu`` 设置：
  它**只影响右键菜单**（``is_visible`` 会收到 ``event`` 参数），
  不会把命令从命令面板或 View 菜单里藏起来。

放在 ``core/`` 里是因为根级插件模块之间不允许互相 import。
"""

from .cph_settings import get_settings


def supported_file(view):
	"""True 表示这个视图是本插件能处理的文件。

	两种情况算数：本插件自己的视图（运行面板 / 测试编辑 / 详情），
	或者扩展名出现在 ``run_settings`` 里的源文件。
	"""
	if view is None:
		return False
	try:
		settings = view.settings()
		if settings.get('cph_run_view'):
			return True
		syntax = settings.get('syntax') or ''
		if syntax.endswith('TestSyntax.sublime-syntax'):
			return True
		file_name = view.file_name()
		if not file_name or '.' not in file_name:
			return False
		ext = file_name.rsplit('.', 1)[-1].lower()
		for entry in (get_settings().get('run_settings') or []):
			for candidate in (entry.get('extensions') or []):
				if str(candidate).lower() == ext:
					return True
	except Exception:
		return False
	return False


def context_menu_enabled():
	"""``context_menu`` 设置：关掉后右键菜单里不再出现本插件的项。"""
	try:
		value = get_settings().get('context_menu', True)
	except Exception:
		return True
	return value is not False


def visible(view, event=None):
	"""各个右键菜单入口共用的 ``is_visible()`` 实现。

	只对**右键菜单**生效：只有从右键菜单调用时 ST 才会传 ``event``，
	所以命令面板和 View 菜单里的项不会被藏掉（审查要求命令都能从命令面板
	找到），而 ``context_menu`` 设置也只影响右键菜单。
	"""
	if event is None:
		return True
	if not context_menu_enabled():
		return False
	return supported_file(view)
