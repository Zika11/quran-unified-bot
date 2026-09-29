# -*- coding: utf-8 -*-
"""إثبات معالجة المسارات الاستثنائية (فشل واجهة خارجية · مدخل غير صالح · ضغط مدخلات · توكن غير صالح · تدهور لطيف).

يُشغَّل:  python tests/failure_paths.py
يُخرج:  tests/failure_paths_report.json
"""
import asyncio
import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from app.config import settings            # noqa: E402
from app.db import DB                       # noqa: E402
from app import services as S               # noqa: E402
from app.util import http_json, ExternalError, friendly_error, ARABIC_ERROR  # noqa: E402
from app.handlers import quran as H_quran    # noqa: E402
from app.handlers import advanced as H_adv   # noqa: E402
from app.handlers import worship as H_worship  # noqa: E402
from app.handlers import start as H_start     # noqa: E402
from stubs import FakeUpdate, FakeContext, FakeApplication, last_text  # noqa: E402

RESULTS = []


def rec(name, ok, note=""):
    RESULTS.append({"test": name, "ok": bool(ok), "note": str(note)[:300]})
    print(("✅ " if ok else "❌ ") + name + (f"  — {note}" if note else ""))


# ============================================================ 1) فشل واجهة حقيقي (شبكة)
def test_real_network_failure():
    print("\n[1] فشل واجهة خارجية حقيقي (عنوان غير قابل للوصول)")
    t0 = time.time()
    try:
        http_json("http://10.255.255.1:9/health", timeout=4, service="UnreachableHost")
        rec("فشل الشبكة يرمي استثناء", False, "لم يرمِ استثناء")
    except ExternalError as e:
        dt = time.time() - t0
        rec("فشل الشبكة يرمي ExternalError", True, f"{e.detail} ({dt:.1f}s)")
        msg = friendly_error(e)
        rec("فشل الشبكة ⇒ رسالة عربية واضحة",
            "تعذّر الاتصال بالخدمة" in msg and "UnreachableHost" in msg, msg[:70])
        rec("لا تعليق (انتهى خلال المهلة)", dt < 12, f"{dt:.1f}s")


# ============================================================ 2) مدخلات غير صالحة عبر الهاندلرات
async def test_bad_input(db):
    print("\n[2] مدخلات غير صالحة عبر الهاندلرات")
    app = FakeApplication(db)
    ctx = FakeContext(app)
    cases = [
        ("/ayah abc", ["abc"], H_quran.cmd_ayah),
        ("/ayah 999:1", ["999:1"], H_quran.cmd_ayah),
        ("/ayah 2:0", ["2:0"], H_quran.cmd_ayah),
        ("/tafsir ::", ["::"], H_quran.cmd_tafsir),
        ("/hz x", ["x"], H_adv.cmd_hz),
        ("/tasmia 5", ["5"], H_adv.cmd_tasmia),
    ]
    for label, args, fn in cases:
        up = FakeUpdate()
        c = FakeContext(app, args=args)
        await fn(up, c)
        txt = last_text(up)
        rec(f"{label} ⇒ رسالة عربية", ("مدخل غير صحيح" in txt) or ("⚠️" in txt) or ("اكتب" in txt), txt[:70])
    # /surah برقم خارج النطاق
    up = FakeUpdate(); c = FakeContext(app, args=["999"])
    await H_quran.cmd_surah(up, c)
    rec("/surah 999 ⇒ رسالة واضحة", "⚠️" in last_text(up) or "1-114" in last_text(up), last_text(up)[:70])


async def test_no_user_update(db):
    print("\n[2b] تحديث بلا مستخدم (منشور قناة/أدمن مجهول)")
    app = FakeApplication(db)
    up = FakeUpdate()
    up.effective_user = None
    c = FakeContext(app, args=["مرحبا"])
    try:
        await H_start.on_text(up, c)
        rec("نص حر بلا مستخدم ⇒ تجاهل بلا انهيار", True, "تم تجاهله بهدوء")
    except Exception as e:  # noqa: BLE001
        rec("نص حر بلا مستخدم ⇒ تجاهل بلا انهيار", False, f"{type(e).__name__}: {e}")
    up2 = FakeUpdate()
    up2.effective_user = None
    try:
        await H_start.cmd_start(up2, FakeContext(app))
        rec("‏/start بلا مستخدم لا ينهار الجلسة", True, "تم تجاهله")
    except Exception as e:  # noqa: BLE001
        rec("‏/start بلا مستخدم لا ينهار الجلسة", False, f"{type(e).__name__}: {e}")


# ============================================================ 3) ضغط مدخلات (سبام)
async def test_spam(db):
    print("\n[3] ضغط مدخلات سريعة (40 طلبًا متزامنًا)")
    app = FakeApplication(db)
    async def one(i):
        up = FakeUpdate(); c = FakeContext(app, args=["صبر" if i % 2 else "نور"])
        await H_quran.cmd_search(up, c)
        return bool(up.message.sent)
    res = await asyncio.gather(*[one(i) for i in range(40)], return_exceptions=True)
    errs = [r for r in res if isinstance(r, Exception)]
    oks = [r for r in res if r is True]
    rec("40 طلبًا متزامنًا بلا انهيار", len(errs) == 0, f"{len(oks)}/40 ردّت، أخطاء غير مُدارة: {len(errs)}")


