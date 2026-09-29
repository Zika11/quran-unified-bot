# -*- coding: utf-8 -*-
"""حارس إعادة التشغيل التلقائي: يراقب عملية البوت ويعيد تشغيلها فور توقفها،
مع فحص صحة حقيقي (getMe) كل ~15 دقيقة وكتابة logs/health.json.
يعمل بلا صلاحيات أدمن. السجل: logs/guard.log
الاستخدام: pythonw deploy/guard.py  (أو من مجلد بدء ويندوز)
"""
import json
import os
import subprocess
import sys
import time
import urllib.request
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOGS = ROOT / "logs"
LOGS.mkdir(exist_ok=True)
LOG = LOGS / "guard.log"
HEALTH = LOGS / "health.json"
PIDFILE = LOGS / "bot.pid"
PY = os.environ.get("QURAN_PY", r"C:\Python314\python.exe")
CHECK_EVERY = int(os.environ.get("GUARD_INTERVAL", "45"))
HEALTH_EVERY = int(os.environ.get("GUARD_HEALTH_EVERY", "20"))  # كل ~15 دقيقة


def _bot_token():
    try:
        for ln in (ROOT / ".env").read_text(encoding="utf-8-sig", errors="ignore").splitlines():
            if ln.strip().startswith("BOT_TOKEN="):
                return ln.split("=", 1)[1].strip()
    except Exception:  # noqa: BLE001
        pass
    return ""


TOKEN = _bot_token()


def health_ping(timeout=12):
    """فحص حقيقي للبوت عبر getMe (لا يتعارض مع polling)."""
    if not TOKEN:
        return None, "no-token"
    try:
        with urllib.request.urlopen(
                f"https://api.telegram.org/bot{TOKEN}/getMe", timeout=timeout) as r:
            d = json.loads(r.read())
            if d.get("ok"):
                return True, d.get("result", {}).get("username")
            return False, d.get("description")
    except Exception as e:  # noqa: BLE001
        return False, f"{type(e).__name__}: {str(e)[:80]}"


def log(msg):
    line = f"{datetime.now().astimezone().isoformat(timespec='seconds')} {msg}"
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def bot_running():
    try:
        out = subprocess.run(["tasklist", "/FI", "IMAGENAME eq python.exe", "/NH"],
                             capture_output=True, text=True, timeout=20).stdout or ""
        pids = [int(p) for p in __import__("re").findall(r"\b(\d{2,7})\b", out)]
    except Exception:
        pids = []
    # تحقق أدق: العمليات التي تشغّل app.main
    try:
        ps = ("Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | "
              "Where-Object { $_.CommandLine -like '*app.main*' } | "
              "Select-Object -ExpandProperty ProcessId")
        out = subprocess.run(["powershell", "-NoProfile", "-Command", ps],
                             capture_output=True, text=True, timeout=40).stdout or ""
        running = [int(x) for x in out.split() if x.strip().isdigit()]
        return running
    except Exception as e:  # noqa: BLE001
        log(f"check failed: {e}")
        return []


def start_bot():
    out = open(LOGS / "bot.out.log", "a", encoding="utf-8")
    err = open(LOGS / "bot.err.log", "a", encoding="utf-8")
    p = subprocess.Popen([PY, "-u", "-m", "app.main"], cwd=str(ROOT),
                         stdout=out, stderr=err,
                         creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    try:
        PIDFILE.write_text(str(p.pid), encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass
    log(f"STARTED pid={p.pid}")
    return p.pid


def main():
    log(f"guard started — interval={CHECK_EVERY}s health_every={HEALTH_EVERY}")
    i = 0
    fails = 0
    while True:
        try:
            running = bot_running()
            if not running:
                log("bot DOWN — restarting")
                start_bot()
            else:
                try:
                    PIDFILE.write_text(str(running[0]), encoding="utf-8")
                except Exception:  # noqa: BLE001
                    pass
            if i % HEALTH_EVERY == 0:
                ok, info = health_ping()
                try:
                    HEALTH.write_text(json.dumps({
                        "ts": datetime.now().astimezone().isoformat(timespec="seconds"),
                        "bot_username": info if ok else None,
                        "api_ok": bool(ok), "detail": None if ok else info,
                        "pid": running[0] if running else None,
                    }, ensure_ascii=False, indent=1), encoding="utf-8")
                except Exception:  # noqa: BLE001
                    pass
                if ok is False:
                    fails += 1
                    log(f"health ping FAILED ({fails}): {info}")
                    if fails >= 2 and running:
                        log("health failed twice — restarting bot")
                        try:
                            subprocess.run(["taskkill", "/PID", str(running[0]), "/F"], timeout=20,
                                           capture_output=True)
                        except Exception:  # noqa: BLE001
                            pass
                        time.sleep(2)
                        start_bot()
                        fails = 0
                else:
                    fails = 0
        except Exception as e:  # noqa: BLE001
            log(f"guard error: {type(e).__name__}: {e}")
        i += 1
        time.sleep(CHECK_EVERY)


if __name__ == "__main__":
    main()
