"""Run real Gemini turns in separate processes; retain actual streaming evidence."""
import json
import os
from pathlib import Path
import subprocess
import sys
import uuid

ROOT = Path(__file__).resolve().parents[1]
evidence = ROOT / "evidence"
evidence.mkdir(exist_ok=True)
thread = "memory-" + uuid.uuid4().hex[:8]
script = ROOT / "S2/FA26_MD_10_S02_chatbot.py"
checkpoint = ROOT / "data/korra_checkpoints.db"
checkpoint.parent.mkdir(exist_ok=True)


def run_turn(label, thread_id, prompt):
    record = evidence / f"S2-{label}.json"
    command = [sys.executable, str(script), "--thread", thread_id, "--prompt", prompt,
               "--checkpoint", str(checkpoint), "--record", str(record)]
    result = subprocess.run(command, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    (evidence / f"S2-{label}.txt").write_text(result.stdout, encoding="utf-8")
    print(result.stdout, flush=True)
    if result.returncode:
        raise RuntimeError(f"S2 {label} failed. See its evidence log.")
    return json.loads(record.read_text())


first = run_turn("1-save", thread, "My name is Casey and my favorite color is turquoise. Remember both.")
second = run_turn("2-reopen", thread, "What is my name and favorite color?")
fresh = run_turn("3-new-thread", thread + "-new", "What is my name and favorite color?")
stream = run_turn("4-streaming", thread, "Explain in five short sentences why persistent conversation history is useful.")
assert "casey" in second["answer"].lower() and "turquoise" in second["answer"].lower(), "Inspect the reopened-thread answer."
assert "casey" not in fresh["answer"].lower() and "turquoise" not in fresh["answer"].lower(), "Inspect the new-thread answer."
assert stream["chunk_count"] > 0, "No visible streamed chunks were received."
bad = subprocess.run([sys.executable, str(script), "--thread", "unwritable-demo",
                      "--checkpoint", str(ROOT / "data"), "--prompt", "Hello"],
                     text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
(evidence / "S2-5-checkpoint-error.txt").write_text(bad.stdout, encoding="utf-8")
assert bad.returncode != 0 and "Checkpoint database" in bad.stdout and "Traceback" not in bad.stdout
print(f"S2 PASS: separate processes retained one thread, isolated another, and received {stream['chunk_count']} visible stream chunks.")
print("The required checkpoint database is in data/korra_checkpoints.db.")