# ============================================================ 4) تدهور لطيف (بدائل)
async def test_graceful(db):
    print("\n[4] تدهور لطيف (بدائل عند غياب مكوّن)")
    app = FakeApplication(db)
    # (أ) فشل ffmpeg في الفيديو ⇒ يجب أن يعطي صورة + صوت بدل أن ينهار
    orig_make = S.make_ayah_video
    def boom(*a, **k):
        raise ExternalError("ffmpeg", "غير مثبّت (محاكاة)")
    S.make_ayah_video = boom
    try:
        up = FakeUpdate(); c = FakeContext(app, args=["112:1"])
        await H_adv.cmd_video(up, c)
        kinds = {x["kind"] for x in up.message.sent}
        rec("فشل ffmpeg ⇒ صورة/صوت بديل بلا انهيار", kinds & {"photo", "audio", "video"} != set(),
            f"المخرجات: {kinds}")
    except Exception as e:  # noqa: BLE001
        rec("فشل ffmpeg ⇒ تدهور لطيف", False, f"{type(e).__name__}: {e}")
    finally:
        S.make_ayah_video = orig_make
    # (ب) صوت السورة غير متاح ⇒ تراجع لصوت الآية الأولى
    orig_reach = S._reachable
    S._reachable = lambda url: False
    try:
        up = FakeUpdate(); c = FakeContext(app, args=["112"])
        await H_quran.cmd_play(up, c)
        got_audio = any(x["kind"] == "audio" for x in up.message.sent)
        rec("صوت السورة غير متاح ⇒ صوت آية بديل", got_audio, last_text(up)[:60] or "أُرسل صوت")
    except Exception as e:  # noqa: BLE001
        rec("صوت السورة غير متاح ⇒ بديل", False, f"{type(e).__name__}: {e}")
    finally:
        S._reachable = orig_reach


# ============================================================ 5) توكن غير صالح
def test_bad_token():
    print("\n[5] توكن غير صالح (تشغيل --check بمفتاح سيئ)")
    env = dict(os.environ)
    env["BOT_TOKEN"] = "123456789:INVALID_TOKEN_FOR_TEST_0000000000000"
    r = subprocess.run([r"C:\Python314\python.exe", "-m", "app.main", "--check"],
                       capture_output=True, text=True, cwd=str(ROOT), env=env,
                       encoding="utf-8", errors="replace", timeout=90)
    out = (r.stdout or "") + (r.stderr or "")
    rec("توكن غير صالح ⇒ لا انهيار + رسالة واضحة",
        "غير صالح" in out or "Unauthorized" in out or r.returncode == 1,
        f"exit={r.returncode} | {out.strip().splitlines()[-1][:80] if out.strip() else ''}")


# ============================================================ 6) التتبّع في التخزين والسجلات
def test_trace_after_failures(db):
    print("\n[6] التتبّع بعد حالات الفشل (تخزين + سجل)")
    stats = db.stats()
    recent = db.last_requests(200)
    statuses = {}
    for r in recent:
        statuses[r["status"]] = statuses.get(r["status"], 0) + 1
    rec("طلبات مسجّلة في التخزين", stats["requests"] > 0, f"{stats['requests']} طلب")
    rec("حالات فشل مسجّلة (bad_input/external_error)",
        any(s in statuses for s in ("bad_input", "external_error", "error")),
        f"التوزيع: {statuses}")
    logf = settings.LOG_DIR / "bot.log"
    tok = settings.BOT_TOKEN
    txt = logf.read_text(encoding="utf-8", errors="ignore") if logf.exists() else ""
    rec("سجل البوت موجود", logf.exists(), str(logf))
    rec("السجل لا يحتوي التوكن", (tok not in txt) if tok else True, "لا تسريب" if (tok and tok not in txt) else "-")


async def _main():
    print("=" * 70)
    print("إثبات معالجة المسارات الاستثنائية — بوت القرآن الموحّد")
    print("=" * 70)
    db = DB(ROOT / "data" / "failure_test.db")
    test_real_network_failure()
    await test_bad_input(db)
    await test_no_user_update(db)
    await test_spam(db)
    await test_graceful(db)
    test_bad_token()
    test_trace_after_failures(db)

    passed = sum(1 for r in RESULTS if r["ok"])
    total = len(RESULTS)
    print("=" * 70)
    print(f"النتيجة: {passed}/{total} ناجح")
    (ROOT / "tests" / "failure_paths_report.json").write_text(
        json.dumps({"passed": passed, "total": total, "results": RESULTS}, ensure_ascii=False, indent=2),
        encoding="utf-8")
    print("تقرير:", ROOT / "tests" / "failure_paths_report.json")
    return passed == total


if __name__ == "__main__":
    ok = asyncio.run(_main())
    sys.exit(0 if ok else 1)
