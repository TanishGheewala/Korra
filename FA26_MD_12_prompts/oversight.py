import hashlib
import hmac
import json
import math
import os
from pathlib import Path
import re
import secrets
import sqlite3
import time
import uuid
from datetime import date


FIELDS = {"name", "email", "major", "gpa", "enrollment_date"}
DECISIONS = {"approve", "reject", "revise", "cancel"}


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def validate_student(value):
    if not isinstance(value, dict) or set(value) != FIELDS:
        raise ValueError("Provide name, email, major, gpa and enrollment_date only.")
    value = dict(value)
    for field in ("name", "major"):
        if not isinstance(value[field], str) or not 1 <= len(value[field].strip()) <= 200:
            raise ValueError("Name and major must contain 1 to 200 characters.")
        value[field] = value[field].strip()
    email = value["email"]
    if not isinstance(email, str) or len(email) > 254 or not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email.strip()):
        raise ValueError("Invalid email.")
    value["email"] = email.strip().lower()
    gpa = value["gpa"]
    if isinstance(gpa, bool) or not isinstance(gpa, (int, float)) or not math.isfinite(gpa) or not 0 <= gpa <= 4:
        raise ValueError("GPA must be between 0 and 4.")
    if not isinstance(value["enrollment_date"], str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value["enrollment_date"]):
        raise ValueError("Use a YYYY-MM-DD date.")
    date.fromisoformat(value["enrollment_date"])
    return value


