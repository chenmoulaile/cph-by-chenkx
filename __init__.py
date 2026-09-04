"""cph-by-chenkx - Sublime Text 测评插件

参考 cph-ng 实现的 Verdict 颜色系统、详情面板
内置 Competitive Companion 浏览器插件支持
"""

import sublime

from .cph_i18n import set_lang, LANG_ZH, LANG_EN
from .cph_settings import try_load_settings


_PLATFORM_SETTINGS = {
    'windows': 'cph-by-chenkx (Windows).sublime-settings',
    'linux': 'cph-by-chenkx (Linux).sublime-settings',
    'osx': 'cph-by-chenkx (OSX).sublime-settings',
}


def _platform_settings_name():
    return _PLATFORM_SETTINGS.get(sublime.platform().lower(),
                                  'cph-by-chenkx.sublime-settings')


def plugin_loaded():
    """Sublime Text 4 插件加载入口"""
    try:
        settings = sublime.load_settings(_platform_settings_name())
        lang = settings.get('language', 'zh')
        sublime.set_timeout(lambda: _setup_language(lang), 100)
    except Exception as e:
        print('[cph-by-chenkx] Error in plugin_loaded: %s' % str(e))


def plugin_unloaded():
    print('[cph-by-chenkx] plugin unloaded')


def _setup_language(lang):
    try:
        from .cph_i18n import set_lang, LANG_ZH, LANG_EN
        if lang in (LANG_ZH, LANG_EN):
            set_lang(lang)
        print('[cph-by-chenkx] plugin loaded, language: %s' % lang)
    except Exception as e:
        print('[cph-by-chenkx] Error setting up language: %s' % str(e))

    try:
        from .cph_settings import try_load_settings
        try_load_settings()
    except Exception as e:
        print('[cph-by-chenkx] Error loading settings: %s' % str(e))
