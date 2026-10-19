"""Project 06 chatbot extended with SQLite checkpoints and streamed replies.

Adapted from the instructor's Project 06 structure; Gemini is retained from
the working project. Reuse a thread ID after exiting to continue its history.
"""
import argparse
import json
import os
from pathlib import Path
import sqlite3
import sys
import time

from langchain_core.messages import HumanMessage
from langgraph.checkpoint.sqlite import SqliteSaver
from korra_m10.chat_graph import build_chat
from korra_m10.config import text_content

ROOT = Path(__file__).resolve().parents[1]


def ask(graph, prompt, config):
    started = time.monotonic()
    received = []
    print("Korra: ", end="", flush=True)
    for message, metadata in graph.stream(
        {"messages": [HumanMessage(content=prompt)]}, config,
        stream_mode="messages", version="v1",
    ):
        if metadata.get("langgraph_node") != "chatbot":
            continue
        text = text_content(message)
        if text:
            received.append({"seconds": round(time.monotonic() - started, 4), "text": text})
            print(text, end="", flush=True)
    print()
    return {"prompt": prompt, "answer": "".join(c["text"] for c in received),
            "chunks": received, "chunk_count": len(received)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--thread", help="Reuse this ID to resume a saved conversation")
    parser.add_argument("--prompt", help="Run one turn and exit (for repeatable demonstrations)")
    parser.add_argument("--checkpoint", default=os.getenv("CHECKPOINT_PATH", str(ROOT / "data/korra_checkpoints.db")))
    parser.add_argument("--record", help="Optional JSON file holding actual streamed chunks")
    args = parser.parse_args()
    try:
        thread = args.thread or input("Thread ID: ").strip()
        if not thread:
            print("Enter a non-empty thread ID.")
            return 1
        path = Path(args.checkpoint).resolve()
        path.parent.mkdir(parents=True, exist_ok=True)
        config = {"configurable": {"thread_id": thread}, "recursion_limit": 30}
        with SqliteSaver.from_conn_string(str(path)) as saver:
            # Trigger initialization before constructing provider clients. A bad
            # checkpoint file is reported as a database error, without a traceback.
            list(saver.list(config, limit=1))
            graph = build_chat(saver)
            print(f"Thread: {thread} | Saved messages: {len(graph.get_state(config).values.get('messages', []))}")
            print("Type quit to exit. Reuse this thread ID to continue later.")
            while True:
                prompt = args.prompt if args.prompt is not None else input("You: ").strip()
                if prompt.lower() in {"quit", "exit", "q"}:
                    return 0
                if not prompt:
                    continue
                result = ask(graph, prompt, config)
                if args.record:
                    destination = Path(args.record)
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    destination.write_text(json.dumps({"thread_id": thread, **result}, indent=2), encoding="utf-8")
                if args.prompt is not None:
                    return 0
    except (sqlite3.Error, OSError):
        print("Checkpoint database could not be opened or written. Check its path and permissions.")
        return 1
    except (EOFError, KeyboardInterrupt):
        print("\nGoodbye.")
        return 0
    except Exception as exc:
        # Provider/validation errors also stay readable for a terminal user.
        print(f"Conversation failed ({type(exc).__name__}). Check your API key, quota, and network.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
