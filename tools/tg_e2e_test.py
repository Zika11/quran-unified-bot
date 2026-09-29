# -*- coding: utf-8 -*-
"""اختبار شامل حقيقي: يسجّل بحساب مستخدم (Telethon) ويرسل كل أوامر البوت إلى @iQuranOfficial_Bot
ويلتقط الردود ويكتشف الأخطاء. المخرجات: tools/e2e_report.json + docs/E2E_TEST_REPORT.md
"""
import asyncio
import json
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path

from telethon import TelegramClient

ROOT = Path(__file__).resolve().parent.parent
BOT_USERNAME = "iQuranOfficial_Bot"
SESSION_DIR = r"C:\Users\af191\OneDrive\Desktop\points_bot"

CASES = [
    ("/start", 40), ("/commands", 30), ("/surah 112", 40), ("/ayah 2:255", 40),
    ("/tafsir 2:255", 40), ("/search صبر", 45), ("/random", 40), ("/play 112", 60),
    ("/reciters", 30), ("/radios", 45), ("/prayer", 40), ("/city Alexandria", 30),
    ("/adhkar", 30), ("/duas", 35), ("/sajda", 30), ("/hadith", 35),
    ("/hifz", 30), ("/hz 112:1", 30), ("/tasmia 112:2", 35), ("/khatma", 30),
    ("/quiz", 30), ("/video 112:1", 120), ("/settings", 30), ("/health", 60),
    ("/stats", 30), ("نور", 45), ("/ayah abc", 30),
    ("/settings", 30), ("/health", 60), ("/khnew", 30), ("/khjoin", 30),
    ("/khprogress", 30), ("/khdone", 30), ("/khmy", 30),
    ("/mood", 30), ("/repeat 112:1", 30), ("/zakat", 30), ("/shuyukh", 40),
    ("/now", 30), ("/next", 40), ("/daily", 30), ("/linkchannel", 30), ("/unlinkchannel", 30),
]

ERROR_MARKERS = ("حدث خطأ غير متوقع", "تعذّر الاتصال بالخدمة", "Traceback",
                 "AttributeError", "TypeError", "KeyError", "ValueError: ")


def load_cfg():
    with open(os.path.join(SESSION_DIR, "config.json"), encoding="utf-8") as f:
        return json.load(f)


def kind_of(msg):
    if msg.photo:
        return "photo"
    if msg.video:
        return "video"
    if msg.audio or msg.voice or msg.document:
        return "audio/file"
    if msg.text:
        return "text"
    return "other"


async def wait_replies(client, entity, after_id, quiet=2.0, timeout=30.0):
    t0 = time.time()
    got = []
    seen = set()
    maxid = after_id or 0
    last_new = t0
    while time.time() - t0 < timeout:
        msgs = await client.get_messages(entity, limit=10)
        new = [m for m in msgs if m.id > maxid and not m.out]
        if new:
            new.sort(key=lambda m: m.id)
            for m in new:
                if m.id not in seen:
                    seen.add(m.id)
                    got.append(m)
            maxid = max(maxid, new[-1].id)
            last_new = time.time()
        if got and (time.time() - last_new) > quiet:
            break
        await asyncio.sleep(0.6)
    return got


async def main():
    cfg = load_cfg()
    client = TelegramClient(os.path.join(SESSION_DIR, "my_account"), cfg["api_id"], cfg["api_hash"],
                            connection_retries=3, timeout=20, request_retries=3)
    await client.connect()
    me = await client.get_me()
    print(f"تسجيل الدخول: @{me.username} (id={me.id})")
    bot = await client.get_entity("@" + BOT_USERNAME)
    results = []
    for cmd, timeout in CASES:
        before = await client.get_messages(bot, limit=1)
        after_id = before[0].id if before else 0
        t0 = time.time()
        sent_ok = True
        send_err = None
        try:
            await client.send_message(bot, cmd)
        except Exception as e:  # noqa: BLE001
            sent_ok = False
            send_err = f"{type(e).__name__}: {e}"
        replies = await wait_replies(client, bot, after_id, timeout=timeout)
        elapsed = round(time.time() - t0, 1)
        texts = []
        for m in replies:
            texts.append({"kind": kind_of(m), "text": (m.text or "")[:500], "id": m.id})
        blob = " ".join(t["text"] for t in texts)
        errs = [mk for mk in ERROR_MARKERS if mk in blob]
        if not sent_ok:
            errs.append("SEND_FAILED")
        if not replies:
            errs.append("NO_REPLY")
        results.append({"command": cmd, "sent": sent_ok, "send_error": send_err,
                        "elapsed_s": elapsed, "replies": texts, "errors": errs})
        flag = "❌" if errs else "✅"
        print(f"{flag} {cmd:16} replies={len(texts)} in {elapsed}s " + (f"errors={errs}" if errs else ""))
        await asyncio.sleep(0.6)

    # اختبار زر Inline على ردّ /start
    button_test = {"ok": None, "note": ""}
    try:
        await client.send_message(bot, "/start")
        msgs = await wait_replies(client, bot, 0, timeout=25)
        target = [m for m in msgs if getattr(m, "reply_markup", None)]
        if target:
            msg = target[-1]
            await msg.click(0, 0)
            await asyncio.sleep(3)
            after = await client.get_messages(bot, limit=3)
            last = after[0] if after else None
            button_test = {"ok": bool(last and (last.text or "")) ,
                           "note": ("تم الضغط على زر؛ آخر نص: " + (last.text or "")[:120]) if last else "لا ردّ"}
        else:
            button_test = {"ok": False, "note": "لا يوجد ردّ بأزرار"}
    except Exception as e:  # noqa: BLE001
        button_test = {"ok": False, "note": f"{type(e).__name__}: {str(e)[:120]}"}
    print(("✅" if button_test["ok"] else "❌"), "زر Inline —", button_test["note"])

    await client.disconnect()
    total = len(results)
    bad = [r for r in results if r["errors"]]
    report = {"generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
              "bot": BOT_USERNAME, "tester_account": f"@{me.username}", "total": total,
              "failures": len(bad), "results": results, "button_test": button_test}
    (ROOT / "tools").mkdir(exist_ok=True)
    (ROOT / "tools" / "e2e_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n=== الإجمالي: {total - len(bad)}/{total} ناجح · فشل {len(bad)} ===")
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
