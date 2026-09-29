# دليل التشغيل المحلي (خطوة بخطوة)

> البيئة المستهدفة: ويندوز · Python مثبّت على `C:\Python314` (ثبّت المكتبات المطلوبة فقط، لا شيء إجباري إضافي).

## 1) التحقق من المتطلبات
المطلوب: `python-telegram-bot` + `requests` (مثبّتان على `C:\Python314`).
```powershell
C:\Python314\python.exe -c "import telegram, requests; print('ok')"
```
اختياري (لتحسين العربية في الفيديو):
```powershell
C:\Python314\python.exe -m pip install arabic-reshaper python-bidi
```
`ffmpeg` اختياري لإنتاج **فيديو** (بدونه يرجع البوت لصورة + صوت):
```powershell
ffmpeg -version
```

## 2) الإعداد
1. انسخ `.env.example` إلى `.env`.
2. ضع توكن البوت:
   ```
   BOT_TOKEN=123456789:AA...        # من @BotFather
   OWNER_IDS=1232067711             # معرّفك (اختياري)
   DEFAULT_CITY=Cairo
   DEFAULT_RECITER=maher
   ```
   > ملاحظة: احفظ `.env` بترميز **UTF-8 بدون BOM** (المفكّر يقرأ `utf-8-sig` أيضًا، لكن الأفضل بدون BOM).
3. تأكد أن البوت لا يعمل في نسخة ثانية (لا يمكن تشغيل نفس التوكن مرتين بـ polling).

## 3) فحص سريع قبل التشغيل
```powershell
cd C:\Users\af191\.openclaw-autoclaw\workspace\projects\quran-unified
C:\Python314\python.exe -m app.main --check
```
المتوقع:
```
✅ قاعدة البيانات جاهزة: ...\data\quran_unified.db
✅ التوكن صالح — البوت: @iQuranOfficial_Bot
✅ AlQuran.Cloud ✅ AlAdhan ✅ MP3Quran
```

## 4) التشغيل
- **بالنقر:** افتح `run.bat` (نافذة ظاهرة)، أو `start_background.bat` (خلفية).
- **بالأمر:**
  ```powershell
  C:\Python314\python.exe -u -m app.main
  ```
المتوقع في اللوج: `🚀 بدء البوت (polling)…` ثم بدء الاستقبال.

## 5) الاختبار
- تليجرام: أرسل `/start` ثم اتبع `docs/TEST_PACK.md`.
- محليًا بدون تليجرام:
  ```powershell
  C:\Python314\python.exe tests\selftest.py
  ```

## 6) الإيقاف
- `stop.bat` (يقرأ `logs\bot.pid`)، أو `Ctrl+C` في نافذة التشغيل.

## إثبات التكرار من الصفر (مُنفَّذ)
تم نسخ المشروع إلى مجلد نظيف (بدون `.env` و`data` و`logs` و`backups`) وتشغيله بمعرّف التوكن من متغير بيئة:
- `--check` في النسخة النظيفة ⇒ ✅ «التوكن صالح — @iQuranOfficial_Bot» + إنشاء قاعدة البيانات من الصفر.
- `tests/selftest.py` في النسخة النظيفة ⇒ **49/49 ناجح**.
- بدون توكن ⇒ فشل لطيف ببند واضح (48/49) لا انهيار، برسالة «⛔ BOT_TOKEN غير موجود في .env».

## حلول الأخطاء الشائعة
| العرض | السبب | الحل |
|---|---|---|
| `⚠️ لا يوجد BOT_TOKEN` | لا يوجد `.env` أو مفتاحه غير مقروء | تأكد من وجود `.env` بجانب `app/` وقيمة `BOT_TOKEN=` صحيحة |
| `ValueError: Command ... is not a valid bot command` | أمر غير ASCII | لا تُضِف أوامر عربية؛ استخدم الأزرار |
| `Conflict: terminated by other getUpdates` | نسخة أخرى تعمل بنفس التوكن | أوقف النسخة الأخرى (`stop.bat`) |
| `ModuleNotFoundError: telegram` | المكتبة على مفسّر آخر | استخدم `C:\Python314\python.exe` |
| العربية منفصلة في الفيديو | `arabic-reshaper` غير مثبّت | `pip install arabic-reshaper python-bidi` |
| لا فيديو، وصلت صورة+صوت | `ffmpeg` غير متاح | ثبّت ffmpeg أو اقبل البديل |
| `تعذّر الاتصال بالخدمة` | انقطاع/حجب واجهة | تحقق من الإنترنت؛ المزوّدات تعمل عادةً في مصر |
| لا صوت للسورة | رابط CDN غير متاح لحظيًا | البوت يتراجع لصوت الآية الأولى تلقائيًا |

## تغيير النطاق والإعدادات
- كل المفاتيح في `.env` (قارئ افتراضي، مدينة، ساعات الإرسال، تعطيل الفيديو `VIDEO_ENABLED=0`).
- مسارات اختيارية: `DATA_DIR` / `DB_PATH` / `LOG_DIR`.
