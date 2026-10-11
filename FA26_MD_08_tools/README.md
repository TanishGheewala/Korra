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

The first Docker stage compiles the C sources and runs all 28 supplied checks. A failing check stops the build. The runtime stage contains Python, the wrapper, test inputs, and the Linux binary, without installing the C compiler. Keys enter at runtime through Compose; they are not copied into the image.

## Evidence prompts

Run these separately at `You:`. Capture the tool calls, results, and final answer, not just the answer.

1. `Use analyze_file_statistics to analyze tools/test.txt. Report its counts.`
2. `Use analyze_file_statistics on each of tools/tests/empty.txt, tools/tests/no_newline.txt, and tools/tests/whitespace_only.txt. Report the counts for each.`
3. `Use analyze_file_statistics on tools/tests/does_not_exist.txt. Explain the result.`
4. `Use Tavily to search for the purpose of the Unix wc command, and use analyze_file_statistics on tools/test.txt. Explain how the returned counts relate to wc and cite your search source.`
5. `Hello!` (ordinary conversation)

Expected file results (lines / words / bytes): `test.txt` = 12 / 64 / 379; empty = 0 / 0 / 0; no_newline = 1 / 3 / 13; whitespace_only = 3 / 0 / 9. Character counts equal byte counts. The missing file must return an error without ending the chat. Type `quit` to exit.

For a direct wrapper check in Docker:

```powershell
docker compose run --rm korra python tools/file_stats_tool.py tools/test.txt
```

Save the build output showing 28 passing checks and screenshots of the scenarios. Record actual outcomes after running; these expected values are not evidence of execution.

## Scope and submission

This package covers the container integration path. It does not include the executed Agentic Search lesson notebook or a verified native Windows comparison. Gemini replaces the starter code's OpenAI model. The C source and fixture folder must be added as described above.

For submission, include this source, the C folder, README, configuration templates, and actual evidence. Exclude `.env`, generated binaries/object files, caches, and unrelated files. Use `Gheewala_Tanish_Project08.zip` as the final submission filename.
