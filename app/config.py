# -*- coding: utf-8 -*-
"""إعدادات البوت — تُقرأ من متغيرات البيئة أو ملف .env (بدون أي مكتبات خارجية)."""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / ".env"


def load_env(path: Path = ENV_PATH):
    """قارئ .env بسيط (KEY=VALUE) بدون الاعتماد على python-dotenv."""
    if not path.exists():
        return
    raw_text = path.read_text(encoding="utf-8-sig", errors="ignore")
    for raw in raw_text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        k = k.strip()
        v = v.strip().strip('"').strip("'")
        os.environ.setdefault(k, v)


load_env()


def _int_list(s):
    out = []
    for part in (s or "").replace(",", " ").split():
        try:
            out.append(int(part))
        except ValueError:
            pass
    return out


class Settings:
    BOT_TOKEN: str = os.environ.get("BOT_TOKEN", "").strip()
    OWNER_IDS: list = _int_list(os.environ.get("OWNER_IDS", ""))
    TIMEZONE: str = os.environ.get("TIMEZONE", "Africa/Cairo")
    DEFAULT_CITY: str = os.environ.get("DEFAULT_CITY", "Cairo")
    DEFAULT_COUNTRY: str = os.environ.get("DEFAULT_COUNTRY", "Egypt")
    DEFAULT_RECITER: str = os.environ.get("DEFAULT_RECITER", "maher")
    DAILY_AYAH_HOUR: int = int(os.environ.get("DAILY_AYAH_HOUR", "8"))
    DAILY_HADITH_HOUR: int = int(os.environ.get("DAILY_HADITH_HOUR", "10"))
    DAILY_ADHKAR_HOUR: int = int(os.environ.get("DAILY_ADHKAR_HOUR", "18"))
    DATA_DIR: Path = Path(os.environ.get("DATA_DIR", str(BASE_DIR / "data")))
    DB_PATH: Path = Path(os.environ.get("DB_PATH", str(BASE_DIR / "data" / "quran_unified.db")))
    LOG_DIR: Path = Path(os.environ.get("LOG_DIR", str(BASE_DIR / "logs")))
    PUBLIC_URL: str = os.environ.get("PUBLIC_URL", "https://example.com/webapp")
    HTTP_TIMEOUT: int = int(os.environ.get("HTTP_TIMEOUT", "15"))
    VIDEO_ENABLED: bool = os.environ.get("VIDEO_ENABLED", "1") not in ("0", "false", "False", "")

    @classmethod
    def ensure_dirs(cls):
        cls.DATA_DIR.mkdir(parents=True, exist_ok=True)
        cls.LOG_DIR.mkdir(parents=True, exist_ok=True)
        cls.DB_PATH.parent.mkdir(parents=True, exist_ok=True)


settings = Settings()

# قرّاء متاحون (folder: everyayah) — المحتوى ثابت كما في المصادر
RECITERS = {
    "maher":   ("ماهر المعيقلي", "Maher_AlMuaiqly_64kbps"),
    "husary":  ("محمود خليل الحصري", "Husary_128kbps"),
    "minshawi": ("محمد صديق المنشاوي", "Minshawy_Murattal_128kbps"),
    "abdulbasit": ("عبد الباسط عبد الصمد (مرتل)", "Abdul_Basit_Murattal_192kbps"),
    "sudais":  ("عبد الرحمن السديس", "Abdurrahmaan_As-Sudais_192kbps"),
    "shuraym": ("سعود الشريم", "Saood_ash-Shuraym_128kbps"),
    "ghamdi":  ("سعد الغامدي", "Ghamadi_40kbps"),
    "ajamy":   ("أحمد بن علي العجمي", "Ahmed_ibn_Ali_al-Ajamy_128kbps"),
}
