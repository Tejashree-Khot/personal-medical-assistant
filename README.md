# Medical AI Agent

## Overview

This project implements AI assistant to compare allopathy and ayurvedic results by LLM agent. it designed to compare both pathies line of treatment, causes and diagnosis, lifestyle.

## Architecture

The system follows a simple orchestration flow:

1. **Input & Safety**: Triage for emergencies.
2. **Routing**: Classifies queries as General or Medical.
3. **Medical Orchestration**: Gathers missing critical data from the user.
4. **Response & Memory**: Delivers the final safe response and updates the conversation history.

For a detailed visual representation, see [Orchestration Flow](docs/orchestration.md).

## Tech Stack

- **Framework**: FastAPI
- **Orchestration**: LangGraph, LangChain
- **Database**: PostgreSQL (with `asyncpg` and `langgraph-checkpoint-postgres`)
- **Runtime**: Python 3.13+
- **Package Manager**: uv

## Getting Started

### Prerequisites

- Python 3.13 or higher
- [uv](https://github.com/astral-sh/uv) package manager
- PostgreSQL database

### Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/Tejashree-Khot/medical-ai-agent.git
   cd medical-ai-agent
   ```

2. Install dependencies using `uv`:

   ```bash
   uv sync
   ```

3. Set up environment variables:
   Create a `.env` file in the `app` directory with necessary API keys (OpenAI, Groq, Database URL, etc.).

### Running the Application

To start the FastAPI server locally:

```bash
# terminal 1
docker-compose up
```

The API will be available at `http://localhost:8080`.

To start the Streamlit chatbot:

```bash
# terminal 2
uv run streamlit run scripts/chatbot.py
```
