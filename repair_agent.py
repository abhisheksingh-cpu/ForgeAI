from state import AgentState


MAX_REPAIR_ATTEMPTS = 3


class RepairAgent:
    """
    Handles repair attempts after validation failures.

    The repair agent reuses the existing Agent and execution state
    instead of starting an unrelated fresh task.
    """

    def __init__(
        self,
        agent,
        dispatcher,
    ):
        self.agent = agent
        self.dispatcher = dispatcher

    def repair(
        self,
        state: AgentState,
        test_command: str,
    ) -> dict:
        """
        Run validation and perform repairs when necessary.

        The same AgentState is reused across attempts so the agent
        retains the implementation history and changed files.
        """

        for attempt in range(
            MAX_REPAIR_ATTEMPTS
        ):

            state.repair_attempts = attempt + 1
            state.current_step = "testing"

            state.add_event(
                "repair_test",
                f"Running validation attempt {attempt + 1}.",
                attempt=attempt + 1,
                command=test_command,
            )

            result = self.dispatcher(
                "run_command",
                {
                    "command": test_command
                },
            )

            state.test_command = test_command
            state.test_result = result

            if result.get("exit_code") == 0:

                state.add_event(
                    "test_passed",
                    "Validation passed.",
                    attempt=attempt + 1,
                )

                return {
                    "status": "success",
                    "attempts": attempt + 1,
                    "result": result,
                }

            state.add_event(
                "test_failed",
                "Validation failed.",
                attempt=attempt + 1,
                result=result,
            )

            if attempt == MAX_REPAIR_ATTEMPTS - 1:
                break

            state.current_step = "repair"

            repair_request = self._build_repair_request(
                state=state,
                test_command=test_command,
                test_result=result,
                attempt=attempt + 1,
            )

            state.add_event(
                "repair_started",
                f"Starting repair attempt {attempt + 1}.",
                attempt=attempt + 1,
            )

            try:

                repaired_state = self.agent.run(
                    user_input=repair_request,
                    state=state,
                )

                state = repaired_state

            except Exception as exc:

                state.add_error(
                    str(exc),
                    source="repair_agent",
                )

                state.add_event(
                    "repair_error",
                    "Repair attempt failed.",
                    attempt=attempt + 1,
                    error=str(exc),
                )

        return {
            "status": "failed",
            "attempts": state.repair_attempts,
            "reason": (
                "Maximum repair attempts exceeded."
            ),
            "result": state.test_result,
        }

    @staticmethod
    def _build_repair_request(
        state: AgentState,
        test_command: str,
        test_result: dict,
        attempt: int,
    ) -> str:
        """
        Build a focused repair instruction from the actual
        validation failure.
        """

        changed_files = "\n".join(
            f"- {path}"
            for path in state.changed_files
        )

        return f"""
ForgeAI repair attempt {attempt}.

The previous implementation failed validation.

Original requirement:
{state.requirement}

Architecture plan:
{state.plan}

Impact analysis:
{state.impact_report}

Validation command:
{test_command}

Validation result:
{test_result}

Files already changed:
{changed_files or "- None recorded"}

Your task:

1. Inspect the failure carefully.

2. Inspect the relevant project files.

3. Determine the actual root cause.

4. Make the smallest correct repair.

5. Do not rewrite unrelated files.

6. Use the available tools to perform the repair.

7. Do not merely explain the repair.

8. After making the repair, stop so ForgeAI can run
   the validation command again.

Do not claim that validation passed yourself.
ForgeAI will run the validation command separately.
""".strip()