# -*- coding: utf-8 -*-
"""متقدّم: الحفظ والتسميع، الختمة الجماعية، المسابقات، مولّد الفيديو."""
import os
import tempfile
import random

from telegram import Update, InlineKeyboardButton, InputMediaPhoto
from telegram.ext import CommandHandler, CallbackQueryHandler, ContextTypes

from .. import keyboards as KB
from .. import services as S
from ..config import RECITERS, settings
from ..util import trace, esc, reply_audio_safe


# ============================================================ الحفظ
@trace("hifz")
async def cmd_hifz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🧠 <b>الحفظ والتسميع</b>", reply_markup=KB.hifz_menu(), parse_mode="HTML")


@trace("hz_mark")
async def cmd_hz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """تسجيل حفظ آية: /hz 2:255"""
    if not context.args:
        await update.message.reply_text("مثال: <code>/hz 2:255</code> لتسجيل حفظ الآية.", parse_mode="HTML")
        return
    ref = S.normalize_ref(" ".join(context.args))
    s, a = map(int, ref.split(":"))
    db = context.application.bot_data["db"]
    db.hifz_set(update.effective_user.id, s, a, "memorized")
    await update.message.reply_text(f"✅ تم تسجيل حفظ {esc(S.surah_name(s))} آية {a}.", parse_mode="HTML")


