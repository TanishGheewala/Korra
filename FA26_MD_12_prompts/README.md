# Project 12: Korra System Prompts

Single-agent student database assistant with structured prompts, a three-step action limit and human approval for writes.

Configuration: `.env` with `GOOGLE_API_KEY` and `GEMINI_MODEL`.

```powershell
docker compose up --build -d --wait
docker compose exec korra python korra.py ask "List students."
docker compose exec korra python validate.py
```

Policy: `prompts/system.txt`. Formats: `schemas/`. Results: `evidence/`.