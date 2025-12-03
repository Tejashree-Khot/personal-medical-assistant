# Medical Personalized Agent

## Overview

The **Medical Personalized Agent** is an advanced AI assistant designed to provide comprehensive, personalized medical advice. It uniquely bridges the gap between modern Western medicine (Allopathy) and traditional healing systems (Ayurveda, TCM/Kampo), while integrating lifestyle and nutritional guidance.

Crucially, the system implements a safety layer—a rigorous contraindication check that ensures traditional remedies (e.g., herbal supplements) do not negatively interact with modern prescriptions or specific patient conditions (e.g., hypertension).

## Key Features

- **Multi-Perspective Analysis**: Aggregates insights from:
  - **Allopathy Agent**: Evidence-based modern medicine guidelines.
  - **Ayurveda Agent**: Ancient Indian holistic healing principles.
  - **TCM/Kampo Agent**: Traditional Chinese and Japanese herbal medicine.
  - **Lifestyle Agent**: Nutrition, exercise, and daily routine recommendations.
- **Safety First Architecture**:
  - **Input Guardrails**: Detects emergencies and blocks unsafe content immediately.
  - **Contraindication Check**: Cross-references all recommendations against the user's health profile to prevent adverse interactions.
- **Personalized Health Profile**: Maintains a persistent user profile (medical history, allergies, location) to tailor advice (e.g., regional diet plans).
- **Orchestrated Workflow**: Uses **LangGraph** to manage complex decision-making flows, ensuring data sufficiency before generating responses.

## Architecture

The system follows a multi-phase orchestration flow:

1. **Input & Safety**: Triage for emergencies.
2. **Routing**: Classifies queries as General or Medical.
3. **Medical Orchestration**: Gathers missing critical data from the user.
4. **Parallel Execution**: Specialist agents run concurrently to generate diverse insights.
5. **Synthesis & Safety**: Merges insights and runs the interaction check.
6. **Response & Memory**: Delivers the final safe response and updates the user profile.

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

```bash
uv run uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`.
