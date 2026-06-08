#!/usr/bin/env python3
"""
Minimal HTTP server with file UPLOAD support — standard library only.

Browse/download:  http://<host>:<port>/
Upload form:      http://<host>:<port>/upload

Usage:
    python3 upload_server.py [PORT] [DIRECTORY]
    # defaults: PORT=8000, DIRECTORY=current working directory

WARNING: No authentication. Anyone who can reach this port can read and
write files in the shared folder, and uploads overwrite files with the
same name. Only run this on networks you trust.
"""

import http.server
import socketserver
import os
import sys
import html

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
DIRECTORY = os.path.abspath(sys.argv[2]) if len(sys.argv) > 2 else os.getcwd()

UPLOAD_PAGE = """<!doctype html>
<html><head><meta charset="utf-8"><title>Upload</title></head>
<body style="font-family:sans-serif;max-width:40em;margin:3em auto">
<h2>Upload files</h2>
<form method="POST" action="/upload" enctype="multipart/form-data">
  <input type="file" name="file" multiple>
  <button type="submit">Upload</button>
</form>
<p><a href="/">&larr; back to file list</a></p>
</body></html>
"""


class UploadHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def do_GET(self):
        if self.path.rstrip("/") == "/upload":
            body = UPLOAD_PAGE.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        super().do_GET()  # normal browse/download

    def do_POST(self):
        if self.path.rstrip("/") != "/upload":
            self.send_error(404, "Not found")
            return

        ctype = self.headers.get("Content-Type", "")
        if "multipart/form-data" not in ctype or "boundary=" not in ctype:
            self.send_error(400, "Expected multipart/form-data")
            return

        boundary = ctype.split("boundary=")[-1].strip().strip('"').encode()
        length = int(self.headers.get("Content-Length", 0))
        data = self.rfile.read(length)

        saved = []
        for part in data.split(b"--" + boundary):
            if part.startswith(b"\r\n"):
                part = part[2:]
            if part.endswith(b"\r\n"):
                part = part[:-2]
            if part in (b"", b"--"):  # preamble / closing marker
                continue

            sep = part.find(b"\r\n\r\n")
            if sep == -1:
                continue
            raw_headers = part[:sep].decode("utf-8", "replace")
            file_bytes = part[sep + 4:]

            filename = None
            for line in raw_headers.split("\r\n"):
                if line.lower().startswith("content-disposition"):
                    for token in line.split(";"):
                        token = token.strip()
                        if token.startswith("filename="):
                            filename = token[len("filename="):].strip('"')
            if not filename:
                continue

            filename = os.path.basename(filename)  # block path traversal
            with open(os.path.join(DIRECTORY, filename), "wb") as f:
                f.write(file_bytes)
            saved.append(filename)

        names = ", ".join(html.escape(n) for n in saved) or "(nothing)"
        body = (
            f"<p>Uploaded: {names}</p>"
            f'<p><a href="/upload">upload more</a> | '
            f'<a href="/">file list</a></p>'
        ).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


class Server(socketserver.ThreadingTCPServer):
    allow_reuse_address = True


if __name__ == "__main__":
    with Server(("", PORT), UploadHandler) as httpd:
        print(f"Serving {DIRECTORY} on http://0.0.0.0:{PORT}")
        print(f"Upload form: http://localhost:{PORT}/upload")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nStopped.")