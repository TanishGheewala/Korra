# ============================================================
# Filename: Dockerfile.frontend
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
#     Builds the Agent UI, the web front end students cloned in Section 3.
#
#     Two stages, for a different reason than the backend. Next.js compiles
#     the site ahead of time, so the first stage installs the whole toolchain
#     and builds, and the second keeps only the compiled output. That needs
#     output: "standalone" in next.config.mjs, which produces a server.js and
#     a trimmed node_modules; without it .next/standalone never exists and
#     the copy below fails.
#
#     The API address is a build argument, not a run-time variable. Anything
#     named NEXT_PUBLIC_ is baked into the JavaScript the browser downloads,
#     so it has to be known while the site is being built, not when the
#     container starts.
#
#     That address is localhost:2024 and not backend:2024. The code that
#     calls it runs in the student's browser, outside Docker, where the name
#     "backend" means nothing. localhost works because compose publishes the
#     backend's port onto the host.
#
# Usage Instructions:
#     Copy this file into the agent-chat-ui folder as "Dockerfile", and copy
#     next.config.mjs in beside it. Then build the stack from the folder
#     holding docker-compose.yml:
#         docker compose up --build
# ============================================================


# ============================================================
# STAGE 1: BUILD THE SITE
# ============================================================

FROM node:22-bookworm-slim AS builder

WORKDIR /app

RUN npm install -g pnpm@10.5.1

# Copied before the source so the dependency layer survives code edits.
# --frozen-lockfile makes the install reproducible: it fails rather than
# quietly resolving different versions than the lockfile records
COPY package.json pnpm-lock.yaml* ./
RUN pnpm install --frozen-lockfile

COPY . .

# Read at build time and compiled into the browser bundle
ARG NEXT_PUBLIC_API_URL=http://localhost:2024
ARG NEXT_PUBLIC_ASSISTANT_ID=agent
ENV NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL}
ENV NEXT_PUBLIC_ASSISTANT_ID=${NEXT_PUBLIC_ASSISTANT_ID}

RUN pnpm build


# ============================================================
# STAGE 2: RUNTIME IMAGE
# ============================================================

FROM node:22-bookworm-slim AS runner

WORKDIR /app

ENV NODE_ENV=production
ENV PORT=3000

# Binds to every interface. The default is loopback inside the container,
# which the published port cannot reach
ENV HOSTNAME="0.0.0.0"

# The standalone output carries its own server and only the packages it
# actually needs, so no pnpm install happens in this stage
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static

EXPOSE 3000

CMD ["node", "server.js"]
