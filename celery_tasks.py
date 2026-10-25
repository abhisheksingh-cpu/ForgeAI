import json

from celery import Celery

from forgeai_graph import app as forgeai_app
from src.db.database import SessionLocal
from src.db.models import Task


# ============================================================
# Celery configuration
# ============================================================

app = Celery(
    "forgeai",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0",
)


# ============================================================
# Redis / Celery configuration
# ============================================================

app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)


# ============================================================
# Helpers
# ============================================================

def _update_task(
    task_id: str,
    status: str,
    result=None,
) -> None:
    session = SessionLocal()

    try:

        task = session.get(
            Task,
            task_id,
        )

        if task is None:
            return

        task.status = status

        if result is not None:
            task.result = json.dumps(
                result,
                ensure_ascii=False,
                default=str,
            )

        session.commit()

    finally:
        session.close()


# ============================================================
# ForgeAI execution task
# ============================================================

@app.task(
    bind=True,
    name="forgeai.run_forgeai",
)
def run_forgeai(
    self,
    task_id: str,
    requirement: str,
):
    """
    Execute one ForgeAI engineering task.

    Celery owns the background execution while LangGraph owns
    the actual engineering workflow.
    """

    _update_task(
        task_id,
        "running",
    )

    try:

        initial_state = {
            "requirement": requirement,
            "status": "running",
            "current_step": "start",
            "plan": "",
            "impact_report": "",
            "messages": [
                {
                    "role": "user",
                    "content": requirement,
                }
            ],
            "tool_calls": [],
            "tool_results": [],
            "changed_files": [],
            "test_command": "",
            "test_result": {},
            "repair_attempts": 0,
            "max_repair_attempts": 3,
            "iterations": 0,
            "max_iterations": 20,
            "errors": [],
            "approval": "",
            "events": [],
            "result": {},
        }

        config = {
            "configurable": {
                "thread_id": task_id,
            }
        }

        result = forgeai_app.invoke(
            initial_state,
            config=config,
        )

        _update_task(
            task_id,
            "completed",
            result,
        )

        return result

    except Exception as exc:

        error_result = {
            "status": "failed",
            "error": str(exc),
        }

        _update_task(
            task_id,
            "failed",
            error_result,
        )

        raise


# ============================================================
# Retry / resume helper
# ============================================================

@app.task(
    bind=True,
    name="forgeai.retry_forgeai",
)
def retry_forgeai(
    self,
    task_id: str,
    requirement: str,
):
    """
    Re-run a failed ForgeAI task from the beginning.

    This is intentionally separate from LangGraph's internal
    repair loop. The graph handles implementation repair;
    this task handles a complete external retry.
    """

    return run_forgeai.delay(
        task_id,
        requirement,
    )