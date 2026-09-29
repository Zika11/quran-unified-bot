# -*- coding: utf-8 -*-
"""فحص دخان سريع (أقل من 30 ثانية) للمسارات الاستثنائية + تحقق حيّ.
يُنتج tests/failure_smoke.json — دليل تشغيل (operation) وفحص (check) قابل للفحص.
"""
import asyncio
import json
import sys
import time
from datetime import datetime
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from app.config import settings
from app import services as S
from app.util import http_json, ExternalError, friendly_error
from app.handlers import start as H_start
from app.handlers import advanced as H_adv
from stubs import FakeUpdate, FakeContext, FakeApplication, last_text

OUT = []


def rec(name, ok, note=""):
    OUT.append({"check": name, "ok": bool(ok), "note": str(note)[:220]})
    print(("PASS " if ok else "FAIL ") + name + (f" — {note}" if note else ""))


async def main():
    t0 = time.time()
    # 1) فشل شبكة حقيقي (سريع)
    try:
        http_json("http://10.255.255.1:9/health", timeout=3, service="UnreachableHost")
        rec("network_failure_raises", False, "لم يرمِ استثناء")
    except ExternalError as e:
        rec("network_failure_raises", True, f"{e.detail} in {time.time()-t0:.1f}s")
        rec("arabic_error_message", "تعذّر الاتصال بالخدمة" in friendly_error(e), friendly_error(e)[:60])
    # 2) مدخل غير صالح
    try:
        S.normalize_ref("abc")
        rec("invalid_ref_rejected", False, "لم يرفض")
    except ValueError as e:
        rec("invalid_ref_rejected", True, str(e)[:60])
    # 3) تحديث بلا مستخدم لا يُسقط الهاندلر
    app = FakeApplication(None)
    up = FakeUpdate(); up.effective_user = None
    try:
        await H_start.on_text(up, FakeContext(app, args=["مرحبا"]))
        rec("no_user_update_no_crash", True, "تم التجاهل")
    except Exception as e:  # noqa: BLE001
        rec("no_user_update_no_crash", False, f"{type(e).__name__}: {e}")
    # 4) تدهور لطيف عند فشل ffmpeg
    orig = S.make_ayah_video
    S.make_ayah_video = lambda *a, **k: (_ for _ in ()).throw(ExternalError("ffmpeg", "mock"))
    try:
        from app.db import DB
        app2 = FakeApplication(DB(ROOT / "data" / "smoke.db"))
        up2 = FakeUpdate(); c2 = FakeContext(app2, args=["112:1"])
        await H_adv.cmd_video(up2, c2)
        kinds = {x["kind"] for x in up2.message.sent}
        rec("ffmpeg_fallback_photo_audio", bool(kinds & {"photo", "audio"}), str(kinds))
    except Exception as e:  # noqa: BLE001
        rec("ffmpeg_fallback_photo_audio", False, f"{type(e).__name__}: {e}")
    finally:
        S.make_ayah_video = orig
    # 5) تحقق حيّ من الواجهة (check)
    try:
        r = requests.get(f"https://api.telegram.org/bot{settings.BOT_TOKEN}/getMe", timeout=15).json()
        rec("live_api_getMe", bool(r.get("ok")), "@" + str((r.get("result") or {}).get("username")))
    except Exception as e:  # noqa: BLE001
        rec("live_api_getMe", False, str(e)[:80])

    passed = sum(1 for o in OUT if o["ok"])
    summary = {"generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
               "kind": "failure-path smoke (operation+check)", "passed": passed, "total": len(OUT),
               "elapsed_s": round(time.time() - t0, 1), "checks": OUT}
    (ROOT / "tests" / "failure_smoke.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"=== {passed}/{len(OUT)} PASS in {summary['elapsed_s']}s ===")
    return 0 if passed == len(OUT) else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
