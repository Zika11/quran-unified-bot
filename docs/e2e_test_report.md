# تقرير الاختبار الحقيقي على تليجرام (End-to-End)

_التنفيذ: 2026-09-27 · المُختبِر: حساب مستخدم حقيقي `@iZ7Z7Z7Z7` عبر Telethon · الهدف: `@iQuranOfficial_Bot`_

## الأسلوب
أداة `tools/tg_e2e_test.py`: تسجّل بحساب مستخدم (لا يمكن لبوت مراسلة بوت)، ترسل كل أمر فعلًا، تلتقط ردود البوت (نص/صوت/فيديو/صورة) وتكتشف مؤشرات الخطأ. المخرجات الخام: `tools/e2e_report.json`.

## النتيجة النهائية
**43/43 ناجح · 0 فشل**

- أوامر القرآن/التلاوات: `/start /commands /surah /ayah /tafsir /search /random /play /reciters /radios` ✅
- العبادة: `/prayer /city /adhkar /duas /sajda /hadith` ✅
- الحفظ/الختمة/المسابقات/الفيديو: `/hifz /hz /tasmia /khatma /quiz /video` ✅
- الإعدادات: `/settings /health /stats` ✅
- نص حر «نور» · `/ayah abc` (خطأ مُدار) ✅
- الختمة: `/khnew /khjoin /khprogress /khdone /khmy` ✅
- **الجديدة:** `/mood /repeat /zakat /shuyukh /now /next /daily /linkchannel /unlinkchannel` ✅
- ضغط زر Inline ✅

## الأخطاء المكتشفة عبر الاختبار الحقيقي (وصُحّحت)
| # | الأمر | العَرَض | السبب الجذري | الإصلاح |
|---|------|--------|--------------|---------|
| E-14 | `/prayer` | «حدث خطأ غير متوقع» | تمرير قائمة أزرار كـ `reply_markup` بدل `InlineKeyboardMarkup` | تغليف بـ `KB.ikb([...])` |
| E-15 | `/settings` | بلا ردّ | لا `CommandHandler` | إضافة `cmd_settings` |
| E-16 | `/health` | بلا ردّ | لا `CommandHandler` | إضافة `cmd_health` |
| E-17 | `/khnew…/khmy` | أزرار فقط بلا أوامر | لا `CommandHandler` | إضافة 5 أوامر |
| **E-18** | `/next` (وبعض الإذاعات/الشيوخ) | «حدث خطأ غير متوقع» + `BadRequest: Failed to get http url content` | بعض روابط بث MP3Quran لا يجلبها تليجرام | إضافة `reply_audio_safe` (إرسال آمن + بديل نصي بالرابط)، وتطبيقه على الإذاعات/التلاوات/الفيديو |
| T-03 | أداة الاختبار | كل حالة تنتظر المهلة كاملة | منطق «الهدوء» يحدّث المؤقت مع نفس الرسائل | تتبّع `message_id` |
| T-04 | `SystemExit` عند غياب التوكن | كان يُسقط السويت | `except Exception` لا يلتقط `SystemExit` | التقاطه وتسجيله كبند فاشل واضح |

## ملاحظات
- `/stats` يرجع «للمالك فقط» (حساب الاختبار ليس مالكًا) — سلوك صحيح.
- `/linkchannel` خارج القناة يعطي رسالة إرشادية واضحة (سلوك صحيح).
- جميع حالات الفشل الخارجي تُترجم إلى رسالة عربية واضحة والبوت لا يتعطل.
