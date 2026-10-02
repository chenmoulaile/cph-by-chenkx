import sublime

from ..core.cph_resources import read_resource


def get_test_styles(view):
	"""CSS for the test cards. Read through the zip-safe resource loader
	(and cached) instead of opening files on disk every refresh."""
	theme = view.settings().get('theme')
	if theme == 'Spacegray.sublime-theme':
		return read_resource('Highlight/test_styles_spacegray.css')
	elif theme == 'Spacegray Light.sublime-theme':
		return read_resource('Highlight/test_styles_spacegraylight.css')
	return read_resource('Highlight/test_styles.css')
