import json
from typing import Any

from state import AgentState, load_state, save_state
from llm_router import LLMRouter


DEFAULT_MAX_ITERATIONS = 20


SYSTEM_PROMPT = """
You are ForgeAI, an autonomous AI software engineer.

Your job is to implement the user's software requirement directly
inside the target project workspace.

You are an execution agent, not a planning-only chatbot.

============================================================
CORE RULES
============================================================

1. Actually implement the user's requirement.

2. Use tools to inspect and modify the workspace.

3. Before modifying an existing project, inspect relevant files.

4. Use list_files when you need to understand project structure.

5. Use read_file when you need existing file contents.

6. Use write_file when creating or replacing a file.

7. Use edit_file when modifying an existing file.

8. Use run_command when you need to install dependencies,
   run tests, validate syntax, build the project, or execute
   an allowed project command.

9. Use web_search only when external technical information
   is genuinely needed.

10. Do not merely describe code that should be written.
    Actually call the appropriate file tool.

11. Do not claim a file was created unless you actually
    called a file-writing tool.

12. Do not claim tests passed unless you actually ran them.

13. Do not modify unrelated files.

14. Preserve existing project functionality when modifying
    an existing project.

15. Prefer the smallest correct implementation.

16. Do not repeatedly inspect the same file when its contents
    are already available.

17. Do not repeatedly run the same command unless the previous
    result indicates another attempt is useful.

18. If a command fails, inspect the failure and determine
    the appropriate correction.

19. If implementation is incomplete, continue using tools.

20. Stop only when the requested implementation is complete
    or a genuine blocking problem prevents completion.

============================================================
ARCHITECTURE CONTEXT
============================================================

ForgeAI may provide:

- an architecture plan
- an impact analysis
- existing project files
- previous tool results

Use this information instead of unnecessarily rediscovering it.

============================================================
FINAL RESPONSE
============================================================

When implementation is complete, return a concise summary containing:

- what was implemented
- important files changed
- validation performed
- any remaining limitation

Do not return large source-code dumps.

You are responsible for performing the engineering work,
not merely explaining how a human could perform it.
"""