class Store:
    def __init__(self, path=None):
        self.path = Path(path or os.getenv("KORRA_DB", "data/korra.db"))
        self.token_path = self.path.parent / "reviewer.token"

    def connect(self):
        conn = sqlite3.connect(self.path, timeout=10)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA busy_timeout=10000")
        return conn

    def initialize(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS students (
                    id INTEGER PRIMARY KEY, name TEXT NOT NULL,
                    email TEXT NOT NULL UNIQUE, major TEXT NOT NULL,
                    gpa REAL NOT NULL CHECK(gpa BETWEEN 0 AND 4),
                    enrollment_date TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS requests (
                    decision_id TEXT PRIMARY KEY, version INTEGER NOT NULL,
                    status TEXT NOT NULL, request TEXT NOT NULL,
                    payload TEXT NOT NULL, created_at REAL NOT NULL,
                    expires_at REAL NOT NULL, student_id INTEGER,
                    reason TEXT
                );
                CREATE TABLE IF NOT EXISTS audit (
                    sequence INTEGER PRIMARY KEY, timestamp REAL NOT NULL,
                    decision_id TEXT, version INTEGER, event TEXT NOT NULL,
                    actor TEXT NOT NULL, status TEXT, payload_hash TEXT
                );
            """)
        if not self.token_path.exists():
            try:
                fd = os.open(self.token_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            except FileExistsError:
                return
            with os.fdopen(fd, "w") as stream:
                stream.write(secrets.token_hex(32))

    def local_reviewer_token(self):
        return self.token_path.read_text().strip()

    def event(self, conn, event, actor, row=None):
        conn.execute(
            "INSERT INTO audit(timestamp,decision_id,version,event,actor,status,payload_hash) VALUES (?,?,?,?,?,?,?)",
            (time.time(), row["decision_id"] if row else None,
             row["version"] if row else None, event, actor,
             row["status"] if row else None,
             digest(json.loads(row["payload"])) if row else None),
        )

    def expire(self, conn):
        for row in conn.execute("SELECT * FROM requests WHERE status='pending' AND expires_at<=?", (time.time(),)).fetchall():
            conn.execute("UPDATE requests SET status='timed_out',reason='deadline_elapsed' WHERE decision_id=?", (row["decision_id"],))
            self.event(conn, "timeout", "system", self.row(conn, row["decision_id"]))

    def row(self, conn, decision_id):
        return conn.execute("SELECT * FROM requests WHERE decision_id=?", (decision_id,)).fetchone()

    def public(self, row):
        value = dict(row)
        value["action"] = "save_database"
        value["proposed_arguments"] = json.loads(value.pop("payload"))
        value["risk"] = "Adds one student permanently; does not create enrollments."
        return value

    def propose(self, payload, request="Save this student", ttl=600):
        payload = validate_student(payload)
        if isinstance(ttl, bool) or not isinstance(ttl, (int, float)) or not math.isfinite(ttl) or not 0 < ttl <= 86400:
            raise ValueError("Timeout must be greater than 0 and at most 86400 seconds.")
        if not isinstance(request, str) or not 1 <= len(request) <= 2000:
            raise ValueError("Request must contain 1 to 2000 characters.")
        decision_id = str(uuid.uuid4())
        now = time.time()
        with self.connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            self.expire(conn)
            conn.execute("INSERT INTO requests VALUES (?,1,'pending',?,?,?,?,NULL,NULL)",
                         (decision_id, request, json.dumps(payload), now, now + ttl))
            row = self.row(conn, decision_id)
            self.event(conn, "interrupted", "requester", row)
            return self.public(row)

    def show(self, decision_id):
        with self.connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            self.expire(conn)
            row = self.row(conn, decision_id)
            return self.public(row) if row else {"status": "not_found"}

    def pending(self):
        with self.connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            self.expire(conn)
            return [self.public(row) for row in conn.execute("SELECT * FROM requests WHERE status='pending' ORDER BY created_at")]

    def decide(self, document, token):
        try:
            authorized = isinstance(token, str) and hmac.compare_digest(token, self.local_reviewer_token())
        except OSError:
            authorized = False
        with self.connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            self.expire(conn)
            if not authorized:
                self.event(conn, "unauthorized", "unverified")
                return {"status": "unauthorized"}
            valid = (isinstance(document, dict)
                     and set(document).issubset({"decision_id", "version", "decision", "changes"})
                     and {"decision_id", "version", "decision"}.issubset(document)
                     and isinstance(document["decision_id"], str)
                     and type(document["version"]) is int
                     and document["version"] > 0
                     and isinstance(document["decision"], str)
                     and document["decision"] in DECISIONS)
            if not valid:
                self.event(conn, "invalid_decision", "reviewer")
                return {"status": "invalid"}
            row = self.row(conn, document["decision_id"])
            if row is None:
                self.event(conn, "unknown_decision", "reviewer")
                return {"status": "not_found"}
            if row["status"] != "pending":
                self.event(conn, "duplicate_blocked", "reviewer", row)
                return {"status": "blocked", "current_status": row["status"]}
            if row["version"] != document["version"]:
                self.event(conn, "stale_blocked", "reviewer", row)
                return {"status": "stale", "version": row["version"]}
            decision = document["decision"]
            if decision != "revise" and "changes" in document:
                self.event(conn, "invalid_decision", "reviewer", row)
                return {"status": "invalid"}
            if decision == "revise":
                changes = document.get("changes")
                try:
                    if not isinstance(changes, dict) or not changes or not set(changes).issubset(FIELDS):
                        raise ValueError()
                    payload = validate_student({**json.loads(row["payload"]), **changes})
                except (ValueError, TypeError):
                    self.event(conn, "invalid_revision", "reviewer", row)
                    return {"status": "invalid"}
                conn.execute("UPDATE requests SET payload=?,version=version+1 WHERE decision_id=?", (json.dumps(payload), row["decision_id"]))
                self.event(conn, "revised", "reviewer", self.row(conn, row["decision_id"]))
            elif decision in ("reject", "cancel"):
                status = "rejected" if decision == "reject" else "cancelled"
                conn.execute("UPDATE requests SET status=? WHERE decision_id=?", (status, row["decision_id"]))
                self.event(conn, decision, "reviewer", self.row(conn, row["decision_id"]))
            else:
                self.event(conn, "approved", "reviewer", row)
                payload = json.loads(row["payload"])
                if conn.execute("SELECT 1 FROM students WHERE email=?", (payload["email"],)).fetchone():
                    conn.execute("UPDATE requests SET status='failed',reason='duplicate_email' WHERE decision_id=?", (row["decision_id"],))
                    self.event(conn, "action_failed", "system", self.row(conn, row["decision_id"]))
                else:
                    result = conn.execute("INSERT INTO students(name,email,major,gpa,enrollment_date) VALUES (?,?,?,?,?)",
                                          tuple(payload[field] for field in ("name", "email", "major", "gpa", "enrollment_date")))
                    conn.execute("UPDATE requests SET status='completed',student_id=? WHERE decision_id=?", (result.lastrowid, row["decision_id"]))
                    self.event(conn, "resumed_and_saved", "system", self.row(conn, row["decision_id"]))
            return self.public(self.row(conn, row["decision_id"]))

    def students(self):
        with self.connect() as conn:
            return [dict(row) for row in conn.execute("SELECT * FROM students ORDER BY id")]

    def audit(self):
        with self.connect() as conn:
            return [dict(row) for row in conn.execute("SELECT * FROM audit ORDER BY sequence")]
