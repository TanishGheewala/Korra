# Project 10 - Korra: Persistence and Streaming

This project adds persistent conversation memory, streaming responses, database tools, and PostgreSQL storage to Korra.

## Section 2 - Persistent Chatbot

Run the chatbot:

```powershell
docker run --rm -it --env-file .env -v "${PWD}:/work" -w /work korra-project10 python S2/FA26_MD_10_S02_chatbot.py
```

Use a thread ID to start a conversation. Reusing the same thread ID continues the saved conversation. A new thread ID starts a separate conversation.

## Section 3 - SQLite Database Tools

Start the SQLite version:

```powershell
docker compose down
docker compose -f compose.sqlite.yml up -d
```

The application provides two database tools:

- `save_database`
- `read_database`

Each tool has its own graph node.

Student records are stored in:

```text
data/test_database.db
```

The tools support:

- Saving a student
- Reading a student
- Duplicate-save handling
- Missing-record handling
- Database error handling
- Persistence after application restart

## Section 4 - PostgreSQL Service

Start the PostgreSQL version:

```powershell
docker compose -f compose.sqlite.yml down
docker compose up --build -d
docker compose ps
```

PostgreSQL stores records in a Docker named volume.

To verify persistence:

```powershell
docker compose down
docker compose up --build -d
```

Previously saved records remain available after the containers are recreated.
