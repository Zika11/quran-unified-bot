# -*- coding: utf-8 -*-
"""نشر بوت القرآن الموحّد على Hugging Face Spaces (Docker, مجاني بلا بطاقة).

الاستخدام:
    python deploy/hf_deploy.py <HF_TOKEN> [spacename]

ما يفعله:
 1) يتحقق من التوكن (whoami).
 2) ينشئ Space من نوع docker.
 3) يرفع ملفات المشروع (app/ deploy/ Dockerfile requirements.txt) + README بترويسة HF.
 4) يضبط السر BOT_TOKEN من .env المحلي.
 5) يضبط KEEPALIVE_URL (للنبض الذاتي ومنع الخمول).
لا يطبع أي قيمة سرية.
"""
import io
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = Path(__file__).resolve().parent.parent
HF = "https://huggingface.co"
SPACE = sys.argv[2] if len(sys.argv) > 2 else "quran-unified-bot"
_tok_file = ROOT.parent.parent / ".openclaw" / "tmp" / "hf_token.txt"
TOKEN = (sys.argv[1] if len(sys.argv) > 1 else os.environ.get("HF_TOKEN") or (
    _tok_file.read_text(encoding="utf-8").strip() if _tok_file.exists() else "")).strip()

if not TOKEN:
    print("⛔ مطلوب توكن HuggingFace: python deploy/hf_deploy.py hf_xxx")
    sys.exit(2)

HDR = {"Authorization": "Bearer " + TOKEN, "User-Agent": "autoclaw-deploy"}

SPACE_README = """---
title: Quran Unified Bot
emoji: 🕌
colorFrom: green
colorTo: blue
sdk: docker
app_port: 8080
pinned: false
---

# Quran Unified Bot (deploy)
بوت القرآن الموحّد — تشغيل مستمر على Hugging Face Spaces (Docker).
الأسرار: BOT_TOKEN (Settings → Variables and secrets).
"""

UPLOADS = [
    ("README.md", SPACE_README, None),
    ("Dockerfile", None, ROOT / "Dockerfile"),
    ("requirements.txt", None, ROOT / "requirements.txt"),
    (".dockerignore", None, ROOT / ".dockerignore"),
]
TREE_DIRS = ["app", "deploy"]


def api(method, url, body=None, raw=False):
    data = json.dumps(body).encode() if body is not None else None
    h = dict(HDR)
    if body is not None:
        h["Content-Type"] = "application/json"
    req = urllib.request.Request(url, method=method, headers=h, data=data)
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            b = r.read()
            if raw:
                return r.status, b.decode("utf-8", "ignore")
            return r.status, (json.loads(b) if b else {})
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "ignore")[:400]
    except Exception as e:  # noqa: BLE001
        return 0, f"{type(e).__name__}: {e}"


def upload(user, space, relpath, content: bytes):
    url = f"{HF}/api/spaces/{user}/{space}/upload/{relpath}"
    req = urllib.request.Request(url, method="POST",
                                 headers={**HDR, "Content-Type": "application/octet-stream"},
                                 data=content)
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            return r.status
    except urllib.error.HTTPError as e:
        return e.code
    except Exception:  # noqa: BLE001
        return 0


def main():
    st, who = api("GET", HF + "/api/whoami-v2")
    if st != 200:
        print("❌ توكن HF غير صالح:", str(who)[:200]); return 1
    user = who.get("name")
    print("✅ HF user:", user)

    st, sp = api("POST", HF + "/api/repos/create",
                 {"type": "space", "name": SPACE, "private": False, "sdk": "docker"})
    print("create space ->", st, "" if st in (200, 201, 409) else str(sp)[:200])

    files = []
    for name, inline, path in UPLOADS:
        files.append((name, inline.encode("utf-8") if inline else path.read_bytes()))
    for d in TREE_DIRS:
        for p in sorted((ROOT / d).rglob("*")):
            if p.is_file() and "__pycache__" not in p.parts:
                files.append((str(p.relative_to(ROOT)).replace("\\", "/"), p.read_bytes()))
    ok = 0
    for name, data in files:
        code = upload(user, SPACE, name, data)
        ok += 1 if code in (200, 201) else 0
        print(f"  upload {name} -> {code}")
    print(f"uploaded {ok}/{len(files)}")

    bot_token = ""
    envp = ROOT / ".env"
    if envp.exists():
        for ln in envp.read_text(encoding="utf-8-sig", errors="ignore").splitlines():
            if ln.strip().startswith("BOT_TOKEN="):
                bot_token = ln.split("=", 1)[1].strip()
    if bot_token:
        st, _ = api("POST", f"{HF}/api/spaces/{user}/{SPACE}/secrets", {"key": "BOT_TOKEN", "value": bot_token})
        print("secret BOT_TOKEN ->", st)
        st, _ = api("POST", f"{HF}/api/spaces/{user}/{SPACE}/variables",
                    {"key": "KEEPALIVE_URL", "value": f"https://{user}-{SPACE}.hf.space"})
        print("variable KEEPALIVE_URL ->", st)
    else:
        print("⚠️ لم أجد BOT_TOKEN في .env — اضبطه يدويًا من إعدادات الـSpace.")

    print(f"\n🌐 Space: {HF}/spaces/{user}/{SPACE}")
    print(f"▶️  يعمل على: https://{user}-{SPACE}.hf.space")
    return 0


if __name__ == "__main__":
    sys.exit(main())
