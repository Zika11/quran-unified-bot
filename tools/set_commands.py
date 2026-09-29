# -*- coding: utf-8 -*-
"""عملية حيّة على البوت: ضبط قائمة الأوامر في تليجرام (setMyCommands) + التحقق منها (getMyCommands).
يكتب tools/telegram_commands.json ويطبع ملخصًا. لا يطبع أي قيم سرية."""
import json
import sys
from datetime import datetime
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from app.config import settings  # noqa: E402

COMMANDS = [
    ("start", "بدء البوت والقائمة الرئيسية"),
    ("commands", "قائمة كل الأوامر"),
    ("surah", "نص سورة + استماع (مثال: 18)"),
    ("ayah", "آية: نص + صوت + تفسير (مثال: 2:255)"),
    ("tafsir", "التفسير الميسر (مثال: 2:255)"),
    ("search", "بحث في القرآن (مثال: رحمة)"),
    ("random", "آية عشوائية"),
    ("play", "تلاوة سورة (مثال: 36)"),
    ("reciters", "اختيار القارئ"),
    ("radios", "الإذاعات المباشرة"),
    ("prayer", "مواقيت الصلاة"),
    ("city", "ضبط المدينة (مثال: Alexandria)"),
    ("adhkar", "الأذكار والأدعية"),
    ("duas", "الأدعية المأثورة"),
    ("sajda", "مواضع سجود التلاوة"),
    ("hadith", "حديث اليوم / تحقّق من حديث"),
    ("hifz", "خطة الحفظ والحالة"),
    ("hz", "تسجيل حفظ آية (مثال: 112:1)"),
    ("tasmia", "تسميع آية (مثال: 112:2)"),
    ("khatma", "الختمة الجماعية"),
    ("khnew", "إنشاء ختمة جديدة"),
    ("khjoin", "الانضمام لختمة"),
    ("khprogress", "تقدّم الختمة"),
    ("khdone", "إنهاء جزئي"),
    ("khmy", "ختماتي"),
    ("quiz", "مسابقات (تجويد/متشابهات/سيرة)"),
    ("mood", "آيات حسب حالتك"),
    ("repeat", "تكرار آية للتدبر"),
    ("zakat", "حاسبة الزكاة"),
    ("shuyukh", "فهرس الشيوخ"),
    ("now", "الإذاعة الحالية"),
    ("next", "الإذاعة التالية"),
    ("video", "فيديو الآية (مثال: 112:1)"),
    ("settings", "الإعدادات"),
    ("health", "حالة الخدمات"),
    ("daily", "بثّ آية اليوم للقناة"),
    ("linkchannel", "ربط القناة"),
    ("unlinkchannel", "إلغاء ربط القناة"),
    ("stats", "إحصاءات (للمالك)"),
    ("help", "المساعدة"),
]
API = "https://api.telegram.org/bot{token}/{method}"


def call(method, **params):
    r = requests.post(API.format(token=settings.BOT_TOKEN, method=method),
                      json=params, timeout=20).json()
    return r


def main():
    if not settings.BOT_TOKEN:
        print("لا يوجد توكن"); return 1
    payload = [{"command": c, "description": d} for c, d in COMMANDS]
    res = call("setMyCommands", commands=payload)
    ok_set = bool(res.get("ok"))
    print("operation=setMyCommands", "ok" if ok_set else "FAILED",
          res.get("description", ""), f"({len(payload)} أمر)")
    chk = call("getMyCommands")
    got = (chk.get("result") or []) if chk.get("ok") else []
    print("check=getMyCommands", "ok" if chk.get("ok") else "FAILED", f"→ {len(got)} أمر مُثبَت")
    names = [c["command"] for c in got]
    print("commands:", ", ".join(names))
    (ROOT / "tools").mkdir(exist_ok=True)
    (ROOT / "tools" / "telegram_commands.json").write_text(json.dumps({
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "set_ok": ok_set, "verified_count": len(got), "commands": got,
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0 if (ok_set and len(got) == len(payload)) else 1


if __name__ == "__main__":
    sys.exit(main())
