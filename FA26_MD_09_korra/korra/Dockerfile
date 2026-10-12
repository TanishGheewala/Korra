# ============================================================
# Filename: Dockerfile.backend
# Author: Professor Denis O. Núñez
# Email: donunez@programmingjourneys.com
# Organization: Programming Journeys
# Project: Project 09 - Korra: MCP Server and User Interface
# Module: Module 09 - Interfacing and Communication
# Layer: Deployment - Container
# Date Created: October 4, 2026
# Date Modified: October 4, 2026
# Version: M09S04
# License: Educational Use
#
# Requirements:
#     Docker Desktop
#
# Description:
#     Builds the Korra backend: the LangGraph server with its three tool
#     nodes. The C tool is compiled from source inside the image, because a
#     Windows file_stats.exe cannot run on Linux.
#
#     Two stages. The first installs a compiler, builds the tool and runs its
#     automated checks, so a broken tool fails the build rather than the
#     container. The second copies only the finished binary, so the shipped
#     image carries no compiler.
#
#     The tool is built with make, not a single gcc command. The Project 07
#     package is three translation units, and main() lives in main.c, so
#     compiling file_stats.c alone fails to link.
#
#     No keys are copied in. docker-compose passes them at run time with
#     env_file, so this image can be rebuilt and shared without carrying
#     secrets.
#
# Usage Instructions:
#     Copy this file into the korra folder as "Dockerfile", then build the
#     whole stack from the folder holding docker-compose.yml:
#         docker compose up --build
#     Run the C tool by itself inside the image:
#         docker compose run --rm backend ./src/react_agent/tools/file_stats \
#             src/react_agent/tools/test.txt
# ============================================================


# ============================================================
# STAGE 1: BUILD AND TEST THE C TOOL
# ============================================================

FROM python:3.11-slim-bookworm AS builder

# gcc and make are needed only to compile the tool. They stay in this stage,
# so the image that ships has no toolchain in it
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build

# The tools folder carries its own Makefile, sources and test fixtures
COPY src/react_agent/tools/ ./

# The Makefile drops the .exe suffix when OS is not Windows_NT, so this
# produces a Linux binary named file_stats. make test runs the automated
# checks, which fails the build if the tool is wrong
RUN make rebuild && make test


# ============================================================
# STAGE 2: RUNTIME IMAGE
# ============================================================

FROM python:3.11-slim-bookworm

WORKDIR /app

# Keep .pyc files out of the image and let log lines appear as they happen
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Copied before the source so the dependency layer survives code edits
COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# The project itself, which langgraph.json points into
COPY pyproject.toml langgraph.json ./
COPY src/ ./src/

# Makes react_agent importable, which is how graph.py reaches the wrapper
RUN pip install --no-cache-dir --no-deps -e .

# The wrapper looks for the executable beside itself, so the Linux binary
# from stage 1 goes in the same folder as file_stats_tool.py
COPY --from=builder /build/file_stats ./src/react_agent/tools/file_stats

# Proves the binary runs and the wrapper can reach it, so a broken image
# fails here rather than on a student's first question
RUN python -c "from react_agent.tools.file_stats_tool import analyze_file_statistics as t; \
r = t.invoke({'filename': 'src/react_agent/tools/test.txt'}); \
print(r); \
exit(0 if r.get('status') == 'success' else 1)"

EXPOSE 2024

# --host 0.0.0.0 is required: the default binds to loopback inside the
# container, which the published port cannot reach
CMD ["langgraph", "dev", "--host", "0.0.0.0", "--port", "2024", "--no-browser"]
