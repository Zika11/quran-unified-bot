# -*- coding: utf-8 -*-
"""العبادة: المواقيت، الأذكار، الأدعية، الحديث، مواضع السجود."""
from telegram import Update, InlineKeyboardButton
from telegram.ext import CommandHandler, CallbackQueryHandler, ContextTypes

from .. import keyboards as KB
from .. import services as S
from ..util import trace, esc

PRAYER_AR = {
    "Fajr": "الفجر", "Sunrise": "الشروق", "Dhuhr": "الظهر", "Asr": "العصر",
    "Sunset": "الغروب", "Maghrib": "المغرب", "Isha": "العشاء", "Imsak": "الإمساك",
    "Midnight": "منتصف الليل", "Firstthird": "الثلث الأول", "Lastthird": "الثلث الأخير",
}


@trace("prayer")
async def cmd_prayer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = context.application.bot_data["db"]
    u = db.user(update.effective_user.id)
    city = " ".join(context.args).strip() or u["city"]
    p = S.prayer_times(city, u["country"])
    t = p["timings"]
    order = ["Fajr", "Sunrise", "Dhuhr", "Asr", "Maghrib", "Isha"]
    lines = [f"🕌 <b>مواقيت الصلاة — {esc(city)}</b>", f"📅 {esc(p['date'])}", ""]
    for k in order:
        if k in t:
            lines.append(f"• {PRAYER_AR.get(k, k)}: <b>{esc(t[k])}</b>")
    await update.message.reply_text("\n".join(lines), parse_mode="HTML", reply_markup=KB.ikb([KB.back_row("menu:worship")]))


@trace("city")
async def cmd_city(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = context.application.bot_data["db"]
    uid = update.effective_user.id
    if not context.args:
        context.user_data["await"] = "city"
        await update.message.reply_text("🏙️ اكتب اسم المدينة (مثال: Alexandria أو القاهرة).")
        return
    db.set_user(uid, city=" ".join(context.args)[:40])
    u = db.user(uid)
    await update.message.reply_text(f"✅ تم ضبط المدينة: {esc(u['city'])}", parse_mode="HTML")


@trace("adhkar")
async def cmd_adhkar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📿 <b>الأذكار والأدعية</b>", reply_markup=KB.adhkar_menu(), parse_mode="HTML")


def _render_adhkar(items, title):
    out = [f"📿 <b>{title}</b>\n"]
    for i, a in enumerate(items, 1):
        out.append(f"{i}. {a.get('text','')}\n   🔁 {a.get('count',1)} مرة" +
                   (f" — {a['note']}" if a.get("note") else ""))
    return esc("\n\n".join(out))[:3900]


@trace("adhkar_cb")
async def on_adhkar_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    d = q.data
    await q.answer()
    if d == "adh:morning":
        await q.edit_message_text(_render_adhkar(S.adhkar("morning"), "أذكار الصباح"),
                                  parse_mode="HTML", reply_markup=KB.ikb([KB.back_row("menu:worship")]))
    elif d == "adh:evening":
        await q.edit_message_text(_render_adhkar(S.adhkar("evening"), "أذكار المساء"),
                                  parse_mode="HTML", reply_markup=KB.ikb([KB.back_row("menu:worship")]))
    elif d == "adh:duas":
        txt = "\n\n".join(f"🤲 <b>{esc(x['title'])}</b>\n{esc(x['text'])}" for x in S.duas())
        await q.edit_message_text(f"🤲 <b>أدعية مأثورة</b>\n\n{esc(txt)[:3600]}",
                                  parse_mode="HTML", reply_markup=KB.ikb([KB.back_row("menu:worship")]))
    elif d == "adh:sajda":
        from ..content.islamic_data import SAJDA_VERSES
        body = "\n".join(f"• {esc(v)}" for v in SAJDA_VERSES)
        await q.edit_message_text(f"🕌 <b>مواضع سجود التلاوة</b> ({len(SAJDA_VERSES)})\n\n{body}",
                                  parse_mode="HTML", reply_markup=KB.ikb([KB.back_row("menu:worship")]))


@trace("duas")
async def cmd_duas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txt = "\n\n".join(f"🤲 <b>{esc(x['title'])}</b>\n{esc(x['text'])}" for x in S.duas())
    await update.message.reply_text(f"🤲 <b>أدعية مأثورة</b>\n\n{esc(txt)[:3600]}", parse_mode="HTML")


@trace("sajda")
async def cmd_sajda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from ..content.islamic_data import SAJDA_VERSES
    body = "\n".join(f"• {esc(v)}" for v in SAJDA_VERSES)
    await update.message.reply_text(f"🕌 <b>مواضع سجود التلاوة</b> ({len(SAJDA_VERSES)})\n\n{body}", parse_mode="HTML")


@trace("hadith")
async def cmd_hadith(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args:
        await _verify_hadith(update.message, context, " ".join(context.args))
        return
    h = S.daily_hadith()
    if not h:
        await update.message.reply_text("⚠️ لا يوجد محتوى أحاديث محلي.")
        return
    await update.message.reply_text(
        f"📜 <b>حديث اليوم</b>\n\n{esc(h['text'])}\n\n📖 {esc(h.get('source',''))} · {esc(h.get('grade',''))}",
        parse_mode="HTML", reply_markup=KB.hadith_menu())


async def _verify_hadith(message, context, text):
    res = S.dorar_search(text)
    import re
    clean = re.sub("<[^>]+>", "", res or "")[:3500]
    await message.reply_text(f"🔍 <b>التحقق من الحديث (الدرر السنية)</b>\n\n{esc(clean) or 'لا نتائج.'}",
                             parse_mode="HTML")


@trace("hadith_cb")
async def on_hadith_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    if q.data == "hd:today":
        h = S.daily_hadith()
        await q.edit_message_text(
            f"📜 <b>حديث اليوم</b>\n\n{esc(h['text'])}\n\n📖 {esc(h.get('source',''))} · {esc(h.get('grade',''))}",
            parse_mode="HTML", reply_markup=KB.ikb([KB.back_row("menu:hadith")]))
    elif q.data == "hd:ask":
        context.user_data["await"] = "hadith"
        await q.edit_message_text("🔍 اكتب نص الحديث للتحقق منه:", reply_markup=KB.ikb([KB.back_row("menu:hadith")]))


def register(app):
    app.add_handler(CommandHandler(["prayer", "salat"], cmd_prayer))
    app.add_handler(CommandHandler(["city"], cmd_city))
    app.add_handler(CommandHandler(["adhkar"], cmd_adhkar))
    app.add_handler(CommandHandler(["duas", "dua"], cmd_duas))
    app.add_handler(CommandHandler(["sajda"], cmd_sajda))
    app.add_handler(CommandHandler(["hadith", "hadeeth"], cmd_hadith))
    app.add_handler(CallbackQueryHandler(on_adhkar_cb, pattern=r"^adh:"))
    app.add_handler(CallbackQueryHandler(on_hadith_cb, pattern=r"^hd:"))
