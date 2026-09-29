# -*- coding: utf-8 -*-
"""خدمات المنطق: القرآن، التفسير، البحث، المواقيت، الحديث، الإذاعات، الصوت، الفيديو."""
import os
import random
import subprocess
import tempfile

from .config import settings, RECITERS
from .util import http_json, ExternalError, log
from .content import islamic_data as DATA

# ---------------------------------------------------------------- القرآن
AYAH_API = "https://api.alquran.cloud/v1/ayah/{ref}/quran-uthmani"
TAFSIR_MUYASSAR = "https://api.alquran.cloud/v1/ayah/{ref}/ar.muyassar"
SURAH_API = "https://api.alquran.cloud/v1/surah/{n}/quran-uthmani"
SEARCH_API = "https://api.alquran.cloud/v1/search/{kw}/all/ar"
QURAN_COM_TAFSIR = "https://api.quran.com/api/v4/quran/tafsirs/817?verse_key={ref}"

CDN_SURAH = "https://cdn.islamic.network/quran/audio-surah/128/{reciter}/{n}.mp3"
CDN_AYAH = "https://cdn.islamic.network/quran/audio/128/{reciter}/{gnum}.mp3"
EVERYAYAH = "https://everyayah.com/data/{folder}/{surah:03d}{ayah:03d}.mp3"

# أكواد قارئي cdn.islamic.network للتلاوة بالسورة
CDN_RECITERS = {
    "maher": "ar.mahermuaiqly",
    "husary": "ar.husary",
    "minshawi": "ar.minshawimujawwad",
    "abdulbasit": "ar.abdulbasitmurattal",
    "sudais": "ar.abdurrahmaansudais",
    "shuraym": "ar.saoodshuraym",
    "ghamdi": "ar.saadalghamdi",
    "ajamy": "ar.ahmedajamy",
}


def surah_name(n: int) -> str:
    if 1 <= n <= 114:
        return DATA.SURAH_NAMES[n - 1]
    return str(n)


def normalize_ref(ref: str):
    ref = (ref or "").strip().replace("/", ":").replace(" ", "")
    if not ref:
        raise ValueError("المرجع فارغ — اكتب مثل: 2:255")
    if ":" not in ref:
        raise ValueError("الصيغة يجب أن تكون سورة:آية (مثال: 2:255)")
    s, a = ref.split(":", 1)
    if not s.isdigit() or not a.isdigit():
        raise ValueError("استخدم أرقامًا فقط بصيغة سورة:آية (مثال: 2:255)")
    s, a = int(s), int(a)
    if not 1 <= s <= 114:
        raise ValueError("رقم السورة يجب أن يكون بين 1 و 114")
    if not 1 <= a <= 286:
        raise ValueError("رقم الآية غير منطقي (1-286)")
    return f"{s}:{a}"


def get_ayah(ref: str):
    data = http_json(AYAH_API.format(ref=ref), service="AlQuran.Cloud")
    d = data.get("data") or {}
    return {
        "ref": ref,
        "surah": d.get("surah", {}).get("number"),
        "ayah": d.get("numberInSurah"),
        "text": d.get("text", ""),
        "surah_name": d.get("surah", {}).get("name", ""),
    }


def get_surah(n: int):
    data = http_json(SURAH_API.format(n=int(n)), service="AlQuran.Cloud")
    d = data.get("data") or {}
    ayahs = [{"num": a["numberInSurah"], "text": a["text"]} for a in d.get("ayahs", [])]
    return {"number": n, "name": d.get("name", surah_name(n)), "ayahs": ayahs}


def get_tafsir(ref: str):
    data = http_json(TAFSIR_MUYASSAR.format(ref=ref), service="AlQuran.Tafsir")
    return (data.get("data") or {}).get("text", "")


def get_tafsir_quran_com(ref: str):
    data = http_json(QURAN_COM_TAFSIR.format(ref=ref), service="Quran.com")
    t = data.get("tafsirs") or []
    return t[0].get("text", "") if t else ""


