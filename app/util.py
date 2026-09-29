# -*- coding: utf-8 -*-
"""أدوات مشتركة: HTTP آمن، سجلات، معرّف طلب، تنسيق نصوص."""
import logging
import uuid
import html
import functools
from logging.handlers import RotatingFileHandler

import requests

from .config import settings

# ---------------------------------------------------------------- logging
def setup_logging():
    settings.ensure_dirs()
    root = logging.getLogger()
    if root.handlers:
        return logging.getLogger("quran")
    root.setLevel(logging.INFO)
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s")
    fh = RotatingFileHandler(settings.LOG_DIR / "bot.log", maxBytes=2_000_000,
                             backupCount=3, encoding="utf-8")
    fh.setFormatter(fmt)
    root.addHandler(fh)
    ch = logging.StreamHandler()
    ch.setFormatter(fmt)
    root.addHandler(ch)
    # لا نُسجّل تفاصيل httpx/telegram.ext حتى لا يُكتب التوكن في اللوجات
    for noisy in ("httpx", "httpcore", "telegram.ext", "apscheduler"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
    return logging.getLogger("quran")


log = setup_logging()


# ---------------------------------------------------------------- HTTP
HTTP_HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0) Chrome/126.0"}


class ExternalError(Exception):
    """فشل واجهة خارجية — يُترجم إلى رسالة عربية واضحة للمستخدم."""

    def __init__(self, service: str, detail: str = ""):
        self.service = service
        self.detail = detail
        super().__init__(f"{service}: {detail}")


def http_json(url, timeout=None, service="api"):
    timeout = timeout or settings.HTTP_TIMEOUT
    try:
        r = requests.get(url, headers=HTTP_HEADERS, timeout=timeout)
        if r.status_code != 200:
            raise ExternalError(service, f"HTTP {r.status_code}")
        return r.json()
    except ExternalError:
        raise
    except requests.exceptions.Timeout:
        raise ExternalError(service, "انتهت مدة الاتصال")
    except requests.exceptions.ConnectionError:
        raise ExternalError(service, "تعذّر الاتصال بالإنترنت")
    except Exception as e:  # noqa: BLE001
        raise ExternalError(service, str(e)[:120])


ARABIC_ERROR = "⚠️ تعذّر الاتصال بالخدمة ({service}) حاليًا. تأكد من الإنترنت وحاول مرة أخرى بعد قليل."


def friendly_error(exc: Exception) -> str:
    if isinstance(exc, ExternalError):
        return ARABIC_ERROR.format(service=exc.service)
    return "⚠️ حدث خطأ غير متوقع. تم تسجيل المشكلة، حاول مرة أخرى."


# ---------------------------------------------------------------- helpers
def esc(s: str) -> str:
    return html.escape(str(s if s is not None else ""))


def short_id() -> str:
    return uuid.uuid4().hex[:12]


def chunk_list(seq, n):
    for i in range(0, len(seq), n):
        yield seq[i:i + n]


def paginate(items, page, per_page):
    total = max(1, (len(items) + per_page - 1) // per_page)
    page = max(1, min(page, total))
    start = (page - 1) * per_page
    return items[start:start + per_page], page, total


def trace(handler_name):
    """يُغلّف الهاندلر: يولّد معرّف طلب، يسجّله في DB، ويعالج الأخطاء برسالة عربية."""
    def deco(fn):
        @functools.wraps(fn)
        async def wrapper(update, context, *a, **kw):
            rid = short_id()
            db = context.application.bot_data.get("db")
            uobj = getattr(update, "effective_user", None)
            user_id = uobj.id if uobj else None
            kind = "callback" if getattr(update, "callback_query", None) else "message"
            if db:
                db.log_request(rid, user_id, kind, handler_name)
            # تحديث بلا مستخدم (منشور قناة / أدمن مجهول) — يُتجاهل بهدوء بدل الانهيار
            if user_id is None and getattr(update, "callback_query", None) is None:
                log.info("req=%s %s ignored: update without user", rid, handler_name)
                if db:
                    db.finish_request(rid, "ignored")
                return
            try:
                res = await fn(update, context, *a, **kw)
                if db:
                    db.finish_request(rid, "ok")
                return res
            except ExternalError as e:
                log.warning("req=%s %s external: %s", rid, handler_name, e)
                if db:
                    db.finish_request(rid, "external_error", str(e)[:300])
                await _reply_error(update, ARABIC_ERROR.format(service=e.service))
            except ValueError as e:
                log.info("req=%s %s bad input: %s", rid, handler_name, e)
                if db:
                    db.finish_request(rid, "bad_input", str(e)[:300])
                await _reply_error(update, "⚠️ مدخل غير صحيح: " + str(e)[:200])
            except Exception as e:  # noqa: BLE001
                log.exception("req=%s %s failed: %s", rid, handler_name, e)
                if db:
                    db.finish_request(rid, "error", f"{type(e).__name__}: {e}"[:300])
                await _reply_error(update, friendly_error(e))
        return wrapper
    return deco


async def reply_audio_safe(message, url, caption=None):
    """يرسل ملفًا صوتيًا، وعند فشل جلب الرابط يتراجع إلى رسالة نصية بالرابط (مسار استثنائي)."""
    try:
        await message.reply_audio(url, caption=caption)
        return True
    except Exception as e:  # noqa: BLE001
        log.info("audio url failed (%s): %s", type(e).__name__, str(e)[:80])
    try:
        await message.reply_text((caption or "🎧") + "\n🔗 " + str(url) +
                                 "\n<i>(تعذّر إرسال الصوت مباشرة — افتح الرابط للاستماع)</i>",
                                 parse_mode="HTML")
    except Exception:  # noqa: BLE001
        pass
    return False


async def _reply_error(update, text):
    msg = getattr(update, "effective_message", None)
    try:
        if msg:
            await msg.reply_text(text)
        elif getattr(update, "callback_query", None):
            await update.callback_query.answer(text, show_alert=True)
    except Exception:  # noqa: BLE001
        pass
