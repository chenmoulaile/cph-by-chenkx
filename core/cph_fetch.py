"""cph-by-chenkx - 从题目 URL 抓题面与样例（没有 Competitive Companion 时用）

用标准库抓取网页，交给 core/cph_html 解析：样例变成测试点，题面转成 Markdown
可以在 Sublime 里读。

没有针对每个站点的硬编码选择器：样例的识别靠 `<pre>` 块 + 前面的标签文字
（样例输入/样例输出/Sample Input/...），所以洛谷、Codeforces、AtCoder 以及
大多数自建 OJ 都能用；抓不到时如实返回空，而不是猜。

放在 core/ 是因为根级插件模块之间不允许互相 import（Package Control 审查规则）。
"""

import re
import urllib.request
import urllib.error

from .cph_html import extract_samples, html_to_markdown, problem_title, strip_tags
from .cph_i18n import t

#: Some judges (Codeforces in particular) serve a challenge page to unknown
#: clients, so send a normal browser UA.
USER_AGENT = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
			  '(KHTML, like Gecko) Chrome/124.0 Safari/537.36')

URL_RE = re.compile(r'^https?://\S+$', re.I)


def looks_like_url(text):
	return bool(text) and bool(URL_RE.match(text.strip()))


def fetch(url, timeout=25):
	"""Download a page. Returns (html, error_message)."""
	url = (url or '').strip()
	if not looks_like_url(url):
		return '', t('fetch_bad_url', url=url)
	request = urllib.request.Request(url)
	request.add_header('User-Agent', USER_AGENT)
	request.add_header('Accept-Language', 'zh-CN,zh;q=0.9,en;q=0.8')
	try:
		with urllib.request.urlopen(request, timeout=timeout) as response:
			raw = response.read()
	except urllib.error.HTTPError as e:
		return '', t('fetch_http_error', code=e.code, url=url)
	except Exception as e:
		return '', t('fetch_failed', url=url, error=str(e))

	for encoding in ('utf-8', 'gb18030', 'latin-1'):
		try:
			return raw.decode(encoding), ''
		except Exception:
			continue
	return raw.decode('utf-8', 'replace'), ''


def samples(html):
	"""[(input, output)] pairs found in the page (may be empty)."""
	try:
		return extract_samples(html or '')
	except Exception:
		return []


def statement(html, url=''):
	"""Markdown version of the statement, with the source URL at the top."""
	title = ''
	try:
		title = problem_title(html or '')
	except Exception:
		title = ''
	body = ''
	try:
		body = html_to_markdown(html or '')
	except Exception:
		body = ''
	header = ''
	if title:
		header += '# %s\n\n' % title
	if url:
		header += t('statement_source', url=url) + '\n\n'
	return header + body


def title_of(html):
	try:
		return problem_title(html or '')
	except Exception:
		return ''


def describe_samples(pairs):
	"""One-line summary for the status bar."""
	if not pairs:
		return t('fetch_no_samples')
	return t('fetch_found_samples', n=len(pairs))


def first_lines(text, limit=200):
	"""Short preview used in messages."""
	flat = ' '.join(strip_tags(text or '').split())
	return flat[:limit]
