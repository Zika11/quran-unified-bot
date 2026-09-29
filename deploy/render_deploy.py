# -*- coding: utf-8 -*-
"""نشر البوت على Render (يحتاج مفتاح API من حسابك — لا يُطبع).

الاستخدام:
    python deploy/render_deploy.py <RENDER_API_KEY>

ما يفعله:
 1) يتحقق من المفتاح (GET /v1/owners).
 2) ينشئ Web Service من مستودع GitHub (Docker) على الخطة free.
 3) يضبط متغيرات البيئة (BOT_TOKEN من .env + PORT) ومسار الصحة "/".
لا يطبع أي قيمة سرية.
"""
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = Path(__file__).resolve().parent.parent
_tok_file = ROOT.parent.parent / ".openclaw" / "tmp" / "render_key.txt"
KEY = *** if len(sys.argv) > 1 else os.environ.get("RENDER_KEY") or (
    _tok_file.read_text(encoding="utf-8").strip() if _tok_file.exists() else "")).strip()
REPO = "https://github.com/Zika11/quran-unified-bot"
NAME = "quran-unified-bot"

if not KEY:
    ***"⛔ مطلوب مفتاح Render: python deploy/render_deploy.py rnd_xxx")
    sys.exit(2)

HDR = {"Authorization": "***" + KEY, "User-Agent": "autoclaw-deploy", "Accept": "application/json"}


def api(method, path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    h = dict(HDR)
    if body is not None:
        h["Content-Type"] = "application/json"
    req = urllib.request.Request("https://api.render.com" + path, method=method, headers=h, data=data)
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            raw = r.read()
            return r.status, (json.loads(raw) if raw else {})
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "ignore")[:400]
    except Exception as e:  # noqa: BLE001
        return 0, f"{type(e).__name__}: {e}"


def main():
    st, owners = api("GET", "/v1/owners?limit=20")
    if st != 200:
        print("❌ مفتاح غير صالح:", str(owners)[:200]); return 1
    owner_id = None
    for o in owners if isinstance(owners, list) else owners.get("owners", []):
        ow = o.get("owner", o)
        if ow.get("type") == "user" or not owner_id:
            owner_id = ow.get("id")
            print("✅ الحساب:", ow.get("name", ow.get("email", "")), "| ownerId:", owner_id)
    if not owner_id:
        print("❌ لم أجد مالك الحساب."); return 1

    bot_token = ""
    envp = ROOT / ".env"
    if envp.exists():
        for ln in envp.read_text(encoding="utf-8-sig", errors="ignore").splitlines():
            if ln.strip().startswith("BOT_TOKEN="):
                bot_token = ln.split("=", 1)[1].strip()
    if not bot_token:
        print("⚠️ لا يوجد BOT_TOKEN في .env — اضبطه من لوحة Render بعد الإنشاء.")
        return 1

    body = {
        "type": "web_service",
        "name": NAME,
        "ownerId": owner_id,
        "repo": REPO,
        "branch": "main",
        "autoDeploy": "yes",
        "serviceDetails": {
            "env": "docker",
            "plan": "free",
            "region": "frankfurt",
            "healthCheckPath": "/",
            "envVars": [
                {"key": "BOT_TOKEN", "value": bot_token},
                {"key": "PORT", "value": "8080"},
                {"key": "OWNER_IDS", "value": "1232067711"},
                {"key": "TIMEZONE", "value": "Africa/Cairo"},
            ],
        },
    }
    st, res = api("POST", "/v1/services", body)
    if st not in (200, 201):
        print("❌ فشل الإنشاء:", st, str(res)[:300]); return 1
    svc = res.get("service", res)
    print("✅ أُنشئت الخدمة:", svc.get("name"), "| id:", svc.get("id"))
    print("⏳ بانتظار النشر… (تابع من لوحة Render)")
    url = (svc.get("serviceDetails") or {}).get("url") or f"https://{NAME}.onrender.com"
    for i in range(30):
        time.sleep(20)
        st2, deps = api("GET", f"/v1/services/{svc.get('id')}/deploys?limit=1")
        if st2 == 200 and deps:
            d = (deps[0] or {}).get("deploy", {})
            print(f"  [{i}] deploy status: {d.get('status')}")
            if d.get("status") == "live":
                print("🚀 LIVE:", url); return 0
            if d.get("status") in ("build_failed", "update_failed", "canceled", "pre_deploy_failed"):
                print("❌ فشل النشر:", d.get("status")); return 1
    print("ℹ️ لم يكتمل بعد — راجع اللوحة:", url)
    return 0


if __name__ == "__main__":
    sys.exit(main())
