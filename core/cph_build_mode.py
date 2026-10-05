"""cph-by-chenkx - Debug / Release 编译模式

README 里一直写着"想要 RE 行号请手动给 compile_cmd 加 -fsanitize"——这很别扭：
加了之后程序慢几十倍，本地时限就没意义了；去掉又拿不到崩溃位置。

这里把两种编译命令做成**一个开关**，按源文件记忆（不写用户设置文件）：

- ``release``（默认）：保证带 ``-O2``，去掉 sanitizer 相关参数。计时用。
- ``debug``：去掉优化、加上 ``-g -fsanitize=address,undefined
  -fno-omit-frame-pointer``。崩溃时 sanitizer 会打印 ``文件:行:列``，
  ``find_crash_location`` 能解析出来，详情视图里可以直接点着跳过去。

模式在内存里按文件记录，插件重载即回到 release；这样既不改用户的
``run_settings``（项目约定：不主动写用户设置），也不会让"上次开过 debug"
在下一题悄悄生效。

放在 core/ 是因为根级插件模块之间不允许互相 import（Package Control 审查规则）。
"""

import re

from .cph_settings import get_settings

#: A quoted segment ("...") or a single-quoted one. A plain path with
#: spaces lives inside the quotes, so whitespace runs there are part of
#: the file name - collapsing them made cc1plus look for
#: "P2517 ZJOI.cpp" while the file on disk was "P2517  ZJOI.cpp".
_QUOTED = re.compile('("[^"]*"|\'[^\']*\')')
_WS_RUN = re.compile('[ \\t]{2,}')

def _tidy(cmd):
	"""Collapse runs of spaces/tabs outside quotes only."""
	parts = _QUOTED.split(cmd)
	for i in range(0, len(parts), 2):
		parts[i] = _WS_RUN.sub(' ', parts[i])
	return ''.join(parts).strip()


MODE_RELEASE = 'release'
MODE_DEBUG = 'debug'
MODES = (MODE_RELEASE, MODE_DEBUG)

#: Flags that make the program slow; only debug mode keeps them.
_SANITIZE = '-fsanitize=address,undefined'
_DEBUG_FLAGS = ('-g ' + _SANITIZE + ' -fno-omit-frame-pointer')

_OPT = re.compile(r'-O[0-3sg]\b')
_SANITIZER = re.compile(r'-fsanitize=\S+')
_FRAME_POINTER = re.compile(r'-fno-omit-frame-pointer\b')
_DEBUG_SYM = re.compile(r'(?:^|\s)-g\b')

_modes = {}


def default_mode():
	"""The 'build_mode' setting, for files the user has not toggled."""
	try:
		mode = get_settings().get('build_mode', MODE_RELEASE)
	except Exception:
		return MODE_RELEASE
	return mode if mode in MODES else MODE_RELEASE


def get_mode(file):
	"""Current build mode for a source file.

	A per-file toggle wins; otherwise the 'build_mode' setting decides.
	"""
	if file:
		stored = _modes.get(_norm(file))
		if stored:
			return stored
	return default_mode()


def set_mode(file, mode):
	if not file or mode not in MODES:
		return get_mode(file)
	_modes[_norm(file)] = mode
	return mode


def toggle(file):
	"""Flip the mode and return the new one."""
	new = MODE_DEBUG if get_mode(file) == MODE_RELEASE else MODE_RELEASE
	return set_mode(file, new)


def forget(file):
	_modes.pop(_norm(file), None)


def _norm(file):
	try:
		return file.replace('\\', '/').lower()
	except Exception:
		return file


def transform(cmd, mode):
	"""Apply the mode to a compile command. Non-strings pass through."""
	if not isinstance(cmd, str) or mode == MODE_RELEASE:
		if not isinstance(cmd, str):
			return cmd
		# release: make sure it is optimised, and drop the sanitizer flags
		out = _SANITIZER.sub('', cmd)
		out = _FRAME_POINTER.sub('', out)
		if not _OPT.search(out):
			out = out.rstrip() + ' -O2'
		return _tidy(out)
	# debug: no optimisation, plus the sanitizer + debug symbols
	out = _OPT.sub('', cmd)
	out = _SANITIZER.sub('', out)
	out = _FRAME_POINTER.sub('', out)
	if not _DEBUG_SYM.search(out):
		out = out.rstrip() + ' -g'
	out = out.rstrip() + ' ' + _SANITIZE + ' -fno-omit-frame-pointer'
	return _tidy(out)

def label(file):
	"""Short status-bar label, or '' in the default (release) mode."""
	return 'DEBUG' if get_mode(file) == MODE_DEBUG else ''
