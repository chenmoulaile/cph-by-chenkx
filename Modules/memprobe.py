"""
Algorithm Competition Assistant - 子进程峰值内存采样（零第三方依赖）

用途：让 MLE（内存超限）判定真正生效。此前 memory_limit_mb 只是传给了判定
函数，但从未有人把"实际用了多少内存"喂进去，所以 MLE 永远判不出来。

实现按平台分别取样：
- Windows: psapi GetProcessMemoryInfo -> PeakWorkingSetSize（进程自启动以来的
  工作集峰值，bytes），句柄用 OpenProcess(QUERY_LIMITED_INFORMATION | VM_READ)
- Linux:   /proc/<pid>/status 的 VmHWM（峰值 RSS，kB），缺失时回退 VmRSS
- macOS:   libproc.proc_pid_rusage(pid, RUSAGE_INFO_V2) 的 ri_phys_footprint
           （bytes，单进程）。**不能**用
           resource.getrusage(RUSAGE_CHILDREN).ru_maxrss —— 那是本进程所有
           已回收子进程（含 g++、历次运行）的累计峰值，会虚高并误判 MLE

采样器（MemorySampler）在进程存活期间每 25ms 取一次最大值，进程退出后再
尽力补取一次；因为 Linux 的 /proc/<pid> 和 Windows 的句柄都会在进程结束后
失效，所以"边跑边取"是唯一可靠的做法。
"""

import os
import sys
import threading
import time

_WINDOWS = sys.platform.startswith('win') or os.name == 'nt'
_LINUX = sys.platform.startswith('linux')
_DARWIN = sys.platform.startswith('darwin')

if _DARWIN:
	import ctypes
	import struct

	try:
		_libproc = ctypes.CDLL('/usr/lib/libproc.dylib', use_errno=True)
	except Exception:
		_libproc = None

	# rusage_info_v2: ri_uuid[16] followed by 8-byte fields, so
	# ri_resident_size sits at offset 64 and ri_phys_footprint at 72.
	_RUSAGE_INFO_V2 = 2
	_RUSAGE_RESIDENT_OFF = 64
	_RUSAGE_FOOTPRINT_OFF = 72


if _WINDOWS:
	import ctypes
	from ctypes import wintypes

	class _PROCESS_MEMORY_COUNTERS_EX(ctypes.Structure):
		_fields_ = [
			('cb', wintypes.DWORD),
			('PageFaultCount', wintypes.DWORD),
			('PeakWorkingSetSize', ctypes.c_size_t),
			('WorkingSetSize', ctypes.c_size_t),
			('QuotaPeakPagedPoolUsage', ctypes.c_size_t),
			('QuotaPagedPoolUsage', ctypes.c_size_t),
			('QuotaPeakNonPagedPoolUsage', ctypes.c_size_t),
			('QuotaNonPagedPoolUsage', ctypes.c_size_t),
			('PagefileUsage', ctypes.c_size_t),
			('PeakPagefileUsage', ctypes.c_size_t),
			('PrivateUsage', ctypes.c_size_t),
		]

	_psapi = None
	try:
		_psapi = ctypes.WinDLL('psapi', use_last_error=True)
		_psapi.GetProcessMemoryInfo.argtypes = [
			wintypes.HANDLE, ctypes.POINTER(_PROCESS_MEMORY_COUNTERS_EX),
			wintypes.DWORD]
		_psapi.GetProcessMemoryInfo.restype = wintypes.BOOL
	except Exception:
		_psapi = None

	_kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
	_kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
	_kernel32.OpenProcess.restype = wintypes.HANDLE
	_kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
	_kernel32.CloseHandle.restype = wintypes.BOOL


def sample_memory_bytes(pid):
	"""Sample the resident/working-set memory of a live process, in bytes.

	Returns None when the platform cannot provide the value or the process
	has already exited.
	"""
	if pid is None:
		return None
	try:
		if _WINDOWS:
			return _sample_windows(pid)
		if _LINUX:
			return _sample_linux(pid)
		if _DARWIN:
			return _sample_darwin(pid)
	except Exception:
		return None
	return None


