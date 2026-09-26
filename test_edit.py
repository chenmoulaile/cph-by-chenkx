"""
cph-by-chenkx - 测试编辑窗口
两个独立标签页:
  - "test N -edit"   编辑测试输入
  - "test N -answer" 编辑标准答案 (预期输出)
save 按钮同时保存两者; 相比旧的 "------ answer ------" 分隔行,
标准答案不再可能被误删。
"""
import sublime, sublime_plugin
from sublime import Region, Phantom, PhantomSet

from .core.cph_settings import base_name, root_dir
from .core.cph_i18n import t as _i18n_t
from .Highlight.test_interface import get_test_styles


class TestEditCommand(sublime_plugin.TextCommand):

	def __init__(self, view):
		self.view = view
		self.mode = 'input'
		self.test_id = None
		self.source_view_id = None
		self.phantoms = PhantomSet(view, 'test-edit-phantoms')

	# ---------- sibling view helpers ----------

	def _sibling_name(self):
		if self.mode == 'input':
			return 'test ' + str(self.test_id) + ' -answer'
		return 'test ' + str(self.test_id) + ' -edit'

	def _find_sibling(self):
		window = self.view.window()
		if window is None:
			return None
		name = self._sibling_name()
		for wv in window.views():
			if wv.name() == name:
				return wv
		return None

	def _find_source_view(self):
		window = self.view.window()
		if window is None or self.source_view_id is None:
			return None
		for wv in window.views():
			if wv.id() == self.source_view_id:
				return wv
		return None

	# ---------- phantom actions ----------

	def cb_action(self, event):
		v = self.view
		if event == 'test-save':
			source = self._find_source_view()
			if source is None:
				sublime.status_message('[cph-by-chenkx] source run view is gone')
				return

			content = v.substr(Region(1, v.size()))
			test_input, answer = None, None
			if self.mode == 'input':
				test_input = content
			else:
				answer = content

			sibling = self._find_sibling()
			if sibling is not None:
				sibling_content = sibling.substr(Region(1, sibling.size()))
				if self.mode == 'input':
					answer = sibling_content
				else:
					test_input = sibling_content

			if test_input is None:
				test_input = ''
			if test_input.strip():
				test_input = test_input.rstrip('\n') + '\n'
			if answer is None:
				answer = ''

			source.run_command('test_manager', {
				'action': 'set_test_input',
				'data': test_input,
				'id': self.test_id
			})
			source.run_command('test_manager', {
				'action': 'set_correct_answer',
				'data': answer,
				'id': self.test_id
			})

			# close both edit views
			if sibling is not None:
				sibling.close()
			v.close()

		elif event == 'test-delete':
			source = self._find_source_view()
			sibling = self._find_sibling()
			if source is not None:
				source.run_command('test_manager', {
					'action': 'delete_test',
					'id': self.test_id
				})
			if sibling is not None:
				sibling.close()
			v.close()

	def update_config(self):
		v = self.view
		styles = get_test_styles(v)
		content = open(root_dir + '/Highlight/test_edit.html').read()

		hint = _i18n_t('edit_input_hint') if self.mode == 'input' \
			else _i18n_t('edit_answer_hint')
		content = content.format(
			test_id=self.test_id,
			save_label=_i18n_t('save'),
			delete_label=_i18n_t('delete'),
			hint=hint,
		)
		content = '<style>' + styles + '</style>' + content
		phantom = Phantom(Region(0), content, sublime.LAYOUT_BLOCK, self.cb_action)
		self.phantoms.update([phantom])

	# ---------- init ----------

	def init(self, edit, mode='input', test='', test_id=None,
			 source_view_id=None, correct_answer=''):
		v = self.view
		self.mode = mode if mode in ('input', 'answer') else 'input'
		self.test_id = test_id
		self.source_view_id = source_view_id

		v.set_scratch(True)
		suffix = ' -edit' if self.mode == 'input' else ' -answer'
		v.set_name('test ' + str(test_id) + suffix)
		v.run_command('toggle_setting', {'setting': 'line_numbers'})
		v.run_command('set_setting', {'setting': 'fold_buttons', 'value': False})
		v.settings().set('edit_mode', True)
		v.set_syntax_file('Packages/%s/TestSyntax.sublime-syntax' % base_name)
		if self.mode == 'input':
			initial_content = '\n' + test.rstrip('\n') + '\n'
		else:
			initial_content = '\n' + (correct_answer or '')
		v.insert(edit, 0, initial_content)
		self.update_config()

	def sync_read_only(self):
		view = self.view
		if view.settings().get('edit_mode'):
			view.set_read_only(False)

	def run(self, edit, action=None, mode='input', test='', test_id=None,
			source_view_id=None, data=None, region=None, text=None):
		v = self.view
		v.set_read_only(False)

		if action == 'init':
			correct_answer = data if data else ''
			self.init(edit, mode=mode, test=test, test_id=test_id,
					  source_view_id=source_view_id, correct_answer=correct_answer)

		elif action == 'replace':
			v.replace(edit, Region(region[0], region[1]), text or '')

		elif action == 'sync_read_only':
			self.sync_read_only()

		elif action == 'set_cursor_to_end':
			v.sel().clear()
			v.sel().add(Region(v.size(), v.size()))


class EditModifyListener(sublime_plugin.EventListener):
	def on_selection_modified(self, view):
		if view.settings().get('edit_mode'):
			if view.size() == 0:
				view.run_command('test_edit', {
					'action': 'replace',
					'region': [0, view.size()],
					'text': '\n'
				})

			mod = []
			change = False
			for reg in view.sel():
				if reg.a == 0:
					change = True
				mod.append(Region(max(reg.a, 1), max(reg.b, 1)))

			if change:
				view.sel().clear()
				view.sel().add_all(mod)
