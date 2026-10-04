"""cph-by-chenkx - 本地练习统计存储

纯标准库（os / sys / json / time / tempfile），不 import 任何其它插件模块，
可以被根级插件、core 子包或独立脚本安全加载。宿主是 Python 3.3，所以这里
只用 % 格式化、time.strftime / time.mktime(time.strptime(...)) 做日期运算，
不用 f-string、海象运算符、os.scandir、datetime.fromisoformat 等新特性。

存储位置（见 stats_path）：
  1. 环境变量 CPH_STATS_PATH 覆盖（测试 / 自定义用，文档化入口）；
  2. sublime.packages_path() + '/User/cph-by-chenkx-stats.json'，
     放在 User 目录里，插件升级不丢、用户也能直接看到；
  3. 上面拿不到时退回系统临时目录。
sublime 在运行时才存在，缺失或抛异常时自动降级，绝不因此报错。

数据格式：
  {
    "problems": {
      "<key>": {
        "file":         "<原始路径>",
        "runs":         已判题运行总次数,
        "attempts":     未完全通过（非 all-AC）的运行次数,
        "first_ac":     第一次 all-AC 的 ISO 时间戳（保留，后续不覆盖）,
        "solved":       是否至少 all-AC 过一次,
        "last":         最近一次运行的 ISO 时间戳,
        "last_verdict": 最近一次运行里最严重的判题结果,
        "ac_runs":      all-AC 的运行次数,
        "by_verdict":   {判题短名: 累计次数},
        "stress_rounds": 对拍累计轮数
      }
    },
    "history": [
      {"key":..,"file":..,"time":ISO,"verdict":..,"all_ac":bool}
    ]
  }
"""

import json
import os
import sys
import tempfile
import time

# ISO 时间戳格式，strftime / strptime 两端保持一致（本地时区）。
_ISO_FMT = '%Y-%m-%dT%H:%M:%S'

# 判题结果优先级：越靠前越"严重"。worst_verdict 返回其中优先级最高的一个。
# CE 最高（根本编译不过），其后依次是 RE / TLE / MLE / OLE / WA / PE / UKE。
_VERDICT_PRIORITY = ['CE', 'RE', 'TLE', 'MLE', 'OLE', 'WA', 'PE', 'UKE']

_STATS_NAME = 'cph-by-chenkx-stats.json'


def stats_path():
	"""返回 JSON 存储的绝对路径。

	优先读环境变量 CPH_STATS_PATH（测试和高级用户可用它把数据放到别处）；
	否则放到 Sublime 的 User 包目录（升级不丢、用户可见）；sublime 不可用
	或 packages_path() 抛异常时退回临时目录。此函数本身不抛异常。
	"""
	override = os.environ.get('CPH_STATS_PATH')
	if override:
		return override

	base = None
	try:
		import sublime
		base = sublime.packages_path()
	except Exception:
		base = None

	if base:
		return os.path.join(base, 'User', _STATS_NAME)

	try:
		tmp = tempfile.gettempdir()
	except Exception:
		tmp = os.getcwd()
	return os.path.join(tmp, _STATS_NAME)


def load():
	"""读取并解析存储；文件缺失或损坏时返回 {}，永不抛异常。"""
	try:
		f = open(stats_path(), 'r', encoding='utf-8')
	except Exception:
		return {}
	try:
		data = json.load(f)
	except Exception:
		return {}
	finally:
		try:
			f.close()
		except Exception:
			pass
	if not isinstance(data, dict):
		return {}
	return data


def save(data):
	"""原子写入存储：先写同目录下的 .tmp，再 os.replace 覆盖。

	返回 True/False，永不抛异常。父目录不存在时会尽力创建；创建失败
	（权限等）则返回 False，调用方不会因此崩溃。
	"""
	path = stats_path()
	tmp = path + '.tmp'

	try:
		parent = os.path.dirname(path)
		if parent and not os.path.isdir(parent):
			os.makedirs(parent)
	except Exception:
		pass

	try:
		f = open(tmp, 'w', encoding='utf-8')
		try:
			json.dump(data, f, ensure_ascii=False, indent=2)
		finally:
			try:
				f.close()
			except Exception:
				pass
		os.replace(tmp, path)
		return True
	except Exception:
		try:
			if os.path.exists(tmp):
				os.remove(tmp)
		except Exception:
			pass
		return False


def key_for(file):
	"""问题的稳定 key。

	用**规范化后的完整路径**，而不是文件名：不同目录下的同名文件是不同题目
	（例如 a/main.cpp 和 b/main.cpp）。反斜杠统一成 '/'，Windows 上再转小写
	（Windows 文件系统大小写不敏感，避免同一文件两种写法产生两条记录）。
	调用方应传入绝对路径，本函数只做分隔符 / 大小写的规范化。
	"""
	if file is None:
		return ''
	p = str(file).replace('\\', '/')
	if sys.platform.startswith('win'):
		p = p.lower()
	return p