def _sample_windows(pid):
	if _psapi is None:
		return None
	PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
	PROCESS_VM_READ = 0x0010
	handle = _kernel32.OpenProcess(
		PROCESS_QUERY_LIMITED_INFORMATION | PROCESS_VM_READ, False, int(pid))
	if not handle:
		return None
	try:
		counters = _PROCESS_MEMORY_COUNTERS_EX()
		counters.cb = ctypes.sizeof(counters)
		ok = _psapi.GetProcessMemoryInfo(handle, ctypes.byref(counters), counters.cb)
		if not ok:
			return None
		# PeakWorkingSetSize is the peak since process start: the single most
		# useful number for a memory limit verdict.
		peak = int(counters.PeakWorkingSetSize or 0)
		cur = int(counters.WorkingSetSize or 0)
		return max(peak, cur) or None
	finally:
		try:
			_kernel32.CloseHandle(handle)
		except Exception:
			pass


def _sample_linux(pid):
	path = '/proc/%d/status' % int(pid)
	try:
		with open(path, 'r', encoding='utf-8', errors='ignore') as f:
			data = f.read()
	except Exception:
		return None
	value = None
	for line in data.split('\n'):
		if line.startswith('VmHWM:'):
			value = line.split(':', 1)[1].strip().split()[0]
			break
	if value is None:
		for line in data.split('\n'):
			if line.startswith('VmRSS:'):
				value = line.split(':', 1)[1].strip().split()[0]
				break
	if value is None:
		return None
	try:
		# /proc reports kB
		return int(value) * 1024
	except ValueError:
		return None


def _sample_darwin(pid):
	"""Memory of ONE process via libproc (macOS).

	resource.getrusage(RUSAGE_CHILDREN) must NOT be used here: it reports the
	cumulative peak of every child that was ever reaped (compilers, previous
	test runs), which inflated the displayed value and made the MLE verdict
	fire on data from a completely different process.
	"""
	if _libproc is None:
		return None
	try:
		buf = ctypes.create_string_buffer(512)
		rc = _libproc.proc_pid_rusage(int(pid), _RUSAGE_INFO_V2,
									  ctypes.byref(buf))
		if rc != 0:
			return None
		raw = buf.raw
		footprint = struct.unpack_from('<Q', raw, _RUSAGE_FOOTPRINT_OFF)[0]
		resident = struct.unpack_from('<Q', raw, _RUSAGE_RESIDENT_OFF)[0]
		return int(footprint or resident) or None
	except Exception:
		return None


class MemorySampler(object):
	"""Poll a running process and remember its peak memory usage."""

	def __init__(self, pid, interval=0.025, max_silence=2.0):
		self.pid = pid
		self.interval = interval
		#: Give up after this many seconds without a single successful sample.
		self.max_silence = max_silence
		self.peak = 0
		self._stop = threading.Event()
		self._thread = None

	def start(self):
		if self._thread is not None:
			return
		self._thread = threading.Thread(target=self.__run)
		self._thread.daemon = True
		self._thread.start()

	def __run(self):
		# Stop on our own once the child is gone. The sampler is a daemon
		# thread, but if the owning listener raised before stop() ran, a leaked
		# thread would poll a dead pid every 25 ms for the rest of the session.
		#
		# Two exit conditions, because one is not enough: 20 consecutive
		# misses covers the normal case, and `silence_until` bounds the total
		# time when a single sample is slow (proc_pid_rusage on macOS takes
		# noticeably longer for a pid that does not exist, which made a
		# sampler thread outlive an 8s join on a loaded runner).
		misses = 0
		silence_until = None
		while not self._stop.is_set():
			value = sample_memory_bytes(self.pid)
			if value:
				misses = 0
				silence_until = None
				if value > self.peak:
					self.peak = value
			else:
				misses += 1
				if misses >= 20:
					break
				now = time.time()
				if silence_until is None:
					silence_until = now + self.max_silence
				elif now > silence_until:
					break
			time.sleep(self.interval)

	def stop(self):
		"""Stop polling and return the peak memory in bytes (0 if unknown)."""
		self._stop.set()
		# one last sample in case the peak only shows up at the very end
		value = sample_memory_bytes(self.pid)
		if value and value > self.peak:
			self.peak = value
		if self._thread is not None:
			self._thread.join(timeout=0.2)
			self._thread = None
		return self.peak


def bytes_to_mb(nbytes):
	if not nbytes:
		return 0.0
	return float(nbytes) / (1024.0 * 1024.0)
