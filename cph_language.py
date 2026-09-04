"""
cph-by-chenkx - 语言切换命令
允许用户在中文和英文之间切换
"""

import sublime
import sublime_plugin

from .cph_i18n import set_lang, get_lang, t, LANG_ZH, LANG_EN


class CphLanguageSetLanguageCommand(sublime_plugin.TextCommand):
    def run(self, edit, language='en'):
        set_lang(language)
        settings = sublime.load_settings('cph-by-chenkx.sublime-settings')
        settings.set('language', language)
        sublime.save_settings('cph-by-chenkx.sublime-settings')
        if language == LANG_ZH:
            sublime.status_message('cph-by-chenkx: Switched to Chinese')
        else:
            sublime.status_message('cph-by-chenkx: Switched to English')

    def is_enabled(self, language='en'):
        return True


class CphLanguageToggleLanguageCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        current = get_lang()
        new_lang = LANG_EN if current == LANG_ZH else LANG_ZH
        set_lang(new_lang)
        settings = sublime.load_settings('cph-by-chenkx.sublime-settings')
        settings.set('language', new_lang)
        sublime.save_settings('cph-by-chenkx.sublime-settings')
        if new_lang == LANG_ZH:
            sublime.status_message('cph-by-chenkx: Switched to Chinese')
        else:
            sublime.status_message('cph-by-chenkx: Switched to English')
