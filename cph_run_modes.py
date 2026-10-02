"""
cph-by-chenkx - 运行模式命令（跑完全部 / 只重跑失败 / 强制重新编译）

这三个模式以前只能靠改设置或手动一个个点，这里做成命令，方便挂到
命令面板与快捷键上。
"""

import sublime
import sublime_plugin


def _is_run_view(view):
	"""The -run panel is a scratch view tagged with this setting."""
	return bool(view.settings().get('cph_run_view'))


class _RunModeMixin(object):
	"""Dispatch a run with extra make_opd flags on the owning source view."""

	flags = {}

	def run(self, edit):
		view = self.view
		args = {'action': 'make_opd'}
		args.update(self.flags)

		if _is_run_view(view):
			# Invoked from inside the panel: reuse its session (source file,
			# limits, output mode) and just add the mode flag on top.
			args['load_session'] = True
			view.run_command('cph_test_manager', args)
			return

		if not view.file_name():
			sublime.status_message('[cph-by-chenkx] save the file first')
			return
		view.run_command('cph_view_tester', args)

	def is_enabled(self):
		return _is_run_view(self.view) or bool(self.view.file_name())


class CphRunAllTestsCommand(_RunModeMixin, sublime_plugin.TextCommand):
	"""Run every test, continuing past failures."""

	flags = {'run_all': True}


class CphRunFailedTestsCommand(_RunModeMixin, sublime_plugin.TextCommand):
	"""Re-run only the tests that are not AC yet (skips the accepted ones)."""

	flags = {'run_failed': True}


class CphRunForceRecompileCommand(_RunModeMixin, sublime_plugin.TextCommand):
	"""Run ignoring the compile cache (force a fresh compile)."""

	flags = {'force_compile': True}


class CphTestMenuCommand(sublime_plugin.TextCommand):
	"""Pick a test and run / inspect / edit it without the mouse."""

	def run(self, edit):
		view = self.view
		if _is_run_view(view):
			view.run_command('cph_test_manager', {'action': 'show_test_menu'})
			return
		if not view.file_name():
			sublime.status_message('[cph-by-chenkx] save the file first')
			return
		view.run_command('cph_view_tester', {'action': 'make_opd'})

	def is_enabled(self):
		return _is_run_view(self.view) or bool(self.view.file_name())
