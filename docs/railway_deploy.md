# النشر السحابي على Railway — دليل + أدلة (2026-09-29)

> الحالة: ✅ **البوت يعمل الآن على Railway 24/7** — النشر والتحقق تمّا فعليًا من جهاز المستخدم
> عبر حساب Railway **المسجَّل مسبقًا** عليه (Railway CLI)، بدون أي بطاقة جديدة وبدون تسجيل دخول جديد.

## 1) المعرّفات الأساسية

| العنصر | القيمة |
|---|---|
| Workspace | My Projects (حساب: ossamamohamed47991@gmail.com) |
| Project | `quran-unified-bot` — `b9e7b4c3-4db0-47e7-8585-b5cbeebca398` |
| Service | `quran-unified` |
| Environment | `production` — `0d82f170-34c7-4864-a367-c9d704cae2ba` (region: sfo) |
| النشر الناجح | `36462bac-74df-4797-a7ae-2e8ceae970d4` — status: SUCCESS · instance: RUNNING |
| صورة الدوكر | digest `sha256:6a0e2e10047974b833ee5fd84b588f6c2245873d71493130bb32f948c0e33e81` |
| الرابط العام (صحة) | <https://quran-unified-production-6645.up.railway.app> → HTTP 200 |
| متغيرات البيئة على الخدمة | `BOT_TOKEN` (سري) · `RAILWAY_DOCKERFILE_PATH=Dockerfile` |
| مولّد البناء | DOCKERFILE (من `railway.json` + `RAILWAY_DOCKERFILE_PATH`) |

## 2) أوامر التشغيل اليومية (من مجلد المشروع)

```powershell
railway status                       # حالة المشروع/الخدمة
railway deployment list --json       # قائمة النشرات وحالتها
railway logs -s quran-unified        # سجلات مباشرة
railway up --ci -s quran-unified     # نشر نسخة جديدة من الكود الحالي
railway redeploy -s quran-unified -y # إعادة تشغيل آخر نشر (بدون بناء)
railway down -s quran-unified -y     # حذف أحدث نشر (إيقاف كامل)
railway domain -s quran-unified --port 8080   # عرض/إنشاء الدومين
```

## 3) إصلاحات اكتشفها النشر (مهمة)

| # | العطل | السبب الجذري | الإصلاح |
|---|---|---|---|
| E-19 | Railway لم يجد الـDockerfile وبنى بـRailpack وفشل | اسم الملف كان `dockerfile` (حروف صغيرة) — أنظمة لينكس حساسة لحالة الأحرف | أُعيد التسمية إلى `Dockerfile` (وكذلك `README.md`) |
| E-20 | `ModuleNotFoundError: No module named 'app'` داخل الحاوية | `python deploy/start.py` يضيف مجلد السكربت فقط لمسار بايثون، وليس جذر المشروع | إضافة `sys.path.insert(0, جذر المشروع)` في `deploy/start.py` + `PYTHONPATH=/app` في Dockerfile |
| E-21 | تحذير `JobQueue غير متاح` (تعطّل المهام الدورية: آية/أذكار يومية) | الحزمة مثبّتة بدون الإضافة `[job-queue]` | `python-telegram-bot[job-queue]==22.8` في Dockerfile و requirements.txt |
| E-22 | `Conflict: terminated by other getUpdates request` | وجود نسختين شغّلتين معًا (نشر قديم + جديد على Railway، وأيضًا النسخة المحلية سابقًا) | حذف النشر القديم فورًا بمجرد وصول الجديد: `deploymentRemove` (GraphQL) — وقاعدة: نسخة واحدة فقط تعمل في أي وقت |

## 4) الأدلة المنفَّذة (قابلة للتحقق)

1. **سجل بناء ونشر ناجح** (من `railway up --ci`):
   - `[5/11] RUN pip install … python-telegram-bot[job-queue]==22.8 …` ثم `image push` ثم **`Deploy complete`**.
2. **سجل تشغيل الحاوية** (من `railway logs -s quran-unified`):
   - `[deploy] health server on :8080`
   - `[deploy] starting polling…`
   - (بدون تحذير JobQueue بعد الإصلاح E-21)
3. **رابط الصحة العام**:
   - `GET https://quran-unified-production-6645.up.railway.app` → `HTTP 200` — المحتوى: `quran-unified OK uptime=345s`
4. **اختبار Telegram حقيقي من حساب المستخدم** (`python tools/tg_cloud_check.py /start /health`) — والنسخة المحلية **متوقفة** أثناءه:
   - `/start` → «🕌 بوت القرآن الموحّد …» (قائمة كاملة)
   - `/health` → «🩺 حالة الخدمات | 👥 المستخدمون: 1 · الطلبات: 3 · الأخطاء: 8 | ✅ AlQuran.Cloud — 0.25s | ✅ AlAdhan — 0.29s»
   - **النتيجة: 2/2 ردود** — أي أن الردّ صادر من النسخة السحابية.
5. **تعافي تلقائي على السحابة**:
   - أثناء الإعداد، النشر الأول `6034e7ab…` انهار في حلقة و**كان Railway يعيد تشغيل الحاوية تلقائيًا مرارًا** (restartPolicy=ON_FAILURE على مستوى الخدمة) حتى استبدلناه بالنسخة المُصلَّحة.
   - محليًا (قبل التحويل للسحابة): سجلان طبيعيان لتعافي البوت تلقائيًا عبر الحارس (19:43 و20:51 بتوقيت القاهرة 2026-09-29) + اختبارا قتل سابقان + حادث إنتاج 2026-09-28.

## 5) المراقبة المزدوجة

| الطبقة | ماذا تفعل | أين |
|---|---|---|
| Railway (منصة) | إعادة تشغيل الحاوية تلقائيًا عند الانهيار | داخل Railway |
| «مراقب بوت القرآن السحابي» (AutoClaw) | كل 30 دقيقة: تفحص الرابط العام؛ إن لم يرجع 200 → `railway redeploy` ثم تتأكد | مهمة مجدولة — id: `312e463b-c23d-4bac-916f-e21d032bcd37` (النتائج تظهر في لوحة «定时» بالتطبيق) |

## 6) التبديل سحابي ⇄ محلي

الوضع الحالي: **سحابي فقط** (مطلوب — نسخة واحدة فقط تعمل).

- **محليًا (احتياطي، فقط إذا توقفت السحابة تمامًا):**
  1. `cd` لمجلد المشروع ثم: `railway down -s quran-unified -y` (يوقف السحابة)
  2. شغّل: `deploy\guard_start.bat` (يشغّل الحارس + البوت محليًا)
  3. أعد تمكين الإقلاع التلقائي: من مجلد بدء ويندوز أعِد تسمية `QuranBotGuard.cmd.disabled` → `QuranBotGuard.cmd`
- **الرجوع للسحابة (الافتراضي):** عطّل المحلي أولًا (اقتل الحارس والبوت + أعد تسمية مدخل الإقلاع لـ`.disabled`)، ثم `railway up --ci -s quran-unified` أو `railway redeploy -s quran-unified -y`.

> ⚠️ قاعدة ذهبية: **لا تشغّل النسختين معًا أبدًا** — سيؤدي ذلك لتعارض `getUpdates` وعدم استقرار الردود.

## 7) أمان

- `BOT_TOKEN` يُخزَّن فقط: (أ) كمتغير بيئة مشفَّر على Railway، (ب) في `quran-unified/.env` محليًا. **لا** يظهر في المستودع العام ولا في السجلات (تُطبع مفاتيح الأسرار مُخفاة).
- ملفات الجلسات/التوكنات المؤقتة تُحذف بعد الاستخدام.
