import json
import os
import subprocess
import sys
from pathlib import Path

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph

from agent import Agent
from architecture_planner import ArchitecturePlanner
from impact_analyzer import ImpactAnalyzer
from llm_client import LLMClient
from repair_agent import RepairAgent
from state import AgentState
from tool_schemas import TOOLS_SCHEMA
from tools import ROOT, dispatcher


# ============================================================
# Configuration
# ============================================================

WORKSPACE = Path(
    os.getenv(
        "FORGEAI_WORKSPACE",
        str(ROOT),
    )
).resolve()

API_PORT = int(
    os.getenv(
        "FORGEAI_API_PORT",
        "8000",
    )
)

APP_PORT = int(
    os.getenv(
        "FORGEAI_APP_PORT",
        "8001",
    )
)


# ============================================================
# Shared services
# ============================================================

llm_client = LLMClient()

agent = Agent(
    llm_client=llm_client,
    dispatcher=dispatcher,
    tool_schemas=TOOLS_SCHEMA,
)

architecture_planner = ArchitecturePlanner(
    llm_client=llm_client,
)

impact_analyzer = ImpactAnalyzer(
    llm_client=llm_client,
)

repair_agent = RepairAgent(
    agent=agent,
    dispatcher=dispatcher,
)


# ============================================================
# Utility helpers
# ============================================================

def _workspace_files() -> list[str]:
    """
    Return visible files in the generated workspace.
    """

    if not WORKSPACE.exists():
        return []

    files = []

    for path in WORKSPACE.rglob("*"):

        if not path.is_file():
            continue

        relative = path.relative_to(
            WORKSPACE
        )

        parts = relative.parts

        if any(
            part in {
                ".git",
                ".venv",
                "venv",
                "__pycache__",
                "node_modules",
            }
            for part in parts
        ):
            continue

        files.append(
            str(relative)
        )

    return sorted(files)


def _find_test_command() -> str | None:
    """
    Determine a safe validation command based on
    the generated project.
    """

    files = _workspace_files()

    # Python test suite
    if any(
        path.startswith("test_")
        or Path(path).name.startswith("test_")
        or Path(path).name.endswith("_test.py")
        for path in files
    ):
        return "pytest"

    # Node project with an explicit test script
    package_path = WORKSPACE / "package.json"

    if package_path.exists():

        try:

            package = json.loads(
                package_path.read_text(
                    encoding="utf-8"
                )
            )

            scripts = package.get(
                "scripts",
                {},
            )

            if "test" in scripts:
                return "npm test"

        except (
            OSError,
            json.JSONDecodeError,
        ):
            pass

    # Static HTML still gets structural validation below.
    if "index.html" in files:
        return None

    return None


def _validate_html() -> dict:
    """
    Validate a generated index.html without requiring
    an external browser or another LLM.
    """

    path = WORKSPACE / "index.html"

    if not path.exists():
        return {
            "passed": False,
            "message": "index.html does not exist.",
        }

    try:
        content = path.read_text(
            encoding="utf-8"
        )
    except OSError as exc:
        return {
            "passed": False,
            "message": f"Unable to read index.html: {exc}",
        }

    normalized = content.lower()

    required_tokens = (
        "<html",
        "<head",
        "<body",
        "</body>",
        "</html>",
    )

    missing = [
        token
        for token in required_tokens
        if token not in normalized
    ]

    if missing:
        return {
            "passed": False,
            "message": (
                "index.html is missing required HTML "
                f"elements: {', '.join(missing)}"
            ),
        }

    visible_content = (
        normalized
        .replace("<html>", "")
        .replace("<head>", "")
        .replace("</head>", "")
        .replace("<body>", "")
        .replace("</body>", "")
        .replace("</html>", "")
        .strip()
    )

    if not visible_content:
        return {
            "passed": False,
            "message": "index.html contains no meaningful content.",
        }

    return {
        "passed": True,
        "message": "index.html passed structural validation.",
    }


def _run_validation(
    command: str,
) -> dict:
    """
    Run an allowed project validation command directly.

    We intentionally do not use a shell.
    """

    try:

        if os.name == "nt":

            if command.startswith("npm "):
                executable = "npm.cmd"
                arguments = command.split()[1:]
            else:
                parts = command.split()
                executable = parts[0]
                arguments = parts[1:]

        else:

            parts = command.split()
            executable = parts[0]
            arguments = parts[1:]

        process = subprocess.run(
            [
                executable,
                *arguments,
            ],
            cwd=str(WORKSPACE),
            capture_output=True,
            text=True,
            timeout=120,
            shell=False,
        )

        return {
            "exit_code": process.returncode,
            "stdout": process.stdout,
            "stderr": process.stderr,
        }

    except subprocess.TimeoutExpired as exc:

        return {
            "exit_code": -1,
            "stdout": exc.stdout or "",
            "stderr": (
                "Validation timed out after 120 seconds."
            ),
        }

    except OSError as exc:

        return {
            "exit_code": -1,
            "stdout": "",
            "stderr": str(exc),
        }


