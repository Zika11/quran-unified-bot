# -*- coding: utf-8 -*-
"""طبقة التخزين الموحّدة (SQLite): المستخدمون، الطلبات، الأحداث، الحفظ، الختمة، المسابقات، الكاش، الأخطاء."""
import sqlite3
import json
import time
from datetime import datetime, timezone
from pathlib import Path

from .config import settings

SCHEMA = """
PRAGMA journal_mode=WAL;

CREATE TABLE IF NOT EXISTS users (
    user_id     INTEGER PRIMARY KEY,
    username    TEXT,
    first_name  TEXT,
    city        TEXT,
    country     TEXT,
    reciter     TEXT DEFAULT 'maher',
    notify_ayah INTEGER DEFAULT 1,
    notify_adhkar INTEGER DEFAULT 0,
    notify_prayer INTEGER DEFAULT 0,
    created_at  TEXT,
    last_seen   TEXT
);

CREATE TABLE IF NOT EXISTS requests (
    req_id      TEXT PRIMARY KEY,
    user_id     INTEGER,
    kind        TEXT,
    handler     TEXT,
    status      TEXT DEFAULT 'running',
    error       TEXT,
    started_at  TEXT,
    finished_at TEXT
);

CREATE TABLE IF NOT EXISTS events (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER,
    req_id      TEXT,
    kind        TEXT,
    payload     TEXT,
    created_at  TEXT
);

CREATE TABLE IF NOT EXISTS hifz (
    user_id     INTEGER,
    surah       INTEGER,
    ayah        INTEGER,
    status      TEXT DEFAULT 'new',   -- new | memorized | reviewing
    updated_at  TEXT,
    PRIMARY KEY (user_id, surah, ayah)
);

CREATE TABLE IF NOT EXISTS hifz_plan (
    user_id     INTEGER PRIMARY KEY,
    daily       INTEGER DEFAULT 3,
    start_surah INTEGER DEFAULT 78,
    created_at  TEXT
);

CREATE TABLE IF NOT EXISTS khatma (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    owner_id    INTEGER,
    title       TEXT,
    parts       INTEGER DEFAULT 30,
    status      TEXT DEFAULT 'open',  -- open | done
    created_at  TEXT
);

CREATE TABLE IF NOT EXISTS khatma_members (
    khatma_id   INTEGER,
    user_id     INTEGER,
    part        INTEGER,
    done        INTEGER DEFAULT 0,
    updated_at  TEXT,
    PRIMARY KEY (khatma_id, user_id)
);

CREATE TABLE IF NOT EXISTS quiz_scores (
    user_id     INTEGER,
    topic       TEXT,
    correct     INTEGER DEFAULT 0,
    wrong       INTEGER DEFAULT 0,
    updated_at  TEXT,
    PRIMARY KEY (user_id, topic)
);

CREATE TABLE IF NOT EXISTS cache (
    key         TEXT PRIMARY KEY,
    value       TEXT,
    created_at  REAL
);

CREATE TABLE IF NOT EXISTS errors (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    req_id      TEXT,
    where_      TEXT,
    message     TEXT,
    created_at  TEXT
);

CREATE TABLE IF NOT EXISTS channel_links (
    user_id     INTEGER,
    chat_id     INTEGER,
    title       TEXT,
    created_at  TEXT,
    PRIMARY KEY (user_id, chat_id)
);

CREATE TABLE IF NOT EXISTS radio_state (
    chat_id     INTEGER PRIMARY KEY,
    station_id  TEXT,
    name        TEXT,
    url         TEXT,
    updated_at  TEXT
);
"""


def now_iso():
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


