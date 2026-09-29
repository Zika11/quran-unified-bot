# -*- coding: utf-8 -*-
"""مغلّف نشر: يشغّل خادم صحة (health) على $PORT + بوت القرآن في نفس العملية.
لا يغيّر منطق البوت — للاستضافة فقط."""
import os
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

# ضمان أن جذر المشروع على مسار الاستيراد مهما كان مجلد التشغيل
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

STARTED = time.time()


class Health(BaseHTTPRequestHandler):
    def do_GET(self):
        body = (f"quran-unified OK uptime={int(time.time()-STARTED)}s").encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *a):
        pass


def serve_health():
    port = int(os.environ.get("PORT", os.environ.get("HEALTH_PORT", "8080")))
    srv = ThreadingHTTPServer(("0.0.0.0", port), Health)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    print(f"[deploy] health server on :{port}", flush=True)


def main():
    serve_health()
    from app.main import build_app
    from telegram import Update
    app = build_app()
    print("[deploy] starting polling…", flush=True)
    app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)


if __name__ == "__main__":
    main()
