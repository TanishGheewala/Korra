FROM python:3.11-slim-bookworm AS c_builder
RUN apt-get update && apt-get install -y --no-install-recommends gcc make libc6-dev && rm -rf /var/lib/apt/lists/*
WORKDIR /build
COPY FA26_MD_07_file_stats/ ./
RUN make rebuild && make test

FROM python:3.11-slim-bookworm AS runtime
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY FA26_MD_06_S03_chatbot.py ./
COPY tools/ ./tools/
COPY --from=c_builder /build/file_stats ./tools/file_stats
COPY --from=c_builder /build/test.txt ./tools/test.txt
COPY --from=c_builder /build/tests/ ./tools/tests/
CMD ["python", "FA26_MD_06_S03_chatbot.py"]
