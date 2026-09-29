# -*- coding: utf-8 -*-
"""كائنات وهمية لاختبار الهاندلرات دون الاتصال بتليجرام."""
import json


class FakeUser:
    def __init__(self, uid=1232067711):
        self.id = uid
        self.username = "tester"
        self.first_name = "Tester"


class FakeMessage:
    def __init__(self):
        self.sent = []

    async def reply_text(self, text, **kw):
        self.sent.append({"kind": "text", "text": text, "markup": kw.get("reply_markup")})

    async def reply_audio(self, audio, **kw):
        self.sent.append({"kind": "audio", "value": str(audio), "caption": kw.get("caption")})

    async def reply_photo(self, photo, **kw):
        self.sent.append({"kind": "photo", "value": "photo", "caption": kw.get("caption")})

    async def reply_video(self, video, **kw):
        self.sent.append({"kind": "video", "value": "video", "caption": kw.get("caption")})


class FakeQuery:
    def __init__(self, user=None):
        self.edits = []
        self.answers = []
        self.message = FakeMessage()
        self.from_user = user or FakeUser()

    async def answer(self, text=None, **kw):
        self.answers.append(text)

    async def edit_message_text(self, text, **kw):
        self.edits.append({"text": text, "markup": kw.get("reply_markup")})


class FakeUpdate:
    def __init__(self, data=None, args=None):
        self.effective_user = FakeUser()
        self.message = FakeMessage()
        self.effective_message = self.message
        self.callback_query = FakeQuery(self.effective_user) if data is not None else None
        if data is not None:
            self.callback_query.data = data


class FakeBot:
    async def send_message(self, *a, **k):
        return None


class FakeApplication:
    def __init__(self, db):
        self.bot_data = {"db": db}
        self.job_queue = None
        self.bot = FakeBot()


class FakeContext:
    def __init__(self, app, args=None):
        self.application = app
        self.user_data = {}
        self.args = args or []
        self.bot = app.bot


def last_text(update):
    """آخر نص أرسله البوت في هذا التحديث (رسالة أو تعديل)، أو وصف المخرج غير النصي."""
    if update.callback_query and update.callback_query.edits:
        return update.callback_query.edits[-1].get("text", "")
    if update.message.sent:
        last = update.message.sent[-1]
        if "text" in last:
            return last["text"]
        return f"[{last.get('kind')}] " + str(last.get("caption") or last.get("value") or "")[:60]
    return ""