class Agent:

    def __init__(
        self,
        llm_client,
        dispatcher,
        tool_schemas,
        max_iterations=DEFAULT_MAX_ITERATIONS,
    ):
        self.llm_client = llm_client
        self.dispatcher = dispatcher
        self.tool_schemas = tool_schemas
        self.max_iterations = max_iterations
        self.router = LLMRouter()

    # ========================================================
    # Main execution loop
    # ========================================================

    def run(
        self,
        user_input: str | None = None,
        resume: bool = False,
        state: AgentState | None = None,
        architecture_plan: str | None = None,
        impact_report: str | None = None,
    ) -> AgentState:

        state = self._initialize_state(
            user_input=user_input,
            resume=resume,
            state=state,
            architecture_plan=architecture_plan,
            impact_report=impact_report,
        )

        while state.iterations < self.max_iterations:

            state.iterations += 1
            state.current_step = "llm"

            state.add_event(
                "agent_iteration",
                f"Agent iteration {state.iterations}",
            )

            routing_text = self._build_routing_text(
                state
            )

            route = self.router.route(
                routing_text
            )

            model = route["model"]

            try:

                message = self.llm_client.chat_with_tools(
                    messages=state.messages,
                    tools=self.tool_schemas,
                    model=model,
                )

            except Exception as exc:

                state.add_error(
                    str(exc),
                    source="llm",
                )

                state.status = "failed"
                state.current_step = "llm_error"

                save_state(state)

                raise

            # ------------------------------------------------
            # No tool calls = agent believes task is complete
            # ------------------------------------------------

            if not message.tool_calls:

                final_content = (
                    message.content
                    or "Implementation completed."
                )

                state.messages.append(
                    {
                        "role": "assistant",
                        "content": final_content,
                    }
                )

                state.status = "completed"
                state.current_step = "finished"

                state.result = {
                    "status": "completed",
                    "message": final_content,
                    "changed_files": state.changed_files,
                    "iterations": state.iterations,
                }

                state.add_event(
                    "agent_completed",
                    "Agent completed its implementation cycle.",
                )

                save_state(state)

                return state

            # ------------------------------------------------
            # Store assistant tool-call message
            # ------------------------------------------------

            normalized_tool_calls = []

            for tool_call in message.tool_calls:

                tool_name = self._normalize_tool_name(
                    tool_call.function.name
                )

                normalized_tool_calls.append(
                    {
                        "id": tool_call.id,
                        "type": "function",
                        "function": {
                            "name": tool_name,
                            "arguments": tool_call.function.arguments,
                        },
                    }
                )

            state.messages.append(
                {
                    "role": "assistant",
                    "content": message.content,
                    "tool_calls": normalized_tool_calls,
                }
            )

            # ------------------------------------------------
            # Execute tools
            # ------------------------------------------------

            for tool_call in message.tool_calls:

                self._execute_tool_call(
                    state,
                    tool_call,
                )

            save_state(state)

        # ====================================================
        # Maximum iteration protection
        # ====================================================

        state.status = "failed"
        state.current_step = "max_iterations"

        state.add_error(
            (
                "Agent reached the maximum number of iterations "
                "before completing the implementation."
            ),
            source="agent",
        )

        state.result = {
            "status": "failed",
            "message": "Maximum agent iterations exceeded.",
            "changed_files": state.changed_files,
            "iterations": state.iterations,
        }

        save_state(state)

        raise RuntimeError(
            "ForgeAI agent exceeded maximum iterations."
        )

    # ========================================================
    # State initialization
    # ========================================================

    def _initialize_state(
        self,
        user_input: str | None,
        resume: bool,
        state: AgentState | None,
        architecture_plan: str | None,
        impact_report: str | None,
    ) -> AgentState:

        # ----------------------------------------------------
        # Existing state
        # ----------------------------------------------------

        if state is not None:

            if architecture_plan:
                state.plan = architecture_plan

            if impact_report:
                state.impact_report = impact_report

            # Make sure the existing state contains the
            # system prompt.
            self._ensure_system_message(state)

            # If a new instruction is explicitly supplied,
            # append it as a user message.
            #
            # This is important for repair_agent.py.
            if user_input and user_input.strip():

                normalized_input = user_input.strip()

                if not self._has_recent_user_message(
                    state,
                    normalized_input,
                ):
                    state.messages.append(
                        {
                            "role": "user",
                            "content": normalized_input,
                        }
                    )

                    state.add_event(
                        "agent_instruction",
                        "New engineering instruction received.",
                    )

            if not state.requirement and user_input:
                state.requirement = user_input.strip()

            if state.status == "pending":
                state.status = "running"

            return state

        # ----------------------------------------------------
        # Resume saved state
        # ----------------------------------------------------

        if resume:

            state = load_state()

            if architecture_plan:
                state.plan = architecture_plan

            if impact_report:
                state.impact_report = impact_report

            self._ensure_system_message(state)

            return state

        # ----------------------------------------------------
        # New execution
        # ----------------------------------------------------

        if not user_input or not user_input.strip():

            raise ValueError(
                "ForgeAI requires a non-empty requirement."
            )

        requirement = user_input.strip()

        state = AgentState(
            requirement=requirement,
            status="running",
            current_step="start",
            max_iterations=self.max_iterations,
        )

        state.plan = architecture_plan or ""
        state.impact_report = impact_report or ""

        state.messages.append(
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            }
        )

        state.messages.append(
            {
                "role": "user",
                "content": self._build_initial_request(
                    user_input=requirement,
                    architecture_plan=architecture_plan,
                    impact_report=impact_report,
                ),
            }
        )

        state.add_event(
            "agent_started",
            "Autonomous engineering agent started.",
        )

        return state

    # ========================================================
    # Message helpers
    # ========================================================

    @staticmethod
    def _ensure_system_message(
        state: AgentState,
    ) -> None:

        if not state.messages:

            state.messages.append(
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT,
                }
            )

            return

        has_system_message = any(
            message.get("role") == "system"
            for message in state.messages
        )

        if not has_system_message:

            state.messages.insert(
                0,
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT,
                },
            )

    @staticmethod
    def _has_recent_user_message(
        state: AgentState,
        content: str,
    ) -> bool:

        for message in reversed(
            state.messages[-5:]
        ):

            if (
                message.get("role") == "user"
                and message.get("content") == content
            ):
                return True

        return False

    # ========================================================
    # Initial request
    # ========================================================

    @staticmethod
    def _build_initial_request(
        user_input: str,
        architecture_plan: str | None,
        impact_report: str | None,
    ) -> str:

        parts = [
            "User requirement:",
            user_input.strip(),
        ]

        if architecture_plan:

            parts.extend(
                [
                    "",
                    "Architecture plan:",
                    architecture_plan,
                ]
            )

        if impact_report:

            parts.extend(
                [
                    "",
                    "Impact analysis:",
                    impact_report,
                ]
            )

        parts.extend(
            [
                "",
                "Implement this requirement in the target workspace.",
                "Use the available tools and continue until the",
                "implementation is complete and appropriately validated.",
            ]
        )

        return "\n".join(parts)

    # ========================================================
    # Routing context
    # ========================================================

    def _build_routing_text(
        self,
        state: AgentState,
    ) -> str:

        recent_messages = state.messages[-6:]

        text_parts = [
            state.requirement,
            state.plan,
            state.impact_report,
        ]

        for message in recent_messages:

            content = message.get(
                "content"
            )

            if content:
                text_parts.append(
                    str(content)
                )

        return "\n".join(
            part
            for part in text_parts
            if part
        )

    # ========================================================
    # Tool execution
    # ========================================================

    def _execute_tool_call(
        self,
        state: AgentState,
        tool_call,
    ) -> None:

        tool_name = self._normalize_tool_name(
            tool_call.function.name
        )

        raw_arguments = (
            tool_call.function.arguments
        )

        # ----------------------------------------------------
        # Parse arguments
        # ----------------------------------------------------

        try:

            arguments = json.loads(
                raw_arguments
            )

        except json.JSONDecodeError as exc:

            error_message = (
                f"Invalid JSON arguments for tool "
                f"'{tool_name}': {exc}"
            )

            state.add_error(
                error_message,
                source=f"tool:{tool_name}",
            )

            result = (
                "Tool execution failed because the "
                f"arguments were not valid JSON: {exc}"
            )

            state.messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result,
                }
            )

            state.add_tool_result(
                tool_name,
                result,
            )

            return

        # ----------------------------------------------------
        # Record call
        # ----------------------------------------------------

        state.add_tool_call(
            tool_name,
            arguments,
        )

        state.current_step = (
            f"tool:{tool_name}"
        )

        state.add_event(
            "tool_call",
            f"Executing tool: {tool_name}",
            tool=tool_name,
            arguments=arguments,
        )

        # ----------------------------------------------------
        # Execute dispatcher
        # ----------------------------------------------------

        try:

            result = self.dispatcher(
                tool_name,
                arguments,
            )

        except Exception as exc:

            error_message = str(exc)

            result = {
                "error": error_message,
            }

            state.add_error(
                error_message,
                source=f"tool:{tool_name}",
            )

            state.add_event(
                "tool_error",
                f"Tool failed: {tool_name}",
                tool=tool_name,
                error=error_message,
            )

        else:

            self._record_file_change(
                state,
                tool_name,
                arguments,
            )

            state.add_event(
                "tool_result",
                f"Tool completed: {tool_name}",
                tool=tool_name,
            )

        # ----------------------------------------------------
        # Store result
        # ----------------------------------------------------

        state.add_tool_result(
            tool_name,
            result,
        )

        state.messages.append(
            {
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": self._serialize_tool_result(
                    result
                ),
            }
        )

        state.current_step = "tool_result"

    # ========================================================
    # File tracking
    # ========================================================

    @staticmethod
    def _record_file_change(
        state: AgentState,
        tool_name: str,
        arguments: dict[str, Any],
    ) -> None:

        if tool_name not in {
            "write_file",
            "edit_file",
        }:
            return

        path = arguments.get(
            "path"
        )

        if path:
            state.add_changed_file(
                path
            )

    # ========================================================
    # Utility functions
    # ========================================================

    @staticmethod
    def _normalize_tool_name(
        name,
    ):

        if not name:
            return ""

        return name.split(
            "<|"
        )[0].strip()

    @staticmethod
    def _serialize_tool_result(
        result,
    ):

        if isinstance(
            result,
            str,
        ):
            return result

        try:

            return json.dumps(
                result,
                ensure_ascii=False,
            )

        except TypeError:

            return str(result)