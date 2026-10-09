# Project 07: C File Statistics Tool

**Student:** Tanish Gheewala

## Purpose and files

This project builds and tests the instructor-provided multi-file C program. It accepts a file path and returns JSON containing the filename, newline count, whitespace-separated word count, character/byte count, and status. Files are read in binary mode, so the character count represents bytes, not Unicode characters.

- `main.c`: validates arguments and reports results or errors.
- `file_stats.c` / `file_stats.h`: analyze the file and define shared types and status codes.
- `json_output.c` / `json_output.h`: format success and error output as JSON.
- `Makefile`: separately compiles source files and links the executable.
- `test_file_stats.c`, `test.txt`, and `tests/`: automated checks and input files.

## Build, run, and test

The verified setup uses Docker Desktop with the `gcc:15` Linux image. Start Docker Desktop and open PowerShell in the folder containing the Makefile. Run:

```powershell
docker run --rm -v "${PWD}:/work" -w /work gcc:15 sh -c "make rebuild && ./file_stats test.txt && make test"
```

This cleans previous build outputs, compiles and links the program, analyzes `test.txt`, and runs the tests. Compilation uses `-Wall -Wextra -Wpedantic -std=c11 -O2`. The executable is built for Linux and runs inside Docker.

To analyze another file in the project folder:

```powershell
docker run --rm -v "${PWD}:/work" -w /work gcc:15 ./file_stats test.txt
```

Replace `test.txt` with the desired relative file path.

## Verified results

The Docker build completed successfully. The included automated tests reported **28 passing checks and 0 failures**.

| Input | Expected lines / words / bytes | Actual |
|---|---|---|
| `test.txt` | 12 / 64 / 379 | Matched |
| `tests/empty.txt` | 0 / 0 / 0 | Matched |
| `tests/no_newline.txt` | 1 / 3 / 13 | Matched |
| `tests/whitespace_only.txt` | 3 / 0 / 9 | Matched |

Invalid-input checks passed for a missing file, a directory, and filenames at and beyond the 255-byte limit. Screenshots accompany the submission as execution evidence.

## Output contract

Standard output contains one JSON object. Errors also produce a diagnostic on standard error. Exit codes are: `0` success, `1` invalid arguments, `2` open failure, `3` read failure, and `4` filename too long. This interface is intended for Project 08 integration.
