# بوت القرآن الموحّد (Quran Unified)

دمج كل بوتات القرآن الموجودة على الجهاز في **بوت واحد**، مع مراجعة الأخطاء وتصحيحها، وتشغيل محلي جاهز للتجربة.

- **البوت:** `@iQuranOfficial_Bot` · **الإطار:** python-telegram-bot 22.8 · **التخزين:** SQLite
- **حالة التشغيل المحلي:** يعمل بنجاح (polling) — راجع `logs/`.

## تشغيل سريع
```powershell
cd C:\Users\af191\.openclaw-autoclaw\workspace\projects\quran-unified
C:\Python314\python.exe -m app.main --check      # فحص سريع
.\run.bat                                         # تشغيل
.\stop.bat                                        # إيقاف
```
بديل الاختبار بدون تليجرام: `C:\Python314\python.exe tests\selftest.py`
اختبار المسارات الاستثنائية: `C:\Python314\python.exe tests\failure_paths.py`

## الوثائق
| الملف | المحتوى |
|---|---|
| `docs/BOT_INVENTORY.md` | جرد كل بوتات القرآن قبل الدمج |
| `docs/FEATURE_COVERAGE.md` | مصفوفة التغطية (ما دُمج/ما أُجّل ولماذا) |
| `docs/ERROR_REVIEW.md` | كل خطأ + سببه + إصلاحه + دليل الزوال |
| `docs/FAILURE_PATHS.md` | معالجة المسارات الاستثنائية + إثبات 20/20 اختبارًا |
| `docs/ACCEPTANCE_MATRIX.md` | مصفوفة القبول: كل معيار + دليله (12/12) |
| `docs/E2E_TEST_REPORT.md` | اختبار حقيقي على تليجرام: 34/34 أمرًا + الأخطاء المكتشفة (E-14..E-17) |
| `docs/COMMANDS.md` | قائمة الأوامر النهائية |
| `docs/RUN_GUIDE.md` | دليل التشغيل + حلول الأخطاء الشائعة |
| `docs/TEST_PACK.md` | 38 اختبارًا يدويًا لتجربتك |
| `docs/ARCHITECTURE.md` | الهيكل وتدفّق البيانات |
| `docs/ROLLBACK.md` | النسخة الاحتياطية وخطة الرجوع |
| `docs/INDEX.html` | صفحة فهرس مقروءة (افتحها في المتصفّح) |

## بنية مختصرة
```
app/ (main, config, util, db, services, keyboards, handlers/, content/)
tests/selftest.py · docs/ · backups/ · data/ · logs/ · .env
```

## ملاحظات
- **قراءة فقط على المصادر:** لم يُعدَّل أي ملف في المشاريع الأصلية؛ كل شيء في مشروع مستقل + نسخة احتياطية في `backups/pre-merge-*/`.
- **سلامة المحتوى:** نصوص القرآن من `api.alquran.cloud` كما هي؛ الأذكار/الأحاديث/الآيات منقولة كملفات JSON دون تغيير.
- **الأسرار:** التوكن في `.env` فقط (مستثنى من git)؛ اللوجات لا تُسجّل التوكن.