def _find_launch_target() -> str | None:
    """
    Determine what kind of generated application can be launched.
    """

    package_path = WORKSPACE / "package.json"

    if package_path.exists():

        try:

            package = json.loads(
                package_path.read_text(
                    encoding="utf-8"
                )
            )

            scripts = package.get(
                "scripts",
                {},
            )

            if "dev" in scripts:
                return "npm_dev"

            if "start" in scripts:
                return "npm_start"

        except (
            OSError,
            json.JSONDecodeError,
        ):
            pass

    if (WORKSPACE / "index.html").exists():
        return "static_html"

    if (WORKSPACE / "main.py").exists():
        return "python_main"

    if (WORKSPACE / "app.py").exists():
        return "python_app"

    return None


def _launch_application() -> dict:
    """
    Launch the generated application on a port that does not
    conflict with the ForgeAI API.
    """

    target = _find_launch_target()

    if target is None:
        return {
            "launched": False,
            "message": "No supported application entry point found.",
        }

    try:

        if target == "static_html":

            command = [
                sys.executable,
                "-m",
                "http.server",
                str(APP_PORT),
            ]

        elif target == "python_main":

            command = [
                sys.executable,
                "main.py",
            ]

        elif target == "python_app":

            command = [
                sys.executable,
                "app.py",
            ]

        elif target == "npm_dev":

            if os.name == "nt":
                command = [
                    "npm.cmd",
                    "run",
                    "dev",
                    "--",
                    "--port",
                    str(APP_PORT),
                ]
            else:
                command = [
                    "npm",
                    "run",
                    "dev",
                    "--",
                    "--port",
                    str(APP_PORT),
                ]

        elif target == "npm_start":

            if os.name == "nt":
                command = [
                    "npm.cmd",
                    "start",
                ]
            else:
                command = [
                    "npm",
                    "start",
                ]

        else:
            return {
                "launched": False,
                "message": "Unsupported launch target.",
            }

        process = subprocess.Popen(
            command,
            cwd=str(WORKSPACE),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            shell=False,
        )

        if target == "static_html":
            url = (
                f"http://localhost:{APP_PORT}"
            )
        else:
            url = (
                f"http://localhost:{APP_PORT}"
            )

        return {
            "launched": True,
            "pid": process.pid,
            "url": url,
            "command": " ".join(command),
        }

    except OSError as exc:

        return {
            "launched": False,
            "message": str(exc),
        }


# ============================================================
# Graph nodes
# ============================================================

def planner_node(
    state: AgentState,
) -> AgentState:

    state.set_status(
        "running",
        "planning",
    )

    state.add_event(
        "planning_started",
        "Analyzing the software requirement.",
    )

    plan = architecture_planner.plan(
        state.requirement
    )

    state.plan = plan.model_dump_json(
        indent=2
    )

    state.add_event(
        "planning_completed",
        "Architecture plan generated.",
    )

    return state


def impact_node(
    state: AgentState,
) -> AgentState:

    state.set_status(
        "running",
        "impact_analysis",
    )

    state.add_event(
        "impact_analysis_started",
        "Inspecting the existing project.",
    )

    report = impact_analyzer.analyze(
        requirement=state.requirement,
        architecture_plan=state.plan,
    )

    state.impact_report = report.model_dump_json(
        indent=2
    )

    state.add_event(
        "impact_analysis_completed",
        "Impact analysis completed.",
    )

    return state


def executor_node(
    state: AgentState,
) -> AgentState:

    state.set_status(
        "running",
        "execution",
    )

    state.add_event(
        "execution_started",
        "Autonomous implementation started.",
    )

    result = agent.run(
        user_input=state.requirement,
        state=state,
        architecture_plan=state.plan,
        impact_report=state.impact_report,
    )

    state = result

    state.set_status(
        "running",
        "execution",
    )

    state.add_event(
        "execution_completed",
        "Implementation phase completed.",
    )

    return state


