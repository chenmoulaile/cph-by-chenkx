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
import time
import codecs

from .memprobe import MemorySampler, bytes_to_mb


def _hidden_startupinfo():
	"""STARTUPINFO that keeps helper consoles from flashing on Windows."""
	if sublime.platform() != 'windows':
		return None
	si = subprocess.STARTUPINFO()
	si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
	return si


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

		# Set to True when the process was killed by the plugin (manual stop
		# or TLE watchdog) so the verdict logic can tell it apart from a
		# genuine non-zero exit of the program itself
		self.terminated = False

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

		# Peak memory sampling (makes the MLE verdict real instead of dead code)
		self.pid = None
		self._mem_sampler = None
		self.peak_memory_mb = None

		# Incremental UTF-8 decoder for the binary stdout pipe (recreated on
		# every run in run_file()).
		self._out_decoder = codecs.getincrementaldecoder('utf-8')('replace')

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
				data = self.stderr_file.read()
				if isinstance(data, bytes):
					return data.decode('utf-8', 'ignore')
				return data
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

	def get_lang_entry(self):
		"""Return the run_settings entry matching this file's extension."""
		opt = self.run_settings
		if not opt:
			return None
		file_ext = path.splitext(self.file)[1][1:]
		for x in opt:
			if file_ext in x['extensions']:
				return x
		return None

	def get_extra_sources(self, entry=None):
		"""Files matched by the 'extra_sources' glob patterns (multi-file
		problems). Patterns are relative to the source file directory."""
		if entry is None:
			entry = self.get_lang_entry()
		if not entry:
			return []
		import glob
		src_dir = path.dirname(self.file)
		found = []
		main_abs = path.abspath(self.file)
		for pat in (entry.get('extra_sources') or []):
			pat = self.format_command(pat)
			full = pat if path.isabs(pat) else path.join(src_dir, pat)
			for f in sorted(glob.glob(full)):
				if path.abspath(f) == main_abs:
					continue
				if f not in found:
					found.append(f)
		return found

	def get_include_dirs(self, entry=None):
		"""Extra -I directories from the 'include_dirs' setting."""
		if entry is None:
			entry = self.get_lang_entry()
		if not entry:
			return []
		src_dir = path.dirname(self.file)
		out = []
		for d in (entry.get('include_dirs') or []):
			d = self.format_command(d)
			if not path.isabs(d):
				d = path.join(src_dir, d)
			out.append(d)
		return out

	def get_compile_inputs(self):
		"""All files a compile depends on (for the compile cache)."""
		files = [self.file]
		try:
			files.extend(self.get_extra_sources())
		except Exception:
			pass
		return files

	def get_compile_cmd(self):
		opt = self.run_settings
		file_ext = path.splitext(self.file)[1][1:]
		for x in opt:
			if file_ext in x['extensions']:
				if x['compile_cmd'] is None:
					return None
				cmd = self.format_command(x['compile_cmd'])
				# Multi-file support: {extra_sources} and {include_dirs} are
				# optional placeholders; commands without them are untouched.
				if '{extra_sources}' in cmd:
					extra = self.get_extra_sources(x)
					cmd = cmd.replace('{extra_sources}',
						' '.join('"%s"' % f for f in extra))
				if '{include_dirs}' in cmd:
					inc = self.get_include_dirs(x)
					cmd = cmd.replace('{include_dirs}',
						' '.join('-I "%s"' % d for d in inc))
				return cmd
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
		if cmd == -1:
			return (1, '[cph-by-chenkx] no compile command configured for this file extension')
		if cmd is not None:
			try:
				PIPE = subprocess.PIPE
				# Windows: hide console window to avoid flashing
				startupinfo = None
				if sublime.platform() == 'windows':
					startupinfo = subprocess.STARTUPINFO()
					startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
				p = subprocess.Popen(
					cmd,
					shell=True,
					stdin=None,
					stdout=PIPE,
					stderr=subprocess.STDOUT,
					cwd=os.path.split(self.file)[0],
					startupinfo=startupinfo
				)
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
		if self.is_run:
			# Recover from a stale flag instead of crashing: if the old
			# process already exited (finished, killed or TLE-terminated)
			# the 'is_run' marker is meaningless and must not block the
			# next run. Same when Popen never even started (e.g. it raised),
			# which used to poison the plugin until Sublime was restarted.
			proc = getattr(self, 'process', None)
			if proc is None or proc.poll() is not None:
				self.is_run = False
			else:
				raise AssertionError('cant run process because is already running')
		cmd = self.get_run_cmd(' '.join(args))

		self.is_run = True
		self.terminated = False
		self.close_stderr()
		PIPE = subprocess.PIPE
		preexec_fn = None

		creationflags = 0
		if sublime.platform() == 'windows':
			use_shell = False
			startupinfo = _hidden_startupinfo()
			preexec_fn = None
			# Own process group so the shell + program can be killed as a
			# tree instead of leaving the program running (see terminate()).
			creationflags = subprocess.CREATE_NEW_PROCESS_GROUP
		else:
			startupinfo = None
			use_shell = True
			preexec_fn = os.setsid

		if self.separate_stderr:
			stderr_target = tempfile.TemporaryFile(mode='w+b')
			self.stderr_file = stderr_target
		else:
			stderr_target = subprocess.STDOUT

		# Binary pipes + explicit UTF-8 codec below. Sublime's plugin host is
		# Python 3.3, where Popen has no encoding/errors/text arguments (those
		# arrived in 3.6/3.7), and the default text mode uses the locale
		# encoding (cp936 on Chinese Windows), which corrupted non-ASCII test
		# data and program output.
		self._out_decoder = codecs.getincrementaldecoder('utf-8')('replace')

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
			creationflags=creationflags
		)

		# Start sampling peak memory while the process is alive: /proc/<pid>
		# and the Windows handle both disappear once it exits.
		self.peak_memory_mb = None
		try:
			self.pid = self.process.pid
			self._mem_sampler = MemorySampler(self.pid)
			self._mem_sampler.start()
		except Exception:
			self._mem_sampler = None

	def finish_memory_sampling(self):
		"""Stop the sampler and return the peak memory usage in MB."""
		if self._mem_sampler is None:
			return self.peak_memory_mb
		try:
			peak = self._mem_sampler.stop()
			if peak:
				self.peak_memory_mb = bytes_to_mb(peak)
		except Exception:
			pass
		self._mem_sampler = None
		return self.peak_memory_mb

	def get_peak_memory_mb(self):
		return self.peak_memory_mb

	def insert(self, s):
		proc = getattr(self, 'process', None)
		if proc is None or proc.poll() is not None:
			return
		if isinstance(s, str):
			s = s.encode('utf-8', 'replace')
		proc.stdin.write(s)
		proc.stdin.flush()

	def communicate(self, s, timeout=None):
		if isinstance(s, str):
			s = s.encode('utf-8', 'replace')
		out, err = self.process.communicate(input=s, timeout=timeout)
		text = (out or b'').decode('utf-8', 'replace')
		try:
			text += self._out_decoder.decode(b'', final=True)
		except Exception:
			pass
		return (text, err)

	def is_stopped(self):
		"""Exit code, or None while still running.

		Returns 0 when no process was ever started: callers treat anything
		that is not None as 'not running', so a failed Popen cannot leave
		them waiting forever.
		"""
		proc = getattr(self, 'process', None)
		if proc is None:
			return 0
		return proc.poll()

	def read(self, bfsize=None):
		"""Read raw bytes and decode incrementally.

		The incremental decoder matters for the byte-at-a-time sync mode:
		a multi-byte UTF-8 character split across two reads would otherwise
		come out as mojibake.
		"""
		try:
			if bfsize is None:
				data = self.process.stdout.read()
			else:
				data = self.process.stdout.read(bfsize)
		except Exception:
			return ''
		if not data:
			# EOF: flush whatever a partial sequence left in the decoder
			try:
				return self._out_decoder.decode(b'', final=True)
			except Exception:
				return ''
		return self._out_decoder.decode(data)

	def new_test(self, input_data=None):
		self.test_counter += 1
		self.run_file()
		if input_data != None:
			self.insert(input_data)

	def terminate(self):
		self.terminated = True
		proc = getattr(self, 'process', None)
		pid = getattr(proc, 'pid', None)
		if pid is None:
			self.is_run = False
			return

		if sublime.platform() == 'windows':
			# The evaluated program can be a child of the shell, so a plain
			# kill(pid) would leave it running: kill the whole tree.
			try:
				subprocess.Popen(
					['taskkill', '/F', '/T', '/PID', str(pid)],
					stdout=subprocess.DEVNULL,
					stderr=subprocess.DEVNULL,
					startupinfo=_hidden_startupinfo()
				).wait(timeout=3)
			except Exception:
				try:
					self.process.kill()
				except Exception:
					pass
		else:
			# linux AND osx: the child leads its own session (setsid), so
			# killing the process group is the only way to reach the real
			# program. Escalate to SIGKILL if SIGTERM is ignored.
			for sig, grace in ((signal.SIGTERM, 0.6), (signal.SIGKILL, 0.0)):
				try:
					os.killpg(os.getpgid(pid), sig)
				except Exception:
					try:
						self.process.kill()
					except Exception:
						pass
				if grace:
					waited = 0.0
					while self.process.poll() is None and waited < grace:
						time.sleep(0.05)
						waited += 0.05
					if self.process.poll() is not None:
						break

		# The process is being killed: clear the running marker right here
		# so a follow-up run_file() never trips over the stale flag even
		# if the listener thread's __on_stop has not fired yet.
		self.is_run = False
