# دليل النشر المجاني (قابل للتكرار)

البوت: `quran-unified-bot` · المستودع: <https://github.com/Zika11/quran-unified-bot> · ملف التشغيل: `deploy/start.py` (يشغّل خادم صحة على `$PORT` + البوت).

## الخيار المُوصى به: Hugging Face Spaces (Docker — مجاني، بلا بطاقة، يعمل باستمرار)
1. أنشئ توكن HF (صلاحية **write**): <https://huggingface.co/settings/tokens>
2. نفّذ من جذر المشروع:
   ```powershell
   C:\Python314\python.exe deploy\hf_deploy.py hf_xxxxxxxxxxxxxxxxx
   ```
   السكربت ينشئ Space (docker) ويرفع الملفات ويضبط السر `BOT_TOKEN` من `.env` ويحدّد `KEEPALIVE_URL`.
3. انتظر البناء (Build) من تبويب الـSpace، ثم تأكد:
   ```powershell
   curl https://<user>-quran-unified-bot.hf.space      # يعيد: quran-unified OK uptime=...
   ```
4. البوت يعمل الآن على كل رسائل تليجرام. **مهم:** أوقف النسخة المحلية أولًا لتفادي تعارض polling:
   ```powershell
   .\stop.bat      # في مجلد المشروع المحلي
   ```

**متغيرات البيئة المطلوبة (أسماء فقط، لا قيم):**
`BOT_TOKEN` (إلزامي) · `OWNER_IDS` · `TIMEZONE` · `DEFAULT_CITY` · `DEFAULT_RECITER` · `VIDEO_ENABLED` · `PORT`.

## الخيار 2: Back4App Containers
1. من لوحة Back4App: **Containers → Create new app → GitHub** واختر المستودع `Zika11/quran-unified-bot` والفرع `main` (Dockerfile موجود).
2. Environment Variables: أضف `BOT_TOKEN` (وربما `PORT`).
3. Health check: المسار `/` على منفذ التطبيق (يعمل من `deploy/start.py`).
4. تأكد من تشغيل **Auto-deploy** عند كل push.

## الخيار 3: Render (يحتاج بطاقة للتحقق)
- Web Service → Docker → المستودع أدناه → Health Check Path: `/` → Env: `BOT_TOKEN`.

## ملاحظات مهمة
- **لا تُشغّل نسختين بنفس التوكن** (سيحدث `Conflict: terminated by other getUpdates`). أوقف المحلية عند تشغيل السحابة.
- **التخزين:** على المنصّات ذات القرص الدائم، اضبط `DATA_DIR=/data` و`DB_PATH=/data/quran_unified.db` (يدعمها Dockerfile).
- **الخمول:** HF Spaces المجانية تنام بعد ~48 ساعة بلا طلب؛ البوت يتلقى تحديثات تليجرام باستمرار (نشاط) ويمكن إضافة نبض ذاتي عبر `KEEPALIVE_URL`.
- **الأسرار:** دائماً عبر متغيرات بيئة/Secrets، لا داخل المستودع.

## التحقق بعد النشر
```powershell
curl https://<host>/                       # 200 + uptime
curl "https://api.telegram.org/bot<TOKEN>/getMe"        # تأكيد التوكن
curl "https://api.telegram.org/bot<TOKEN>/getWebhookInfo"  # لا ويب هوك (polling)
```
ثم أرسل `/start` إلى البوت من تليجرام وتأكد من الرد.
