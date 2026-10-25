import json
from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class AgentState:
    """
    Complete execution state for a ForgeAI task.

    This state is shared across the LangGraph workflow and is also
    serializable so that execution can be inspected or resumed.
    """

    # ---------------------------------------------------------
    # Request
    # ---------------------------------------------------------

    requirement: str = ""

    # ---------------------------------------------------------
    # Overall execution
    # ---------------------------------------------------------

    status: str = "pending"
    current_step: str = "start"

    # ---------------------------------------------------------
    # Planning
    # ---------------------------------------------------------

    plan: str = ""
    impact_report: str = ""

    # ---------------------------------------------------------
    # Agent conversation
    # ---------------------------------------------------------

    messages: list[dict[str, Any]] = field(default_factory=list)

    # ---------------------------------------------------------
    # Tool execution
    # ---------------------------------------------------------

    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    tool_results: list[dict[str, Any]] = field(default_factory=list)

    # ---------------------------------------------------------
    # Files
    # ---------------------------------------------------------

    changed_files: list[str] = field(default_factory=list)

    # ---------------------------------------------------------
    # Validation
    # ---------------------------------------------------------

    test_command: str = ""
    test_result: dict[str, Any] = field(default_factory=dict)

    # ---------------------------------------------------------
    # Repair
    # ---------------------------------------------------------

    repair_attempts: int = 0
    max_repair_attempts: int = 3

    # ---------------------------------------------------------
    # Execution limits
    # ---------------------------------------------------------

    iterations: int = 0
    max_iterations: int = 20

    # ---------------------------------------------------------
    # Errors
    # ---------------------------------------------------------

    errors: list[dict[str, Any]] = field(default_factory=list)

    # ---------------------------------------------------------
    # Human approval
    # ---------------------------------------------------------

    approval: str = ""

    # ---------------------------------------------------------
    # Live execution events
    # ---------------------------------------------------------

    events: list[dict[str, Any]] = field(default_factory=list)

    # ---------------------------------------------------------
    # Final result
    # ---------------------------------------------------------

    result: dict[str, Any] = field(default_factory=dict)

    # ---------------------------------------------------------
    # Utility methods
    # ---------------------------------------------------------

    def add_event(
        self,
        event_type: str,
        message: str,
        **data: Any
    ) -> None:
        """
        Add a structured event to the execution history.

        The website will eventually consume these events to show
        live ForgeAI progress.
        """

        event = {
            "type": event_type,
            "message": message,
        }

        if data:
            event["data"] = data

        self.events.append(event)

    def add_error(
        self,
        error: str,
        source: str = "unknown"
    ) -> None:
        """
        Record an execution error without crashing the state object.
        """

        self.errors.append({
            "source": source,
            "error": error,
        })

        self.add_event(
            "error",
            error,
            source=source,
        )

    def add_changed_file(self, path: str) -> None:
        """
        Add a changed file once.
        """

        if path and path not in self.changed_files:
            self.changed_files.append(path)

    def add_tool_call(
        self,
        name: str,
        arguments: dict[str, Any]
    ) -> None:
        """
        Record a tool invocation.
        """

        self.tool_calls.append({
            "name": name,
            "arguments": arguments,
        })

    def add_tool_result(
        self,
        name: str,
        result: Any
    ) -> None:
        """
        Record a tool result.
        """

        self.tool_results.append({
            "name": name,
            "result": result,
        })

    def set_status(
        self,
        status: str,
        step: str | None = None
    ) -> None:
        """
        Update execution status and optionally the current step.
        """

        self.status = status

        if step is not None:
            self.current_step = step

    def to_dict(self) -> dict[str, Any]:
        """
        Convert the state into a JSON-serializable dictionary.
        """

        return asdict(self)


def save_state(
    state: AgentState,
    path: str = "forgeai_state.json"
) -> None:
    """
    Persist ForgeAI execution state to disk.
    """

    with open(
        path,
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(
            state.to_dict(),
            file,
            indent=2,
            ensure_ascii=False,
        )


def load_state(
    path: str = "forgeai_state.json"
) -> AgentState:
    """
    Load a previously saved ForgeAI execution state.
    """

    with open(
        path,
        "r",
        encoding="utf-8"
    ) as file:
        data = json.load(file)

    return AgentState(**data)