@trace("tasmia")
async def cmd_tasmia(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("مثال: <code>/tasmia 2:255</code>", parse_mode="HTML")
        return
    ref = S.normalize_ref(" ".join(context.args))
    v = S.get_ayah(ref)
    s, a = int(v["surah"]), int(v["ayah"])
    words = v["text"].split()
    hide = max(1, len(words) // 3)
    masked = " ".join(words[:-hide]) + " … " + "▁▁▁ " * hide
    await update.message.reply_text(
        f"🔥 <b>تسميع — {esc(S.surah_name(s))} آية {a}</b>\n\n{esc(masked)}",
        parse_mode="HTML",
        reply_markup=KB.ikb([[InlineKeyboardButton("👁️ إظهار الإجابة", callback_data=f"hz:reveal:{s}:{a}")],
                             KB.back_row("menu:hifz")]))


@trace("hifz_cb")
async def on_hifz_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    db = context.application.bot_data["db"]
    uid = q.from_user.id
    d = q.data
    if d == "hz:plan":
        db.set_hifz_plan(uid, 3, 78)
        await q.edit_message_text("📋 <b>خطة الحفظ</b>\nالهدف: 3 آيات يوميًا بدءًا من سورة النبأ (78).\n"
                                  "سجّل ما حفظته بـ <code>/hz سورة:آية</code>.",
                                  parse_mode="HTML", reply_markup=KB.ikb([KB.back_row("menu:hifz")]))
    elif d == "hz:status":
        c = db.hifz_counts(uid)
        rows = db.hifz_list(uid)
        txt = (f"📊 <b>حالتك</b>\n✅ محفوظ: {c.get('memorized',0)}\n"
               f"🔁 مراجعة: {c.get('reviewing',0)}\n📈 إجمالي: {len(rows)}")
        if rows:
            txt += "\n\nآخر ما سجّلته:\n" + "\n".join(
                f"• {esc(S.surah_name(r['surah']))} {r['ayah']} — {esc(r['status'])}" for r in rows[-8:])
        await q.edit_message_text(txt, parse_mode="HTML", reply_markup=KB.ikb([KB.back_row("menu:hifz")]))
    elif d == "hz:ask_tasmia":
        await q.edit_message_text("اكتب: <code>/tasmia سورة:آية</code>", parse_mode="HTML",
                                  reply_markup=KB.ikb([KB.back_row("menu:hifz")]))
    elif d.startswith("hz:reveal:"):
        _, _, s, a = d.split(":")
        v = S.get_ayah(f"{s}:{a}")
        db.hifz_set(uid, int(s), int(a), "memorized")
        await q.edit_message_text(f"✅ <b>{esc(S.surah_name(int(s)))} آية {a}</b>\n\n{esc(v['text'])}",
                                  parse_mode="HTML", reply_markup=KB.ikb([KB.back_row("menu:hifz")]))


# ============================================================ الختمة
@trace("khatma")
async def cmd_khatma(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤝 <b>الختمة الجماعية</b>\nتقاسم 30 جزءًا بين المشاركين.",
                                    reply_markup=KB.khatma_menu(), parse_mode="HTML")


def _khatma_text(k):
    filled = len(k["members"])
    done = len([m for m in k["members"] if m["done"]])
    lines = [f"🤝 <b>{esc(k['title'])}</b> (#{k['id']})",
             f"الأجزاء: {k['parts']} · مشاركون: {filled} · مكتمل: {done}", ""]
    for m in k["members"]:
        lines.append(f"• الجزء {m['part']} — <code>{m['user_id']}</code> {'✅' if m['done'] else '⏳'}")
    return "\n".join(lines)


@trace("khatma_cb")
async def on_khatma_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    db = context.application.bot_data["db"]
    uid = q.from_user.id
    d = q.data
    await q.answer()
    if d == "kh:new":
        import datetime
        kid = db.khatma_create(uid, f"ختمة {datetime.date.today().isoformat()}")
        k = db.khatma_get(kid)
        await q.edit_message_text(_khatma_text(k) + "\n\nانضم بـ /khjoin", parse_mode="HTML",
                                  reply_markup=KB.ikb([KB.back_row("menu:khatma")]))
    elif d == "kh:join":
        k = db.khatma_open()
        if not k:
            await q.edit_message_text("لا توجد ختمة مفتوحة. أنشئ واحدة.", reply_markup=KB.khatma_menu())
            return
        taken = db.khatma_taken_parts(k["id"])
        free = [i for i in range(1, k["parts"] + 1) if i not in taken]
        if not free:
            await q.edit_message_text("اكتملت الأجزاء في هذه الختمة.", reply_markup=KB.khatma_menu())
            return
        part = random.choice(free)
        db.khatma_join(k["id"], uid, part)
        await q.edit_message_text(f"✅ تم تسجيلك في الجزء {part} من {esc(k['title'])}.", parse_mode="HTML",
                                  reply_markup=KB.ikb([KB.back_row("menu:khatma")]))
    elif d == "kh:progress":
        k = db.khatma_open()
        await q.edit_message_text(_khatma_text(k) if k else "لا توجد ختمة مفتوحة.",
                                  parse_mode="HTML", reply_markup=KB.ikb([KB.back_row("menu:khatma")]))
    elif d == "kh:done":
        k = db.khatma_open()
        if not k:
            await q.edit_message_text("لا توجد ختمة مفتوحة.", reply_markup=KB.khatma_menu())
            return
        db.khatma_done(k["id"], uid)
        await q.edit_message_text("✅ تم تسجيل إنهاء جزئك. جزاك الله خيرًا.", reply_markup=KB.khatma_menu())
    elif d == "kh:mine":
        mine = db.khatma_mine(uid)
        if not mine:
            await q.edit_message_text("لم تنضم لأي ختمة بعد.", reply_markup=KB.khatma_menu())
            return
        txt = "\n".join(f"• ختمة #{m['id']} — الجزء {m['part']} {'✅' if m['done'] else '⏳'}" for m in mine)
        await q.edit_message_text(f"📚 <b>ختماتي</b>\n\n{txt}", parse_mode="HTML", reply_markup=KB.khatma_menu())


# ============================================================ المسابقات
@trace("quiz")
async def cmd_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❓ <b>مسابقات</b>", reply_markup=KB.quiz_menu(), parse_mode="HTML")


@trace("quiz_cb")
async def on_quiz_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    db = context.application.bot_data["db"]
    uid = q.from_user.id
    d = q.data
    await q.answer()
    if d == "qz:score":
        rows = []
        for t in S.QUIZ_TOPICS:
            sc = db.quiz_score(uid, t)
            rows.append(f"• {t}: ✅ {sc['correct']} · ❌ {sc['wrong']}")
        await q.edit_message_text("📊 <b>نتائجك</b>\n\n" + "\n".join(rows), parse_mode="HTML",
                                  reply_markup=KB.ikb([KB.back_row("menu:quiz")]))
        return
    if d.startswith("qz:start:"):
        topic = d.split(":", 2)[2]
        qs = S.build_quiz(topic, 1)
        if not qs:
            await q.edit_message_text("⚠️ لا توجد أسئلة متاحة لهذا الموضوع.", reply_markup=KB.quiz_menu())
            return
        item = qs[0]
        context.user_data["quiz"] = {"topic": topic, "item": item}
        rows = [[InlineKeyboardButton(opt[:60], callback_data=f"qz:ans:{i}")] for i, opt in enumerate(item["options"])]
        rows.append(KB.back_row("menu:quiz"))
        await q.edit_message_text(f"❓ <b>{topic}</b>\n\n{esc(item['q'])}", parse_mode="HTML", reply_markup=KB.ikb(rows))
        return
    if d.startswith("qz:ans:"):
        idx = int(d.split(":")[-1])
        st = context.user_data.get("quiz")
        if not st:
            await q.edit_message_text("انتهت الجلسة، ابدأ من جديد.", reply_markup=KB.quiz_menu())
            return
        item = st["item"]
        chosen = item["options"][idx]
        correct = (chosen == item["answer"])
        db.quiz_add(uid, st["topic"], correct)
        if correct:
            body = f"✅ <b>إجابة صحيحة!</b>\n\n{item['answer']}"
        else:
            body = f"❌ <b>إجابة خاطئة.</b>\nالصحيح: <b>{esc(item['answer'])}</b>"
        await q.edit_message_text(body, parse_mode="HTML",
                                  reply_markup=KB.ikb([[InlineKeyboardButton("➡️ سؤال آخر", callback_data=f"qz:start:{st['topic']}")],
                                                       KB.back_row("menu:quiz")]))


# ============================================================ الفيديو
@trace("video")
async def cmd_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not settings.VIDEO_ENABLED:
        await update.message.reply_text("🎬 مولّد الفيديو معطّل في الإعدادات (VIDEO_ENABLED=0).")
        return
    if not context.args:
        await update.message.reply_text("مثال: <code>/video 2:255</code>", parse_mode="HTML")
        return
    ref = S.normalize_ref(" ".join(context.args))
    v = S.get_ayah(ref)
    s, a = int(v["surah"]), int(v["ayah"])
    db = context.application.bot_data["db"]
    reciter = db.user(update.effective_user.id)["reciter"]
    label = f"{S.surah_name(s)} — {a} ({RECITERS[reciter][0]})"
    audio_url = S.ayah_audio_url(s, a, reciter)
    with tempfile.TemporaryDirectory() as td:
        img = os.path.join(td, "ayah.png")
        try:
            S.render_ayah_image(v["text"], img, label)
        except Exception as e:  # noqa: BLE001
            await reply_audio_safe(update.message, audio_url, caption=f"🔊 {label}\n{v['text']}")
            return
        # محاولة فيديو إن توفّر ffmpeg
        try:
            mp3 = os.path.join(td, "ayah.mp3")
            S.download(audio_url, mp3)
            out = os.path.join(td, "ayah.mp4")
            S.make_ayah_video(v["text"], mp3, out, label)
            with open(out, "rb") as f:
                await update.message.reply_video(f, caption=f"🎬 {label}")
            return
        except Exception:  # noqa: BLE001
            with open(img, "rb") as f:
                await update.message.reply_photo(f, caption=f"🖼️ {label}\n{v['text'][:900]}")
            await reply_audio_safe(update.message, audio_url, caption=f"🔊 {label}")


@trace("kh_new")
async def cmd_khnew(update: Update, context: ContextTypes.DEFAULT_TYPE):
    import datetime
    db = context.application.bot_data["db"]
    kid = db.khatma_create(update.effective_user.id, f"ختمة {datetime.date.today().isoformat()}")
    k = db.khatma_get(kid)
    await update.message.reply_text(_khatma_text(k) + "\n\nانضمّ بـ /khjoin", parse_mode="HTML",
                                    reply_markup=KB.ikb([KB.back_row("menu:khatma")]))


@trace("kh_join")
async def cmd_khjoin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = context.application.bot_data["db"]
    uid = update.effective_user.id
    k = db.khatma_open()
    if not k:
        await update.message.reply_text("لا توجد ختمة مفتوحة. أنشئ واحدة بـ /khnew")
        return
    taken = db.khatma_taken_parts(k["id"])
    free = [i for i in range(1, k["parts"] + 1) if i not in taken]
    if not free:
        await update.message.reply_text("اكتملت الأجزاء في هذه الختمة.")
        return
    part = random.choice(free)
    db.khatma_join(k["id"], uid, part)
    await update.message.reply_text(f"✅ تم تسجيلك في الجزء {part} من {esc(k['title'])}.", parse_mode="HTML")


@trace("kh_progress")
async def cmd_khprogress(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = context.application.bot_data["db"]
    k = db.khatma_open()
    await update.message.reply_text(_khatma_text(k) if k else "لا توجد ختمة مفتوحة.", parse_mode="HTML",
                                    reply_markup=KB.ikb([KB.back_row("menu:khatma")]))


@trace("kh_done")
async def cmd_khdone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = context.application.bot_data["db"]
    k = db.khatma_open()
    if not k:
        await update.message.reply_text("لا توجد ختمة مفتوحة.")
        return
    db.khatma_done(k["id"], update.effective_user.id)
    await update.message.reply_text("✅ تم تسجيل إنهاء جزئك. جزاك الله خيرًا.", reply_markup=KB.khatma_menu())


@trace("kh_mine")
async def cmd_khmy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = context.application.bot_data["db"]
    mine = db.khatma_mine(update.effective_user.id)
    if not mine:
        await update.message.reply_text("لم تنضم لأي ختمة بعد.", reply_markup=KB.khatma_menu())
        return
    txt = "\n".join(f"• ختمة #{m['id']} — الجزء {m['part']} {'✅' if m['done'] else '⏳'}" for m in mine)
    await update.message.reply_text(f"📚 <b>ختماتي</b>\n\n{txt}", parse_mode="HTML", reply_markup=KB.khatma_menu())


def register(app):
    app.add_handler(CommandHandler(["hifz"], cmd_hifz))
    app.add_handler(CommandHandler(["hz", "hifz_add"], cmd_hz))
    app.add_handler(CommandHandler(["tasmia"], cmd_tasmia))
    app.add_handler(CommandHandler(["khatma", "kh"], cmd_khatma))
    app.add_handler(CommandHandler(["khnew"], cmd_khnew))
    app.add_handler(CommandHandler(["khjoin"], cmd_khjoin))
    app.add_handler(CommandHandler(["khprogress"], cmd_khprogress))
    app.add_handler(CommandHandler(["khdone"], cmd_khdone))
    app.add_handler(CommandHandler(["khmy"], cmd_khmy))
    app.add_handler(CommandHandler(["quiz"], cmd_quiz))
    app.add_handler(CommandHandler(["video"], cmd_video))
    app.add_handler(CallbackQueryHandler(on_hifz_cb, pattern=r"^hz:"))
    app.add_handler(CallbackQueryHandler(on_khatma_cb, pattern=r"^kh:"))
    app.add_handler(CallbackQueryHandler(on_quiz_cb, pattern=r"^qz:"))
