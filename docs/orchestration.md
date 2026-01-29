# LangGraph Orchestration Flow - Mermaid Diagram

## Orchestration Graph

```mermaid
---
config:
  flowchart:
    curve: linear
---
%%{init: {'theme': 'neutral'}}%%
graph TD
    START([START]) -->|input_guardrail| input_guardrail{Input Guardrail}

    %% Input routing
    input_guardrail -->|General query| general_agent[General Agent]
    input_guardrail -->|Medical Query| medical_router[Medical Router]

    %%Medical routing
    medical_router -->|Emergency detected | emergency_medical_agent[Emergency Medical Agent]
    medical_router --> ensure_details[Ensure Details]

    %% General Agent
    general_agent --> response

    %% Profile and details
    ensure_details -->|request more details| response
    ensure_details -->|sufficient details| ancient_knowledge_router{Is Ancient Knowledge <br/> Collected?}

    %% Supervisor routing
    ancient_knowledge_router -->|Bypass if ancient knowledge <br/> is already collected | medical_agent
    ancient_knowledge_router -->|collect ancient knowledge <br/> only once | ancient_knowledge{Ancient Knowledge}

    %% Knowledge agents
    ancient_knowledge --> allopathy_specialist[Allopathy Specialist]
    ancient_knowledge --> ayurveda_specialist[Ayurveda Specialist]
    ancient_knowledge --> tcm_kampo_specialist[TCM/Kampo Specialist]
    ancient_knowledge --> lifestyle_specialist[Lifestyle Specialist]

    %% Synthesis
    allopathy_specialist --> synthesizer[Synthesizer]
    ayurveda_specialist --> synthesizer
    tcm_kampo_specialist --> synthesizer
    lifestyle_specialist --> synthesizer

    %% Safety & adjustments
    emergency_medical_agent --> response
    medical_agent --> response
    synthesizer --> response

    %% Response generation
    response --> END([END])

    %% Styling
    classDef processNode fill:#e1f5fe,stroke:#01579b,stroke-width:2px
    classDef decisionNode fill:#fff3e0,stroke:#e65100,stroke-width:2px
    classDef startEndNode fill:#c8e6c9,stroke:#1b5e20,stroke-width:3px

    class general_agent,allopathy_agent,ayurveda_agent,tcm_kampo_agent,lifestyle_agent processNode
    class load_profile,ensure_details,ancient_knowledge_router,ancient_knowledge,synthesis_node,contraindication_check,adjustment_node,medical_agent processNode
    class input_guardrail,ancient_knowledge_router,ancient_knowledge,contraindication_check decisionNode
    class START,END startEndNode
```

## Flow Description

### Phase 1: Input and Safety

- **START** → `input_guardrail`: Analyzes input for safety and appropriateness.
  - **Unsafe/Inappropriate** → `response` → **END**: Direct response for filtered content.
  - **General Query** → `general_agent` → `response` → **END**: Handles non-medical, casual conversation.
  - **Medical Query** → `load_profile`: Proceeds to load user context.

### Phase 2: Profile Loading and Detail Verification

- `load_profile`: Retrieves user profile and conversation history.
- `load_profile` → `ensure_details`: Validates if sufficient information exists to answer the medical query.
  - **Missing Critical Data** → `response` → **END**: Requests clarification from the user.
  - **Data Sufficient** → `medical_supervisor`: Proceeds to medical orchestration.

### Phase 3: Medical Supervisor

- `medical_supervisor`: Orchestrates the medical consultation flow and determines the approach.
  - **Direct Response Needed** → `response` → **END**: Provides immediate response for simple queries.
  - **Comprehensive Analysis Required** → `ancient_knowledge`: Triggers specialist agents.

### Phase 4: Specialist Agents (Parallel Execution)

- `ancient_knowledge`: Coordinates parallel execution of specialist agents to gather diverse medical perspectives:
  - `allopathy_agent`: Conventional medicine and evidence-based guidelines (uses PubMed RAG).
  - `tcm_kampo_agent`: Traditional Chinese Medicine and Kampo herbal medicine (uses Kampo DB).
  - `ayurveda_agent`: Ayurvedic principles and holistic remedies.
  - `lifestyle_agent`: Nutrition and lifestyle recommendations (uses Nutrition API).
- All specialist agents converge at `synthesis_node`.

### Phase 5: Synthesis and Safety Validation

- `synthesis_node`: Aggregates insights from all specialist agents into a cohesive draft response.
- `synthesis_node` → `contraindication_check`: Safety Layer - validates interactions between recommendations (e.g., Western medications vs. herbal supplements, dietary restrictions).
  - **Risk Detected** → `adjustment_node` → `response_generator`: Refines recommendations to eliminate safety risks.
  - **Safe** → `response_generator`: Proceeds directly to response generation.

### Phase 6: Response Generation and Memory Update

- `response_generator`: Formats the final comprehensive response for the user.
- `response_generator` → `profile_extractor`: Extracts and updates user profile with new health data or preferences learned during the session.
- `profile_extractor` → `response`: Prepares final response.
- `response` → **END**: Delivers response to user.

### Nodes

| Node | Type | Description |
|------|------|-------------|
| `input_guardrail` | Safety | Filters unsafe content and routes based on query type. |
| `general_agent` | Agent | Handles casual/general non-medical queries. |
| `load_profile` | Memory | Retrieves user history and health profile. |
| `ensure_details` | Decision | Validates if sufficient information exists to proceed with medical consultation. |
| `medical_supervisor` | Orchestrator | Decides if direct response is needed or if specialist agents should run. |
| `ancient_knowledge` | Orchestrator | Coordinates parallel execution of specialist medical agents. |
| `allopathy_agent` | Specialist | Western medicine expert with evidence-based guidelines. |
| `tcm_kampo_agent` | Specialist | Traditional Chinese Medicine and Kampo herbal medicine expert. |
| `ayurveda_agent` | Specialist | Ayurvedic medicine and holistic health expert. |
| `lifestyle_agent` | Specialist | Lifestyle, nutrition, and wellness expert. |
| `synthesis_node` | Logic | Combines specialist outputs into a cohesive draft response. |
| `contraindication_check` | Safety | Validates drug-herb-food interactions and safety conflicts. |
| `adjustment_node` | Logic | Modifies response to resolve safety conflicts identified by contraindication check. |
| `response_generator` | Output | Formats final comprehensive response for the user. |
| `profile_extractor` | Memory | Extracts and updates persistent user profile with new health data. |
| `response` | Output | Final response node that delivers output to the user. |
