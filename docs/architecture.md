# الهيكل وتدفّق البيانات

## شجرة المشروع
```
quran-unified/
├─ app/
│  ├─ main.py            نقطة الدخول: بناء التطبيق + المهام الدورية + --check
│  ├─ config.py          قارئ .env مدمج + الإعدادات + قائمة القرّاء
│  ├─ util.py            سجلات دوّارة + HTTP آمن + معرّف طلب (trace) + رسائل خطأ عربية
│  ├─ db.py              طبقة SQLite الموحّدة (مستخدمون/طلبات/أحداث/حفظ/ختمة/مسابقات/كاش/أخطاء)
│  ├─ services.py        منطق الخدمات: القرآن، التفسير، البحث، المواقيت، الحديث، الإذاعات، الصوت، الفيديو
│  ├─ keyboards.py       لوحات الأزرار (Inline)
│  ├─ content/           محتوى ثابت كما هو من المصادر (islamic_data.py + JSON)
│  └─ handlers/
│     ├─ start.py        /start · القوائم · الإعدادات · الإحصاءات · النص الحر
│     ├─ quran.py        /surah /ayah /tafsir /search /random /play /radios + Inline
│     ├─ worship.py      /prayer /city /adhkar /duas /hadith /sajda
│     └─ advanced.py     الحفظ · التسميع · الختمة · المسابقات · الفيديو
├─ content/…             (يُقرأ من app/content)
├─ tests/selftest.py     اختبار ذاتي شامل (49 اختبارًا)
├─ docs/                 الجرد · التغطية · الأخطاء · الأوامر · التشغيل · الاختبار · الهيكل · الرجوع
├─ backups/pre-merge-*/  نسخة ما قبل الدمج + manifest.json (SHA256)
├─ data/                 قاعدة البيانات (تُنشأ تلقائيًا)
├─ logs/                 bot.log (دوّار) + bot.out.log + bot.err.log + bot.pid
├─ .env / .env.example
├─ requirements.txt
└─ run.bat · start_background.bat · stop.bat
```

## تدفّق الطلب (قابل للتتبع)
```
تليجرام (Update)
   ↓
Handler مُغلّف بـ @trace
   ├─ توليد req_id (12 حرفًا)
   ├─ db.log_request(req_id, user, kind, handler)
   ├─ تنفيذ المنطق عبر services
   │     └─ http_json → ExternalError عند الفشل
   ├─ نجاح: db.finish_request(req_id, "ok")
   └─ فشل: db.finish_request(req_id, "<status>", error) + رسالة عربية للمستخدم
   ↓
الرد للمستخدم
```
- **معرّف الطلب** يُسجَّل لكل تفاعل ويمكن رؤيته في `/stats`.
- أي خطأ يُكتب في جدول `errors` مع `req_id` وسياقه.

## المهام الدورية (JobQueue)
| المهمة | التوقيت | الوظيفة |
|---|---|---|
| `daily_ayah` | يوميًا (DAILY_AYAH_HOUR، افتراضي 8ص) | إرسال آية اليوم للمشتركين |
| `daily_adhkar` | يوميًا (DAILY_ADHKAR_HOUR:30، افتراضي 6:30م) | أذكار المساء للمشتركين |
| `prayer_reminder` | كل 5 دقائق | تنبيه الصلاة لمن فعّل التنبيه |

## طبقة التخزين (SQLite)
جداول: `users`, `requests`, `events`, `hifz`, `hifz_plan`, `khatma`, `khatma_members`,
`quiz_scores`, `cache`, `errors` — كلها في ملف `data/quran_unified.db` (WAL).

## مصادر البيانات الخارجية
| الخدمة | الاستخدام |
|---|---|
| api.alquran.cloud | نص القرآن (عثماني)، التفسير الميسر، البحث، السور |
| api.quran.com | التفسير (ابن كثير 817) — محاولة ثانوية |
| api.aladhan.com | مواقيت الصلاة |
| dorar.net | التحقق من الأحاديث |
| everyayah.com / cdn.islamic.network | صوت الآيات والسور |
| mp3quran.net | قائمة الإذاعات والقرّاء |

## المرونة (Fallbacks)
- صوت السورة غير متاح ⇒ يتراجع لصوت الآية الأولى.
- فيديو غير متاح (ffmpeg) ⇒ صورة الآية + الصوت.
- تشكيل العربية غير متاح ⇒ صورة بعربية غير مشكّلة + إرشاد التثبيت.
- تفسير ابن كثير يفشل ⇒ التفسير الميسر يكفي.