def test_node(
    state: AgentState,
) -> AgentState:

    state.set_status(
        "running",
        "testing",
    )

    state.add_event(
        "testing_started",
        "Validating the generated implementation.",
    )

    html_result = _validate_html()

    if not html_result["passed"]:
        if (
            WORKSPACE / "index.html"
        ).exists():

            state.test_command = "html_validation"

            state.test_result = {
                "exit_code": 1,
                "stdout": "",
                "stderr": html_result["message"],
            }

            state.add_event(
                "testing_failed",
                html_result["message"],
            )

            return state

    if (
        WORKSPACE / "index.html"
    ).exists():

        if html_result["passed"]:

            state.test_command = "html_validation"

            state.test_result = {
                "exit_code": 0,
                "stdout": html_result["message"],
                "stderr": "",
            }

            state.add_event(
                "testing_passed",
                "HTML structural validation passed.",
            )

            return state

    command = _find_test_command()

    if command is None:

        state.test_command = ""

        state.test_result = {
            "exit_code": 0,
            "stdout": (
                "No automated test suite was found. "
                "No test command was required."
            ),
            "stderr": "",
        }

        state.add_event(
            "testing_passed",
            "No automated test suite was found.",
        )

        return state

    state.test_command = command

    result = _run_validation(
        command
    )

    state.test_result = result

    if result["exit_code"] == 0:

        state.add_event(
            "testing_passed",
            "Validation passed.",
        )

    else:

        state.add_event(
            "testing_failed",
            "Validation failed.",
            exit_code=result["exit_code"],
        )

    return state


def repair_node(
    state: AgentState,
) -> AgentState:

    state.set_status(
        "running",
        "repair",
    )

    state.add_event(
        "repair_started",
        "Attempting autonomous repair.",
    )

    result = repair_agent.repair(
        state=state,
        test_command=state.test_command,
    )

    if result.get("success"):

        state.add_event(
            "repair_completed",
            "Autonomous repair completed successfully.",
        )

    else:

        state.add_event(
            "repair_failed",
            "Autonomous repair could not resolve the failure.",
        )

    return state


def launch_node(
    state: AgentState,
) -> AgentState:

    state.set_status(
        "running",
        "launch",
    )

    state.add_event(
        "launch_started",
        "Preparing the generated application.",
    )

    launch_result = _launch_application()

    state.result = {
        "status": "completed",
        "message": (
            "Application implemented, validated, and launched."
        ),
        "changed_files": state.changed_files,
        "test_result": state.test_result,
        "launch": launch_result,
    }

    if launch_result.get("launched"):

        state.add_event(
            "launch_completed",
            "Application launched successfully.",
            url=launch_result["url"],
            pid=launch_result["pid"],
        )

        state.status = "completed"

    else:

        state.add_event(
            "launch_skipped",
            launch_result.get(
                "message",
                "Application could not be launched.",
            ),
        )

        state.status = "completed"

    return state


def failed_node(
    state: AgentState,
) -> AgentState:

    state.status = "failed"

    state.current_step = "failed"

    state.result = {
        "status": "failed",
        "message": (
            "ForgeAI could not complete the requested "
            "implementation."
        ),
        "changed_files": state.changed_files,
        "test_result": state.test_result,
        "errors": state.errors,
    }

    state.add_event(
        "execution_failed",
        "ForgeAI execution failed.",
    )

    return state


# ============================================================
# Conditional routing
# ============================================================

def route_after_test(
    state: AgentState,
) -> str:

    result = state.test_result

    if result.get("exit_code") == 0:
        return "launch"

    if state.repair_attempts >= state.max_repair_attempts:
        return "failed"

    return "repair"


def route_after_repair(
    state: AgentState,
) -> str:

    if (
        state.test_result.get("exit_code")
        == 0
    ):
        return "launch"

    if (
        state.repair_attempts
        >= state.max_repair_attempts
    ):
        return "failed"

    return "test"


# ============================================================
# Build graph
# ============================================================

builder = StateGraph(
    AgentState
)

builder.add_node(
    "planner",
    planner_node,
)

builder.add_node(
    "impact",
    impact_node,
)

builder.add_node(
    "executor",
    executor_node,
)

builder.add_node(
    "test",
    test_node,
)

builder.add_node(
    "repair",
    repair_node,
)

builder.add_node(
    "launch",
    launch_node,
)

builder.add_node(
    "failed",
    failed_node,
)


builder.add_edge(
    START,
    "planner",
)

builder.add_edge(
    "planner",
    "impact",
)

builder.add_edge(
    "impact",
    "executor",
)

builder.add_edge(
    "executor",
    "test",
)

builder.add_conditional_edges(
    "test",
    route_after_test,
    {
        "launch": "launch",
        "repair": "repair",
        "failed": "failed",
    },
)

builder.add_conditional_edges(
    "repair",
    route_after_repair,
    {
        "test": "test",
        "launch": "launch",
        "failed": "failed",
    },
)

builder.add_edge(
    "launch",
    END,
)

builder.add_edge(
    "failed",
    END,
)


# ============================================================
# Compile
# ============================================================

checkpointer = InMemorySaver()

app = builder.compile(
    checkpointer=checkpointer
)