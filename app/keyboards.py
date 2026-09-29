# -*- coding: utf-8 -*-
"""لوحات الأزرار (Inline Keyboards)."""
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from .config import RECITERS
from .util import chunk_list


def ikb(rows):
    return InlineKeyboardMarkup(rows)


def back_row(target="menu:main"):
    return [InlineKeyboardButton("◀️ رجوع للقائمة", callback_data=target)]


def main_menu():
    return ikb([
        [InlineKeyboardButton("📖 القرآن الكريم", callback_data="menu:quran"),
         InlineKeyboardButton("🎧 التلاوات والإذاعات", callback_data="menu:audio")],
        [InlineKeyboardButton("🕌 المواقيت والأذكار", callback_data="menu:worship"),
         InlineKeyboardButton("📚 الحديث والدعاء", callback_data="menu:hadith")],
        [InlineKeyboardButton("🧠 الحفظ والتسميع", callback_data="menu:hifz"),
         InlineKeyboardButton("🤝 الختمة الجماعية", callback_data="menu:khatma")],
        [InlineKeyboardButton("🎬 مولّد فيديو الآية", callback_data="menu:video"),
         InlineKeyboardButton("❓ مسابقات", callback_data="menu:quiz")],
        [InlineKeyboardButton("⚙️ الإعدادات", callback_data="menu:settings"),
         InlineKeyboardButton("ℹ️ عن البوت", callback_data="menu:about")],
    ])


def quran_actions(s, a):
    return ikb([
        [InlineKeyboardButton("🔊 استمع للآية", callback_data=f"a:play:{s}:{a}"),
         InlineKeyboardButton("📚 التفسير الميسر", callback_data=f"a:tafsir:{s}:{a}")],
        [InlineKeyboardButton("👥 قارن القرّاء", callback_data=f"a:reciters:{s}:{a}"),
         InlineKeyboardButton("🎬 فيديو الآية", callback_data=f"a:video:{s}:{a}")],
        back_row("menu:quran"),
    ])


def surahs_page(page, per_page=24, prefix="q:open:"):
    from .content.islamic_data import SURAH_NAMES
    total = 114
    pages = (total + per_page - 1) // per_page
    page = max(1, min(page, pages))
    start = (page - 1) * per_page
    rows = []
    for grp in range(0, per_page, 3):
        row = []
        for i in range(grp, grp + 3):
            n = start + i + 1
            if n > total:
                break
            row.append(InlineKeyboardButton(f"{n}. {SURAH_NAMES[n-1]}", callback_data=f"{prefix}{n}"))
        if row:
            rows.append(row)
    nav = []
    if page > 1:
        nav.append(InlineKeyboardButton("▶️ السابق", callback_data=f"q:list:{page-1}"))
    nav.append(InlineKeyboardButton(f"({page}/{pages})", callback_data="noop"))
    if page < pages:
        nav.append(InlineKeyboardButton("التالي ◀️", callback_data=f"q:list:{page+1}"))
    rows.append(nav)
    rows.append(back_row("menu:quran"))
    return ikb(rows)


def reciter_menu(prefix="rc:set:"):
    rows = []
    for key, (name, _) in RECITERS.items():
        rows.append([InlineKeyboardButton(name, callback_data=f"{prefix}{key}")])
    rows.append(back_row("menu:settings"))
    return ikb(rows)


def radios_page(radios, page, per_page=8):
    items, page, total = _paginate(radios, page, per_page)
    rows = []
    for r in items:
        rows.append([InlineKeyboardButton(r.get("name", "إذاعة"), callback_data=f"rd:open:{r['id']}")])
    nav = []
    if page > 1:
        nav.append(InlineKeyboardButton("▶️", callback_data=f"rd:list:{page-1}"))
    nav.append(InlineKeyboardButton(f"({page}/{total})", callback_data="noop"))
    if page < total:
        nav.append(InlineKeyboardButton("◀️", callback_data=f"rd:list:{page+1}"))
    rows.append(nav)
    rows.append(back_row("menu:audio"))
    return ikb(rows)


def adhkar_menu():
    return ikb([
        [InlineKeyboardButton("🌄 أذكار الصباح", callback_data="adh:morning"),
         InlineKeyboardButton("🌙 أذكار المساء", callback_data="adh:evening")],
        [InlineKeyboardButton("💤 أذكار النوم", callback_data="adh:sleep"),
         InlineKeyboardButton("🤲 الأدعية المأثورة", callback_data="adh:duas")],
        [InlineKeyboardButton("🕌 مواضع السجود", callback_data="adh:sajda")],
        back_row(),
    ])


def hadith_menu():
    return ikb([
        [InlineKeyboardButton("📜 حديث اليوم", callback_data="hd:today"),
         InlineKeyboardButton("🔍 تحقّق من حديث", callback_data="hd:ask")],
        back_row(),
    ])


def hifz_menu():
    return ikb([
        [InlineKeyboardButton("📋 خطة الحفظ", callback_data="hz:plan"),
         InlineKeyboardButton("📊 حالتي", callback_data="hz:status")],
        [InlineKeyboardButton("🔥 تسميع آية", callback_data="hz:ask_tasmia")],
        back_row(),
    ])


def khatma_menu():
    return ikb([
        [InlineKeyboardButton("➕ ختمة جديدة", callback_data="kh:new"),
         InlineKeyboardButton("🙋 انضمّ للختمة", callback_data="kh:join")],
        [InlineKeyboardButton("📈 تقدّم الختمة", callback_data="kh:progress"),
         InlineKeyboardButton("✅ أنهيت جزئي", callback_data="kh:done")],
        [InlineKeyboardButton("📚 ختماتي", callback_data="kh:mine")],
        back_row(),
    ])


def quiz_menu():
    return ikb([
        [InlineKeyboardButton("📗 تجويد", callback_data="qz:start:تجويد"),
         InlineKeyboardButton("🃏 متشابهات", callback_data="qz:start:متشابهات")],
        [InlineKeyboardButton("🏛️ سيرة", callback_data="qz:start:سيرة"),
         InlineKeyboardButton("📊 نتائجي", callback_data="qz:score")],
        back_row(),
    ])


def settings_menu(reciter_key, city):
    return ikb([
        [InlineKeyboardButton(f"🎙️ القارئ: {RECITERS.get(reciter_key, ('-',''))[0]}", callback_data="set:reciter")],
        [InlineKeyboardButton(f"🏙️ المدينة: {city}", callback_data="set:city")],
        [InlineKeyboardButton("🔔 تفعيل/تعطيل آية اليوم", callback_data="set:toggle_ayah")],
        [InlineKeyboardButton("🕌 تفعيل/تعطيل تنبيه الصلاة", callback_data="set:toggle_prayer")],
        back_row(),
    ])


def about_menu():
    return ikb([
        [InlineKeyboardButton("📋 قائمة الأوامر", callback_data="menu:commands"),
         InlineKeyboardButton("🩺 حالة الخدمات", callback_data="menu:health")],
        back_row(),
    ])


def _paginate(items, page, per_page):
    total = max(1, (len(items) + per_page - 1) // per_page)
    page = max(1, min(page, total))
    start = (page - 1) * per_page
    return items[start:start + per_page], page, total
