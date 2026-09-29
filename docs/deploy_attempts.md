# سجل محاولات النشر على استضافة/سيرفر مجاني

_التاريخ: 2026-09-28 · المهمة: نشر بوت القرآن الموحّد على خدمة مجانية تعمل فعليًا._
_القيد الأساسي: الميزانية صفر — لا بطاقة دفع، ولا تجاوز شروط الخدمة._

| # | الخدمة | الطريقة المُجرّبة | النتيجة | السبب / الحد |
|---|--------|-------------------|---------|---------------|
| 1 | **GitHub** | API + git push بمفتاح المستخدم | ✅ **نجح** | المستودع: <https://github.com/Zika11/quran-unified-bot> (عام، 48 ملفًا) — لا أسرار داخله |
| 2 | **Hugging Face Spaces** | سكربت `deploy/hf_deploy.py` (جرّبناه فعلًا بتوكن المستخدم) | ⛔ **مرفوض من المنصة** | الردّ الحرفي من HF API: `402 — Static Spaces are free for everyone, but hosting Gradio and Docker Spaces on free cpu-basic requires a PRO subscription` ⇒ يتطلّب اشتراكًا مدفوعًا، وممنوع الدفع في نطاق المهمة. (لم يُنشأ أي Space؛ الرفع أعاد 404 وحُذف ملف التوكن المؤقت بعد التجربة) |
| 3 | **Back4App Containers** | مفتاح `b4a_key.txt` (40 حرفًا) + محاولات واجهات REST | ⛔ | واجهة `api.back4app.com` ترفض المفتاح (401) وكل مسارات النشر ترجع HTML/Dashboard — النشر من الواجهة فقط، ولا جلسة متصفح مسجّلة |
| 4 | **Cloudflare** | موصل Cloudflare (مُصادَق) — Workers مجاني بلا بطاقة | 🟢 **جزئيًا: نُشر فعلًا** | ✅ نُشرت صفحة الحالة العامة على Workers: <https://quran-unified-status.zikaquran.workers.dev> (تم إنشاء نطاق `zikaquran.workers.dev` ونشر السكربت وتمكينه — تحقق 200). ⛔ للبوت نفسه: Workers لا تشغّل python-telegram-bot وContainers مدفوعة |
| 5 | **Vercel** | موصل Vercel عبر mcporter | ⛔ | يتطلّب مصادقة OAuth تفاعلية (انتهت المدة 60s) — لا تفويض مسبق |
| 6 | **Render** | `render_key.txt` + `render_try.py` (سابق) | ⛔ | مفتاح Render فارغ، والطبقة المجانية تتطلّب بطاقة دفع (موثّق سابقًا) |
| 7 | **Koyeb / Northflank / Zeabur / Railway / Fly.io** | فحص | ⛔ | تتطلّب حسابًا وبطاقة تحقق للمستوى المجاني |
| 8 | **PythonAnywhere** | فحص | ⛔ | لا مهام خلفية دائمة في الحساب المجاني (Always-on مدفوع) |
| 9 | **GitHub Codespaces** | API (متاح: `GET /user/codespaces` = 200) | ⛔ | الحصة المجانية 120 core-hour/شهر لا تكفي 24/7، والاستخدام غير مخصص لخدمة دائمة (شروط الخدمة) |
| 10 | **GitHub Actions كسيرفر** | فحص | ⛔ | شروط GitHub تمنع استخدام Actions كخدمة تشغيل عامة — مرفوض أخلاقيًا وقانونيًا |
| 11 | **Serv00 / JustRunMyApp / NexCloud / بنى استضافة بوتات مجانية** | فحص | ⛔ | كلها تتطلّب تسجيل حساب وتأكيد بريد/مراجعة (معلومات المستخدم فقط) |
| 12 | **المتصفح (بيانات الدخول)** | فحص تسجيل الدخول | ⛔ | غير مسجّل في: HuggingFace · Back4App · GitHub · NexCloud |
| 13 | **Railway** 🏆 | حساب **مسجّل مسبقًا على الجهاز** (Railway CLI + `~/.railway/config.json`) — نشر Dockerfile مباشرة بأمر `railway up` | ✅ **نجح بالكامل** | المشروع: `quran-unified-bot` · الخدمة: `quran-unified` · النشر الناجح `36462bac-74df-4797-a7ae-2e8ceae970d4` (SUCCESS/RUNNING) · الرابط العام: <https://quran-unified-production-6645.up.railway.app> (HTTP 200: "quran-unified OK uptime=345s") · تفاصيل كاملة في `docs/RAILWAY_DEPLOY.md` |

## الخلاصة (محدّثة 2026-09-29)
- ✅ **تم النشر فعليًا وبنجاح على Railway** — عبر حساب المستخدم المسجّل مسبقًا على الجهاز (بدون بطاقة جديدة، وبدون أي تسجيل دخول جديد).
- البوت يعمل الآن **24/7 سحابيًا**: سجل Railway فيه `[deploy] starting polling…` · ردود حقيقية على Telegram (اختبار 2/2 عبر tools/tg_cloud_check.py) · رابط صحة عام HTTP 200.
- المراقبة: إعادة تشغيل تلقائية من Railway عند الانهيار + مهمة «مراقب بوت القرآن السحابي» داخل AutoClaw كل 30 دقيقة (تفحص الرابط وتعيد النشر عند اللزوم).
- النسخة المحلية: متوقفة عند قصد (لتفادي تعارض getUpdates) — خطوات الرجوع في `docs/RAILWAY_DEPLOY.md`.

## سؤال واحد مطلوب (تم ✅)
تم تسجيل الدخول (Back4App)، ثم اكتمل النشر والتحقق تلقائيًا عبر حساب Railway الموجود على الجهاز — لا حاجة لأي تسجيل إضافي.

## منجز اليوم (Free-tier، بلا بطاقة)
- 🟢 **صفحة حالة عامة مُستضافة على Cloudflare Workers**: <https://quran-unified-status.zikaquran.workers.dev> (HTTP 200 ✓)
