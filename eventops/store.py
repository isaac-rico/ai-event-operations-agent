"""Synthetic event snapshot and private, local operator memory."""
import os
import sqlite3
from contextlib import contextmanager
from datetime import date

AS_OF = date(2026, 11, 19)
EVENTS = [
    ("summit", "Systems Summit", 120, 84, 3, "2026-11-30", "Catering guarantee", "2026-11-21"),
    ("lab", "Sensor Lab", 40, 40, 2, "2026-11-27", "Ship demo kits", "2026-11-18"),
    ("forum", "Data Forum", 80, 68, 0, "2026-12-12", "Sponsor artwork", "2026-12-02"),
    ("expo", "Edge Expo", 100, 32, 4, "2026-12-20", "Venue deposit", "2026-11-25"),
]

@contextmanager
def database():
    conn = sqlite3.connect(os.getenv("EVENTOPS_DB", "eventops.sqlite3"), timeout=10)
    conn.row_factory = sqlite3.Row
    try:
        with conn:
            yield conn
    finally:
        conn.close()

def initialize():
    with database() as db:
        db.executescript("""
        CREATE TABLE IF NOT EXISTS events(id TEXT PRIMARY KEY,name TEXT,target INT,start TEXT);
        CREATE TABLE IF NOT EXISTS registrations(event TEXT,status TEXT,number INT,PRIMARY KEY(event,status,number));
        CREATE TABLE IF NOT EXISTS deadlines(event TEXT,label TEXT,due TEXT,PRIMARY KEY(event,label));
        CREATE TABLE IF NOT EXISTS history(id INTEGER PRIMARY KEY,session TEXT,question TEXT,answer TEXT,event TEXT);
        CREATE TABLE IF NOT EXISTS preferences(key TEXT PRIMARY KEY,value INT);
        """)
        for key, name, target, confirmed, cancelled, start, label, due in EVENTS:
            db.execute("INSERT OR IGNORE INTO events VALUES(?,?,?,?)", (key,name,target,start))
            db.execute("INSERT OR IGNORE INTO deadlines VALUES(?,?,?)", (key,label,due))
            for status, count in [("confirmed",confirmed),("cancelled",cancelled)]:
                db.executemany("INSERT OR IGNORE INTO registrations VALUES(?,?,?)",
                               ((key,status,i) for i in range(count)))

def context(session):
    with database() as db:
        rows = db.execute("SELECT question,answer,event FROM history WHERE session=? ORDER BY id DESC LIMIT 4",(session,)).fetchall()
        pref = db.execute("SELECT value FROM preferences WHERE key='window'").fetchone()
    return [dict(r) for r in reversed(rows)], pref[0] if pref else 7

def save(session, question, answer, event, window=None):
    with database() as db:
        if window is not None:
            db.execute("INSERT OR REPLACE INTO preferences VALUES('window',?)",(window,))
        db.execute("INSERT INTO history(session,question,answer,event) VALUES(?,?,?,?)",
                   (session,question,answer,event))
