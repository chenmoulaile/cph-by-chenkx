"""
cph-by-chenkx - Competitive Companion 监听器
接收来自浏览器插件 Competitive Companion 的 POST 请求
参考: https://github.com/jmerle/competitive-companion
原始代码来自 FastOlympicCodingHook (https://github.com/DrSchwad/FastOlympicCodingHook)
"""

import sublime
import sublime_plugin
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import _thread
import threading
import platform
from os import path

from .cph_i18n import t


def make_handler_class_from_filename(file_full_path, tests_relative_dir, tests_file_suffix, source_view_id):
    if not tests_file_suffix:
        tests_file_suffix = ":tests"

    class HandleRequests(BaseHTTPRequestHandler):
        def log_message(self, format, *args):
            pass

        def do_POST(self):
            try:
                content_length = int(self.headers['Content-Length'])
                body = self.rfile.read(content_length)
                data = json.loads(body.decode('utf8'))
                tests = data.get("tests", [])

                time_limit_ms = None
                memory_limit_mb = None
                if 'timeLimit' in data:
                    time_limit_ms = int(data['timeLimit'])
                if 'memoryLimit' in data:
                    memory_limit_mb = int(data['memoryLimit']) // (1024 * 1024)

                ntests = []
                for test in tests:
                    ntest = {
                        "test": test.get("input", ""),
                        "correct_answers": [test.get("output", "").strip()]
                    }
                    ntests.append(ntest)

                file_relative_dir = path.dirname(file_full_path)
                file_name = path.basename(file_full_path)
                nfilename = path.join(file_relative_dir, tests_relative_dir, file_name + tests_file_suffix) \
                    if tests_relative_dir else path.join(file_relative_dir, file_name + tests_file_suffix)
                print(t('new_test_file_path', path=nfilename))

                with open(nfilename, "w", encoding="utf-8") as f:
                    f.write(json.dumps(ntests))

                if source_view_id is not None:
                    for view in sublime.windows():
                        for v in view.views():
                            if v.id() == source_view_id:
                                v.run_command('test_manager', {
                                    'action': 'make_opd',
                                    'load_session': True,
                                    'time_limit_ms': time_limit_ms,
                                    'memory_limit_mb': memory_limit_mb,
                                })
                                sublime.status_message(
                                    t('tests_loaded_with_limits',
                                      count=len(ntests),
                                      time=time_limit_ms or '-',
                                      memory=memory_limit_mb or '-')
                                )
                                return

                sublime.status_message(t('tests_loaded', count=len(ntests)))

            except Exception as e:
                print(t('error_handling_post', error=str(e)))
            threading.Thread(target=self.server.shutdown, daemon=True).start()

    return HandleRequests


class CompetitiveCompanionServer:
    def start_server(file_full_path, cph_settings, source_view_id):
        host = 'localhost'
        port = 12345
        tests_relative_dir = cph_settings.get("tests_relative_dir")
        tests_file_suffix = cph_settings.get("tests_file_suffix")
        HandlerClass = make_handler_class_from_filename(
            file_full_path, tests_relative_dir, tests_file_suffix, source_view_id
        )
        httpd = HTTPServer((host, port), HandlerClass)
        print('[cph-by-chenkx] ' + t('server_started'))
        httpd.serve_forever()
        print('[cph-by-chenkx] server has been shutdown')


class CphCompanionListenerCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        try:
            sublime.status_message('[cph-by-chenkx] ' + t('server_started'))
            _thread.start_new_thread(
                CompetitiveCompanionServer.start_server,
                (
                    self.view.file_name(),
                    sublime.load_settings("cph-by-chenkx.sublime-settings"),
                    self.view.id()
                )
            )
        except Exception as e:
            print(t('error_starting_thread', error=str(e)))
