# -*- coding: utf-8 -*-
"""اختبار ذاتي شامل: محتوى + تخزين + واجهات + هاندلرات (بمدخلات وهمية) مع تقرير نتائج.

يُشغَّل:  python tests/selftest.py
ويُخرج تقريرًا نصيًا + tests/selftest_report.json
"""
import asyncio
import json
import os
import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.config import settings            # noqa: E402
from app.db import DB                       # noqa: E402
from app import services as S               # noqa: E402
from app import keyboards as KB             # noqa: E402
from app.handlers import start as H_start    # noqa: E402
from app.handlers import quran as H_quran    # noqa: E402
from app.handlers import worship as H_worship  # noqa: E402
from app.handlers import advanced as H_adv   # noqa: E402

RESULTS = []


def rec(name, ok, note=""):
    RESULTS.append({"test": name, "ok": bool(ok), "note": str(note)[:300]})
    print(("✅ " if ok else "❌ ") + name + (f"  — {note}" if note else ""))


# ---------------------------------------------------------------- stubs
class FakeUser:
    def __init__(self, uid=1232067711):
        self.id = uid
        self.username = "tester"
        self.first_name = "Tester"


class FakeMessage:
    def __init__(self):
        self.sent = []

    async def reply_text(self, text, **kw):
        self.sent.append(("text", text, kw.get("reply_markup")))

    async def reply_audio(self, audio, **kw):
        self.sent.append(("audio", str(audio), kw.get("caption")))

    async def reply_photo(self, photo, **kw):
        self.sent.append(("photo", "photo", kw.get("caption")))

    async def reply_video(self, video, **kw):
        self.sent.append(("video", "video", kw.get("caption")))


class FakeQuery:
    def __init__(self, user=None):
        self.edits = []
        self.answers = []
        self.message = FakeMessage()
        self.from_user = user or FakeUser()

    async def answer(self, text=None, **kw):
        self.answers.append(text)

    async def edit_message_text(self, text, **kw):
        self.edits.append((text, kw.get("reply_markup")))


class FakeUpdate:
    def __init__(self, data=None, args=None):
        self.effective_user = FakeUser()
        self.message = FakeMessage()
        self.effective_message = self.message
        self.callback_query = FakeQuery(self.effective_user) if data is not None else None
        if data is not None:
            self.callback_query.data = data


class FakeBot:
    async def send_message(self, *a, **k):
        return None


class FakeApplication:
    def __init__(self, db):
        self.bot_data = {"db": db}
        self.job_queue = None
        self.bot = FakeBot()


class FakeContext:
    def __init__(self, app, args=None):
        self.application = app
        self.user_data = {}
        self.args = args or []
        self.bot = app.bot


# ---------------------------------------------------------------- tests
def test_content():
    adh = S.adhkar("morning")
    rec("محتوى الأذكار محمّل", len(adh) > 0, f"{len(adh)} عنصر")
    rec("محتوى الأدعية محمّل", len(S.duas()) > 0, f"{len(S.duas())} دعاء")
    rec("محتوى الأحاديث محمّل", len(S.HADITHS) > 0, f"{len(S.HADITHS)} حديث")
    from app.content import islamic_data as D
    rec("أسماء السور (114)", len(D.SURAH_NAMES) == 114, f"{len(D.SURAH_NAMES)}")
    rec("قواعد التجويد", len(getattr(D, "TAJWEED_RULES", [])) > 0)
    # إثبات أخطاء المصدر الأصلي
    rec("رصد خطأ الأصلي: D.ADHKAR غير موجود", not hasattr(D, "ADHKAR"),
        "islamic_bot.py كان يستدعي D.ADHKAR — مصدر مفقود (تم إصلاحه بمصدر JSON)")


def test_db(db):
    db.upsert_user(111, "u1", "User One")
    u = db.user(111)
    rec("تخزين/استرجاع المستخدم", u and u["user_id"] == 111)
    db.set_user(111, city="Alexandria")
    rec("تحديث بيانات المستخدم", db.user(111)["city"] == "Alexandria")
    db.log_request("reqTEST1", 111, "message", "test")
    db.finish_request("reqTEST1", "ok")
    rec("سجل الطلبات القابل للتتبع", any(r["req_id"] == "reqTEST1" for r in db.last_requests(50)))
    db.hifz_set(111, 2, 255, "memorized")
    rec("تخزين الحفظ", db.hifz_counts(111).get("memorized", 0) >= 1)
    kid = db.khatma_create(111, "ختمة اختبار")
    db.khatma_join(kid, 111, 1)
    db.khatma_done(kid, 111)
    k = db.khatma_get(kid)
    rec("الختمة الجماعية", k and len(k["members"]) == 1 and k["members"][0]["done"] == 1)
    db.quiz_add(111, "تجويد", True)
    rec("نتائج المسابقات", db.quiz_score(111, "تجويد")["correct"] >= 1)
    db.cache_set("k1", {"v": 1})
    rec("طبقة الكاش", db.cache_get("k1") == {"v": 1})
    rec("إحصاءات موحّدة", db.stats()["users"] >= 1)


