import json
import uuid

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from celery_tasks import run_forgeai
from src.db.database import SessionLocal, init_db
from src.db.models import Task


# ============================================================
# FastAPI application
# ============================================================

api = FastAPI(
    title="ForgeAI",
    description="Autonomous AI software engineering platform.",
    version="1.0.0",
)


# ============================================================
# CORS
# ============================================================

api.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# Startup
# ============================================================

@api.on_event("startup")
def startup() -> None:
    init_db()


# ============================================================
# Request models
# ============================================================

class TaskRequest(BaseModel):
    requirement: str = Field(
        min_length=1,
        max_length=20_000,
    )


# ============================================================
# Database helpers
# ============================================================

def _get_task_or_404(task_id: str) -> Task:
    try:
        parsed_id = str(uuid.UUID(task_id))
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail="Invalid task ID.",
        ) from exc

    session = SessionLocal()

    try:
        task = session.get(Task, parsed_id)

        if task is None:
            raise HTTPException(
                status_code=404,
                detail="Task not found.",
            )

        return task

    finally:
        session.close()


def _parse_result(result):
    if not result:
        return None

    try:
        return json.loads(result)
    except json.JSONDecodeError:
        return result


# ============================================================
# Task helpers
# ============================================================

def _task_events(
    task: Task,
    parsed_result,
) -> list[dict]:

    if isinstance(parsed_result, dict):

        events = parsed_result.get("events")

        if isinstance(events, list):
            return events

    if task.status == "pending":

        return [
            {
                "type": "queued",
                "message": (
                    "Task is waiting for a ForgeAI worker."
                ),
            }
        ]

    if task.status == "running":

        return [
            {
                "type": "running",
                "message": (
                    "ForgeAI is processing the requirement."
                ),
            }
        ]

    if task.status == "completed":

        return [
            {
                "type": "completed",
                "message": (
                    "ForgeAI completed the task."
                ),
            }
        ]

    if task.status == "failed":

        return [
            {
                "type": "failed",
                "message": (
                    "ForgeAI failed to complete the task."
                ),
            }
        ]

    return []


def _task_response(task: Task) -> dict:

    parsed_result = _parse_result(
        task.result
    )

    return {
        "task_id": task.id,
        "status": task.status,
        "requirement": task.requirement,
        "created_at": task.created_at,
        "updated_at": task.updated_at,
        "result": parsed_result,
    }


# ============================================================
# Routes
# ============================================================

@api.get("/")
def root() -> dict:

    return {
        "name": "ForgeAI",
        "status": "online",
        "version": "1.0.0",
    }


@api.get("/health")
def health() -> dict:

    return {
        "status": "healthy",
    }


@api.post(
    "/tasks",
    status_code=201,
)
def create_task(
    request: TaskRequest,
) -> dict:

    requirement = request.requirement.strip()

    if not requirement:

        raise HTTPException(
            status_code=400,
            detail="Requirement cannot be empty.",
        )

    task_id = str(
        uuid.uuid4()
    )

    session = SessionLocal()

    try:

        task = Task(
            id=task_id,
            requirement=requirement,
            status="pending",
        )

        session.add(task)
        session.commit()

    except Exception:

        session.rollback()
        raise

    finally:

        session.close()

    try:

        run_forgeai.delay(
            task_id,
            requirement,
        )

    except Exception as exc:

        session = SessionLocal()

        try:

            task = session.get(
                Task,
                task_id,
            )

            if task is not None:

                task.status = "failed"

                task.result = json.dumps(
                    {
                        "status": "failed",
                        "error": (
                            "Unable to enqueue ForgeAI task: "
                            f"{exc}"
                        ),
                    },
                    ensure_ascii=False,
                )

                session.commit()

        finally:

            session.close()

        raise HTTPException(
            status_code=503,
            detail=(
                "ForgeAI worker is unavailable. "
                "Make sure Redis and the Celery worker "
                "are running."
            ),
        ) from exc

    return {
        "task_id": task_id,
        "status": "pending",
        "requirement": requirement,
    }


@api.get(
    "/tasks/{task_id}"
)
def get_task(
    task_id: str,
) -> dict:

    task = _get_task_or_404(
        task_id
    )

    return _task_response(
        task
    )


@api.get(
    "/tasks/{task_id}/events"
)
def get_task_events(
    task_id: str,
) -> dict:

    task = _get_task_or_404(
        task_id
    )

    parsed_result = _parse_result(
        task.result
    )

    events = _task_events(
        task,
        parsed_result,
    )

    return {
        "task_id": task.id,
        "status": task.status,
        "events": events,
    }