# Korra: AI Chatbot — Project 06

Korra is a terminal chatbot built with Python and LangGraph. It uses Google Gemini for responses and Tavily for web searches.

## Setup

Use Python 3.11 for local execution, or Docker Desktop for container execution. Run the commands below from `FA26_MD_06_S04_container`.

Create a `.env` file beside the chatbot script:

```dotenv
GOOGLE_API_KEY=your_google_api_key
TAVILY_API_KEY=your_tavily_api_key
```

Replace the placeholders with your own keys.

## Run locally

In your activated Python environment:

```bash
python -m pip install -r requirements.txt
python FA26_MD_06_S03_chatbot.py
```

## Run with Docker

Start Docker Desktop, then run:

```bash
docker compose build
docker compose run --rm korra
```

At the `You:` prompt, enter a question. Type `quit`, `exit`, or `q` to stop. Run Docker commands at the shell prompt after exiting the chatbot.
