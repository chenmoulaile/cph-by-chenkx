from os.path import dirname
from os import path
from subprocess import Popen, PIPE
import os
import sys
import subprocess
import shlex
import signal
import sublime
import tempfile


class ProcessManager(object):
	def __init__(self, file, syntax, run_settings=None):

		super(ProcessManager, self).__init__()
		self.syntax = syntax
		self.file = file
		self.is_run = False
		self.test_counter = 0
		self.write = self.insert
		self.run = self.run_file
		self.run_settings = run_settings
		self.file_name = path.splitext(path.split(file)[1])[0]

		# When enabled, stderr (e.g. cerr debug output) is captured separately
		# so it never mixes into stdout and is ignored when comparing answers
		self.separate_stderr = False
		self.stderr_file = None

		# Extract time/memory limits from run_settings
		self.time_limit_ms = None
		self.memory_limit_mb = None
		if run_settings:
			file_ext = path.splitext(self.file)[1][1:]
			for x in run_settings:
				if file_ext in x['extensions']:
					self.time_limit_ms = x.get('time_limit_ms')
					self.memory_limit_mb = x.get('memory_limit_mb')
					break

		self.time_limit_override = None
		self.memory_limit_override = None

	def set_time_limit(self, time_ms):
		self.time_limit_override = time_ms

	def set_memory_limit(self, mem_mb):
		self.memory_limit_override = mem_mb

	def set_separate_stderr(self, separate=True):
		self.separate_stderr = separate

	def get_stderr(self):
		"""Return captured stderr content (only in separate_stderr mode)."""
		if self.stderr_file is not None:
			try:
				self.stderr_file.seek(0)
				return self.stderr_file.read()
			except Exception:
				return ''
		return ''

	def close_stderr(self):
		if self.stderr_file is not None:
			try:
				self.stderr_file.close()
			except Exception:
				pass
			self.stderr_file = None

	def get_time_limit_ms(self):
		if self.time_limit_override is not None:
			return self.time_limit_override
		return self.time_limit_ms

	def get_memory_limit_mb(self):
		if self.memory_limit_override is not None:
			return self.memory_limit_override
		return self.memory_limit_mb

	def get_path(self, lst):
		rez = ''
		for x in lst:
			if x[0] == '-':
				rez += ' ' + x
			elif x[0] == '.':
				rez += x
			else:
				rez += ' "' + x + '" '
		return rez

	def format_command(self, cmd, args=''):
		file = path.split(self.file)[1]
		return cmd.format(
			file=file,
			source_file=self.file,
			source_file_dir=path.dirname(self.file),
			file_name=self.file_name,
			args=args
		)

	def has_var_view_api(self):
		return False

	def get_compile_cmd(self):
		opt = self.run_settings
		file_ext = path.splitext(self.file)[1][1:]
		for x in opt:
			if file_ext in x['extensions']:
				if x['compile_cmd'] is None:
					return None
				return self.format_command(x['compile_cmd'])
		else:
			return -1

	def get_run_cmd(self, args):
		opt = self.run_settings
		file_ext = path.splitext(self.file)[1][1:]
		for x in opt:
			if file_ext in x['extensions']:
				if x['run_cmd'] is None:
					return None
				return self.format_command(x['run_cmd'], args=args)
		else:
			return -1

	def compile(self, wait_close=True):
		cmd = self.get_compile_cmd()
		if cmd is not None:
			try:
				PIPE = subprocess.PIPE
				# Windows: hide console window to avoid flashing
				startupinfo = None
				if sublime.platform() == 'windows':
					startupinfo = subprocess.STARTUPINFO()
					startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
				p = subprocess.Popen(cmd, \
					shell=True, stdin=PIPE, stdout=PIPE, stderr=subprocess.STDOUT, \
						cwd=os.path.split(self.file)[0], startupinfo=startupinfo)
				# Timeout so a hanging compiler doesn't freeze the plugin forever
				try:
					compile_result = p.communicate(timeout=30)[0].decode('utf-8', 'ignore')
				except subprocess.TimeoutExpired:
					try:
						p.kill()
					except Exception:
						pass
					return (1, '[cph-by-chenkx] compile timed out after 30s\n(cmd: %s)' % cmd)
				return (p.returncode, compile_result)
			except Exception as e:
				return (1, '[cph-by-chenkx] failed to run compile command: %s\n(cmd: %s)' % (e, cmd))

	def run_file(self, args=[]):
		if self.is_run and False:
			raise AssertionError('cant run process because is already running')
		cmd = self.get_run_cmd(' '.join(args))

		self.is_run = False
		self.close_stderr()
		PIPE = subprocess.PIPE
		preexec_fn = None

		if sublime.platform() == 'windows':
			use_shell = False
			startupinfo = subprocess.STARTUPINFO()
			startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
			preexec_fn = None
		else:
			startupinfo = None
			use_shell = True
			preexec_fn = os.setsid

		if self.separate_stderr:
			stderr_target = tempfile.TemporaryFile(mode='w+', encoding='utf-8', errors='ignore')
			self.stderr_file = stderr_target
		else:
			stderr_target = subprocess.STDOUT

		self.process = subprocess.Popen(
			cmd,
			shell=use_shell,
			stdin=PIPE,
			stdout=PIPE,
			stderr=stderr_target,
			bufsize=0,
			cwd=os.path.split(self.file)[0],
			startupinfo=startupinfo,
			preexec_fn=preexec_fn,
			universal_newlines=True
		)

	def insert(self, s):
		if self.process.poll() is None:
			self.process.stdin.write(s)
			self.process.stdin.flush()

	def communicate(self, s, timeout=None):
		return self.process.communicate(input=s, timeout=timeout)

	def is_stopped(self):
		return self.process.poll()

	def read(self, bfsize=None):
		if bfsize is None:
			return self.process.stdout.read()
		else:
			return self.process.stdout.read(bfsize)

	def new_test(self, input_data=None):
		self.test_counter += 1
		self.run_file()
		if input_data != None:
			self.insert(input_data)

	def terminate(self):
		if sublime.platform() == 'linux':
			os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
		else:
			self.process.kill()