def worst_verdict(verdicts):
	"""返回一组判题结果里最严重的一个。

	全部为 'AC'（含空列表）时返回 'AC'；否则按 _VERDICT_PRIORITY
	（CE > RE > TLE > MLE > OLE > WA > PE > UKE）返回优先级最高者；
	出现未知短名时，返回其中第一个非 'AC' 的项。
	"""
	items = list(verdicts or [])
	if not items:
		return 'AC'
	all_ac = True
	for v in items:
		if v != 'AC':
			all_ac = False
			break
	if all_ac:
		return 'AC'
	present = set(items)
	for v in _VERDICT_PRIORITY:
		if v in present:
			return v
	for v in items:
		if v != 'AC':
			return v
	return 'AC'


def _to_epoch(now):
	"""把 now（None / epoch 数字 / ISO 字符串）统一成 epoch 秒。"""
	if now is None:
		return time.time()
	if isinstance(now, str):
		e = _iso_to_epoch(now)
		if e is not None:
			return e
		return time.time()
	try:
		return float(now)
	except Exception:
		return time.time()


def _iso(ts):
	"""epoch 秒 -> 本地时区 ISO 字符串。"""
	try:
		return time.strftime(_ISO_FMT, time.localtime(ts))
	except Exception:
		return time.strftime(_ISO_FMT, time.localtime(time.time()))


def _iso_to_epoch(s):
	"""ISO 字符串 -> epoch 秒；解析失败返回 None。"""
	if not isinstance(s, str):
		return None
	try:
		return time.mktime(time.strptime(s[:19], _ISO_FMT))
	except Exception:
		return None


def _short(path):
	"""只取路径最后一段，让报告行保持简短。"""
	if not path:
		return '(unknown)'
	p = str(path).replace('\\', '/')
	return p.rsplit('/', 1)[-1]


def _fmt_duration(seconds):
	"""把秒数格式化成 '1h 20m' / '5m 3s' / '42s'。"""
	try:
		seconds = int(seconds)
	except Exception:
		seconds = 0
	if seconds < 0:
		seconds = 0
	h = seconds // 3600
	m = (seconds % 3600) // 60
	s = seconds % 60
	if h:
		return '%dh %dm' % (h, m)
	if m:
		return '%dm %ds' % (m, s)
	return '%ds' % s


def record_run(file, verdicts, now=None):
	"""记录 file 的一次判题运行，返回更新后的问题记录 dict。

	verdicts 是判题短名列表（'AC' / 'WA' / 'TLE' ...），顺序无关。
	attempts 的定义：**未完全通过（非 all-AC）的运行次数**。第一次 AC 之前
	的每次运行都是非 AC，第一次 AC 之后只有非 all-AC 的运行才计入，合起来
	正好等于"非 all-AC 的运行数"，实现上就按后者简单计数。
	first_ac 只写一次，之后的运行永不覆盖。
	"""
	items = list(verdicts or [])
	ts = _to_epoch(now)
	iso = _iso(ts)
	key = key_for(file)
	all_ac = bool(items)
	for v in items:
		if v != 'AC':
			all_ac = False
			break
	worst = 'UKE' if not items else worst_verdict(items)

	data = load()
	problems = data.get('problems')
	if not isinstance(problems, dict):
		problems = {}
	rec = problems.get(key)
	if not isinstance(rec, dict):
		rec = {}

	rec['file'] = file
	rec['runs'] = int(rec.get('runs') or 0) + 1
	rec['attempts'] = int(rec.get('attempts') or 0)
	rec['ac_runs'] = int(rec.get('ac_runs') or 0)

	if all_ac:
		rec['ac_runs'] += 1
		rec['solved'] = True
		if not rec.get('first_ac'):
			rec['first_ac'] = iso
	else:
		rec['attempts'] += 1
		if 'solved' not in rec:
			rec['solved'] = False
		if 'first_ac' not in rec:
			rec['first_ac'] = None

	rec['last'] = iso
	rec['last_verdict'] = worst

	by_verdict = rec.get('by_verdict')
	if not isinstance(by_verdict, dict):
		by_verdict = {}
	for v in items:
		by_verdict[v] = int(by_verdict.get(v) or 0) + 1
	rec['by_verdict'] = by_verdict
	if 'stress_rounds' not in rec:
		rec['stress_rounds'] = 0

	problems[key] = rec
	data['problems'] = problems

	history = data.get('history')
	if not isinstance(history, list):
		history = []
	history.append({
		'key': key,
		'file': file,
		'time': iso,
		'verdict': worst,
		'all_ac': all_ac,
	})
	data['history'] = history

	save(data)
	return rec