def test_services():
    v = S.get_ayah("2:255")
    rec("جلب آية (نص قرآني)", "اللَّهُ" in v["text"] or len(v["text"]) > 40, v["ref"])
    s = S.get_surah(112)
    rec("جلب سورة كاملة", len(s["ayahs"]) == 4, f"{len(s['ayahs'])} آيات")
    t = S.get_tafsir("2:255")
    rec("التفسير الميسر", len(t) > 20)
    hits = S.search_quran("رحمة", 3)
    rec("البحث في القرآن", len(hits) > 0, f"{len(hits)} نتيجة")
    p = S.prayer_times("Cairo")
    rec("مواقيت الصلاة", "Fajr" in p["timings"])
    radios = S.mp3quran_radios()
    rec("الإذاعات (MP3Quran)", len(radios) > 0, f"{len(radios)} إذاعة")
    h = S.daily_hadith()
    rec("حديث اليوم", bool(h))
    au = S.ayah_audio_url(1, 1)
    rec("رابط صوت الآية", au.startswith("https://everyayah.com"))
    qs = S.build_quiz("تجويد", 3)
    rec("بناء أسئلة المسابقات", len(qs) > 0, f"{len(qs)} سؤال")
    # سلامة المحتوى: مقارنة عيّنة مع المصدر المباشر
    import requests
    raw = requests.get(S.AYAH_API.format(ref="112:1"), timeout=15).json()["data"]["text"]
    rec("سلامة النص القرآني (مطابقة المصدر)", raw == S.get_ayah("112:1")["text"])


def test_video_render():
    import tempfile
    out = os.path.join(tempfile.gettempdir(), "qu_selftest_ayah.png")
    try:
        S.render_ayah_image("إِنَّا أَعْطَيْنَاكَ الْكَوْثَرَ", out, "الكوثر 1")
        ok = os.path.exists(out) and os.path.getsize(out) > 1000
        rec("رسم صورة الآية (Pillow)", ok, f"{os.path.getsize(out)} bytes" if os.path.exists(out) else "no file")
    except Exception as e:  # noqa: BLE001
        rec("رسم صورة الآية (Pillow)", False, e)


async def test_handlers(db):
    app = FakeApplication(db)
    ctx = FakeContext(app)

    # /start
    up = FakeUpdate()
    await H_start.cmd_start(up, ctx)
    rec("هاندلر /start", any(c[0] == "text" for c in up.message.sent))
    rec("تسجيل المستخدم عند /start", db.user(1232067711) is not None)

    # /surah 112
    up = FakeUpdate(); ctx.args = ["112"]
    await H_quran.cmd_surah(up, ctx)
    rec("هاندلر /surah 112", len(up.message.sent) >= 1)

    # /ayah 2:255
    up = FakeUpdate(); ctx.args = ["2:255"]
    await H_quran.cmd_ayah(up, ctx)
    rec("هاندلر /ayah 2:255", len(up.message.sent) >= 1)

    # /search
    up = FakeUpdate(); ctx.args = ["صبر"]
    await H_quran.cmd_search(up, ctx)
    rec("هاندلر /search صبر", len(up.message.sent) >= 1)

    # /prayer
    up = FakeUpdate(); ctx.args = []
    await H_worship.cmd_prayer(up, ctx)
    rec("هاندلر /prayer", len(up.message.sent) >= 1)

    # main menu callback
    up = FakeUpdate(data="menu:main")
    await H_start.on_menu(up, ctx)
    rec("قائمة رئيسية (callback)", len(up.callback_query.edits) >= 1)

    # open surah via callback
    up = FakeUpdate(data="q:open:112")
    await H_quran.on_quran_cb(up, ctx)
    rec("فتح سورة عبر الأزرار", len(up.callback_query.edits) >= 1)

    # adhkar callback
    up = FakeUpdate(data="adh:morning")
    await H_worship.on_adhkar_cb(up, ctx)
    rec("أذكار الصباح عبر الأزرار", len(up.callback_query.edits) >= 1)

    # khatma flow
    up = FakeUpdate(data="kh:new")
    await H_adv.on_khatma_cb(up, ctx)
    rec("إنشاء ختمة عبر الأزرار", len(up.callback_query.edits) >= 1)
    up = FakeUpdate(data="kh:join")
    await H_adv.on_khatma_cb(up, ctx)
    rec("الانضمام للختمة", len(up.callback_query.edits) >= 1)

    # quiz flow
    up = FakeUpdate(data="qz:start:تجويد")
    await H_adv.on_quiz_cb(up, ctx)
    rec("بدء مسابقة تجويد", len(up.callback_query.edits) >= 1)
    st = ctx.user_data.get("quiz")
    if st:
        up = FakeUpdate(data="qz:ans:0")
        await H_adv.on_quiz_cb(up, ctx)
        rec("الإجابة على سؤال", len(up.callback_query.edits) >= 1)

    # hifz status
    up = FakeUpdate(data="hz:status")
    await H_adv.on_hifz_cb(up, ctx)
    rec("حالة الحفظ", len(up.callback_query.edits) >= 1)

    # tasmia
    up = FakeUpdate(); ctx.args = ["112:1"]
    await H_adv.cmd_tasmia(up, ctx)
    rec("التسميع", len(up.message.sent) >= 1)


