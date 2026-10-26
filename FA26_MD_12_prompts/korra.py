import argparse
import json
import os
from pathlib import Path
import sqlite3
import time

from agent import run
from oversight import Store


def output(value):
    print(json.dumps(value, indent=2, allow_nan=False), flush=True)


def review(store, decision_id):
    state = store.show(decision_id)
    output(state)
    if state["status"] != "pending":
        return
    choice = input("approve / reject / revise / cancel: ").strip().lower()
    document = {"decision_id": decision_id, "version": state["version"], "decision": choice}
    if choice == "revise":
        document["changes"] = json.loads(input("Changes: "))
    output(store.decide(document, store.local_reviewer_token()))


def main():
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ["serve", "init", "students", "pending", "audit"]:
        commands.add_parser(name)
    commands.add_parser("ask").add_argument("request")
    commands.add_parser("run").add_argument("file")
    commands.add_parser("review").add_argument("decision_id")
    args = parser.parse_args()
    store = Store()
    try:
        if args.command in {"serve", "init"}:
            store.initialize()
            print("Korra ready.", flush=True)
            if args.command == "serve":
                while True:
                    store.pending()
                    time.sleep(1)
        elif args.command == "ask":
            output(run({"request": args.request, "context": {"course": os.getenv("KORRA_COURSE", "COMPE475"), "term": os.getenv("KORRA_TERM", "Fall 2026")}}, store=store))
        elif args.command == "run":
            try:
                request = json.loads(Path(args.file).read_text())
            except json.JSONDecodeError:
                output(run(None, store=store))
                return 1
            output(run(request, store=store))
        elif args.command == "review":
            review(store, args.decision_id)
        else:
            output(getattr(store, args.command)())
        return 0
    except (ValueError, OSError, sqlite3.Error):
        output({"status": "error", "message": "Invalid input or unavailable storage."})
    except (KeyboardInterrupt, EOFError):
        print("Stopped.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
