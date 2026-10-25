# ForgeAI — AI-Powered Engineering Assistant

ForgeAI is an AI-powered engineering assistant designed to explore how autonomous AI agents can assist with software development tasks, from understanding requirements and analyzing codebases to diagnosing failures and supporting code repair.

The project combines agent orchestration, tool calling, architecture planning, impact analysis, and repair workflows into a Python-based engineering system.

> **Project status:** Active development. Features, integrations, and execution workflows are evolving as the system is tested and improved.

## Overview

Traditional AI coding assistants primarily focus on generating code from prompts. ForgeAI explores a broader engineering workflow: understanding a task, gathering relevant context, selecting appropriate tools, analyzing potential changes, and assisting with implementation and debugging.

The goal is to build a system that makes AI-assisted software engineering more structured, context-aware, and practical.

## Key Capabilities

- **AI Agent Orchestration:** Organizes engineering tasks through agent-based workflows.
- **Requirement Analysis:** Parses development requirements to help determine the work needed.
- **Architecture Planning:** Explores potential application structures and implementation approaches.
- **Codebase Impact Analysis:** Helps reason about the components that may be affected by a proposed change.
- **Tool Calling:** Connects agent reasoning with programmatic tools and structured tool schemas.
- **Debugging and Repair Workflows:** Includes components for analyzing failures and supporting code repair.
- **Backend and Data Management:** Uses a Python backend and database-related components to support application workflows.
- **Testing:** Includes automated tests for key components and workflows.

*The availability and maturity of individual capabilities depend on the current implementation. Not every workflow should be assumed to be production-ready or fully autonomous.*

## Architecture

ForgeAI is organized around several cooperating components:

```text
              User Request
                   |
                   v
          Requirement Analysis
                   |
                   v
          Agent Orchestration
                   |
          +--------+---------+
          |        |         |
          v        v         v
      Architecture Impact   Tool
        Planning  Analysis  Execution
          |        |         |
          +--------+---------+
                   |
                   v
          Diagnosis and Repair
                   |
                   v
          Results and Feedback
```

This diagram represents the intended high-level workflow; the exact execution path depends on the implemented components and task.

## Technology Stack

The repository includes components built around the following technologies and engineering concepts:

- **Language:** Python
- **Backend:** Python API/backend components
- **AI Architecture:** Agent orchestration, LLM integration, and structured tool calling
- **Workflow Design:** Graph-based agent workflows
- **Database:** Database integration and data models
- **Testing:** Pytest and component-level tests
- **Frontend:** HTML-based frontend entry point

Refer to the source code and dependency files for the exact libraries and versions used by the current implementation.

## Project Structure

```text
ForgeAI/
├── agent.py
├── architecture.py
├── architecture_planner.py
├── forgeai_graph.py
├── impact.py
├── impact_analyzer.py
├── llm_client.py
├── llm_router.py
├── main.py
├── repair_agent.py
├── requirement_parser.py
├── state.py
├── tool_schemas.py
├── tools.py
├── database.py
├── models/
├── src/
│   └── db/
├── frontend/
│   └── index.html
├── tests and test modules
├── requirements.txt
├── .env.example
└── README.md
```

*This is a simplified overview of the main components, not an exhaustive file listing.*

## Getting Started

### Prerequisites

- Python installed
- Git
- An API key for the LLM provider configured by the project, if required
- Any additional services required by the current configuration

### 1. Clone the repository

```bash
git clone https://github.com/abhisheksingh-cpu/ForgeAI.git
cd ForgeAI
```

### 2. Create a virtual environment

**Windows PowerShell**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a local `.env` file using `.env.example` as a reference.

Add the credentials and configuration required by the integrations actually enabled in your setup. Never commit real API keys, passwords, or other secrets.

### 5. Run the application

Inspect `main.py` and the project's current configuration to determine the supported entry point. If `main.py` exposes the application through FastAPI, the development server can typically be started with:

```bash
uvicorn main:app --reload
```

This command assumes that the FastAPI application object is named `app`. Adjust it if the actual entry point differs.

## Testing

The repository includes test modules covering agent behavior, architecture planning, backend functionality, tool execution, and repair-related components.

Run the tests with:

```bash
pytest -v
```

Some tests may require environment variables, external services, or provider credentials. Configure those dependencies before running the full suite.

## Engineering Principles

ForgeAI is being developed around several practical engineering goals:

1. **Structured workflows:** Break complex engineering tasks into manageable stages.
2. **Tool-assisted reasoning:** Use programmatic tools to gather context and perform supported operations.
3. **Modularity:** Keep orchestration, analysis, data access, and repair logic in separate components where practical.
4. **Testability:** Validate component behavior through repeatable tests.
5. **Maintainability:** Prefer understandable, extensible workflows over unnecessary complexity.

## Roadmap

Planned areas for further development include:

- Improving task planning and agent coordination
- Strengthening codebase understanding and change-impact analysis
- Making debugging and repair workflows more reliable
- Improving execution safeguards and failure handling
- Expanding automated test coverage
- Improving the developer interface and setup experience
- Documenting end-to-end workflows with reproducible examples

These are development goals, not claims that every feature is already implemented.

## Current Limitations

ForgeAI is an evolving project. AI-generated analysis and repair suggestions may be incorrect, and tool execution can introduce unintended changes. Review generated changes and use an isolated development environment when experimenting with code execution or repair.

Production use would require additional validation of security boundaries, permissions, error handling, observability, and recovery behavior.

## Contributing

Contributions, bug reports, and suggestions are welcome. Before submitting a change:

1. Describe the problem or improvement.
2. Keep changes focused and understandable.
3. Run the relevant tests.
4. Document any new configuration requirements.
5. Never include credentials or private data.

## Author

**Abhishek Singh**

GitHub: [@abhisheksingh-cpu](https://github.com/abhisheksingh-cpu)

## License

No license has been specified yet. Until a license is added to the repository, permissions to reuse, modify, or redistribute the code are not explicitly granted.
