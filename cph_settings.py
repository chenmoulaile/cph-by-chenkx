"""
cph-by-chenkx - 设置管理 + 测试数据存储路径解析

支持两种测试数据存储模式:
1. 传统模式 (FastOlympicCoding 兼容): tests 存在 "{filename}{suffix}" 同目录下
   e.g. "foo.cpp" -> "foo.cpp__tests"
2. cph-ng 模式: tests 存在 "{source_dir}/{tests_folder_name}/{filename}{suffix}"
   e.g. "foo.cpp" -> "tests/foo.cpp__tests"

两种模式可以同时存在,合并时去重(同目录下文件优先)
"""

import sublime
from os import path
import os


root_dir = path.split(__file__)[0]
base_name = path.split(root_dir)[1]

settings_file = 'cph-by-chenkx ({os}).sublime-settings'.format(
	os={ 'windows': 'Windows', 'linux': 'Linux', 'osx': 'OSX' }[sublime.platform().lower()]
)

tests_file_suffix_default = '__tests'
tests_relative_dir_default = ''
tests_folder_name_default = 'tests'

settings = {}
run_supported_exts = set()


def get_settings():
	return settings


def init_settings(_settings):
	global settings
	settings = _settings


def is_run_supported_ext(ext):
	_run_settings = get_settings().get('run_settings', None)
	if _run_settings is not None:
		for option in _run_settings:
			if ext in option['extensions']:
				return True
	return False


def get_supported_exts(lang):
	_run_settings = get_settings().get('run_settings', None)
	if _run_settings is not None:
		for option in _run_settings:
			if option['name'] == lang:
				return option['extensions']
		return []
	return []


def is_lang_view(view, lang):
	if view.file_name() is None:
		return False
	return path.splitext(view.file_name())[1][1:] in get_supported_exts(lang)


def try_load_settings():
	_settings = sublime.load_settings(settings_file)
	if _settings is None:
		sublime.set_timeout_async(load_settings, 200)
	else:
		init_settings(_settings)
		sublime.status_message('cph-by-chenkx: settings loaded')


def get_tests_file_suffix():
	return get_settings().get('tests_file_suffix', tests_file_suffix_default)


def get_tests_relative_dir():
	return get_settings().get('tests_relative_dir', tests_relative_dir_default)


def get_tests_folder_name():
	return get_settings().get('tests_folder_name', tests_folder_name_default)


def get_tests_paths(file):
	if not file:
		return []

	dirname = os.path.dirname(file)
	filename = os.path.basename(file)
	suffix = get_tests_file_suffix()
	folder_name = get_tests_folder_name()

	paths = []

	traditional_path = os.path.join(dirname, filename + suffix)
	paths.append(traditional_path)

	folder_path = os.path.join(dirname, folder_name, filename + suffix)
	paths.append(folder_path)

	folder_path_no_suffix = os.path.join(dirname, folder_name, filename + '.json')
	if folder_path_no_suffix not in paths:
		paths.append(folder_path_no_suffix)

	return paths


def get_tests_file_path(file):
	if not file:
		return None
	dirname = os.path.dirname(file)
	filename = os.path.basename(file)
	suffix = get_tests_file_suffix()
	return os.path.join(dirname, filename + suffix)


def get_folder_tests_file_path(file):
	if not file:
		return None
	dirname = os.path.dirname(file)
	filename = os.path.basename(file)
	suffix = get_tests_file_suffix()
	folder_name = get_tests_folder_name()
	folder_dir = os.path.join(dirname, folder_name)
	if not os.path.exists(folder_dir):
		try:
			os.makedirs(folder_dir)
		except:
			pass
	return os.path.join(folder_dir, filename + suffix)


def load_all_tests(file):
	all_paths = get_tests_paths(file)
	seen = set()
	merged = []

	for p in all_paths:
		if not os.path.exists(p):
			continue
		try:
			with open(p, 'r', encoding='utf-8') as f:
				content = f.read().strip()
			if not content:
				continue
			data = sublime.decode_value(content)
			if not isinstance(data, list):
				continue
			for test in data:
				key = (test.get('test', ''),
					   tuple(sorted(test.get('correct_answers', []))))
				if key in seen:
					continue
				seen.add(key)
				merged.append(test)
		except Exception as e:
			print('[cph-by-chenkx] Failed to load tests from %s: %s' % (p, e))

	return merged


def save_tests(file, tests):
	if not file:
		return False

	dirname = os.path.dirname(file)
	filename = os.path.basename(file)
	suffix = get_tests_file_suffix()
	folder_name = get_tests_folder_name()
	relative_dir = get_tests_relative_dir()

	target_path = None
	if relative_dir:
		target_dir = os.path.join(dirname, relative_dir)
		if not os.path.exists(target_dir):
			try:
				os.makedirs(target_dir)
			except:
				pass
		target_path = os.path.join(target_dir, filename + suffix)
	elif os.path.exists(os.path.join(dirname, filename + suffix)):
		target_path = os.path.join(dirname, filename + suffix)
	else:
		target_dir = os.path.join(dirname, folder_name)
		if not os.path.exists(target_dir):
			try:
				os.makedirs(target_dir)
			except:
				pass
		target_path = os.path.join(target_dir, filename + suffix)

	if target_path is None:
		return False

	try:
		with open(target_path, 'w', encoding='utf-8') as f:
			f.write(sublime.encode_value(tests, True))
		return True
	except Exception as e:
		print('[cph-by-chenkx] Failed to save tests to %s: %s' % (target_path, e))
		return False
