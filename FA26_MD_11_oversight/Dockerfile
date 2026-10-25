FROM python:3.12-slim-bookworm
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
COPY oversight.py korra.py demo.py sample.json ./
COPY tests/ ./tests/
CMD ["python", "korra.py", "serve"]