def search_quran(kw: str, limit: int = 10):
    data = http_json(SEARCH_API.format(kw=kw), service="AlQuran.Search")
    d = data.get("data") or {}
    out = []
    for m in (d.get("matches") or [])[:limit]:
        out.append({
            "ref": f'{m["surah"]["number"]}:{m["numberInSurah"]}',
            "surah_name": m["surah"]["name"],
            "text": m["text"],
        })
    return out


def random_ayah():
    n = random.randint(1, 114)
    s = get_surah(n)
    if not s["ayahs"]:
        raise ExternalError("AlQuran.Cloud", "سورة فارغة")
    a = random.choice(s["ayahs"])
    return {"ref": f"{n}:{a['num']}", "surah_name": s["name"], "text": a["text"]}


# ---------------------------------------------------------------- الصوت
def ayah_audio_url(surah: int, ayah: int, reciter: str = None):
    folder = RECITERS.get(reciter or settings.DEFAULT_RECITER, RECITERS["maher"])[1]
    return EVERYAYAH.format(folder=folder, surah=int(surah), ayah=int(ayah))


def surah_audio_urls(n: int, reciter: str = None):
    """يعيد قائمة مرشّحين لصوت السورة (بالترتيب)."""
    code = CDN_RECITERS.get(reciter or settings.DEFAULT_RECITER, CDN_RECITERS["maher"])
    return [CDN_SURAH.format(reciter=code, n=int(n))]


def _reachable(url: str) -> bool:
    try:
        import requests
        r = requests.head(url, timeout=8, allow_redirects=True)
        return r.status_code == 200
    except Exception:  # noqa: BLE001
        return False


def resolve_surah_audio(n: int, reciter: str = None):
    for u in surah_audio_urls(n, reciter):
        if _reachable(u):
            return u
    return None


# ---------------------------------------------------------------- الإذاعات
def mp3quran_radios():
    data = http_json("https://mp3quran.net/api/v3/radios?language=ar", service="MP3Quran")
    return data.get("radios", [])


def mp3quran_reciters():
    data = http_json("https://mp3quran.net/api/v3/reciters?language=ar", service="MP3Quran")
    return data.get("reciters", [])


# ---------------------------------------------------------------- المواقيت
def prayer_times(city: str, country: str = None):
    from urllib.parse import quote
    url = ("https://api.aladhan.com/v1/timingsByCity?city=" + quote(city) +
           "&country=" + quote(country or settings.DEFAULT_COUNTRY) + "&method=5")
    data = http_json(url, service="AlAdhan")
    d = data.get("data") or {}
    return {"timings": d.get("timings", {}), "date": (d.get("date") or {}).get("readable", "")}


# ---------------------------------------------------------------- الحديث
def dorar_search(text: str):
    from urllib.parse import quote
    url = "https://dorar.net/dorar_api.json?skey=" + quote(text)
    data = http_json(url, service="Dorar")
    return data.get("ahadith", {}).get("result", "")


# ---------------------------------------------------------------- الأذكار (محتوى ثابت من islamic_data)
def adhkar_categories():
    return list(getattr(DATA, "ADHKAR", {}).keys())


def adhkar(key: str):
    return getattr(DATA, "ADHKAR", {}).get(key, [])


# ---------------------------------------------------------------- محتوى محلي (مأخوذ كما هو من المشاريع الأصلية)
import json
from pathlib import Path

_CONTENT = Path(__file__).resolve().parent / "content"


