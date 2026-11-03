"""Strict local GitHub project-Pages emulator; serves assets only, no backend or SPA fallback."""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

BASE = '/RelayOps-AI/'
DIST = Path(__file__).resolve().parents[1] / 'web' / 'dist-pages'


class PagesHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        path = urlsplit(self.path).path
        if path == BASE.rstrip('/'):
            self.send_response(301)
            self.send_header('Location', BASE)
            self.end_headers()
            return
        if not path.startswith(BASE):
            self.send_error(404)
            return
        self.path = path[len(BASE)-1:]
        super().do_GET()

    def do_HEAD(self):
        # The browser tests use GET; refuse unrelated HEAD paths as well.
        path = urlsplit(self.path).path
        if not path.startswith(BASE):
            self.send_error(404)
            return
        self.path = path[len(BASE)-1:]
        super().do_HEAD()


if __name__ == '__main__':
    if not (DIST / 'index.html').is_file():
        raise SystemExit('Run npm --prefix web run build:pages first')
    handler = partial(PagesHandler, directory=str(DIST))
    ThreadingHTTPServer(('127.0.0.1', 8004), handler).serve_forever()
