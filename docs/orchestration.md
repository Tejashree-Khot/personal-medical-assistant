# LangGraph Orchestration Flow - Mermaid Diagram

## Orchestration Graph

```mermaid
%%{init: {'theme': 'neutral'}}%%
graph TD
    START([START]) -->|route_input| route_input{Route Input}

    %% Input routing
    route_input -->|query_type != MEDICAL| query_classification{Query Classification}
    route_input -->|query_type = MEDICAL| medical_agent{Medical Agent}

    %% Query classification routing
    query_classification -->|GENERAL| general_agent[General Agent]
    query_classification -->|MEDICAL| medical_agent{Medical Agent}

    %% General agent
    general_agent --> response

    %% Medical agent
    medical_agent --> response

    %% Final steps
    response --> END([END])

    %% Styling
    classDef processNode fill:#e1f5fe,stroke:#01579b,stroke-width:2px
    classDef decisionNode fill:#fff3e0,stroke:#e65100,stroke-width:2px
    classDef startEndNode fill:#c8e6c9,stroke:#1b5e20,stroke-width:3px

    class general_agent,medical_agent,response processNode
    class route_input,query_classification decisionNode
    class START,END startEndNode
```

## Flow Description

### Entry Point
- **START** → `route_input` (Route Input decision)

### Main Routing Paths

#### 1. Route Input (`route_input`)
Determines initial routing based on query type and state:
- **query_type != "MEDICAL"** → Go to `query_classification`
- **query_type = "MEDICAL"** → Go to `medical_agent`

#### 2. Query Classification (`route_classification`)
Classifies the user query:
- **query_type = "GENERAL"** → Go to `general_agent`
- **query_type = "MEDICAL"** → Go to `medical_agent`

#### 3. General Agent
Handles general queries:
- → `response` → END

#### 4. Medical Agent
Handles medical queries:
- → `response` → END

### Nodes

| Node | Description |
|------|-------------|
| `route_input` | Routes based on query type and session state |
| `query_classification` | Classifies query as GENERAL or MEDICAL |
| `general_agent` | Handles general queries |
| `medical_agent` | Handles medical queries |
| `response` | Sends response to user |
