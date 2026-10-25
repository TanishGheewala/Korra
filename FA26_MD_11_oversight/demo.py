import contextlib
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import platform
import socket
import sys
import time
import uuid

from korra import output, review
from oversight import Store


class Tee:
    def __init__(self, stream):
        self.stream = stream
        self.console = sys.stdout

    def write(self, text):
        self.console.write(text)
        self.stream.write(text)
        self.stream.flush()
        return len(text)

    def flush(self):
        self.console.flush()
        self.stream.flush()


def check(condition, label):
    if not condition:
        raise RuntimeError(label)
    print("PASS:", label, flush=True)


def student(tag):
    return {"name": "Demo Student", "email": f"{tag}@example.invalid", "major": "Computer Engineering",
            "gpa": 3.6, "enrollment_date": "2026-10-25"}


def decision(row, choice, **extra):
    return {"decision_id": row["decision_id"], "version": row["version"], "decision": choice, **extra}


def before(store, folder):
    run_id = str(uuid.uuid4())
    state = {"run_id": run_id, "started_at": datetime.now(timezone.utc).isoformat(),
             "hostname_before": socket.gethostname(), "docker_before": Path("/.dockerenv").exists(),
             "initial_count": len(store.students()), "checks": {}}
    token = store.local_reviewer_token()
    first = store.propose(student(f"approve-{run_id}"))
    check(not any(s["email"] == first["proposed_arguments"]["email"] for s in store.students()), "Paused before the student was inserted")
    state["checks"]["paused"] = first
    print("\nAPPROVAL: type approve. Capture 01-paused.png when the decision prompt appears.")
    approved = review(store, first["decision_id"])
    check(approved["status"] == "completed", "Human approval saved one student")
    state["checks"]["approval"] = approved
    retry = store.decide(decision(first, "approve"), token)
    check(retry["status"] == "blocked" and len(store.students()) == state["initial_count"] + 1, "Repeated approval blocked; no second insert")
    state["checks"]["duplicate_approval"] = retry

    second = store.propose(student(f"reject-{run_id}"))
    unauthorized = store.decide(decision(second, "approve"), "invalid-reviewer-token")
    invalid = store.decide(decision(second, "run_anyway"), token)
    check(unauthorized["status"] == "unauthorized" and invalid["status"] == "invalid", "Unauthorized and invalid decisions blocked")
    check(store.show(second["decision_id"])["status"] == "pending", "Invalid decisions left the request pending")
    state["checks"]["unauthorized"] = unauthorized
    state["checks"]["invalid"] = invalid
    print("\nREJECTION: type reject.")
    rejected = review(store, second["decision_id"])
    check(rejected["status"] == "rejected", "Rejection stopped the write")
    state["checks"]["rejection"] = rejected

    third = store.propose(student(f"revise-{run_id}"))
    print('\nREVISION: type revise, then enter {"major":"Electrical Engineering"}.')
    revised = review(store, third["decision_id"])
    check(revised["status"] == "pending" and revised["version"] == 2 and revised["proposed_arguments"] != third["proposed_arguments"], "Revision saved new arguments but did not execute")
    stale = store.decide(decision(third, "approve"), token)
    check(stale["status"] == "stale", "Approval for the old version blocked")
    state["checks"]["stale"] = stale
    state["checks"]["revision_pending"] = revised
    print("\nREVISED APPROVAL: inspect the new arguments and type approve.")
    revised = review(store, third["decision_id"])
    check(revised["status"] == "completed", "Revised request approved and saved")
    saved = next(s for s in store.students() if s["id"] == revised["student_id"])
    check(all(saved[key] == value for key, value in revised["proposed_arguments"].items()), "Database contains the revised values")
    state["checks"]["revision_completed"] = revised

    fourth = store.propose(student(f"cancel-{run_id}"))
    print("\nCANCELLATION: type cancel.")
    cancelled = review(store, fourth["decision_id"])
    check(cancelled["status"] == "cancelled", "Cancellation stopped the write")
    state["checks"]["cancellation"] = cancelled

    fifth = store.propose(student(f"timeout-{run_id}"), ttl=1)
    time.sleep(1.2)
    timed_out = store.show(fifth["decision_id"])
    check(timed_out["status"] == "timed_out", "Expired request did not execute")
    late = store.decide(decision(fifth, "approve"), token)
    check(late["status"] == "blocked", "Late approval blocked")
    state["checks"]["timeout"] = timed_out
    state["checks"]["late_approval"] = late

    duplicate = store.propose(first["proposed_arguments"])
    print("\nFAILURE: this email already exists. Type approve to test safe failure.")
    failed = review(store, duplicate["decision_id"])
    check(failed["status"] == "failed" and failed["reason"] == "duplicate_email", "Duplicate email failed without another insert")
    state["checks"]["action_failure"] = failed
    check(len(store.students()) == state["initial_count"] + 2, "Only the approved and revised records were added")

    pending = store.propose(student(f"restart-{run_id}"), ttl=86400)
    state["restart"] = pending
    (folder / "run.json").write_text(json.dumps(state, indent=2))
    print("\nBEFORE RESTART: PASS")
    for name, value in state["checks"].items():
        print(f"{name}: {value['status']}")
    print("Restart decision:", pending["decision_id"], "version:", pending["version"], "status:", pending["status"])
    print("Container:", state["hostname_before"])
    print("Capture 02-outcomes.png now. Then recreate the container and run demo.py after.")


