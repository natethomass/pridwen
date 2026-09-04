"""The local learning store: one SQLite file, nothing leaves the machine.

Tables
  events    every shell command the hooks reported (scrubbed), with the rule that fired
  firings   when each rule last fired (cooldowns)
  counters  running counts used by nudges (key -> n)
  nudges    per-nudge state: sent time, snoozed until, disabled
  meta      key/value (schema version, install id)
"""
import os
import sqlite3
import time

from . import data_dir

SCHEMA = """
CREATE TABLE IF NOT EXISTS events (
  id INTEGER PRIMARY KEY,
  ts REAL NOT NULL,
  cmd TEXT NOT NULL,
  exit INTEGER NOT NULL,
  ms INTEGER NOT NULL DEFAULT 0,
  cwd TEXT,
  shell TEXT,
  pid INTEGER,
  rule TEXT
);
CREATE INDEX IF NOT EXISTS events_ts ON events(ts);
CREATE TABLE IF NOT EXISTS firings (rule TEXT PRIMARY KEY, ts REAL NOT NULL, n INTEGER NOT NULL DEFAULT 1);
CREATE TABLE IF NOT EXISTS counters (key TEXT PRIMARY KEY, n INTEGER NOT NULL DEFAULT 0);
CREATE TABLE IF NOT EXISTS nudges (id TEXT PRIMARY KEY, sent_ts REAL, snoozed_until REAL, disabled INTEGER NOT NULL DEFAULT 0, n INTEGER NOT NULL DEFAULT 0);
CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT);
"""


class Store:
    def __init__(self, path=None):
        self.path = path or os.path.join(data_dir(), "pridwen.db")
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        self.db = sqlite3.connect(self.path, timeout=2.0)
        self.db.row_factory = sqlite3.Row
        self.db.executescript(SCHEMA)
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.commit()

    def close(self):
        self.db.close()

    # ---- events -------------------------------------------------------------
    def add_event(self, cmd, exit_code, ms=0, cwd=None, shell=None, pid=None, rule=None, ts=None):
        cur = self.db.execute(
            "INSERT INTO events (ts, cmd, exit, ms, cwd, shell, pid, rule) VALUES (?,?,?,?,?,?,?,?)",
            (ts or time.time(), cmd, int(exit_code), int(ms or 0), cwd, shell, pid, rule))
        self.db.commit()
        return cur.lastrowid

    def set_event_rule(self, event_id, rule):
        self.db.execute("UPDATE events SET rule=? WHERE id=?", (rule, event_id))
        self.db.commit()

    def last_failed(self, within=3600):
        return self.db.execute(
            "SELECT * FROM events WHERE exit != 0 AND ts > ? ORDER BY id DESC LIMIT 1",
            (time.time() - within,)).fetchone()

    def last_event(self):
        return self.db.execute("SELECT * FROM events ORDER BY id DESC LIMIT 1").fetchone()

    def recent(self, n=10):
        return self.db.execute("SELECT * FROM events ORDER BY id DESC LIMIT ?", (n,)).fetchall()

    def count_events(self):
        return self.db.execute("SELECT COUNT(*) FROM events").fetchone()[0]

    # ---- rule cooldowns -----------------------------------------------------
    def fired_recently(self, rule, cooldown):
        row = self.db.execute("SELECT ts FROM firings WHERE rule=?", (rule,)).fetchone()
        return bool(row) and (time.time() - row["ts"]) < cooldown

    def record_firing(self, rule):
        self.db.execute(
            "INSERT INTO firings (rule, ts, n) VALUES (?, ?, 1) ON CONFLICT(rule) DO UPDATE SET ts=excluded.ts, n=n+1",
            (rule, time.time()))
        self.db.commit()

    def firings(self):
        return {r["rule"]: (r["ts"], r["n"]) for r in self.db.execute("SELECT * FROM firings")}

    # ---- counters -----------------------------------------------------------
    def bump(self, key, by=1):
        self.db.execute(
            "INSERT INTO counters (key, n) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET n=n+excluded.n", (key, by))
        self.db.commit()
        return self.db.execute("SELECT n FROM counters WHERE key=?", (key,)).fetchone()[0]

    def counter(self, key):
        row = self.db.execute("SELECT n FROM counters WHERE key=?", (key,)).fetchone()
        return row[0] if row else 0

    # ---- nudges -------------------------------------------------------------
    def nudge(self, nid):
        return self.db.execute("SELECT * FROM nudges WHERE id=?", (nid,)).fetchone()

    def nudge_sent(self, nid):
        self.db.execute(
            "INSERT INTO nudges (id, sent_ts, n) VALUES (?, ?, 1) ON CONFLICT(id) DO UPDATE SET sent_ts=excluded.sent_ts, n=n+1",
            (nid, time.time()))
        self.db.commit()

    def nudge_snooze(self, nid, until):
        self.db.execute(
            "INSERT INTO nudges (id, snoozed_until) VALUES (?, ?) ON CONFLICT(id) DO UPDATE SET snoozed_until=excluded.snoozed_until",
            (nid, until))
        self.db.commit()

    def nudge_disable(self, nid):
        self.db.execute(
            "INSERT INTO nudges (id, disabled) VALUES (?, 1) ON CONFLICT(id) DO UPDATE SET disabled=1", (nid,))
        self.db.commit()

    def nudges_sent_since(self, ts):
        return self.db.execute("SELECT COUNT(*) FROM nudges WHERE sent_ts > ?", (ts,)).fetchone()[0]

    # ---- meta ---------------------------------------------------------------
    def get(self, key, default=None):
        row = self.db.execute("SELECT value FROM meta WHERE key=?", (key,)).fetchone()
        return row[0] if row else default

    def set(self, key, value):
        self.db.execute("INSERT INTO meta (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                        (key, str(value)))
        self.db.commit()
