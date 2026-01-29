# Personalized Medical Assistant

## Overview

The **Personalized Medical Assistant** is an advanced AI system that delivers comprehensive, tailored health guidance by bridging modern Western medicine (Allopathy) with traditional healing systems (Ayurveda, TCM/Kampo) and lifestyle recommendations.

It ensures **safety and relevance** through input guardrails, contraindication checks, and a persistent user health profile, preventing adverse interactions between treatments. Powered by **LangGraph**, it orchestrates parallel specialist agents to generate **accurate, personalized, and safe responses**.

## Getting Started

### Prerequisites

- Python 3.13 or higher
- [uv](https://github.com/astral-sh/uv) package manager
- docker and docker-compose

### Installation

1. Clone the repository:

   ```bash
   git clone <repository-url>
   cd personal-medical-assistant
   ```

2. Install dependencies using `uv`:

   ```bash
   uv sync
   ```

3. Set up environment variables:
   Create a `.env` file in the `app` directory with necessary API keys (OpenAI, Groq, Database URL, etc.).

### Running the Application

To start the FastAPI server locally:
In terminal 1

```bash
cd app
docker-compose up
```

API will be available at `http://localhost:8080`.

In terminal 2

```bash
uv run streamlit run scripts/chatbot.py
```

The UI will be available at `http://localhost:8501`.

## Orchestration

```mermaid
graph TD
    START([START]) --> input_guardrail{Input Guardrail}

    %% Input routing
    input_guardrail -->|General query| general_agent[General Agent]
    input_guardrail -->|Medical query| medical_router{Medical Router}

    %% Medical routing
    medical_router -->|Emergency detected| emergency_medical_agent[Emergency Medical Agent]
    medical_router -->|Standard query| ensure_details{Ensure Details}

    %% General Agent
    general_agent --> response[Response]

    %% Details verification
    ensure_details -->|Missing details| response
    ensure_details -->|Sufficient details| ancient_knowledge_router{Ancient Knowledge Router}

    %% Ancient knowledge routing
    ancient_knowledge_router -->|Already collected| medical_agent[Medical Agent]
    ancient_knowledge_router -->|Not collected| ancient_knowledge[Ancient Knowledge]

    %% Specialist agents - parallel execution
    ancient_knowledge --> allopathy_specialist[Allopathy Specialist]
    ancient_knowledge --> ayurveda_specialist[Ayurveda Specialist]
    ancient_knowledge --> tcm_kampo_specialist[TCM/Kampo Specialist]
    ancient_knowledge --> lifestyle_specialist[Lifestyle Specialist]

    %% Synthesis
    allopathy_specialist --> synthesis_and_safety[Synthesis and Safety]
    ayurveda_specialist --> synthesis_and_safety
    tcm_kampo_specialist --> synthesis_and_safety
    lifestyle_specialist --> synthesis_and_safety

    %% Final responses
    emergency_medical_agent --> response
    medical_agent --> response
    synthesis_and_safety --> response

    %% End
    response --> END([END])
```

## Tech Stack

- **Framework**: FastAPI
- **Orchestration**: LangGraph, LangChain
- **Database**: PostgreSQL (with `asyncpg` and `langgraph-checkpoint-postgres`)
- **Runtime**: Python 3.13+
- **Package Manager**: uv