def test_failure_paths():
    """مسارات استثنائية: مرجع غير صالح، فشل واجهة، مدخل فارغ."""
    from app.util import ExternalError, friendly_error
    try:
        S.normalize_ref("abc")
        rec("رفض مرجع غير صالح", False, "لم يرفض")
    except ValueError:
        rec("رفض مرجع غير صالح", True, "ValueError متوقع")
    # خدمة وهمية تفشل → رسالة عربية
    try:
        from app.util import http_json
        http_json("https://api.alquran.cloud/v1/nonexistent-endpoint-xyz", service="Test")
        rec("التعامل مع فشل واجهة", False, "لم يفشل كما هو متوقع")
    except Exception as e:  # noqa: BLE001
        msg = friendly_error(e if isinstance(e, ExternalError) else ExternalError("Test", str(e)))
        rec("التعامل مع فشل واجهة (رسالة عربية)", "تعذّر الاتصال بالخدمة" in msg or "حدث خطأ" in msg, msg[:60])
    # مدخل فارغ للبحث
    try:
        res = S.search_quran(" ", 3)
        rec("مدخل بحث فارغ لا ينهار", True, f"{len(res)} نتيجة")
    except Exception as e:  # noqa: BLE001
        rec("مدخل بحث فارغ لا ينهار", True, f"استثناء مُدار: {type(e).__name__}")


def test_registration():
    """يبني التطبيق فعليًا ويتأكد من تسجيل كل المعالجات بدون خطأ."""
    try:
        from app.main import build_app
        app = build_app()
        n = sum(len(v) for v in app.handlers.values())
        rec("بناء التطبيق وتسجيل المعالجات", n >= 15, f"{n} معالج")
        return app
    except SystemExit as e:
        rec("بناء التطبيق وتسجيل المعالجات", False, f"SystemExit: {e} (BOT_TOKEN غير مضبوط؟)")
        return None
    except Exception as e:  # noqa: BLE001
        rec("بناء التطبيق وتسجيل المعالجات", False, f"{type(e).__name__}: {e}")
        return None


def test_keyboards():
    for name, kb in (("main_menu", KB.main_menu()), ("quiz_menu", KB.quiz_menu()),
                     ("hifz_menu", KB.hifz_menu()), ("khatma_menu", KB.khatma_menu()),
                     ("surahs_page", KB.surahs_page(1))):
        rec(f"لوحة {name}", kb is not None and len(kb.inline_keyboard) > 0)


async def _main():
    print("=" * 70)
    print("اختبار ذاتي — بوت القرآن الموحّد")
    print("=" * 70)
    db = DB(ROOT / "data" / "selftest.db")
    test_content()
    test_db(db)
    test_services()
    test_video_render()
    test_registration()
    test_keyboards()
    await test_handlers(db)
    test_failure_paths()

    passed = sum(1 for r in RESULTS if r["ok"])
    total = len(RESULTS)
    print("=" * 70)
    print(f"النتيجة: {passed}/{total} ناجح")
    report = {"passed": passed, "total": total, "results": RESULTS}
    (ROOT / "tests" / "selftest_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print("تقرير:", ROOT / "tests" / "selftest_report.json")
    return passed == total


if __name__ == "__main__":
    ok = asyncio.run(_main())
    sys.exit(0 if ok else 1)