class DB:
    def __init__(self, path: Path = None):
        settings.ensure_dirs()
        self.path = str(path or settings.DB_PATH)
        self.conn = sqlite3.connect(self.path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(SCHEMA)
        self.conn.commit()

    # ---------------------------------------------------------- users
    def upsert_user(self, user_id, username=None, first_name=None):
        self.conn.execute(
            """INSERT INTO users(user_id, username, first_name, city, country, created_at, last_seen)
               VALUES(?,?,?,?,?,?,?)
               ON CONFLICT(user_id) DO UPDATE SET
                 username=excluded.username, first_name=excluded.first_name, last_seen=excluded.last_seen""",
            (user_id, username, first_name, settings.DEFAULT_CITY, settings.DEFAULT_COUNTRY, now_iso(), now_iso()))
        self.conn.commit()

    def user(self, user_id):
        self.upsert_user(user_id)
        row = self.conn.execute("SELECT * FROM users WHERE user_id=?", (user_id,)).fetchone()
        return dict(row) if row else None

    def set_user(self, user_id, **kw):
        if not kw:
            return
        cols = ", ".join(f"{k}=?" for k in kw)
        self.conn.execute(f"UPDATE users SET {cols} WHERE user_id=?", (*kw.values(), user_id))
        self.conn.commit()

    def subscribers(self, column):
        rows = self.conn.execute(f"SELECT user_id FROM users WHERE {column}=1").fetchall()
        return [r["user_id"] for r in rows]

    def all_users(self):
        return [dict(r) for r in self.conn.execute("SELECT * FROM users").fetchall()]

    # ---------------------------------------------------------- requests / logs
    def log_request(self, req_id, user_id, kind, handler):
        self.conn.execute(
            "INSERT OR REPLACE INTO requests(req_id,user_id,kind,handler,status,started_at) VALUES(?,?,?,?,?,?)",
            (req_id, user_id, kind, handler, "running", now_iso()))
        self.conn.commit()

    def finish_request(self, req_id, status, error=None):
        self.conn.execute(
            "UPDATE requests SET status=?, error=?, finished_at=? WHERE req_id=?",
            (status, error, now_iso(), req_id))
        if error:
            self.conn.execute("INSERT INTO errors(req_id, where_, message, created_at) VALUES(?,?,?,?)",
                              (req_id, "handler", error, now_iso()))
        self.conn.commit()

    def event(self, user_id, req_id, kind, payload=None):
        self.conn.execute("INSERT INTO events(user_id,req_id,kind,payload,created_at) VALUES(?,?,?,?,?)",
                          (user_id, req_id, kind, json.dumps(payload, ensure_ascii=False) if payload else None, now_iso()))
        self.conn.commit()

    def last_requests(self, limit=20):
        return [dict(r) for r in self.conn.execute(
            "SELECT * FROM requests ORDER BY started_at DESC LIMIT ?", (limit,)).fetchall()]

    def errors_count(self):
        return self.conn.execute("SELECT COUNT(*) c FROM errors").fetchone()["c"]

    def stats(self):
        q = self.conn.execute
        return {
            "users": q("SELECT COUNT(*) c FROM users").fetchone()["c"],
            "requests": q("SELECT COUNT(*) c FROM requests").fetchone()["c"],
            "errors": q("SELECT COUNT(*) c FROM errors").fetchone()["c"],
            "khatmas": q("SELECT COUNT(*) c FROM khatma").fetchone()["c"],
            "hifz_rows": q("SELECT COUNT(*) c FROM hifz").fetchone()["c"],
        }

    # ---------------------------------------------------------- hifz
    def hifz_plan(self, user_id):
        row = self.conn.execute("SELECT * FROM hifz_plan WHERE user_id=?", (user_id,)).fetchone()
        return dict(row) if row else None

    def set_hifz_plan(self, user_id, daily, start_surah):
        self.conn.execute(
            """INSERT INTO hifz_plan(user_id,daily,start_surah,created_at) VALUES(?,?,?,?)
               ON CONFLICT(user_id) DO UPDATE SET daily=excluded.daily, start_surah=excluded.start_surah""",
            (user_id, daily, start_surah, now_iso()))
        self.conn.commit()

    def hifz_set(self, user_id, surah, ayah, status):
        self.conn.execute(
            """INSERT INTO hifz(user_id,surah,ayah,status,updated_at) VALUES(?,?,?,?,?)
               ON CONFLICT(user_id,surah,ayah) DO UPDATE SET status=excluded.status, updated_at=excluded.updated_at""",
            (user_id, surah, ayah, status, now_iso()))
        self.conn.commit()

    def hifz_list(self, user_id):
        return [dict(r) for r in self.conn.execute(
            "SELECT * FROM hifz WHERE user_id=? ORDER BY surah, ayah", (user_id,)).fetchall()]

    def hifz_counts(self, user_id):
        rows = self.conn.execute(
            "SELECT status, COUNT(*) c FROM hifz WHERE user_id=? GROUP BY status", (user_id,)).fetchall()
        return {r["status"]: r["c"] for r in rows}

    # ---------------------------------------------------------- khatma
    def khatma_create(self, owner_id, title, parts=30):
        cur = self.conn.execute(
            "INSERT INTO khatma(owner_id,title,parts,status,created_at) VALUES(?,?,?,?,?)",
            (owner_id, title, parts, "open", now_iso()))
        self.conn.commit()
        return cur.lastrowid

    def khatma_join(self, khatma_id, user_id, part):
        self.conn.execute(
            """INSERT INTO khatma_members(khatma_id,user_id,part,done,updated_at) VALUES(?,?,?,0,?)
               ON CONFLICT(khatma_id,user_id) DO UPDATE SET part=excluded.part""",
            (khatma_id, user_id, part, now_iso()))
        self.conn.commit()

    def khatma_done(self, khatma_id, user_id):
        self.conn.execute("UPDATE khatma_members SET done=1, updated_at=? WHERE khatma_id=? AND user_id=?",
                          (now_iso(), khatma_id, user_id))
        self.conn.commit()

    def khatma_get(self, khatma_id):
        row = self.conn.execute("SELECT * FROM khatma WHERE id=?", (khatma_id,)).fetchone()
        if not row:
            return None
        members = self.conn.execute(
            "SELECT * FROM khatma_members WHERE khatma_id=? ORDER BY part", (khatma_id,)).fetchall()
        d = dict(row)
        d["members"] = [dict(m) for m in members]
        return d

    def khatma_open(self):
        row = self.conn.execute("SELECT * FROM khatma WHERE status='open' ORDER BY id DESC").fetchone()
        return self.khatma_get(row["id"]) if row else None

    def khatma_mine(self, user_id):
        return [dict(r) for r in self.conn.execute(
            """SELECT k.*, m.part, m.done FROM khatma k JOIN khatma_members m ON m.khatma_id=k.id
               WHERE m.user_id=? ORDER BY k.id DESC""", (user_id,)).fetchall()]

    def khatma_taken_parts(self, khatma_id):
        rows = self.conn.execute("SELECT part FROM khatma_members WHERE khatma_id=?", (khatma_id,)).fetchall()
        return {r["part"] for r in rows}

    # ---------------------------------------------------------- quiz
    def quiz_add(self, user_id, topic, correct):
        self.conn.execute(
            """INSERT INTO quiz_scores(user_id,topic,correct,wrong,updated_at) VALUES(?,?,?,?,?)
               ON CONFLICT(user_id,topic) DO UPDATE SET
                 correct=correct+excluded.correct, wrong=wrong+excluded.wrong, updated_at=excluded.updated_at""",
            (user_id, topic, 1 if correct else 0, 0 if correct else 1, now_iso()))
        self.conn.commit()

    def quiz_score(self, user_id, topic):
        row = self.conn.execute("SELECT * FROM quiz_scores WHERE user_id=? AND topic=?",
                                (user_id, topic)).fetchone()
        return dict(row) if row else {"correct": 0, "wrong": 0}

    # ---------------------------------------------------------- cache
    def cache_get(self, key, ttl=3600):
        row = self.conn.execute("SELECT value, created_at FROM cache WHERE key=?", (key,)).fetchone()
        if not row:
            return None
        if time.time() - row["created_at"] > ttl:
            return None
        try:
            return json.loads(row["value"])
        except Exception:  # noqa: BLE001
            return None

    def cache_set(self, key, value):
        self.conn.execute("INSERT OR REPLACE INTO cache(key,value,created_at) VALUES(?,?,?)",
                          (key, json.dumps(value, ensure_ascii=False), time.time()))
        self.conn.commit()

    # ---------------------------------------------------------- channels
    def link_channel(self, user_id, chat_id, title):
        self.conn.execute(
            """INSERT INTO channel_links(user_id,chat_id,title,created_at) VALUES(?,?,?,?)
               ON CONFLICT(user_id,chat_id) DO UPDATE SET title=excluded.title""",
            (user_id, chat_id, title, now_iso()))
        self.conn.commit()

    def unlink_channel(self, user_id, chat_id=None):
        if chat_id is None:
            self.conn.execute("DELETE FROM channel_links WHERE user_id=?", (user_id,))
        else:
            self.conn.execute("DELETE FROM channel_links WHERE user_id=? AND chat_id=?", (user_id, chat_id))
        self.conn.commit()

    def channels_of(self, user_id):
        return [dict(r) for r in self.conn.execute(
            "SELECT * FROM channel_links WHERE user_id=? ORDER BY created_at DESC", (user_id,)).fetchall()]

    def all_channels(self):
        return [dict(r) for r in self.conn.execute("SELECT * FROM channel_links").fetchall()]

    # ---------------------------------------------------------- radio
    def radio_set(self, chat_id, station_id, name, url):
        self.conn.execute(
            """INSERT INTO radio_state(chat_id,station_id,name,url,updated_at) VALUES(?,?,?,?,?)
               ON CONFLICT(chat_id) DO UPDATE SET station_id=excluded.station_id, name=excluded.name, url=excluded.url, updated_at=excluded.updated_at""",
            (chat_id, str(station_id), name, url, now_iso()))
        self.conn.commit()

    def radio_get(self, chat_id):
        row = self.conn.execute("SELECT * FROM radio_state WHERE chat_id=?", (chat_id,)).fetchone()
        return dict(row) if row else None
