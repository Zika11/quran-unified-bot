# -*- coding: utf-8 -*-
"""يجرّب الاتصال بجلسة Telethon موجودة (قراءة فقط: get_me). يطبع قيمًا مُخفّاة فقط."""
import asyncio
import json
import os
import sys

from telethon import TelegramClient


def load_cfg(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


async def probe(name, session_path, api_id, api_hash, proxy=None):
    print(f"--- {name} (proxy={proxy}) ---")
    client = TelegramClient(session_path, api_id, api_hash, proxy=proxy,
                            connection_retries=2, timeout=15, request_retries=2)
    try:
        await asyncio.wait_for(client.connect(), timeout=30)
        ok = await client.is_user_authorized()
        me = await client.get_me() if ok else None
        if me:
            ident = getattr(me, "id", None)
            uname = getattr(me, "username", None)
            print(f"    connected={client.is_connected()} authorized={ok} id={ident} username=@{uname}")
        else:
            print(f"    connected={client.is_connected()} authorized={ok}")
        return ok
    except Exception as e:  # noqa: BLE001
        print(f"    FAILED: {type(e).__name__}: {str(e)[:140]}")
        return False
    finally:
        try:
            await client.disconnect()
        except Exception:  # noqa: BLE001
            pass


async def main():
    base = r"C:\Users\af191\OneDrive\Desktop\points_bot"
    cfg = load_cfg(os.path.join(base, "config.json"))
    api_id, api_hash = cfg["api_id"], cfg["api_hash"]
    sess = os.path.join(base, "my_account")
    ok_direct = await probe("points_bot/my_account DIRECT", sess, api_id, api_hash)
    if not ok_direct:
        ok_proxy = await probe("points_bot/my_account SOCKS5", sess, api_id, api_hash,
                               proxy=("socks5", "77.239.106.24", 1080))
        print("proxy_ok=", ok_proxy)
    print("RESULT direct_ok=", ok_direct)


if __name__ == "__main__":
    asyncio.run(main())
