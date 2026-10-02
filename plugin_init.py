"""cph-by-chenkx plugin initialization entrypoint."""
import sublime


def plugin_loaded():
    """Called when the package loads."""
    try:
        # Defer language and settings initialization
        sublime.set_timeout(_init, 100)
    except Exception as e:
        print('[cph-by-chenkx] Error in plugin_loaded: %s' % str(e))


def plugin_unloaded():
    print('[cph-by-chenkx] plugin unloaded')
    try:
        # Drop cached HTML/CSS so an updated package is picked up, and stop
        # any listener so the port is released.
        from .core.cph_resources import clear_cache
        clear_cache()
    except Exception:
        pass


def _init():
    try:
        from .core.cph_resources import clear_cache
        clear_cache()
    except Exception:
        pass

    try:
        from .core.cph_i18n import set_lang, LANG_ZH, LANG_EN
        # Load language from platform settings file
        settings_file = 'cph-by-chenkx.sublime-settings'
        settings = sublime.load_settings(settings_file)
        lang = settings.get('language', 'zh')
        if lang in (LANG_ZH, LANG_EN):
            set_lang(lang)

        # Apply a language change made in the settings file without a restart
        def _on_settings_change():
            try:
                new_lang = settings.get('language', 'zh')
                if new_lang in (LANG_ZH, LANG_EN):
                    set_lang(new_lang)
            except Exception:
                pass

        settings.add_on_change('cph_language', _on_settings_change)
        print('[cph-by-chenkx] plugin loaded, language: %s' % lang)
    except Exception as e:
        print('[cph-by-chenkx] Error setting up language: %s' % str(e))

    try:
        from .core.cph_settings import try_load_settings
        try_load_settings()
    except Exception as e:
        print('[cph-by-chenkx] Error loading settings: %s' % str(e))

    try:
        from .core.cph_settings import try_load_settings
        try_load_settings()
    except Exception as e:
        print('[cph-by-chenkx] Error loading settings: %s' % str(e))