def record_stress(file, rounds, now=None):
	"""给问题的 'stress_rounds' 累加 rounds 轮对拍。返回问题记录。"""
	key = key_for(file)
	try:
		rounds = int(rounds)
	except Exception:
		return None
	if rounds < 0:
		rounds = 0

	data = load()
	problems = data.get('problems')
	if not isinstance(problems, dict):
		problems = {}
	rec = problems.get(key)
	if not isinstance(rec, dict):
		rec = {}
	rec['file'] = file
	rec['stress_rounds'] = int(rec.get('stress_rounds') or 0) + rounds
	problems[key] = rec
	data['problems'] = problems
	save(data)
	return rec


def summary(days=7, now=None):
	"""返回最近 days 天的纯文本练习报告（英文，无 i18n）。永不抛异常。

	内容顺序：标题行（题目数 / 运行数）-> 'Solved: N' -> 每日表格
	（日期 / 运行数 / 当日首次 AC 数）-> 'Needs work' 列表（最近一次非 AC，
	按尝试次数降序，最多 10 条）-> 若有时间戳则给出 'Total time on task'。
	每行都不带行尾空格。
	"""
	try:
		days = int(days)
	except Exception:
		days = 7
	if days < 0:
		days = 0
	now_ts = _to_epoch(now)
	cutoff = now_ts - days * 86400

	data = load()
	history = data.get('history')
	if not isinstance(history, list):
		history = []

	parsed = []
	for e in history:
		if not isinstance(e, dict):
			continue
		t = _iso_to_epoch(e.get('time'))
		if t is None:
			continue
		parsed.append((t, e))

	window = [(t, e) for (t, e) in parsed if t >= cutoff]

	touched = []
	seen = set()
	for t, e in window:
		k = e.get('key')
		if k not in seen:
			seen.add(k)
			touched.append(k)

	# 首次 AC 在完整历史里找：一旦解决过就永远是"已解决"。
	first_ac = {}
	for t, e in parsed:
		k = e.get('key')
		if e.get('all_ac'):
			if k not in first_ac or t < first_ac[k]:
				first_ac[k] = t

	solved = 0
	for k in touched:
		if k in first_ac:
			solved += 1

	lines = []
	lines.append('CPH practice stats (last %d days): %d problems, %d runs'
	             % (days, len(touched), len(window)))
	lines.append('Solved: %d' % solved)

	# 每日表格
	day_runs = {}
	day_order = []
	for t, e in window:
		d = time.strftime('%Y-%m-%d', time.localtime(t))
		if d not in day_runs:
			day_runs[d] = 0
			day_order.append(d)
		day_runs[d] += 1
	day_solved = {}
	for k in first_ac:
		d = time.strftime('%Y-%m-%d', time.localtime(first_ac[k]))
		day_solved[d] = day_solved.get(d, 0) + 1

	lines.append('Per-day:')
	if day_order:
		for d in sorted(day_order):
			lines.append('  %s  %d runs  %d solved'
			             % (d, day_runs[d], day_solved.get(d, 0)))
	else:
		lines.append('  (no runs)')

	# 最近一次运行 + 尝试次数
	last_by_key = {}
	for t, e in parsed:
		k = e.get('key')
		if k not in last_by_key or t >= last_by_key[k][0]:
			last_by_key[k] = (t, e)
	attempts_by_key = {}
	for t, e in parsed:
		k = e.get('key')
		if not e.get('all_ac'):
			attempts_by_key[k] = attempts_by_key.get(k, 0) + 1

	needs = []
	for k in touched:
		entry = last_by_key.get(k)
		if entry is None:
			continue
		if not entry[1].get('all_ac'):
			needs.append((attempts_by_key.get(k, 0), k, entry[1].get('file')))
	needs.sort(key=lambda x: (-x[0], x[2] or ''))

	lines.append('Needs work (%d):' % len(needs))
	if needs:
		shown = 0
		for attempts, k, f in needs:
			if shown >= 10:
				break
			shown += 1
			lines.append('  %d. %s  attempts=%d'
			             % (shown, _short(f), attempts))
	else:
		lines.append('  none')

	if window:
		times = [t for (t, e) in window]
		span = max(times) - min(times)
		lines.append('Total time on task: %s' % _fmt_duration(span))

	return '\n'.join(line.rstrip() for line in lines)


def reset():
	"""删除存储文件。文件已不存在或删除成功都返回 True。"""
	path = stats_path()
	try:
		if os.path.exists(path):
			os.remove(path)
		return not os.path.exists(path)
	except Exception:
		return False
