# -*- coding: utf-8 -*-
"""القرآن: سور، آيات، تفسير، بحث، تلاوات، إذاعات، وبحث مضمّن."""
from telegram import Update, InlineKeyboardButton, InlineQueryResultArticle, InputTextMessageContent
from telegram.ext import CommandHandler, CallbackQueryHandler, InlineQueryHandler, ContextTypes

from .. import keyboards as KB
from .. import services as S
from ..config import RECITERS, settings
from ..util import trace, esc
from ..util import reply_audio_safe

MAXLEN = 3800


def _chunks(text, size=MAXLEN):
    out, cur = [], ""
    for line in text.split("\n"):
        if len(cur) + len(line) + 1 > size:
            out.append(cur)
            cur = ""
        cur += line + "\n"
    if cur.strip():
        out.append(cur)
    return out or [""]


@trace("surah")
async def cmd_surah(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = context.application.bot_data["db"]
    u = db.user(update.effective_user.id)
    args = context.args
    if not args:
        await update.message.reply_text("اكتب رقم السورة أو اسمها، مثال: <code>/surah 18</code> أو /surah الكهف",
                                        parse_mode="HTML", reply_markup=KB.surahs_page(1))
        return
    raw = " ".join(args)
    import re
    m = re.search(r"\d+", raw)
    n = None
    if m:
        n = int(m.group())
    else:
        from ..content.islamic_data import SURAH_NAMES
        for i, name in enumerate(SURAH_NAMES, 1):
            if raw.strip() == name or raw.strip() in name:
                n = i
                break
    if not n or not 1 <= n <= 114:
        await update.message.reply_text("⚠️ رقم السورة غير صحيح (1-114).")
        return
    s = S.get_surah(n)
    head = f"📖 <b>سورة {esc(s['name'])}</b> ({n})\n"
    body = "\n".join(f"﴿{a['num']}﴾ {a['text']}" for a in s["ayahs"])
    chunks = _chunks(head + "\n" + body)
    for i, ch in enumerate(chunks):
        markup = KB.ikb([[InlineKeyboardButton(f"🎧 استماع ({RECITERS[u['reciter']][0]})",
                                               callback_data=f"q:play:{n}")], KB.back_row("menu:quran")]) \
            if i == len(chunks) - 1 else None
        await update.message.reply_text(ch, parse_mode="HTML", reply_markup=markup)


@trace("ayah")
async def cmd_ayah(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("مثال: <code>/ayah 2:255</code>", parse_mode="HTML")
        return
    await _send_ayah(update.message, context, " ".join(context.args))


@trace("tafsir")
async def cmd_tafsir(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("مثال: <code>/tafsir 2:255</code>", parse_mode="HTML")
        return
    ref = S.normalize_ref(" ".join(context.args))
    t = S.get_tafsir(ref)
    await update.message.reply_text(f"📚 <b>التفسير الميسر — {esc(ref)}</b>\n\n{esc(t)[:MAXLEN]}", parse_mode="HTML")


@trace("search")
async def cmd_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("مثال: <code>/search رحمة</code>", parse_mode="HTML")
        return
    kw = " ".join(context.args)
    hits = S.search_quran(kw, 8)
    if not hits:
        await update.message.reply_text(f"لا نتائج لـ «{esc(kw)}».")
        return
    parts = [f"🔍 <b>نتائج «{esc(kw)}»</b> ({len(hits)})\n"]
    for h in hits:
        parts.append(f"<b>{esc(h['surah_name'])} {esc(h['ref'].split(':')[1])}</b>\n{esc(h['text'][:260])}\n")
    await update.message.reply_text("\n".join(parts)[:MAXLEN * 2], parse_mode="HTML")


@trace("random")
async def cmd_random(update: Update, context: ContextTypes.DEFAULT_TYPE):
    v = S.random_ayah()
    s, a = v["ref"].split(":")
    await update.message.reply_text(
        f"🎲 <b>آية عشوائية — {esc(v['surah_name'])} ({esc(v['ref'])})</b>\n\n{esc(v['text'])}",
        parse_mode="HTML", reply_markup=KB.quran_actions(int(s), int(a)))


@trace("play")
async def cmd_play(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("مثال: <code>/play 18</code>", parse_mode="HTML")
        return
    db = context.application.bot_data["db"]
    u = db.user(update.effective_user.id)
    import re
    m = re.search(r"\d+", " ".join(context.args))
    if not m:
        await update.message.reply_text("⚠️ اكتب رقم السورة.")
        return
    await _send_surah_audio(update.message, int(m.group()), u["reciter"])


async def _send_ayah(message, context, ref_raw):
    ref = S.normalize_ref(ref_raw)
    v = S.get_ayah(ref)
    s, a = int(v["surah"]), int(v["ayah"])
    txt = f"📖 <b>{esc(v['surah_name'])} — الآية {a}</b>\n\n{esc(v['text'])}"
    await message.reply_text(txt, parse_mode="HTML", reply_markup=KB.quran_actions(s, a))


async def _send_surah_audio(message, n, reciter_key):
    url = S.resolve_surah_audio(n, reciter_key)
    if not url:
        # بديل: تلاوة الآية الأولى
        s = S.get_surah(n)
        if s["ayahs"]:
            await reply_audio_safe(message, S.ayah_audio_url(n, s["ayahs"][0]["num"], reciter_key),
                                   caption=f"🎧 سورة {s['name']} — تلاوة الآية الأولى ({RECITERS[reciter_key][0]})")
            return
        await message.reply_text("⚠️ تعذّر إيجاد تلاوة لهذه السورة حاليًا.")
        return
    await reply_audio_safe(message, url, caption=f"🎧 سورة {S.surah_name(n)} — {RECITERS[reciter_key][0]}")


@trace("quran_cb")
async def on_quran_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    db = context.application.bot_data["db"]
    u = db.user(q.from_user.id)
    d = q.data
    if d == "noop":
        await q.answer()
        return
    await q.answer()
    if d.startswith("q:list:"):
        page = int(d.split(":")[-1])
        await q.edit_message_text("📖 <b>القرآن الكريم</b> — اختر سورة:", reply_markup=KB.surahs_page(page),
                                  parse_mode="HTML")
        return
    if d.startswith("q:open:") or d.startswith("q:play:"):
        n = int(d.split(":")[-1])
        if d.startswith("q:play:"):
            await _send_surah_audio(q.message, n, u["reciter"])
            return
        s = S.get_surah(n)
        head = f"📖 <b>سورة {esc(s['name'])}</b> ({n})\n"
        body = "\n".join(f"﴿{a['num']}﴾ {a['text']}" for a in s["ayahs"])
        chunks = _chunks(head + "\n" + body)
        await q.edit_message_text(chunks[0], parse_mode="HTML",
                                  reply_markup=KB.ikb([[InlineKeyboardButton(f"🎧 استماع", callback_data=f"q:play:{n}")],
                                                       KB.back_row("menu:quran")]))
        for ch in chunks[1:]:
            await q.message.reply_text(ch, parse_mode="HTML")
        return
    if d.startswith("a:play:"):
        _, _, s, a = d.split(":")
        await reply_audio_safe(q.message, S.ayah_audio_url(int(s), int(a), u["reciter"]),
                               caption=f"🔊 {S.surah_name(int(s))} — آية {a} ({RECITERS[u['reciter']][0]})")
        return
    if d.startswith("a:tafsir:"):
        _, _, s, a = d.split(":")
        ref = f"{s}:{a}"
        t = S.get_tafsir(ref)
        extra = ""
        try:
            t2 = S.get_tafsir_quran_com(ref)
            if t2:
                import re as _re
                extra = "\n\n" + "\n".join(_re.sub("<[^>]+>", "", t2).split("\n")[:6])
        except Exception:  # noqa: BLE001
            pass
        await q.message.reply_text(f"📚 <b>التفسير — {esc(ref)}</b>\n\n{esc(t)[:2600]}{esc(extra)[:1200]}",
                                   parse_mode="HTML")
        return
    if d.startswith("a:reciters:"):
        _, _, s, a = d.split(":")
        rows = [[InlineKeyboardButton(name, callback_data=f"a:p2:{k}:{s}:{a}")] for k, (name, _) in RECITERS.items()]
        await q.edit_message_text("👥 اختر القارئ للمقارنة:", reply_markup=KB.ikb(rows + [KB.back_row("menu:quran")]))
        return
    if d.startswith("a:p2:"):
        _, _, k, s, a = d.split(":")
        await reply_audio_safe(q.message, S.ayah_audio_url(int(s), int(a), k),
                               caption=f"🔊 {S.surah_name(int(s))} — آية {a} ({RECITERS[k][0]})")
        return
    if d.startswith("a:video:"):
        _, _, s, a = d.split(":")
        context.user_data["video_ref"] = f"{s}:{a}"
        await q.message.reply_text("🎬 لإنتاج الفيديو اكتب: <code>/video " + f"{s}:{a}</code>", parse_mode="HTML")
        return


@trace("reciters")
async def cmd_reciters(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🎙️ اختر القارئ:", reply_markup=KB.reciter_menu())


@trace("radios")
async def cmd_radios(update: Update, context: ContextTypes.DEFAULT_TYPE):
    radios = S.mp3quran_radios()
    context.application.bot_data.setdefault("radios", {})
    for r in radios:
        context.application.bot_data["radios"][r["id"]] = r
    await update.message.reply_text(f"📻 <b>الإذاعات</b> ({len(radios)})", reply_markup=KB.radios_page(radios, 1),
                                    parse_mode="HTML")


@trace("radios_cb")
async def on_radio_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    d = q.data
    if d.startswith("rd:list:"):
        page = int(d.split(":")[-1])
        radios = S.mp3quran_radios()
        context.application.bot_data.setdefault("radios", {})
        for r in radios:
            context.application.bot_data["radios"][r["id"]] = r
        await q.answer()
        await q.edit_message_text(f"📻 <b>الإذاعات</b>", reply_markup=KB.radios_page(radios, page), parse_mode="HTML")
        return
    if d.startswith("rd:open:"):
        rid = d.split(":")[-1]
        r = context.application.bot_data.get("radios", {}).get(int(rid)) or context.application.bot_data.get("radios", {}).get(rid)
        await q.answer()
        if not r:
            await q.message.reply_text("⚠️ تعذّر إيجاد الإذاعة، أعد فتح القائمة: /radios")
            return
        context.application.bot_data["db"].radio_set(
            q.message.chat_id, r.get("id"), r.get("name", "إذاعة"), r.get("url"))
        await reply_audio_safe(q.message, r.get("url"), caption=f"📻 {r.get('name','إذاعة')}")
        return


@trace("inline")
async def on_inline(update: Update, context: ContextTypes.DEFAULT_TYPE):
    iq = update.inline_query
    kw = (iq.query or "").strip()
    results = []
    if kw:
        try:
            hits = S.search_quran(kw, 8)
        except Exception:  # noqa: BLE001
            hits = []
        for i, h in enumerate(hits):
            results.append(InlineQueryResultArticle(
                id=f"{h['ref']}-{i}",
                title=f"{h['surah_name']} — {h['ref']}",
                description=h["text"][:90],
                input_message_content=InputTextMessageContent(
                    f"📖 <b>{esc(h['surah_name'])} ({esc(h['ref'])})</b>\n\n{esc(h['text'][:900])}",
                    parse_mode="HTML")))
    if not results:
        results.append(InlineQueryResultArticle(
            id="hint", title="اكتب كلمة للبحث في القرآن",
            description="مثال: رحمة، صبر، نور",
            input_message_content=InputTextMessageContent("🔎 اكتب اسم البوت ثم كلمة للبحث في القرآن.")))
    await iq.answer(results, cache_time=30, is_personal=True)


def register(app):
    app.add_handler(CommandHandler(["surah", "s"], cmd_surah))
    app.add_handler(CommandHandler(["ayah", "a"], cmd_ayah))
    app.add_handler(CommandHandler(["tafsir"], cmd_tafsir))
    app.add_handler(CommandHandler(["search", "q"], cmd_search))
    app.add_handler(CommandHandler(["random"], cmd_random))
    app.add_handler(CommandHandler(["play"], cmd_play))
    app.add_handler(CommandHandler(["reciters", "reciter"], cmd_reciters))
    app.add_handler(CommandHandler(["radios"], cmd_radios))
    app.add_handler(CallbackQueryHandler(on_radio_cb, pattern=r"^rd:"))
    app.add_handler(CallbackQueryHandler(on_quran_cb, pattern=r"^(q:|a:|noop)"))
    app.add_handler(InlineQueryHandler(on_inline))
