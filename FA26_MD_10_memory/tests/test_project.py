"""Offline checks: real SQLite, checkpoints, and tool routing; no paid API calls."""
import asyncio
import importlib
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from langchain_core.language_models.fake_chat_models import FakeListChatModel
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langgraph.checkpoint.sqlite import SqliteSaver
from korra_m10 import database
from korra_m10.chat_graph import build_chat

ROOT = Path(__file__).resolve().parents[1]


class DatabaseTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "students.db"
        self.env = patch.dict(os.environ, {"DB_BACKEND": "sqlite", "STUDENT_DB_PATH": str(self.path)})
        self.env.start()
        database.initialize_sqlite()

    def tearDown(self):
        self.env.stop()
        self.temp.cleanup()

    def save(self, **changes):
        fields = dict(name="Example Student", email="example@example.invalid", major="Computing", gpa=3.5, enrollment_date="2026-10-18")
        fields.update(changes)
        return database.save_student(**fields)

    def test_seed_counts(self):
        self.assertEqual(database.read_students()["counts"], {"students": 5, "courses": 5, "enrollments": 10})

    def test_save_and_reopen_preserve_enrollments(self):
        self.assertEqual(self.save()["status"], "success")
        # Every read/save opens a fresh connection.
        result = database.read_students("example@example.invalid")
        self.assertEqual(result["students"][0]["name"], "Example Student")
        self.assertEqual(result["counts"], {"students": 6, "courses": 5, "enrollments": 10})

    def test_seed_only_once(self):
        self.save()
        self.assertFalse(database.initialize_sqlite())
        self.assertEqual(database.read_students()["counts"]["students"], 6)

    def test_duplicate_refused(self):
        self.save()
        self.assertEqual(self.save()["status"], "refused")

    def test_missing_record(self):
        self.assertEqual(database.read_students("absent@example.invalid")["status"], "not_found")

    def test_validation(self):
        for changes in ({"gpa": 9}, {"gpa": float("nan")}, {"gpa": float("inf")}, {"gpa": True},
                        {"email": "bad"}, {"name": ""}, {"major": ""}, {"enrollment_date": "2026-02-30"}):
            with self.subTest(changes=changes):
                self.assertEqual(self.save(**changes)["status"], "refused")

    def test_sql_injection_is_data(self):
        text = "Robert'); DROP TABLE students;--"
        self.assertEqual(self.save(name=text)["student"]["name"], text)
        self.assertEqual(database.read_students()["counts"]["students"], 6)
        self.assertEqual(database.read_students("' OR 1=1 --")["status"], "not_found")

    def test_missing_database_not_created(self):
        absent = Path(self.temp.name) / "not-there.db"
        with patch.dict(os.environ, {"STUDENT_DB_PATH": str(absent)}):
            self.assertEqual(database.read_students()["status"], "error")
            self.assertEqual(self.save()["status"], "error")
        self.assertFalse(absent.exists())

    def test_corrupt_database_is_error_data(self):
        corrupt = Path(self.temp.name) / "corrupt.db"
        corrupt.write_text("not sqlite")
        with patch.dict(os.environ, {"STUDENT_DB_PATH": str(corrupt)}):
            self.assertEqual(database.read_students()["status"], "error")
            self.assertEqual(self.save()["status"], "error")

    def test_tool_nodes_route_multiple_calls(self):
        class FakeModel:
            def bind_tools(self, tools):
                return self

            async def ainvoke(self, messages, config=None):
                if isinstance(messages[-1], ToolMessage):
                    results = [m for m in messages if isinstance(m, ToolMessage)]
                    assert [m.name for m in results] == ["save_database", "read_database"]
                    return AIMessage(content="Done")
                return AIMessage(content="", tool_calls=[
                    {"name": "save_database", "id": "save", "args": {"name": "Route Test", "email": "route@example.invalid", "major": "Computing", "gpa": 3.0, "enrollment_date": "2026-10-18"}},
                    {"name": "read_database", "id": "read", "args": {"email": "route@example.invalid"}},
                ])
        with patch("korra_m10.config.make_model", return_value=FakeModel()):
            module = importlib.import_module("korra_m10.graph")
        graph = module.build_graph(FakeModel())
        output = asyncio.run(graph.ainvoke({"messages": [HumanMessage(content="Save and read")]}))
        self.assertEqual(output["messages"][-1].content, "Done")
        self.assertEqual(database.read_students("route@example.invalid")["status"], "success")


class CheckpointTests(unittest.TestCase):
    def test_checkpoint_reopen_and_thread_isolation(self):
        with tempfile.TemporaryDirectory() as temp:
            path = str(Path(temp) / "checkpoint.db")
            config = {"configurable": {"thread_id": "a"}}
            with SqliteSaver.from_conn_string(path) as saver:
                graph = build_chat(saver, model=FakeListChatModel(responses=["Acknowledged"]), with_search=False)
                graph.invoke({"messages": [HumanMessage(content="My name is Casey.")]}, config)
            with SqliteSaver.from_conn_string(path) as saver:
                graph = build_chat(saver, model=FakeListChatModel(responses=["Acknowledged"]), with_search=False)
                self.assertEqual(graph.get_state(config).values["messages"][0].content, "My name is Casey.")
                self.assertEqual(graph.get_state({"configurable": {"thread_id": "b"}}).values, {})

    def test_streaming_yields_incremental_chunks(self):
        with SqliteSaver.from_conn_string(":memory:") as saver:
            graph = build_chat(saver, model=FakeListChatModel(responses=["Hello"]), with_search=False)
            chunks = list(graph.stream({"messages": [HumanMessage(content="Hi")]},
                {"configurable": {"thread_id": "stream"}}, stream_mode="messages", version="v1"))
            self.assertGreater(len(chunks), 1)
            self.assertEqual("".join(m.content for m, meta in chunks), "Hello")

    def test_bad_checkpoint_has_no_traceback(self):
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run([sys.executable, str(ROOT / "S2/FA26_MD_10_S02_chatbot.py"),
                "--thread", "test", "--checkpoint", directory, "--prompt", "Hi"],
                capture_output=True, text=True)
            self.assertEqual(result.returncode, 1)
            self.assertIn("Checkpoint database", result.stdout)
            self.assertNotIn("Traceback", result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
