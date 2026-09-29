# مصفوفة القبول — دليل كل معيار

_مُولّدة: 2026-09-28T00:02:02+03:00 · الاختبار الذاتي 49/49 · المسارات الاستثنائية 20/20 · البوت PID 3848 · التوكن صالح: True (@iQuranOfficial_Bot)_

| المعيار | الحالة | الدليل |
|---|---|---|
| كل البوتات مُحصاة وموثّقة | ✅ مُستوفى | `docs/BOT_INVENTORY.md` · `docs/FEATURE_COVERAGE.md` |
| أوامر موحّدة في بوت واحد | ✅ مُستوفى | `docs/COMMANDS.md` · `tests/selftest_report.json (49/49)` |
| لا فقدان لأي وظيفة أصلية | ✅ مُستوفى | `docs/FEATURE_COVERAGE.md` · `selftest handlers/feature tests` |
| مراجعة الأخطاء وتصحيحها | ✅ مُستوفى | `docs/ERROR_REVIEW.md (13 خطأ + إصلاحات)` |
| سلامة النص القرآني | ✅ مُستوفى | `selftest: 'سلامة النص القرآني (مطابقة المصدر)' صحيح` |
| تخزين موحّد | ✅ مُستوفى | `app/db.py` · `data/quran_unified.db` |
| سجلات قابلة للتتبع | ✅ مُستوفى | `logs/bot.log` · `app/util.py @trace` |
| تشغيل محلي ناجح | ✅ مُستوفى | `bot.pid=3848` · `getMe ok → @iQuranOfficial_Bot` · `logs/bot.log` |
| حزمة تجربة جاهزة | ✅ مُستوفى | `docs/TEST_PACK.md (38 اختبارًا)` |
| معالجة المسارات الاستثنائية | ✅ مُستوفى | `docs/FAILURE_PATHS.md` · `tests/failure_paths_report.json (20/20)` · `tests/failure_smoke.json (6/6 in ~5s)` · `tools/e2e_report.json (43/43 on live bot)` · `تشغيل فعلي: network fail / invalid input / spam / no-user update / ffmpeg fallback / bad token` |
| فصل الإعدادات والمفاتيح | ✅ مُستوفى | `.env.example` · `.env (خارج git)` · `فحص أسرار آلي = 0` |
| نسخة احتياطية وخطة رجوع | ✅ مُستوفى | `docs/ROLLBACK.md` · `backups/pre-merge-*/manifest.json (SHA256)` |

**النتيجة: 12/12 معيار مستوفى بدليل قابل للفحص.**