def after(store, folder):
    state = json.loads((folder / "run.json").read_text())
    pending = store.show(state["restart"]["decision_id"])
    hostname = socket.gethostname()
    check(hostname != state["hostname_before"], "Container ID changed after recreation")
    check(pending == state["restart"], "Pending decision ID, version, arguments and deadline survived restart")
    print("Previous container:", state["hostname_before"], "Current container:", hostname)
    print("\nRESUME: capture 03-restart.png at the prompt, then type approve.")
    completed = review(store, pending["decision_id"])
    check(completed["status"] == "completed", "Resumed the preserved decision after restart")
    again = store.decide(decision(pending, "approve"), store.local_reviewer_token())
    check(again["status"] == "blocked", "Restarted request also executes only once")
    check(len(store.students()) == state["initial_count"] + 3, "Exactly three intended records were inserted")
    audit = store.audit()
    allowed = {"sequence", "timestamp", "decision_id", "version", "event", "actor", "status", "payload_hash"}
    check(all(set(row) == allowed for row in audit), "Audit contains only allowed metadata fields")
    audit_text = json.dumps(audit, indent=2)
    forbidden = [store.local_reviewer_token(), os.getenv("GOOGLE_API_KEY", "")]
    check(not any(secret and secret in audit_text for secret in forbidden), "No reviewer token or configured API key in audit")
    (folder / "audit.json").write_text(audit_text)
    (folder / "students.json").write_text(json.dumps(store.students(), indent=2))
    state.update({"status": "PASS", "hostname_after": hostname,
                  "docker_after": Path("/.dockerenv").exists(), "restart_completed": completed,
                  "finished_at": datetime.now(timezone.utc).isoformat(), "audit_secrets_found": False})
    (folder / "summary.json").write_text(json.dumps(state, indent=2))
    print("\nFINAL: PASS")
    print("Approve / reject / revise / cancel / timeout / invalid / unauthorized / duplicate / restart: PASS")
    print("Audit secrets found: false")
    print("Evidence saved in evidence/. Capture 04-final.png now.")


def main():
    if len(sys.argv) != 2 or sys.argv[1] not in {"before", "after"}:
        print("Use: python demo.py before|after")
        return 1
    phase = sys.argv[1]
    folder = Path("evidence")
    folder.mkdir(exist_ok=True)
    if phase == "before":
        (folder / "summary.json").unlink(missing_ok=True)
    (folder / f"containers-{phase}.txt").write_text(
        f"hostname={socket.gethostname()}\ndocker={Path('/.dockerenv').exists()}\n"
        f"python={platform.python_version()}\ncheckpoint={Store().path.resolve()}\n")
    with (folder / f"{phase}.txt").open("w") as stream, contextlib.redirect_stdout(Tee(stream)):
        print(datetime.now(timezone.utc).isoformat(), "Interactive demonstration", phase)
        try:
            globals()[phase](Store(), folder)
            return 0
        except (Exception, KeyboardInterrupt) as exc:
            print("STOPPED:", type(exc).__name__, "Demonstration incomplete. No success report was generated.")
            if (folder / "summary.json").exists():
                (folder / "summary.json").unlink()
            return 1


if __name__ == "__main__":
    raise SystemExit(main())
