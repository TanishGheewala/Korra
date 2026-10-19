FROM python:3.12-slim-bookworm
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 LANGGRAPH_CLI_NO_ANALYTICS=1 LANGSMITH_TRACING=false
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY pyproject.toml langgraph.json ./
COPY src/ ./src/
COPY schema/ ./schema/
COPY scripts/ ./scripts/
COPY S1/ ./S1/
COPY S2/ ./S2/
COPY tests/ ./tests/
RUN pip install --no-cache-dir --no-deps -e .
EXPOSE 2024
CMD ["python", "scripts/server.py"]
