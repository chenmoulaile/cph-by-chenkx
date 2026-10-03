"""cph-by-chenkx - 自定义快捷键上下文

Package Control 审查要求包内快捷键必须带具体 context（不能用"全局绑定"），
所以这里提供几个自定义 context key，让快捷键只在真正有意义时生效：

- ``cph_run_view``        当前视图就是运行面板（-run）
- ``cph_has_run_panel``   当前视图是运行面板，或当前源文件已经有配对的运行面板
- ``cph_stress_running``  对拍正在运行
- ``cph_listener_running``Competitive Companion 监听器正在运行
- ``cph_supported_file``  当前视图是本插件能处理的文件（见 core/cph_target）
- ``cph_context_menu_enabled`` context_menu 设置是否为 true

状态从 ``core/cph_state`` / ``core/cph_target`` 读取，
避免根级插件之间互相 import。
"""

import sublime
import sublime_plugin

from .core.cph_state import is_listener_running, is_stress_running
from .core.cph_target import context_menu_enabled, supported_file


def _is_run_view(view):
	return bool(view.settings().get('cph_run_view'))


def _has_run_panel(view):
	"""True when collapsing/restoring a run panel would do something."""
	if _is_run_view(view):
		return True
	file_name = view.file_name()
	if not file_name:
		return False
	window = view.window()
	if window is None:
		return False
	target = file_name.replace('\\', '/').split('/')[-1] + ' -run'
	for other in window.views():
		if (other.name() or '') == target:
			return True
	return False


class CphContextListener(sublime_plugin.EventListener):
	"""Answer the custom context keys used by this package's key bindings."""

	def on_query_context(self, view, key, operator, operand, match_all):
		if key == 'cph_run_view':
			value = _is_run_view(view)
		elif key == 'cph_has_run_panel':
			value = _has_run_panel(view)
		elif key == 'cph_stress_running':
			value = is_stress_running()
		elif key == 'cph_listener_running':
			value = is_listener_running()
		elif key == 'cph_supported_file':
			value = supported_file(view)
		elif key == 'cph_context_menu_enabled':
			value = context_menu_enabled()
		else:
			return None

		if operator == sublime.OP_EQUAL:
			return value == bool(operand)
		if operator == sublime.OP_NOT_EQUAL:
			return value != bool(operand)
		return None
