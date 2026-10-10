"""Algorithm Competition Assistant - 跳到源码位置（命令入口）

逻辑在 core/cph_jump.py（根级插件模块之间不允许互相 import）。
"""

import sublime
import sublime_plugin

from .core.cph_jump import jump_to


class CphJumpToLocationCommand(sublime_plugin.TextCommand):
	"""Jump to the Nth target stored in this view's `cph_jump_targets`."""

	def run(self, edit, target=None):
		if not jump_to(self.view, target):
			sublime.status_message('[Algorithm Competition Assistant] no such jump target')

	def is_enabled(self, target=None):
		return bool(self.view.settings().get('cph_jump_targets'))
