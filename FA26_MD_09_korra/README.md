# Project 09 - Korra MCP Server and User Interface

Korra uses Gemini through LangGraph, Tavily web search, the supplied compiled C
file statistics tool, and GitHub's remote MCP repository search. The official
Agent Chat UI connects to the same backend used by LangGraph Studio.

## Run with Docker Desktop

1. Copy `korra/.env.example` to `korra/.env`.
2. Set `GOOGLE_API_KEY` and `TAVILY_API_KEY` to your existing keys.
3. Set `GITHUB_TOKEN` to a GitHub personal access token for MCP search.
4. From the folder containing `docker-compose.yml`, run:

```powershell
docker compose up --build -d
docker compose ps
docker compose logs --tail 50 backend
```

Open http://localhost:3000.