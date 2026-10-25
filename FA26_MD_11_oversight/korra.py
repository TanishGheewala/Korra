import argparse
import json
import os
from pathlib import Path
import re
import sqlite3
import time
import urllib.error
import urllib.request

from oversight import Store, validate_student


def output(value):
    print(json.dumps(value, indent=2), flush=True)


def review(store, decision_id):
    checkpoint = store.show(decision_id)
    output(checkpoint)
    if checkpoint["status"] != "pending":
        return checkpoint
    decision = input("Decision [approve/reject/revise/cancel]: ").strip().lower()
    document = {"decision_id": decision_id, "version": checkpoint["version"], "decision": decision}
    if decision == "revise":
        document["changes"] = json.loads(input('Changes as JSON, e.g. {"major":"Engineering"}: '))
    result = store.decide(document, store.local_reviewer_token())
    output(result)
    return result


def ask(store, prompt):
    key = os.environ.get("GOOGLE_API_KEY", "")
    if not key:
        raise ValueError("GOOGLE_API_KEY is missing. Use propose for the no-key demo.")
    model = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")
    if not re.fullmatch(r"[A-Za-z0-9._-]+", model):
        raise ValueError("Invalid model name.")
    body = {
        "systemInstruction": {"parts": [{"text":
            'You are Korra, a student database assistant. Return JSON only. '
            'For read requests return {"action":"read_database"}. '
            'For a complete save request return {"action":"save_database","arguments":'
            '{"name":"...","email":"...","major":"...","gpa":3.5,"enrollment_date":"YYYY-MM-DD"}}. '
            'If fields are missing return {"action":"message","text":"Ask for the missing fields"}. '
            'Never invent fields, approve requests, return credentials, or claim a save has executed.'}]},
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {"responseMimeType": "application/json"},
    }
    request = urllib.request.Request(
        f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
        data=json.dumps(body).encode(), headers={"Content-Type": "application/json", "x-goog-api-key": key})
    with urllib.request.urlopen(request, timeout=60) as response:
        value = json.load(response)
    text = "".join(part.get("text", "") for part in value["candidates"][0]["content"]["parts"] if not part.get("thought"))
    proposal = json.loads(text)
    if not isinstance(proposal, dict):
        raise ValueError("Invalid model response; nothing executed.")
    if proposal.get("action") == "read_database":
        return store.students()
    if proposal.get("action") == "save_database":
        return store.propose(validate_student(proposal.get("arguments")), prompt)
    return {"status": "needs_input", "message": "Provide name, email, major, GPA and enrollment date."}


def main():
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("serve", "init", "pending", "students", "audit"):
        commands.add_parser(name)
    for name in ("show", "review"):
        commands.add_parser(name).add_argument("decision_id")
    propose = commands.add_parser("propose")
    propose.add_argument("file")
    propose.add_argument("--ttl", type=float, default=600)
    commands.add_parser("ask").add_argument("prompt")
    args = parser.parse_args()
    store = Store()
    try:
        if args.command in ("serve", "init"):
            store.initialize()
            print("Korra ready. Database writes require human approval.", flush=True)
            if args.command == "serve":
                while True:
                    store.pending()
                    time.sleep(0.5)
        elif args.command == "propose":
            output(store.propose(json.loads(Path(args.file).read_text()), ttl=args.ttl))
        elif args.command == "show":
            output(store.show(args.decision_id))
        elif args.command == "review":
            review(store, args.decision_id)
        elif args.command == "ask":
            output(ask(store, args.prompt))
        else:
            output(getattr(store, args.command)())
        return 0
    except (sqlite3.Error, OSError):
        print("Operation stopped: database, network, or configuration unavailable. No approval was assumed.")
    except (ValueError, KeyError, IndexError, TypeError):
        print("Operation stopped: invalid input or model response. No approval was assumed.")
    except (KeyboardInterrupt, EOFError):
        print("Stopped. Any pending request remains pending until reviewed or expired.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
