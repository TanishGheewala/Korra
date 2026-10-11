# Project 08: Korra Tools

Student: Tanish Gheewala

This adaptation connects the supplied C file-statistics wrapper to the Project 06 Gemini chatbot. Tavily search remains available. LangGraph routes model tool calls through a ToolNode and sends returned results back to the model. The terminal prints actual TOOL CALL and TOOL RESULT records for evidence.

## Setup

1. Place this folder beside the existing Project 06 and Project 07 folders.
2. Copy the complete `FA26_MD_07_file_stats` folder inside this folder. Its Makefile, C sources, headers, `test.txt`, and `tests` must remain together, without an extra nested folder.
3. Copy your Project 06 `.env` here. It must contain `GOOGLE_API_KEY` and `TAVILY_API_KEY`. `.env.example` shows placeholders only.
4. Start Docker Desktop. Run from this folder in PowerShell:

```powershell
docker compose --progress plain build
docker compose run --rm korra
```