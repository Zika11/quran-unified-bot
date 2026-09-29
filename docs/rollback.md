# النسخة الاحتياطية وخطة الرجوع

## ما تم حفظه (قبل الدمج)
مجلد: `backups/pre-merge-YYYYMMDD-HHMMSS/` (أُنشئ بتاريخ **2026-09-27 21:33:42**) ويحتوي:

| الملف المحفوظ | المصدر الأصلي |
|---|---|
| `islamic_bot.py` | `D:\Projects\islamic_bot\islamic_bot.py` |
| `islamic_data.py` | `D:\Projects\islamic_bot\islamic_data.py` |
| `stream_quran.py`, `stream_userbot.py` | `D:\Projects\islamic_bot\` |
| `islamic_bot.env` | `D:\Projects\islamic_bot\.env` |
| `quran_video_main.py`, `quran_video_video_gen.py`, `quran_video_config.py` | `C:\Users\af191\OneDrive\Desktop\Z\quran-telegram-bot\` |
| `merged_quran_all_bot.py` | `D:\TelegramBots\bots\merged\quran_all_bot.py` |
| `merged_religious_all_bot.py` | `D:\TelegramBots\bots\merged\religious_all_bot.py` |
| `manifest.json` | قائمة بالمسارات + الأحجام + بصمات SHA256 |

**مهم:** لم يُحذف أو يُعدَّل أي ملف في المشاريع الأصلية. الدمج أُنشئ في مشروع مستقل تمامًا.

## خطة الرجوع (استعادة الوضع السابق)
الدمج لا يعدّل شيئًا من الأصل، لذا «الرجوع» ببساطة = التوقف عن استخدام المشروع الموحّد:

1. **إيقاف البوت الموحّد:**
   ```powershell
   cd C:\Users\af191\.openclaw-autoclaw\workspace\projects\quran-unified
   .\stop.bat
   ```
2. **التأكد من أن المشاريع الأصلية سليمة** (لم تُمَس):
   ```powershell
   Get-FileHash "D:\Projects\islamic_bot\islamic_bot.py" -Algorithm SHA256
   ```
   طابق الناتج مع بصمة `islamic_bot.py` في `backups/pre-merge-*/manifest.json`.
3. **(اختياري) استعادة أي ملف من النسخة الاحتياطية** إلى مكانه الأصلي:
   ```powershell
   Copy-Item "backups\pre-merge-20260927-213342\islamic_bot.py" "D:\Projects\islamic_bot\islamic_bot.py" -Force
   ```
4. **تشغيل البوت الأصلي كما كان** (اختياري):
   ```powershell
   cd D:\Projects\islamic_bot
   .\stream_venv\Scripts\python.exe islamic_bot.py
   ```
   (مع ملاحظة أن البوت الأصلي فيه أخطاء موثّقة في `ERROR_REVIEW.md`.)

## تجربة الرجوع (مُنفَّذة)
- تم التحقق أن ملفات المصدر لم تتغيّر: بصمات SHA256 مطابقة للمُسجّلة في `manifest.json` وقت الإنشاء.
- المشروع الموحّد معزول في مجلد مستقل، ولا يشارك أي ملف مع المصادر الأصلية.
- البيانات المُنشأة (قاعدة البيانات والسجلات) كلها داخل `quran-unified\data` و`\logs` فقط.

## مخاطر معروفة
| الخطر | الأثر | التخفيف |
|---|---|---|
| تشغيل نفس التوكن مرتين | تعارض polling | تأكد من إيقاف أي نسخة أخرى |
| حجب شبكة محلي للواجهات | فشل بعض الأوامر | البوت يعطي رسالة عربية ولا يتعطّل |
| تعطّل الجهاز/البوابة | توقف البوت | أعد التشغيل `start_background.bat` |
| تلف قاعدة البيانات | فقدان بيانات الحفظ/الختمة | احتفظ بنسخة من `data/quran_unified.db` |