def _load_json(name, default):
    try:
        return json.loads((_CONTENT / name).read_text(encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        log.warning("content %s missing: %s", name, e)
        return default


ADHKAR = _load_json("adhkar.json", {"morning": [], "evening": []})
DUAS = _load_json("duas.json", [])
HADITHS = _load_json("hadiths.json", [])
VERSES = _load_json("verses.json", [])


def adhkar_categories():
    return list(ADHKAR.keys()) or list(getattr(DATA, "ADHKAR", {}).keys())


def adhkar(key: str):
    if key in ADHKAR:
        return ADHKAR[key]
    return getattr(DATA, "ADHKAR", {}).get(key, [])


def duas():
    return DUAS


def daily_hadith():
    return random.choice(HADITHS) if HADITHS else None


def daily_verse():
    return random.choice(VERSES) if VERSES else None


def build_quiz(topic: str, count: int = 5):
    """يبني أسئلة اختيار من متعدد من محتوى المشروع الأصلي (تجويد/متشابهات/سيرة) دون اختلاق أي نص."""
    pool = []
    if topic == "تجويد":
        rules = getattr(DATA, "TAJWEED_RULES", [])
        names = [r[0] for r in rules]
        for name, rule, example, note in rules:
            others = [n for n in names if n != name][:3]
            if len(others) < 3:
                continue
            pool.append({"q": f"أي قاعدة تنطبق على المثال: ‹{example}›؟", "answer": name,
                         "options": [name] + others, "topic": topic})
    elif topic == "متشابهات":
        pairs = getattr(DATA, "SIMILAR_PAIRS", [])
        refs = [p[1] for p in pairs]
        for verse, ref in pairs:
            others = [x for x in refs if x != ref][:3]
            if len(others) < 3:
                continue
            pool.append({"q": f"أين وردت هذه الآية: ‹{verse[:45]}…›؟", "answer": ref,
                         "options": [ref] + others, "topic": topic})
    elif topic == "سيرة":
        seerah = getattr(DATA, "SEERAH", [])
        events = [e[1] for e in seerah]
        for date, ev in seerah:
            others = [x for x in events if x != ev][:3]
            if len(others) < 3:
                continue
            pool.append({"q": f"ما الحدث المرتبط بـ {date} في السيرة؟", "answer": ev,
                         "options": [ev] + others, "topic": topic})
    random.shuffle(pool)
    out = []
    for item in pool[:count]:
        opts = item["options"][:]
        random.shuffle(opts)
        out.append({"q": item["q"], "answer": item["answer"], "options": opts, "topic": topic})
    return out


QUIZ_TOPICS = ["تجويد", "متشابهات", "سيرة"]


# ---------------------------------------------------------------- آيات حسب الحالة (نص قرآني حقيقي من المصدر)
MOODS = {
    "😢 حزن": "لا تحزن",
    "😰 قلق": "تطمئن",
    "🤲 شكر": "لئن شكرتم",
    "😔 ضيق": "العسر يسرا",
    "🌅 أمل": "ورحمة",
    "😨 خوف": "لا تخف",
}


def mood_ayahs(mood: str, limit: int = 3):
    kw = MOODS.get(mood)
    if not kw:
        return []
    return search_quran(kw, limit)


# ---------------------------------------------------------------- أذكار النوم (تُبنى من نص قرآني من الـAPI + أعداد تسبيح ثابتة)
def sleep_adhkar_items():
    items = []
    try:
        items.append({"text": get_ayah("2:255")["text"], "count": 1,
                      "note": "آية الكرسي — من قالها حين يأوي إلى فراشه"})
    except Exception:  # noqa: BLE001
        pass
    for s in (112, 113, 114):
        try:
            items.append({"text": get_ayah(f"{s}:1")["text"].split("\n")[0], "count": 3,
                          "note": f"سورة {surah_name(s)} — تُقرأ ثلاثًا"})
        except Exception:  # noqa: BLE001
            pass
    items.append({"text": "سُبْحَانَ اللهِ", "count": 33, "note": "تسبيح"})
    items.append({"text": "الْحَمْدُ لِلَّهِ", "count": 33, "note": "تحميد"})
    items.append({"text": "اللهُ أَكْبَرُ", "count": 34, "note": "تكبير"})
    return items


# ---------------------------------------------------------------- فهرس الشيوخ (MP3Quran)
def reciter_index():
    recs = mp3quran_reciters()
    out = []
    for r in recs:
        moshaf = (r.get("moshaf") or [{}])[0]
        server = (moshaf.get("server") or "").rstrip("/")
        if server:
            out.append({"id": r.get("id"), "name": r.get("name", ""), "server": server,
                        "surahs": moshaf.get("surah_total") or moshaf.get("surah_list", "")})
    return out


def reciter_surah_url(server: str, surah: int):
    return f"{server.rstrip('/')}/{int(surah):03d}.mp3"


def radio_stations(limit: int = 60):
    out = []
    for r in mp3quran_radios()[:limit]:
        if r.get("url"):
            out.append({"id": r.get("id"), "name": r.get("name", "إذاعة"), "url": r["url"]})
    return out


# ---------------------------------------------------------------- الزكاة
def zakat_for(amount: float):
    return round(float(amount) * 0.025, 2)


# ---------------------------------------------------------------- الفيديو/الصورة
def render_ayah_image(text: str, out_path: str, surah_label: str = "", size=(1080, 1080)):
    """يرسم الآية على صورة PNG. يحاول تشكيل العربية إن توفّرت المكتبات، وإلا يكتب النص كما هو."""
    try:
        from PIL import Image, ImageDraw, ImageFont
    except Exception as e:  # noqa: BLE001
        raise ExternalError("Pillow", str(e))
    reshaped = text
    try:
        import arabic_reshaper
        from bidi.algorithm import get_display
        reshaped = get_display(arabic_reshaper.reshape(text))
    except Exception:  # noqa: BLE001
        pass
    img = Image.new("RGB", size, (12, 26, 38))
    d = ImageDraw.Draw(img)
    font = None
    for fp in [r"C:\Windows\Fonts\amiri-regular.ttf", r"C:\Windows\Fonts\tahoma.ttf",
               r"C:\Windows\Fonts\arial.ttf"]:
        if os.path.exists(fp):
            try:
                font = ImageFont.truetype(fp, 46 if "amiri" in fp else 40)
                break
            except Exception:  # noqa: BLE001
                continue
    if font is None:
        font = ImageFont.load_default()
    # لفّ النص يدويًا
    words, lines, cur = reshaped.split(), [], ""
    for w in words:
        if d.textlength(cur + " " + w, font=font) > size[0] - 120:
            lines.append(cur.strip()); cur = w
        else:
            cur += " " + w
    if cur.strip():
        lines.append(cur.strip())
    y = 120
    for ln in lines:
        w = d.textlength(ln, font=font)
        d.text(((size[0] - w) / 2, y), ln, font=font, fill=(240, 245, 250))
        y += 66
    if surah_label:
        sf = ImageFont.truetype(r"C:\Windows\Fonts\tahoma.ttf", 30) if os.path.exists(
            r"C:\Windows\Fonts\tahoma.ttf") else font
        w = d.textlength(surah_label, font=sf)
        d.text(((size[0] - w) / 2, size[1] - 110), surah_label, font=sf, fill=(180, 200, 220))
    img.save(out_path, "PNG")
    return out_path


def make_ayah_video(text, audio_path, out_path, surah_label="", size=(1080, 1080)):
    """يبني MP4 من صورة ثابتة + صوت الآية عبر ffmpeg. يعيد مسار الفيديو أو يرفع استثناء."""
    img = out_path + ".png"
    render_ayah_image(text, img, surah_label, size)
    ffmpeg = "ffmpeg"
    cmd = [ffmpeg, "-y", "-loop", "1", "-i", img, "-i", audio_path,
           "-c:v", "libx264", "-tune", "stillimage", "-c:a", "aac", "-b:a", "128k",
           "-pix_fmt", "yuv420p", "-shortest", out_path]
    try:
        subprocess.run(cmd, check=True, capture_output=True, timeout=120)
    except FileNotFoundError:
        raise ExternalError("ffmpeg", "غير مثبّت على الجهاز")
    except subprocess.CalledProcessError as e:
        raise ExternalError("ffmpeg", (e.stderr or b"")[:120].decode("utf-8", "ignore"))
    return out_path


def download(url: str, dest: str, timeout=30):
    import requests
    r = requests.get(url, timeout=timeout)
    r.raise_for_status()
    with open(dest, "wb") as f:
        f.write(r.content)
    return dest
