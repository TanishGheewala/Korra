"""Capture actual graph tool calls before and after server/container restarts."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import uuid

from langgraph_sdk import get_sync_client
from korra_m10.database import backend_name, read_students
from korra_m10.tools import read_database, save_database

parser = argparse.ArgumentParser()
parser.add_argument("phase", choices=["before", "after"])
args = parser.parse_args()
backend = backend_name()
section = "S3" if backend == "sqlite" else "S4"
out = Path("evidence")
out.mkdir(exist_ok=True)
marker = out / f"{section}-record.json"
report = {"section": section, "backend": backend, "phase": args.phase,
          "utc": datetime.now(timezone.utc).isoformat(), "runs": []}
client = get_sync_client(url="http://127.0.0.1:2024")


def ask(prompt, tool_name, expected_status):
    # Each request has a fresh thread: any retrieved record must be in the DB,
    # rather than merely in a previous conversation's state.
    thread = client.threads.create()
    result = client.runs.wait(thread["thread_id"], "agent", input={"messages": [{"role": "human", "content": prompt}]})
    entry = {"prompt": prompt, "thread_id": thread["thread_id"], "result": result}
    report["runs"].append(entry)
    (out / f"{section}-{args.phase}.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    results = []
    for message in result.get("messages", []):
        if message.get("type") == "tool" and message.get("name") == tool_name:
            content = message.get("content", "")
            if isinstance(content, list):
                content = "".join(block.get("text", "") for block in content if isinstance(block, dict))
            try:
                results.append(json.loads(content))
            except (ValueError, TypeError):
                pass
    matching = [r for r in results if r.get("status") == expected_status]
    assert matching, f"Expected {tool_name} -> {expected_status}; inspect {section}-{args.phase}.json."
    print(f"PASS: {tool_name} returned {expected_status}", flush=True)
    return matching[-1]


if args.phase == "before":
    email = f"{backend}.demo.{uuid.uuid4().hex[:8]}@example.invalid"
    marker.write_text(json.dumps({"email": email}), encoding="utf-8")
    initial = ask("Use read_database to list the students and the student, course, and enrollment counts.", "read_database", "success")
    save_prompt = (f"Use save_database to add Demo Student, email {email}, major Computer Engineering, "
                   "GPA 3.6, enrollment date 2026-10-18.")
    ask(save_prompt, "save_database", "success")
    ask("This is a duplicate-save validation test. Call the save tool again with exactly this record and explain its returned status: " + save_prompt,
        "save_database", "refused")
    ask("Use read_database to find missing-record@example.invalid and explain the result.", "read_database", "not_found")
    after = read_students(email)
    assert after["status"] == "success"
    assert after["counts"]["enrollments"] == initial["counts"]["enrollments"]
    report["enrollments_unchanged"] = True
    # Run failure inputs through the actual tool wrappers in this isolated
    # evidence process, without changing the running server's configuration.
    report["invalid_save"] = save_database.invoke({"name": "Invalid Demo", "email": "invalid@example.invalid",
        "major": "Computing", "gpa": 9.0, "enrollment_date": "2026-10-18"})
    assert report["invalid_save"]["status"] == "refused"
    os.environ["DB_BACKEND"] = "sqlite"
    os.environ["STUDENT_DB_PATH"] = "/nonexistent-korra-test-folder/missing.db"
    report["unreadable_database"] = read_database.invoke({"email": ""})
    assert report["unreadable_database"]["status"] == "error"
    print("PASS: invalid save, missing record, duplicate, and unavailable database return data.")
else:
    email = json.loads(marker.read_text())["email"]
    record = ask(f"Use read_database to look up {email}. Report the stored student.", "read_database", "success")
    assert any(s["email"] == email for s in record["students"])
    report["persisted_record_found"] = True
    print(f"PASS: {email} still exists after restart/recreation.")
(out / f"{section}-{args.phase}.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
