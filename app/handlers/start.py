# -*- coding: utf-8 -*-
"""أوامر البداية والقوائم والإعدادات والإدارة."""
from telegram import Update, InlineKeyboardButton
from telegram.ext import CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

from .. import keyboards as KB
from ..config import settings, RECITERS
from ..util import trace, esc
from .. import services as S

WELCOME = (
    "🕌 <b>بوت القرآن الموحّد</b>\n\n"
    "كل بوتات القرآن في بوت واحد: تلاوات، تفسير، بحث، مواقيت، أذكار، حديث، حفظ، ختمة، مسابقات، وفيديو آية.\n\n"
    "اختر من القائمة، أو اكتب: /surah · /ayah 2:255 · /search رحمة · /prayer · /adhkar · /kh\n\n"
    "📋 قائمة كل الأوامر: /commands"
)

COMMANDS = (
    "📋 <b>الأوامر</b>\n"
    "<b>القرآن</b>\n"
    "/surah &lt;رقم|اسم&gt; — نص السورة + استماع\n"
    "/ayah &lt;سورة:آية&gt; — آية + صوت + تفسير\n"
    "/tafsir &lt;سورة:آية&gt; — التفسير الميسر\n"
    "/search &lt;كلمة&gt; — بحث في القرآن\n"
    "/random — آية عشوائية\n\n"
    "<b>التلاوات</b>\n"
    "/reciters — تغيير القارئ\n"
    "/play &lt;سورة&gt; — تلاوة السورة\n"
    "/radios — الإذاعات المباشرة\n\n"
    "<b>العبادة</b>\n"
    "/prayer [مدينة] — مواقيت الصلاة\n"
    "/city &lt;مدينة&gt; — ضبط المدينة\n"
    "/adhkar — الأذكار · /duas — أدعية · /hadith — حديث اليوم · /sajda — مواضع السجود\n\n"
    "<b>الحفظ والختمة</b>\n"
    "/hifz — خطة الحفظ · /hz &lt;سورة:آية&gt; — تسجيل حفظ · /tasmia — تسميع\n"
    "/kh — الختمة · /khjoin — انضمام · /khprogress — التقدّم · /khdone — أنهيت جزئي\n\n"
    "<b>أخرى</b>\n"
    "/quiz — مسابقات · /video &lt;سورة:آية&gt; — فيديو الآية\n"
    "/settings — الإعدادات · /health — حالة الخدمات · /stats — إحصاءات (للمالك)\n"
    "🔎 يمكنك البحث مباشرة بكتابة الكلمة، أو عبر: <code>@البوت كلمة</code>"
)


def _user(context, user):
    return context.application.bot_data["db"].user(user.id)


@trace("start")
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = context.application.bot_data["db"]
    u = update.effective_user
    db.upsert_user(u.id, u.username, u.first_name)
    await update.message.reply_text(WELCOME, reply_markup=KB.main_menu(), parse_mode="HTML")


@trace("help")
async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(COMMANDS, parse_mode="HTML", reply_markup=KB.about_menu())


