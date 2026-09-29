# -*- coding: utf-8 -*-
"""تسجيل كل المعالجات في تطبيق واحد."""
from . import start, quran, worship, advanced, extra


def register_all(app):
    start.register(app)
    quran.register(app)
    worship.register(app)
    advanced.register(app)
    extra.register(app)
