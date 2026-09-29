# -*- coding: utf-8 -*-
"""فحص e2e سحابي: يرسل أوامر من حساب المستخدم إلى @iQuranOfficial_Bot وينتظر الردود.
يثبت أن النسخة المستضافة (Railway) هي التي ترد. الاستخدام:
    python tools/tg_cloud_check.py [أوامر...]   (افتراضي: /start /health)
"""
import asyncio
import json
import os
import sys

from telethon import TelegramClient

BASE = r"C:\Users\af191\OneDrive\Desktop\points_bot"
BOT = "iQuranOfficial_Bot"


async def wait_reply(client, bot, sent, timeout=30):
    deadline = asyncio.get_event_loop().time() + timeout
    while asyncio.get_event_loop().time() < deadline:
        msgs = await client.get_messages(bot, limit=4)
        for m in msgs:
            if (not m.out) and getattr(m, "id", 0) > sent.id:
                return m
        await asyncio.sleep(2)
    return None


async def main():
    cfg = json.load(open(os.path.join(BASE, "config.json"), encoding="utf-8"))
    client = TelegramClient(os.path.join(BASE, "my_account"), cfg["api_id"], cfg["api_hash"],
                            connection_retries=3, timeout=20)
    await client.connect()
    if not await client.is_user_authorized():
        print("NOT_AUTHORIZED")
        return
    bot = await client.get_entity(BOT)
    cmds = sys.argv[1:] or ["/start", "/health"]
    ok = 0
    for c in cmds:
        sent = await client.send_message(bot, c)
        print(f">>> sent {c}")
        m = await wait_reply(client, bot, sent)
        if m:
            txt = (m.text or "").replace("\n", " | ")[:230]
            print(f"<<< reply: {txt}")
            ok += 1
        else:
            print("<<< NO REPLY within 30s")
    print(f"RESULT {ok}/{len(cmds)} replied")
    await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
