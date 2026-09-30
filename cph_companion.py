"""
cph-by-chenkx - Competitive Companion 持久监听器
接收来自浏览器扩展 Competitive Companion 的 POST 请求
参考: https://github.com/jmerle/competitive-companion
思路来自 FastOlympicCodingHook (https://github.com/DrSwad/FastOlympicCodingHook)

与旧版 (FastOlympicCodingHook 一次性会话) 的区别:
- 一次启动后持续监听 (cph-ng 风格), 浏览器扩展可反复点击发送样例
- 再次执行本命令只会切换目标文件, 不会重复起服务器/产生端口冲突
- 收到样例后通过 cph_view_tester 正常走 Run 流程, 不会向源代码文件插入任何文字
"""

import sublime
import sublime_plugin
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import threading

from .core.cph_i18n import t
from .core.cph_settings import save_tests


_listener = {
    'server': None,      # HTTPServer instance
    'thread': None,      # serving thread
    'view_id': None,     # target source view id
    'lock': threading.Lock(),
}


def _find_view(view_id):
    if view_id is None:
        return None
    for window in sublime.windows():
        for view in window.views():
            if view.id() == view_id:
                return view
    return None


class _CompanionHandler(BaseHTTPRequestHandler):

    def log_message(self, format, *args):
        pass

    def do_POST(self):
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            data = json.loads(body.decode('utf-8'))
            tests = data.get('tests', [])
            problem_name = data.get('name', '')

            time_limit_ms = data.get('timeLimit')
            memory_limit_mb = data.get('memoryLimit')
            try:
                time_limit_ms = int(time_limit_ms) if time_limit_ms else None
            except (TypeError, ValueError):
                time_limit_ms = None
            try:
                memory_limit_mb = int(memory_limit_mb) // (1024 * 1024) if memory_limit_mb else None
            except (TypeError, ValueError):
                memory_limit_mb = None

            ntests = []
            for test in tests:
                output = (test.get('output') or '').strip()
                ntests.append({
                    'test': test.get('input', ''),
                    'correct_answers': [output] if output else [],
                })

            view = _find_view(_listener.get('view_id'))
            if view is None or not view.file_name():
                sublime.status_message(t('listener_no_target'))
                return

            # 样例保存位置与插件其余部分完全一致 (save_tests)
            if not save_tests(view.file_name(), ntests):
                sublime.status_message(t('import_save_failed'))
                return
            print('[cph-by-chenkx] %s' % t('new_test_file_path', path=view.file_name()))

            count = len(ntests)
            tl = time_limit_ms if time_limit_ms is not None else '-'
            ml = memory_limit_mb if memory_limit_mb is not None else '-'

            def _reload(view_id=_listener.get('view_id')):
                target = _find_view(view_id)
                if target is None:
                    return
                # 正常 Run 流程: 复用/创建 -run 视图并从磁盘读取刚保存的样例
                target.run_command('cph_view_tester', {
                    'action': 'make_opd',
                    'time_limit_ms': time_limit_ms,
                    'memory_limit_mb': memory_limit_mb,
                })
                sublime.status_message(t('tests_received',
                                         name=problem_name or '?',
                                         count=count, time=tl, memory=ml))

            sublime.set_timeout(_reload, 0)
        except Exception as e:
            print(t('error_handling_post', error=str(e)))
        finally:
            try:
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b'ok')
            except Exception:
                pass
            # 保持服务器运行, 不 shutdown —— 浏览器扩展可以反复点击


def _start_listener(view):
    file_name = view.file_name()
    if not file_name:
        sublime.status_message(t('listener_need_save'))
        return

    with _listener['lock']:
        _listener['view_id'] = view.id()
        if _listener['server'] is not None:
            sublime.status_message(t('listener_retarget', file=file_name))
            return
        try:
            port = int(sublime.load_settings('cph-by-chenkx.sublime-settings')
                       .get('companion_port', 12345) or 12345)
            server = HTTPServer(('localhost', port), _CompanionHandler)
        except Exception as e:
            sublime.status_message(t('listener_port_error', port=12345, error=str(e)))
            return
        _listener['server'] = server
        thread = threading.Thread(target=server.serve_forever)
        thread.daemon = True
        _listener['thread'] = thread
        thread.start()

    sublime.status_message(t('listener_started', file=file_name, port=port))
    print('[cph-by-chenkx] ' + t('listener_started', file=file_name, port=port))


def _stop_listener():
    with _listener['lock']:
        server = _listener.get('server')
        if server is None:
            sublime.status_message(t('listener_not_running'))
            return
        _listener['server'] = None
        _listener['thread'] = None
        _listener['view_id'] = None
    threading.Thread(target=server.shutdown, daemon=True).start()
    try:
        server.server_close()
    except Exception:
        pass
    sublime.status_message(t('listener_stopped'))


class CphCompanionListenerCommand(sublime_plugin.TextCommand):
    """Listen to Competitive Companion: 启动/切换目标文件 (幂等, 可反复点击)."""

    def run(self, edit):
        _start_listener(self.view)


class CphCompanionStopListenerCommand(sublime_plugin.TextCommand):
    """停止 Competitive Companion 监听."""

    def run(self, edit):
        _stop_listener()


def plugin_unloaded():
    """插件重载/卸载时关闭监听, 释放端口, 避免重启后端口占用."""
    try:
        with _listener['lock']:
            server = _listener.get('server')
            _listener['server'] = None
            _listener['thread'] = None
    except Exception:
        return
    if server is not None:
        try:
            threading.Thread(target=server.shutdown, daemon=True).start()
            server.server_close()
        except Exception:
            pass