@trace("commands")
async def cmd_commands(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(COMMANDS, parse_mode="HTML")


@trace("menu")
async def on_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    db = context.application.bot_data["db"]
    u = db.user(q.from_user.id)
    routes = {
        "menu:main": (WELCOME, KB.main_menu()),
        "menu:about": ("ℹ️ <b>عن البوت</b>\nبوت قرآن موحّد (دمج كل بوتات القرآن) — تشغيل محلي. "
                       "البيانات: AlQuran.Cloud · MP3Quran · AlAdhan · Dorar · Quran.com.\n"
                       "تخزين محلي SQLite + سجلات قابلة للتتبع.", KB.about_menu()),
        "menu:commands": (COMMANDS, KB.about_menu()),
        "menu:quran": ("📖 <b>القرآن الكريم</b>\nاختر سورة، أو استخدم:\n/surah 18 · /ayah 2:255 · /search رحمة · /random",
                       KB.surahs_page(1)),
        "menu:audio": ("🎧 <b>التلاوات والإذاعات</b>\n/reciters لتغيير القارئ · /radios للإذاعات · /play 18",
                       KB.ikb([[InlineKeyboardButton("🎙️ اختيار القارئ", callback_data="set:reciter"),
                                InlineKeyboardButton("📻 الإذاعات", callback_data="rd:list:1")], KB.back_row()])),
        "menu:worship": ("🕌 <b>المواقيت والأذكار</b>\n/prayer · /city القاهرة · /adhkar · /duas · /sajda",
                         KB.adhkar_menu()),
        "menu:hadith": ("📚 <b>الحديث والدعاء</b>", KB.hadith_menu()),
        "menu:hifz": ("🧠 <b>الحفظ والتسميع</b>", KB.hifz_menu()),
        "menu:khatma": ("🤝 <b>الختمة الجماعية</b>", KB.khatma_menu()),
        "menu:video": ("🎬 <b>مولّد فيديو الآية</b>\nاكتب: <code>/video 2:255</code> لإنتاج فيديو بالآية والصوت.",
                       KB.back_row()),
        "menu:quiz": ("❓ <b>مسابقات</b> (من محتوى المشاريع الأصلي)", KB.quiz_menu()),
        "menu:settings": (None, KB.settings_menu(u["reciter"], u["city"])),
    }
    text, markup = routes.get(q.data, (None, KB.main_menu()))
    if q.data == "menu:settings":
        text = (f"⚙️ <b>الإعدادات</b>\nالقارئ: {RECITERS.get(u['reciter'], ('-',''))[0]}\n"
                f"المدينة: {u['city']} · الدولة: {u['country']}\n"
                f"آية اليوم: {'✅' if u['notify_ayah'] else '❌'} · "
                f"تنبيه الصلاة: {'✅' if u['notify_prayer'] else '❌'}")
    if q.data == "menu:health":
        text, markup = await _health_text(context), KB.about_menu()
    if text:
        await q.edit_message_text(text, reply_markup=markup, parse_mode="HTML")


@trace("settings")
async def on_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    db = context.application.bot_data["db"]
    uid = q.from_user.id
    d = q.data
    if d == "set:reciter":
        await q.edit_message_text("🎙️ اختر القارئ:", reply_markup=KB.reciter_menu(), parse_mode="HTML")
        return
    if d.startswith("rc:set:"):
        key = d.split(":")[-1]
        if key in RECITERS:
            db.set_user(uid, reciter=key)
            await q.answer("تم تغيير القارئ ✅", show_alert=True)
        u = db.user(uid)
        await q.edit_message_text("⚙️ <b>الإعدادات</b>", reply_markup=KB.settings_menu(u["reciter"], u["city"]),
                                  parse_mode="HTML")
        return
    if d == "set:city":
        context.user_data["await"] = "city"
        await q.edit_message_text("🏙️ اكتب اسم المدينة (مثال: Cairo أو الإسكندرية).")
        return
    if d == "set:toggle_ayah":
        u = db.user(uid)
        db.set_user(uid, notify_ayah=0 if u["notify_ayah"] else 1)
    elif d == "set:toggle_prayer":
        u = db.user(uid)
        db.set_user(uid, notify_prayer=0 if u["notify_prayer"] else 1)
    u = db.user(uid)
    await q.edit_message_text(
        f"⚙️ <b>الإعدادات</b>\nالقارئ: {RECITERS.get(u['reciter'], ('-',''))[0]}\nالمدينة: {u['city']}",
        reply_markup=KB.settings_menu(u["reciter"], u["city"]), parse_mode="HTML")


async def _health_text(context):
    import datetime
    db = context.application.bot_data["db"]
    st = db.stats()
    lines = [f"🩺 <b>حالة الخدمات</b>", f"👥 المستخدمون: {st['users']} · الطلبات: {st['requests']} · الأخطاء: {st['errors']}"]
    for name, fn in (("AlQuran.Cloud", lambda: S.get_ayah("2:255")), ("AlAdhan", lambda: S.prayer_times("Cairo"))):
        t0 = datetime.datetime.now()
        try:
            fn()
            lines.append(f"✅ {name} — {(datetime.datetime.now()-t0).total_seconds():.2f}s")
        except Exception as e:  # noqa: BLE001
            lines.append(f"❌ {name} — {type(e).__name__}")
    return "\n".join(lines)


@trace("settings_cmd")
async def cmd_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = context.application.bot_data["db"]
    u = db.user(update.effective_user.id)
    await update.message.reply_text(
        f"⚙️ <b>الإعدادات</b>\nالقارئ: {esc(RECITERS.get(u['reciter'], ('-',''))[0])}\n"
        f"المدينة: {esc(u['city'])} · الدولة: {esc(u['country'])}\n"
        f"آية اليوم: {'✅' if u['notify_ayah'] else '❌'} · تنبيه الصلاة: {'✅' if u['notify_prayer'] else '❌'}",
        parse_mode="HTML", reply_markup=KB.settings_menu(u["reciter"], u["city"]))


@trace("health_cmd")
async def cmd_health(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txt = await _health_text(context)
    await update.message.reply_text(txt, parse_mode="HTML", reply_markup=KB.about_menu())


@trace("stats")
async def cmd_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if settings.OWNER_IDS and update.effective_user.id not in settings.OWNER_IDS:
        await update.message.reply_text("⛔ هذا الأمر للمالك فقط.")
        return
    db = context.application.bot_data["db"]
    st = db.stats()
    recent = db.last_requests(8)
    txt = ["📊 <b>إحصاءات</b>", f"👥 مستخدمون: {st['users']}", f"📨 طلبات: {st['requests']}",
           f"⚠️ أخطاء: {st['errors']}", f"🤝 ختمات: {st['khatmas']}", f"🧠 صفوف حفظ: {st['hifz_rows']}", "",
           "🕒 آخر الطلبات:"]
    for r in recent:
        txt.append(f"· <code>{esc(r['req_id'])}</code> {esc(r['handler'])} → {esc(r['status'])}")
    await update.message.reply_text("\n".join(txt), parse_mode="HTML")


@trace("text_router")
async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نص حر: ضبط المدينة، أو بحث قرآن افتراضي."""
    db = context.application.bot_data["db"]
    uid = update.effective_user.id
    if context.user_data.get("await") == "city":
        context.user_data.pop("await", None)
        db.set_user(uid, city=update.message.text.strip()[:40])
        u = db.user(uid)
        await update.message.reply_text(f"✅ تم ضبط المدينة: {esc(u['city'])}",
                                        reply_markup=KB.settings_menu(u["reciter"], u["city"]), parse_mode="HTML")
        return
    if context.user_data.get("await") == "zakat":
        context.user_data.pop("await", None)
        from . import extra as _extra
        await _extra.handle_zakat_text(update, context, (update.message.text or "").strip())
        return
    if context.user_data.get("await") == "hadith":
        context.user_data.pop("await", None)
        from .. import services as S2
        res = S2.dorar_search(update.message.text.strip())
        import re as _re
        clean = _re.sub("<[^>]+>", "", res or "")[:3500]
        await update.message.reply_text(f"🔍 <b>نتيجة التحقق</b>\n\n{esc(clean) or 'لا نتائج.'}", parse_mode="HTML")
        return
    kw = (update.message.text or "").strip()
    if len(kw) < 2:
        await update.message.reply_text("اكتب كلمة للبحث في القرآن، أو /start للقائمة.")
        return
    hits = S.search_quran(kw, 5)
    if not hits:
        await update.message.reply_text(f"لا نتائج لـ «{esc(kw)}».")
        return
    parts = [f"🔍 <b>نتائج «{esc(kw)}»</b>\n"]
    for h in hits:
        parts.append(f"<b>{esc(h['surah_name'])} {esc(h['ref'].split(':')[1])}</b>\n{esc(h['text'][:300])}\n")
    await update.message.reply_text("\n".join(parts), parse_mode="HTML")


def register(app):
    app.add_handler(CommandHandler(["start"], cmd_start))
    app.add_handler(CommandHandler(["help"], cmd_help))
    app.add_handler(CommandHandler(["commands", "list"], cmd_commands))
    app.add_handler(CommandHandler(["settings", "set"], cmd_settings))
    app.add_handler(CommandHandler(["health", "status"], cmd_health))
    app.add_handler(CommandHandler(["stats", "admin"], cmd_stats))
    app.add_handler(CallbackQueryHandler(on_settings, pattern=r"^(set:|rc:set:)"))
    app.add_handler(CallbackQueryHandler(on_menu, pattern=r"^menu:"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))
