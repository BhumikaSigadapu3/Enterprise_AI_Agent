# Enterprise AI Agent Platform

An end-to-end **AI engineering project** that demonstrates a multi-step enterprise agent workflow using **LangGraph**, **FastAPI**, **RAG**, and the **Model Context Protocol (MCP)**.

The system processes supported tasks, selects appropriate tools, retrieves information from an enterprise knowledge base, performs calculations, executes multi-step workflows, and returns structured responses with execution traces.

**Stack:** Python · FastAPI · LangGraph · LangChain/OpenAI · MCP · ChromaDB · Sentence Transformers · Docker · Pytest · GitHub Actions

---

## Overview

This project implements an agent-style workflow for enterprise tasks. It combines workflow orchestration, retrieval, tool execution, guardrails, and evaluation in a single backend application.

The workflow supports:

- Enterprise document retrieval
- Safe calculator execution
- Multi-step task processing
- Tool permission validation
- Prompt-injection checks
- Execution tracing
- MCP-based tool integration
- RAG-based knowledge retrieval
- Evaluation and testing
- Docker deployment

---

## Architecture

```text
User Request
    |
    v
Input Guardrails
    |
    v
Task Planning
    |
    v
LangGraph Orchestrator
    |
    +----------------------+----------------------+
    |                      |                      |
    v                      v                      v
Document Search         Calculator             Research
    |                      |                      |
    +----------------------+----------------------+
                           |
                           v
                    Tool Execution
                           |
                           v
                    Evidence Collection
                           |
                           v
                    Response Generation
                           |
                           v
                    Output Validation
                           |
                           v
                    Final Response
```

The LangGraph workflow manages task routing and tool execution for supported tasks. Tool outputs are collected as evidence and used to construct the final response.

---

## Example Workflow

For a request such as:

> According to the employee policy, how many annual leave days correspond to 3 months of a 20-day yearly allowance?

The workflow can:

1. Search the enterprise knowledge base for relevant leave policy information.
2. Retrieve the required policy context.
3. Perform the required calculation.
4. Collect the tool outputs.
5. Return a structured final response with execution details.

---

## Key Features

- **LangGraph orchestration** for multi-step execution
- Task routing for supported workflows
- **RAG pipeline** using ChromaDB and sentence-transformer embeddings
- Enterprise document ingestion and retrieval
- Safe calculator tool
- External research integration
- **MCP client/server integration** for enterprise tools
- Tool permission enforcement
- Prompt-injection heuristics and output validation
- Structured execution traces
- Sample enterprise knowledge base bootstrapping
- Evaluation harness for answer quality, tool accuracy, latency, and completion
- Unit tests and GitHub Actions CI
- Docker deployment

---

## Project Structure

```text
enterprise-ai-agent-platform/
│
├── app/
│   ├── agent/
│   │   ├── graph.py          # LangGraph workflow
│   │   └── state.py          # Agent state
│   ├── api/
│   │   └── routes.py         # FastAPI endpoints
│   ├── guardrails/
│   │   └── security.py       # Input/output/tool guardrails
│   ├── llm/
│   │   ├── client.py         # Shared LLM client
│   │   └── prompts.py        # LLM prompts
│   ├── mcp/
│   │   └── client.py         # MCP client
│   ├── observability/
│   ├── rag/
│   │   └── store.py          # ChromaDB document store
│   ├── tools/
│   │   └── registry.py       # Local/external tool implementations
│   ├── config.py
│   ├── main.py
│   └── models.py
│
├── evaluation/
│   ├── dataset.json
│   └── run_evaluation.py
│
├── mcp_server/
│   └── server.py             # MCP tool server
│
├── sample_data/
│   └── employee_policy.txt
│
├── tests/
│   ├── test_guardrails.py
│   ├── test_agent_routing.py
│   └── test_tools.py
│
├── .github/workflows/ci.yml
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

---

## Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/BhumikaSigadapu3/Enterprise_AI_Agent.git
cd enterprise-ai-agent-platform
```

### 2. Create a virtual environment

**Windows:**

```bash
python -m venv .venv
.venv\Scripts\activate
```

**Linux/macOS:**

```bash
python -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

On Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

Add your API key:

```env
OPENAI_API_KEY=your_key_here
OPENAI_MODEL=gpt-4o-mini
MCP_ENABLED=true
```

> `.env` is ignored by Git and should never be committed.

### 5. Start the API

```bash
uvicorn app.main:app --reload
```

Open:

- Swagger UI: `http://127.0.0.1:8000/docs`
- Health endpoint: `http://127.0.0.1:8000/health`

