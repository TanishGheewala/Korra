"""Prepare the explicitly selected SQLite demo, then start the Studio server."""
import os
import sys
from korra_m10.database import backend_name, initialize_sqlite

if backend_name() == "sqlite":
    try:
        created = initialize_sqlite()
        print("SQLite seed created." if created else "Using existing SQLite student database.", flush=True)
    except Exception:
        print("Cannot initialize the SQLite database. Check STUDENT_DB_PATH and permissions.")
        sys.exit(1)
os.execvp("langgraph", ["langgraph", "dev", "--host", "0.0.0.0", "--port", "2024", "--no-browser"])
