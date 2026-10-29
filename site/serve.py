"""Tiny static server with HTTP Range support (needed so the audio can seek to the 'live' position)."""
import os, re, sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

class H(SimpleHTTPRequestHandler):
    def send_head(self):
        rng = self.headers.get('Range')
        path = self.translate_path(self.path)
        if not rng or not os.path.isfile(path):
            return super().send_head()
        m = re.match(r'bytes=(\d*)-(\d*)', rng)
        size = os.path.getsize(path)
        start = int(m.group(1)) if m.group(1) else 0
        end = int(m.group(2)) if m.group(2) else size - 1
        end = min(end, size - 1)
        if start > end:
            self.send_error(416); return None
        f = open(path, 'rb'); f.seek(start)
        self.send_response(206)
        self.send_header('Content-Type', self.guess_type(path))
        self.send_header('Accept-Ranges', 'bytes')
        self.send_header('Content-Range', f'bytes {start}-{end}/{size}')
        self.send_header('Content-Length', str(end - start + 1))
        self.end_headers()
        self._left = end - start + 1
        return f

    def copyfile(self, src, dst):
        left = getattr(self, '_left', None)
        try:
            if left is None:
                return super().copyfile(src, dst)
            while left > 0:
                buf = src.read(min(65536, left))
                if not buf: break
                dst.write(buf); left -= len(buf)
        except (BrokenPipeError, ConnectionResetError):
            pass
        finally:
            self._left = None

    def end_headers(self):
        self.send_header('Accept-Ranges', 'bytes')
        if not self.path.split('?')[0].endswith('.mp3'):
            self.send_header('Cache-Control', 'no-store')
        super().end_headers()

if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8077
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    print(f'Radioport on http://localhost:{port}')
    ThreadingHTTPServer(('127.0.0.1', port), H).serve_forever()
