import os
import sys
from pathlib import Path


# Make sure the ForgeAI root is importable.
ROOT = Path(__file__).resolve().parent

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def test_imports():
    """
    Verify that the main ForgeAI modules can be imported.
    """

    import agent
    import architecture
    import architecture_planner
    import celery_tasks
    import forgeai_graph
    import impact
    import impact_analyzer
    import llm_client
    import llm_router
    import main
    import repair_agent
    import state
    import tool_schemas
    import tools

    assert agent.Agent is not None
    assert architecture.ArchitecturePlan is not None
    assert architecture_planner.ArchitecturePlanner is not None
    assert celery_tasks.app is not None
    assert forgeai_graph.app is not None
    assert impact.ImpactReport is not None
    assert impact_analyzer.ImpactAnalyzer is not None
    assert llm_client.LLMClient is not None
    assert llm_router.LLMRouter is not None
    assert main.api is not None
    assert repair_agent.RepairAgent is not None
    assert state.AgentState is not None
    assert tool_schemas.TOOLS_SCHEMA is not None
    assert tools.dispatcher is not None


def test_agent_state():
    """
    Verify that AgentState can be created and serialized.
    """

    from state import AgentState

    state = AgentState(
        requirement="Build a test application.",
        status="running",
    )

    state.add_event(
        "test",
        "Backend validation event.",
    )

    state.add_changed_file(
        "index.html"
    )

    state.add_tool_call(
        "list_files",
        {},
    )

    state.add_tool_result(
        "list_files",
        ["index.html"],
    )

    data = state.to_dict()

    assert data["requirement"] == (
        "Build a test application."
    )

    assert data["status"] == "running"

    assert len(data["events"]) == 1

    assert data["changed_files"] == [
        "index.html"
    ]

    assert len(data["tool_calls"]) == 1

    assert len(data["tool_results"]) == 1


def test_llm_router():
    """
    Verify deterministic LLM routing without calling an LLM.
    """

    from llm_router import LLMRouter

    router = LLMRouter()

    simple = router.route(
        "Create a simple HTML page."
    )

    complex_task = router.route(
        "Design a scalable distributed architecture."
    )

    repair = router.route(
        "Fix the failing test."
    )

    assert simple["category"] == "simple"

    assert complex_task["category"] == "complex"

    assert repair["category"] == "repair"


def test_tool_registry():
    """
    Verify that all expected tools are registered.
    """

    from tools import TOOLS

    expected_tools = {
        "list_files",
        "read_file",
        "write_file",
        "edit_file",
        "run_command",
        "start_server",
        "git_status",
        "git_diff",
        "git_log",
        "web_search",
    }

    assert expected_tools.issubset(
        set(TOOLS.keys())
    )


def test_database():
    """
    Verify database initialization and task persistence.
    """

    from src.db.database import (
        SessionLocal,
        init_db,
    )

    from src.db.models import Task

    init_db()

    session = SessionLocal()

    try:

        task = Task(
            requirement="Backend database test.",
            status="pending",
        )

        session.add(task)
        session.commit()
        session.refresh(task)

        task_id = task.id

        assert task_id is not None

        stored = session.get(
            Task,
            task_id,
        )

        assert stored is not None

        assert stored.requirement == (
            "Backend database test."
        )

        assert stored.status == "pending"

        session.delete(stored)
        session.commit()

    finally:

        session.close()


def test_api():
    """
    Verify the FastAPI application without
    starting a real HTTP server.
    """

    from fastapi.testclient import TestClient

    from main import api

    with TestClient(api) as client:

        response = client.get(
            "/"
        )

        assert response.status_code == 200

        data = response.json()

        assert data["name"] == "ForgeAI"

        assert data["status"] == "online"

        response = client.get(
            "/health"
        )

        assert response.status_code == 200

        assert response.json() == {
            "status": "healthy"
        }


def test_tool_path_security():
    """
    Verify that the file tools reject paths that escape
    the ForgeAI workspace.
    """

    from tools import read_file

    try:
        read_file("../../outside.txt")
    except (ValueError, FileNotFoundError):
        return

    raise AssertionError(
        "Path traversal was not rejected."
    )


def test_empty_requirement_rejected():
    """
    Verify that the agent refuses an empty requirement.
    """

    from agent import Agent

    class FakeLLM:
        pass

    agent = Agent(
        llm_client=FakeLLM(),
        dispatcher=lambda name, args: None,
        tool_schemas=[],
    )

    try:

        agent.run(
            user_input=""
        )

    except ValueError as exc:

        assert (
            "non-empty requirement"
            in str(exc)
        )

        return

    raise AssertionError(
        "Empty requirement was not rejected."
    )