On startup, the bundled `sample_data/employee_policy.txt` can be indexed for enterprise document retrieval.

---

## API Usage

### Run the agent

```bash
curl -X POST http://127.0.0.1:8000/agent/run \
  -H "Content-Type: application/json" \
  -d '{
    "task": "According to the employee policy, how many annual leave days correspond to 3 months of a 20-day yearly allowance?",
    "session_id": "demo-session",
    "allowed_tools": ["document_search", "calculator"]
  }'
```

The response can include:

- Final response
- Execution plan
- Tool calls and inputs
- Tool outputs
- Execution trace
- Latency information
- Validation results

### Ingest a document

```bash
curl -X POST http://127.0.0.1:8000/documents/ingest \
  -F "file=@sample_data/employee_policy.txt"
```

### Search documents directly

```bash
curl -X POST http://127.0.0.1:8000/documents/search \
  -H "Content-Type: application/json" \
  -d '{"query": "employee leave policy", "k": 4}'
```

---

## RAG Pipeline

The project uses ChromaDB and sentence-transformer embeddings to retrieve relevant enterprise knowledge.

```text
Enterprise Document
        |
        v
Text Processing
        |
        v
Embedding Generation
        |
        v
ChromaDB Vector Store
        |
        v
Similarity Search
        |
        v
Relevant Context
        |
        v
Agent Workflow
```

The bundled sample enterprise policy document is used to demonstrate document ingestion and retrieval.

---

## MCP Integration

The project includes both an MCP client and server for exposing enterprise capabilities through the Model Context Protocol.

```text
LangGraph Agent
      |
      v
MCP Client
      |
      v
MCP Server
      |
      +--> search_enterprise_documents
      |
      +--> calculate
```

The MCP layer provides a standardized boundary for integrating external tools with the agent workflow.

You can also run the MCP server manually:

```bash
python -m mcp_server.server
```

---

## Guardrails

The project includes basic security and validation mechanisms, including:

- Tool permission validation
- Prompt-injection detection heuristics
- Safe calculator expression handling
- Output validation
- Tool execution limits

These checks help reduce unsafe or unauthorized tool execution.

---

## Evaluation

Run:

```bash
python -m evaluation.run_evaluation
```

The evaluation reports metrics such as:

- Response keyword quality
- Required tool-call accuracy
- Task completion rate
- Average latency

The dataset includes examples involving:

1. Calculator tasks
2. Enterprise RAG retrieval tasks
3. Multi-step RAG and calculation tasks

---

## Tests

Run:

```bash
pytest -q
```

The tests cover:

- Prompt-injection guardrails
- Tool permission checks
- Agent routing
- Safe calculator execution
- Rejection of unsafe calculator expressions

GitHub Actions runs the test suite on pushes and pull requests.

---

## Docker

Build and run:

```bash
docker compose up --build
```

The API becomes available at:

```text
http://localhost:8000
```

---

## Design Decisions

### Why LangGraph?

LangGraph provides a structured way to model multi-step workflows with explicit state transitions.

The project uses LangGraph to manage:

- Agent state
- Tool execution
- Workflow routing
- Iterative task processing
- Final response generation

### Why RAG?

Enterprise applications often need answers grounded in internal knowledge.

The RAG pipeline retrieves relevant information from indexed documents and makes that information available to the agent workflow.

### Why MCP?

MCP provides a standardized protocol boundary for exposing external capabilities as tools.

This allows enterprise capabilities to be integrated separately from the core agent workflow.

### Why Guardrails?

Tool-using systems can execute actions based on user input.

Permission checks and input validation help reduce unsafe or unauthorized tool execution.

---

## Suggested GitHub Demo

For a strong project demonstration:

1. Start the FastAPI server.
2. Open Swagger UI.
3. Run a document retrieval task.
4. Run a calculator task.
5. Run a multi-step RAG and calculation task.
6. Inspect the execution trace.
7. Demonstrate MCP tools.
8. Run the evaluation harness.
9. Run the test suite.
10. Demonstrate Docker deployment.

---

## Future Improvements

- Add fully LLM-driven task planning with structured output
- Add LLM-based response synthesis grounded in tool evidence
- Add Redis-backed conversation memory
- Add human-in-the-loop approval for sensitive tools
- Add tool retries and timeout policies
- Add a production web-search provider
- Add document support for PDF and DOCX files
- Add authentication and role-based tool permissions
- Add LangSmith or OpenTelemetry tracing

---

## Author

**Bhumika Sigadapu**

- GitHub: https://github.com/BhumikaSigadapu3
- Project Repository: https://github.com/BhumikaSigadapu3/Enterprise_AI_Agent
