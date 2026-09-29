# -*- coding: utf-8 -*-
"""ميزات أُعيد دمجها من البوتات الأصلية: آيات حسب الحالة، تكرار الآية، حاسبة الزكاة،
أذكار النوم، فهرس الشيوخ، الإذاعة (الآن/التالي)، وربط القناة."""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackQueryHandler, ContextTypes

from .. import keyboards as KB
from .. import services as S
from ..util import trace, esc, reply_audio_safe

PER_PAGE = 8


def _ikb(rows):
    return InlineKeyboardMarkup(rows)


def _back(target="menu:main"):
    return [InlineKeyboardButton("◀️ رجوع", callback_data=target)]


# ============================================================ آيات حسب الحالة
@trace("mood")
async def cmd_mood(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rows = [[InlineKeyboardButton(m, callback_data=f"mood:{m}")] for m in S.MOODS]
    rows.append(_back())
    await update.message.reply_text("🌟 <b>آيات حسب حالك</b>\nاختر حالتك:", parse_mode="HTML", reply_markup=_ikb(rows))


@trace("mood_cb")
async def on_mood_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    mood = q.data.split(":", 1)[1]
    hits = S.mood_ayahs(mood, 3)
    if not hits:
        await q.edit_message_text("⚠️ لا توجد نتائج لهذه الحالة حاليًا.", reply_markup=_ikb([_back()]))
        return
    parts = [f"🌟 <b>{esc(mood)}</b>\n"]
    for h in hits:
        parts.append(f"<b>{esc(h['surah_name'])} ({esc(h['ref'])})</b>\n{esc(h['text'][:280])}\n")
    await q.edit_message_text("\n".join(parts)[:3800], parse_mode="HTML", reply_markup=_ikb([_back()]))


# ============================================================ تكرار الآية للتدبر
def _repeat_kb(s=None, a=None):
    if s is None:
        return _ikb([_back("menu:quran")])
    rows = [[InlineKeyboardButton(f"🔁 ×{n}", callback_data=f"rep:go:{s}:{a}:{n}")] for n in (3, 5, 10)]
    rows.append(_back("menu:quran"))
    return _ikb(rows)


@trace("repeat")
async def cmd_repeat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args:
        ref = S.normalize_ref(" ".join(context.args))
    else:
        v = S.random_ayah()
        ref = v["ref"]
    v = S.get_ayah(ref)
    s, a = int(v["surah"]), int(v["ayah"])
    await update.message.reply_text(
        f"🔁 <b>تكرار الآية للتدبر — {esc(S.surah_name(s))} ({s}:{a})</b>\n\n{esc(v['text'])}\n\n"
        f"اختر عدد المرات (تُرسل التلاوة مع وقفة للتأمل):",
        parse_mode="HTML", reply_markup=_repeat_kb(s, a))


@trace("repeat_cb")
async def on_repeat_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    db = context.application.bot_data["db"]
    reciter = db.user(q.from_user.id)["reciter"]
    if q.data == "rep:ask":
        await q.answer()
        v = S.random_ayah()
        ref = v["ref"]
        v2 = S.get_ayah(ref)
        s, a = int(v2["surah"]), int(v2["ayah"])
        await q.edit_message_text(
            f"🔁 <b>تكرار الآية للتدبر — {esc(S.surah_name(s))} ({s}:{a})</b>\n\n{esc(v2['text'])}\n\nاختر عدد المرات:",
            parse_mode="HTML", reply_markup=_repeat_kb(s, a))
        return
    _, _, s, a, n = q.data.split(":")
    await q.answer(f"سيتم التكرار ×{n}")
    url = S.ayah_audio_url(int(s), int(a), reciter)
    for i in range(int(n)):
        await q.message.reply_audio(url, caption=f"🔁 {i+1}/{n} — {S.surah_name(int(s))} آية {a}")


# ============================================================ حاسبة الزكاة
@trace("zakat")
async def cmd_zakat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["await"] = "zakat"
    await update.message.reply_text(
        "💰 <b>حاسبة الزكاة</b>\n\nاكتب مجموع أموالك (نقد + ذهب + فضة + عروض تجارية) بالجنيه:\n"
        "مثال: 100000\n\n"
        "<i>النصاب: ما يعادل 85 جرام ذهبًا أو 595 جرام فضة — تأكد أن مالك بلغ النصاب وحال عليه الحول.</i>",
        parse_mode="HTML", reply_markup=_ikb([_back()]))


async def handle_zakat_text(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    import re
    m = re.findall(r"[\d.,]+", text.replace(",", ""))
    if not m:
        await update.message.reply_text("⚠️ اكتب رقمًا صحيحًا، مثال: 100000")
        return
    amount = float(m[0].replace(",", ""))
    zakat = S.zakat_for(amount)
    await update.message.reply_text(
        f"💰 <b>حساب الزكاة</b>\nالمال: {amount:,.0f}\nالزكاة الواجبة (2.5%): <b>{zakat:,.2f}</b>\n\n"
        f"<i>إن كان مالك أقل من النصاب فلا زكاة فيه.</i>", parse_mode="HTML")


# ============================================================ أذكار النوم
@trace("sleep_adhkar")
async def on_sleep_adhkar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    items = S.sleep_adhkar_items()
    if not items:
        await q.edit_message_text("⚠️ تعذّر جلب المحتوى حاليًا.", reply_markup=_ikb([_back("menu:worship")]))
        return
    out = ["💤 <b>أذكار النوم</b>\n"]
    for i, it in enumerate(items, 1):
        out.append(f"{i}. {esc(it['text'])}\n   🔁 {it['count']} مرة" + (f" — {esc(it['note'])}" if it.get("note") else ""))
    await q.edit_message_text("\n\n".join(out)[:3900], parse_mode="HTML", reply_markup=_ikb([_back("menu:worship")]))


# ============================================================ فهرس الشيوخ
@trace("shuyukh")
async def cmd_shuyukh(update: Update, context: ContextTypes.DEFAULT_TYPE):
    recs = S.reciter_index()
    context.application.bot_data["reciters"] = recs
    rows = []
    for i, r in enumerate(recs[:PER_PAGE]):
        rows.append([InlineKeyboardButton(r["name"][:40], callback_data=f"shy:r:{i}")])
    rows.append(_back("menu:audio"))
    await update.message.reply_text(f"🎙️ <b>فهرس الشيوخ</b> ({len(recs)} قارئًا) — صفحة 1",
                                    parse_mode="HTML", reply_markup=_ikb(rows))


@trace("shuyukh_cb")
async def on_shuyukh_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    recs = context.application.bot_data.get("reciters") or S.reciter_index()
    context.application.bot_data["reciters"] = recs
    parts = q.data.split(":")
    if parts[1] == "p":  # صفحة قائمة القراء
        page = int(parts[2])
        start = (page - 1) * PER_PAGE
        rows = [[InlineKeyboardButton(r["name"][:40], callback_data=f"shy:r:{i}")]
                for i, r in enumerate(recs[start:start + PER_PAGE], start)]
        nav = []
        if page > 1:
            nav.append(InlineKeyboardButton("▶️", callback_data=f"shy:p:{page-1}"))
        nav.append(InlineKeyboardButton(f"({page}/{(len(recs)+PER_PAGE-1)//PER_PAGE})", callback_data="noop"))
        if start + PER_PAGE < len(recs):
            nav.append(InlineKeyboardButton("◀️", callback_data=f"shy:p:{page+1}"))
        rows.append(nav); rows.append(_back("menu:audio"))
        await q.edit_message_text(f"🎙️ <b>فهرس الشيوخ</b> ({len(recs)})", parse_mode="HTML", reply_markup=_ikb(rows))
        return
    if parts[1] == "r":  # قائمة سور الشيخ
        idx = int(parts[2])
        page = int(parts[3]) if len(parts) > 3 else 1
        per = 12
        start = (page - 1) * per
        rows = []
        for s in range(start + 1, min(start + per, 114) + 1):
            rows.append([InlineKeyboardButton(f"{s}. {S.surah_name(s)}", callback_data=f"shy:go:{idx}:{s}")])
        nav = []
        if page > 1:
            nav.append(InlineKeyboardButton("▶️", callback_data=f"shy:r:{idx}:{page-1}"))
        nav.append(InlineKeyboardButton(f"({page}/{(114+per-1)//per})", callback_data="noop"))
        if start + per < 114:
            nav.append(InlineKeyboardButton("◀️", callback_data=f"shy:r:{idx}:{page+1}"))
        rows.append(nav); rows.append(_back("menu:audio"))
        await q.edit_message_text(f"🎙️ <b>{esc(recs[idx]['name'])}</b> — اختر سورة:", parse_mode="HTML", reply_markup=_ikb(rows))
        return
    if parts[1] == "go":
        idx, s = int(parts[2]), int(parts[3])
        url = S.reciter_surah_url(recs[idx]["server"], s)
        await reply_audio_safe(q.message, url, caption=f"🎧 سورة {S.surah_name(s)} — {recs[idx]['name'][:50]}")


# ============================================================ الإذاعة (الآن/التالي)
@trace("now")
async def cmd_now(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = context.application.bot_data["db"]
    st = db.radio_get(update.effective_chat.id)
    if not st:
        await update.message.reply_text("📻 لا توجد إذاعة مختارة. افتح /radios واختر إذاعة.")
        return
    await update.message.reply_text(f"📻 <b>الإذاعة الحالية:</b> {esc(st['name'])}", parse_mode="HTML")


@trace("next")
async def cmd_next(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = context.application.bot_data["db"]
    stations = context.application.bot_data.get("stations") or S.radio_stations()
    context.application.bot_data["stations"] = stations
    cur = db.radio_get(update.effective_chat.id)
    ids = [str(s["id"]) for s in stations]
    idx = (ids.index(str(cur["station_id"])) + 1) % len(stations) if cur and str(cur["station_id"]) in ids else 0
    s = stations[idx]
    db.radio_set(update.effective_chat.id, s["id"], s["name"], s["url"])
    await update.message.reply_text(f"📻 <b>التالي:</b> {esc(s['name'])}", parse_mode="HTML")
    await reply_audio_safe(update.message, s["url"], caption=f"📻 {s['name']}")


# ============================================================ ربط القناة
@trace("linkchannel")
async def cmd_linkchannel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    db = context.application.bot_data["db"]
    if chat.type not in ("channel", "supergroup"):
        await update.message.reply_text(
            "ℹ️ استخدم هذا الأمر داخل القناة نفسها (بعد إضافة البوت كمشرف).\n"
            "للقنوات: أضِف البوت مشرفًا ثم أرسل /linkchannel داخل القناة.")
        return
    db.link_channel(update.effective_user.id, chat.id, chat.title or str(chat.id))
    await update.message.reply_text(
        f"✅ تم ربط القناة «{esc(chat.title or chat.id)}».\nاستخدم /daily لبثّ آية اليوم في القناة.")


@trace("unlinkchannel")
async def cmd_unlinkchannel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = context.application.bot_data["db"]
    db.unlink_channel(update.effective_user.id)
    await update.message.reply_text("✅ تم إلغاء ربط القنوات.")


@trace("daily")
async def cmd_daily(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = context.application.bot_data["db"]
    chans = db.channels_of(update.effective_user.id) or db.all_channels()
    if not chans:
        await update.message.reply_text("ℹ️ لا توجد قناة مرتبطة. أضف البوت مشرفًا ثم /linkchannel داخل القناة.")
        return
    v = S.daily_verse() or S.random_ayah()
    txt = f"🌅 <b>آية اليوم</b>\n\n{esc(v.get('text',''))}\n\n{esc(v.get('surah',''))}"
    ok, fail = 0, 0
    for c in chans:
        try:
            await context.bot.send_message(c["chat_id"], txt, parse_mode="HTML")
            ok += 1
        except Exception:  # noqa: BLE001
            fail += 1
    await update.message.reply_text(f"📤 أُرسلت لـ {ok} قناة" + (f" · فشل {fail} (تأكد أن البوت مشرف)" if fail else ""))


def register(app):
    app.add_handler(CommandHandler(["mood"], cmd_mood))
    app.add_handler(CommandHandler(["repeat"], cmd_repeat))
    app.add_handler(CommandHandler(["zakat"], cmd_zakat))
    app.add_handler(CommandHandler(["shuyukh"], cmd_shuyukh))
    app.add_handler(CommandHandler(["now"], cmd_now))
    app.add_handler(CommandHandler(["next"], cmd_next))
    app.add_handler(CommandHandler(["linkchannel"], cmd_linkchannel))
    app.add_handler(CommandHandler(["unlinkchannel"], cmd_unlinkchannel))
    app.add_handler(CommandHandler(["daily"], cmd_daily))
    app.add_handler(CallbackQueryHandler(on_mood_cb, pattern=r"^mood:"))
    app.add_handler(CallbackQueryHandler(on_repeat_cb, pattern=r"^rep:"))
    app.add_handler(CallbackQueryHandler(on_shuyukh_cb, pattern=r"^shy:"))
    app.add_handler(CallbackQueryHandler(on_sleep_adhkar, pattern=r"^adh:sleep$"))
