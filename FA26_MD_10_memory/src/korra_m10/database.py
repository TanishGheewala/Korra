"""The same student operations for SQLite (S3) and PostgreSQL (S4).

Schema and sample records come from the instructor's Module 10 create_db.py.
SQL is fixed by this module; user/model input is always a bound parameter.
"""
from contextlib import contextmanager
from datetime import date
import math
import os
from pathlib import Path
import re
import sqlite3

ROOT = Path(__file__).resolve().parents[2]


def backend_name():
    return os.getenv("DB_BACKEND", "sqlite").lower()


def sqlite_path():
    return Path(os.getenv("STUDENT_DB_PATH", str(ROOT / "data/test_database.db"))).resolve()


def initialize_sqlite():
    """Explicit setup only; tool calls never create or seed a missing database."""
    path = sqlite_path()
    if path.exists():
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as conn:
        conn.executescript((ROOT / "schema/sqlite.sql").read_text())
    return True


@contextmanager
def connection(*, write=False):
    if backend_name() == "sqlite":
        # mode=rw/ro prevents sqlite3 from silently creating an empty database.
        mode = "rw" if write else "ro"
        conn = sqlite3.connect(sqlite_path().as_uri() + f"?mode={mode}", uri=True, timeout=5)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
    elif backend_name() == "postgres":
        import psycopg
        from psycopg.rows import dict_row
        conn = psycopg.connect(
            host=os.getenv("POSTGRES_HOST", "db"),
            port=int(os.getenv("POSTGRES_PORT", "5432")),
            dbname=os.getenv("POSTGRES_DB", "korra"),
            user=os.getenv("POSTGRES_USER", "korra"),
            password=os.environ.get("POSTGRES_PASSWORD", ""),
            row_factory=dict_row, connect_timeout=5,
        )
    else:
        raise ValueError("Unsupported DB_BACKEND")
    try:
        yield conn
        if write:
            conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def execute(conn, sql, values=()):
    # Only our constant SQL uses ?; no user text is substituted into SQL.
    if backend_name() == "postgres":
        sql = sql.replace("?", "%s")
    return conn.execute(sql, values)


def public_student(row):
    result = dict(row)
    if result.get("gpa") is not None:
        result["gpa"] = round(float(result["gpa"]), 4)
    return result


def validation_error(name, email, major, gpa, enrollment_date):
    if not isinstance(name, str) or not name.strip() or len(name.strip()) > 200:
        return "Name is required and must be at most 200 characters."
    if not isinstance(email, str) or len(email) > 254 or not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email.strip()):
        return "Provide a valid email address."
    if not isinstance(major, str) or not major.strip() or len(major.strip()) > 200:
        return "Major is required and must be at most 200 characters."
    if isinstance(gpa, bool) or not isinstance(gpa, (float, int)) or not math.isfinite(gpa) or not 0 <= gpa <= 4:
        return "GPA must be a finite number from 0.0 to 4.0."
    try:
        if not isinstance(enrollment_date, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", enrollment_date):
            raise ValueError()
        date.fromisoformat(enrollment_date)
    except (TypeError, ValueError):
        return "Enrollment date must be a real date in YYYY-MM-DD format."
    return None


def save_student(name, email, major, gpa, enrollment_date):
    """Return success, refused, or error data; never overwrite an existing email."""
    error = validation_error(name, email, major, gpa, enrollment_date)
    if error:
        return {"status": "refused", "reason": error}
    email = email.strip().lower()
    try:
        with connection(write=True) as conn:
            if execute(conn, "SELECT id FROM students WHERE email = ?", (email,)).fetchone():
                return {"status": "refused", "reason": "A student with this email already exists."}
            row = execute(conn,
                "INSERT INTO students(name,email,major,gpa,enrollment_date) VALUES (?,?,?,?,?) "
                "RETURNING id,name,email,major,gpa,enrollment_date",
                (name.strip(), email, major.strip(), float(gpa), enrollment_date)).fetchone()
        return {"status": "success", "student": public_student(row)}
    except Exception as exc:
        # Includes a concurrent duplicate after the pre-insert lookup.
        if isinstance(exc, sqlite3.IntegrityError) or getattr(exc, "sqlstate", "") in ("23505", "23502", "23514"):
            return {"status": "refused", "reason": "The database refused the record (duplicate or constraint)."}
        return {"status": "error", "reason": "Student database could not be written. Check its path, availability, and permissions."}


def read_students(email=""):
    """Read one email, or a bounded list and the course/enrollment counts."""
    if not isinstance(email, str):
        return {"status": "error", "reason": "Email must be text."}
    try:
        with connection() as conn:
            sql = "SELECT id,name,email,major,gpa,enrollment_date FROM students"
            if email.strip():
                rows = execute(conn, sql + " WHERE email = ?", (email.strip().lower(),)).fetchall()
                if not rows:
                    return {"status": "not_found", "students": [], "reason": "No student has this email."}
            else:
                rows = execute(conn, sql + " ORDER BY id LIMIT 100").fetchall()
            counts = {}
            # Table identifiers are constants, not model-provided text.
            for table in ("students", "courses", "enrollments"):
                counts[table] = dict(execute(conn, f"SELECT COUNT(*) AS count FROM {table}").fetchone())["count"]
        return {"status": "success", "students": [public_student(row) for row in rows], "counts": counts}
    except Exception:
        return {"status": "error", "reason": "Student database could not be read. Check its path, availability, and permissions."}
