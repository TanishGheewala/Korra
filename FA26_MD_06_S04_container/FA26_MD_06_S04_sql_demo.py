"""
Filename: FA26_MD_06_S04_sql_demo.py
Author: Professor Denis O. Nunez
Organization: Programming Journeys
Project: Project 06 - Korra: AI Chatbot
Module: Module 06 - Programming-Related Topics
Layer: Application - SQL Demonstration

Description:
    A small, dependency-free SQLite example for demonstrating how a Python
    class can create a table, write rows, and read them back with SQL.

Usage:
    python FA26_MD_06_S04_sql_demo.py
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Iterator


class ConversationDatabase:
    """Store and retrieve chatbot messages in a local SQLite database."""

    def __init__(self, database_path: str | Path = ":memory:") -> None:
        self.connection = sqlite3.connect(database_path)
        self.connection.row_factory = sqlite3.Row
        self.create_messages_table()

    def create_messages_table(self) -> None:
        """Create the messages table if it does not already exist."""
        self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                speaker TEXT NOT NULL,
                message TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        self.connection.commit()

    def add_message(self, speaker: str, message: str) -> int:
        """Insert one message safely and return its generated ID."""
        cursor = self.connection.execute(
            "INSERT INTO messages (speaker, message) VALUES (?, ?)",
            (speaker, message),
        )
        self.connection.commit()
        return int(cursor.lastrowid)

    def get_messages(self) -> Iterator[sqlite3.Row]:
        """Return messages in the order they were added."""
        cursor = self.connection.execute(
            """
            SELECT id, speaker, message, created_at
            FROM messages
            ORDER BY id
            """
        )
        yield from cursor

    def close(self) -> None:
        """Close the database connection."""
        self.connection.close()

    def __enter__(self) -> ConversationDatabase:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()


def main() -> None:
    """Run a short demonstration of the ConversationDatabase class."""
    with ConversationDatabase() as database:
        database.add_message("user", "What is SQL?")
        database.add_message(
            "assistant",
            "SQL is used to create, read, update, and delete data.",
        )

        print("Messages stored in SQLite:")
        for row in database.get_messages():
            print(f"{row['id']}: {row['speaker']} - {row['message']}")


if __name__ == "__main__":
    main()
