# -*- coding: utf-8 -*-
"""نقطة الدخول: يبني التطبيق، يسجّل المعالجات، ويشغّل المهام الدورية."""
import argparse
import asyncio
import os
import sys
from datetime import time as dtime
from zoneinfo import ZoneInfo

from telegram import Update
from telegram.ext import Application, ContextTypes

from .config import settings, RECITERS
from .db import DB
from .util import log, esc, short_id
from . import services as S
from . import handlers

CAIRO = ZoneInfo(settings.TIMEZONE)


def build_app() -> Application:
    settings.ensure_dirs()
    if not settings.BOT_TOKEN:
        raise SystemExit("⛔ BOT_TOKEN غير موجود في .env — راجع .env.example")
    app = Application.builder().token(settings.BOT_TOKEN).build()
    app.bot_data["db"] = DB()
    handlers.register_all(app)
    app.add_error_handler(on_error)
    _register_jobs(app)
    return app


# ---------------------------------------------------------------- jobs
async def job_daily_ayah(context: ContextTypes.DEFAULT_TYPE):
    db = context.application.bot_data["db"]
    try:
        v = S.daily_verse() or S.random_ayah()
    except Exception as e:  # noqa: BLE001
        log.warning("daily_ayah fetch failed: %s", e)
        return
    text = (f"🌅 <b>آية اليوم — {esc(v.get('surah',''))}</b>\n\n{esc(v.get('text',''))}\n\n"
            f"{('📖 ' + esc(v['tafsir'])) if v.get('tafsir') else ''}")
    for uid in db.subscribers("notify_ayah"):
        try:
            await context.bot.send_message(uid, text, parse_mode="HTML")
        except Exception as e:  # noqa: BLE001
            log.info("daily_ayah to %s failed: %s", uid, e)


async def job_daily_adhkar(context: ContextTypes.DEFAULT_TYPE):
    db = context.application.bot_data["db"]
    items = S.adhkar("evening")
    txt = "🌙 <b>أذكار المساء</b>\n\n" + "\n\n".join("• " + a["text"] for a in items)
    for uid in db.subscribers("notify_adhkar"):
        try:
            await context.bot.send_message(uid, esc(txt)[:3900], parse_mode="HTML")
        except Exception as e:  # noqa: BLE001
            log.info("daily_adhkar to %s failed: %s", uid, e)


async def job_prayer_reminder(context: ContextTypes.DEFAULT_TYPE):
    """تنبيه عند دخول وقت صلاة (فحص كل 5 دقائق)."""
    db = context.application.bot_data["db"]
    from datetime import datetime
    now = datetime.now(CAIRO).strftime("%H:%M")
    for u in db.all_users():
        if not u.get("notify_prayer"):
            continue
        try:
            t = S.prayer_times(u["city"], u["country"])["timings"]
        except Exception:  # noqa: BLE001
            continue
        for k in ("Fajr", "Dhuhr", "Asr", "Maghrib", "Isha"):
            if t.get(k, "").startswith(now):
                try:
                    await context.bot.send_message(u["user_id"], f"🕌 حان الآن وقت صلاة {k}", parse_mode="HTML")
                except Exception:  # noqa: BLE001
                    pass


def _register_jobs(app: Application):
    jq = app.job_queue
    if jq is None:
        log.warning("JobQueue غير متاح (تحتاج python-telegram-bot[job-queue])")
        return
    jq.run_daily(job_daily_ayah, time=dtime(settings.DAILY_AYAH_HOUR, 0, tzinfo=CAIRO), name="daily_ayah")
    jq.run_daily(job_daily_adhkar, time=dtime(settings.DAILY_ADHKAR_HOUR, 30, tzinfo=CAIRO), name="daily_adhkar")
    jq.run_repeating(job_prayer_reminder, interval=300, first=30, name="prayer_reminder")


# ---------------------------------------------------------------- errors
async def on_error(update: object, context: ContextTypes.DEFAULT_TYPE):
    err = context.error
    log.exception("unhandled error: %s", err)
    db = context.application.bot_data.get("db")
    if db:
        try:
            db.finish_request(short_id(), "unhandled", f"{type(err).__name__}: {err}"[:300])
        except Exception:  # noqa: BLE001
            pass
    if isinstance(update, Update) and update.effective_message:
        try:
            await update.effective_message.reply_text("⚠️ حدث خطأ غير متوقع، تم تسجيله. حاول مرة أخرى.")
        except Exception:  # noqa: BLE001
            pass


# ---------------------------------------------------------------- CLI
def run_checks(verbose=True):
    """فحص سريع: التوكن + القاعدة + عيّنات من الواجهات."""
    import requests
    ok = True
    settings.ensure_dirs()
    DB()
    if verbose:
        print("✅ قاعدة البيانات جاهزة:", settings.DB_PATH)
    if settings.BOT_TOKEN:
        try:
            r = requests.get(f"https://api.telegram.org/bot{settings.BOT_TOKEN}/getMe", timeout=15).json()
            if r.get("ok"):
                print(f"✅ التوكن صالح — البوت: @{r['result'].get('username')}")
            else:
                ok = False
                print("❌ التوكن غير صالح:", r.get("description"))
        except Exception as e:  # noqa: BLE001
            ok = False
            print("❌ تعذّر الوصول لتليجرام:", e)
    else:
        print("⚠️ لا يوجد BOT_TOKEN.")
    for name, fn in (("AlQuran.Cloud", lambda: S.get_ayah("2:255")),
                     ("AlAdhan", lambda: S.prayer_times("Cairo")),
                     ("MP3Quran", lambda: S.mp3quran_radios())):
        try:
            fn()
            print(f"✅ {name}")
        except Exception as e:  # noqa: BLE001
            ok = False
            print(f"❌ {name}: {e}")
    return ok


def main():
    ap = argparse.ArgumentParser(description="بوت القرآن الموحّد")
    ap.add_argument("--check", action="store_true", help="فحص الإعدادات والواجهات ثم الخروج")
    ap.add_argument("--selftest", action="store_true", help="اختبار وظائف دون الاتصال بتليجرام")
    args = ap.parse_args()
    if args.check:
        sys.exit(0 if run_checks() else 1)
    if args.selftest:
        import runpy
        from pathlib import Path
        runpy.run_path(str(Path(__file__).resolve().parent.parent / "tests" / "selftest.py"), run_name="__main__")
        sys.exit(0)
    app = build_app()
    log.info("🚀 بدء البوت (polling)…")
    pid_file = settings.LOG_DIR / "bot.pid"
    try:
        pid_file.write_text(str(os.getpid()), encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass
    try:
        app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)
    finally:
        try:
            pid_file.unlink(missing_ok=True)
        except Exception:  # noqa: BLE001
            pass


def _cloud_health():
    """وضع الاستضافة: خادم صحة HTTP على $PORT عندما يكون مضبوطًا (Back4App/Render...)."""
    port = os.environ.get("PORT")
    if not port:
        return
    try:
        import threading
        import time as _t
        from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
        started = _t.time()

        class _H(BaseHTTPRequestHandler):
            def do_GET(self):  # noqa: N802
                body = f"quran-unified OK uptime={int(_t.time()-started)}s".encode()
                self.send_response(200)
                self.send_header("Content-Type", "text/plain; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, *a):  # noqa: A003
                pass

        srv = ThreadingHTTPServer(("0.0.0.0", int(port)), _H)
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        log.info("cloud health server on :%s", port)
    except Exception as e:  # noqa: BLE001
        log.warning("health server failed: %s", e)


if __name__ == "__main__":
    _cloud_health()
    main()
