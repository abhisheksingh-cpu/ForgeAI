from pathlib import Path
import os
import shlex
import subprocess

from dotenv import load_dotenv
from tavily import TavilyClient


load_dotenv()


# ============================================================
# Workspace
# ============================================================

ROOT = Path(
    os.getenv(
        "FORGEAI_WORKSPACE",
        "workspace/target_project",
    )
).resolve()


IGNORED = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    ".env",
    "node_modules",
}


# ============================================================
# Command policy
# ============================================================

ALLOWED_COMMANDS = {
    "python",
    "pytest",
    "npm",
    "npx",
    "git",
}


ALLOWED_GIT_COMMANDS = {
    "status",
    "diff",
    "log",
}


ALLOWED_NPM_COMMANDS = {
    "install",
    "run",
    "test",
}


ALLOWED_NPX_COMMANDS = {
    "vite",
}


COMMAND_TIMEOUT = 60


# ============================================================
# Workspace initialization
# ============================================================

ROOT.mkdir(
    parents=True,
    exist_ok=True,
)


# ============================================================
# Path security
# ============================================================

def _safe_path(path: str) -> Path:
    """
    Resolve a workspace-relative path safely.

    ForgeAI must never be able to access files outside
    workspace/target_project.
    """

    if not path or not path.strip():
        raise ValueError(
            "Path cannot be empty."
        )

    target = (ROOT / path).resolve()

    if target != ROOT and ROOT not in target.parents:
        raise ValueError(
            "Path is outside the ForgeAI workspace."
        )

    relative_parts = target.relative_to(ROOT).parts

    if any(
        part in IGNORED
        for part in relative_parts
    ):
        raise ValueError(
            "Access to this path is not allowed."
        )

    return target


# ============================================================
# File tools
# ============================================================

def list_files() -> list[str]:
    """
    Return all visible files inside the target workspace.
    """

    files = []

    for path in ROOT.rglob("*"):

        if not path.is_file():
            continue

        relative = path.relative_to(ROOT)

        if any(
            part in IGNORED
            for part in relative.parts
        ):
            continue

        files.append(
            str(relative).replace("\\", "/")
        )

    return sorted(files)


def read_file(
    path: str,
    encoding: str = "utf-8",
) -> str:
    """
    Read a file from the target workspace.
    """

    target = _safe_path(path)

    if not target.is_file():
        raise FileNotFoundError(
            f"File not found: {path}"
        )

    return target.read_text(
        encoding=encoding
    )


def write_file(
    path: str,
    content: str,
) -> str:
    """
    Create or completely replace a workspace file.
    """

    target = _safe_path(path)

    target.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    target.write_text(
        content,
        encoding="utf-8",
    )

    return (
        f"File written successfully: {path}"
    )


def edit_file(
    path: str,
    content: str,
) -> str:
    """
    Replace the complete contents of an existing file.

    The agent should read the file first when modifying
    an existing implementation.
    """

    target = _safe_path(path)

    if not target.is_file():
        raise FileNotFoundError(
            f"File not found: {path}"
        )

    target.write_text(
        content,
        encoding="utf-8",
    )

    return (
        f"File edited successfully: {path}"
    )


# ============================================================
# Command validation
# ============================================================

def _parse_command(command: str) -> list[str]:
    """
    Parse a command without invoking a shell.

    This prevents shell operators such as:
        &&
        ||
        >
        |
        ;

    from being interpreted by the operating system.
    """

    if not command or not command.strip():
        raise ValueError(
            "Command cannot be empty."
        )

    try:
        parts = shlex.split(
            command,
            posix=False,
        )
    except ValueError as exc:
        raise ValueError(
            f"Invalid command syntax: {exc}"
        ) from exc

    if not parts:
        raise ValueError(
            "Command cannot be empty."
        )

    return parts


def _normalize_executable(
    parts: list[str],
) -> tuple[list[str], str]:
    """
    Normalize Windows npm/npx executables while preserving
    the logical command name for validation.
    """

    executable = parts[0].lower()

    if executable == "npm.cmd":
        executable = "npm"
        parts[0] = "npm.cmd"

    elif executable == "npx.cmd":
        executable = "npx"
        parts[0] = "npx.cmd"

    elif executable == "python.exe":
        executable = "python"

    return parts, executable


def _validate_command(
    parts: list[str],
    executable: str,
) -> None:
    """
    Validate a command against ForgeAI's execution policy.
    """

    if executable not in ALLOWED_COMMANDS:
        raise ValueError(
            f"Command not allowed: {executable}"
        )

    if executable == "git":

        if (
            len(parts) < 2
            or parts[1].lower()
            not in ALLOWED_GIT_COMMANDS
        ):
            raise ValueError(
                "Git command not allowed."
            )

    elif executable == "npm":

        if len(parts) < 2:
            raise ValueError(
                "NPM requires a subcommand."
            )

        subcommand = parts[1].lower()

        if subcommand == "--version":
            return

        if subcommand not in ALLOWED_NPM_COMMANDS:
            raise ValueError(
                f"NPM command not allowed: {subcommand}"
            )

    elif executable == "npx":

        if len(parts) < 2:
            raise ValueError(
                "NPX requires a command."
            )

        if parts[1].lower() not in ALLOWED_NPX_COMMANDS:
            raise ValueError(
                f"NPX command not allowed: {parts[1]}"
            )


# ============================================================
# Command execution
# ============================================================

def run_command(
    command: str,
) -> dict:
    """
    Execute an allowed command inside the target workspace.
    """

    try:

        parts = _parse_command(
            command
        )

        parts, executable = _normalize_executable(
            parts
        )

        _validate_command(
            parts,
            executable,
        )

    except ValueError as exc:

        return {
            "exit_code": -1,
            "stdout": "",
            "stderr": str(exc),
        }

    try:

        result = subprocess.run(
            parts,
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=COMMAND_TIMEOUT,
            shell=False,
        )

        return {
            "exit_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }

    except subprocess.TimeoutExpired as exc:

        stdout = (
            exc.stdout
            if isinstance(exc.stdout, str)
            else ""
        )

        stderr = (
            exc.stderr
            if isinstance(exc.stderr, str)
            else ""
        )

        return {
            "exit_code": -1,
            "stdout": stdout,
            "stderr": (
                stderr
                + "\nCommand timed out."
            ).strip(),
        }

    except FileNotFoundError:

        return {
            "exit_code": -1,
            "stdout": "",
            "stderr": (
                f"Executable not found: {parts[0]}"
            ),
        }

    except OSError as exc:

        return {
            "exit_code": -1,
            "stdout": "",
            "stderr": str(exc),
        }


# ============================================================
# Server tool
# ============================================================

def start_server(
    command: str,
) -> dict:
    """
    Start an allowed development server.

    This is intentionally separate from run_command because
    a server is expected to remain running.
    """

    try:

        parts = _parse_command(
            command
        )

        parts, executable = _normalize_executable(
            parts
        )

        _validate_command(
            parts,
            executable,
        )

    except ValueError as exc:

        return {
            "status": "failed",
            "error": str(exc),
        }

    try:

        kwargs = {
            "cwd": ROOT,
            "shell": False,
        }

        if os.name == "nt":

            kwargs["creationflags"] = (
                subprocess.CREATE_NEW_CONSOLE
            )

        process = subprocess.Popen(
            parts,
            **kwargs,
        )

        return {
            "status": "started",
            "pid": process.pid,
            "command": command,
        }

    except OSError as exc:

        return {
            "status": "failed",
            "error": str(exc),
        }


# ============================================================
# Git tools
# ============================================================

def git_status() -> dict:
    return run_command(
        "git status"
    )


def git_diff() -> dict:
    return run_command(
        "git diff"
    )


def git_log() -> dict:
    return run_command(
        "git log"
    )


# ============================================================
# Web search
# ============================================================

def web_search(
    query: str,
) -> list[dict]:
    """
    Search the web when the engineering task genuinely
    requires external technical information.
    """

    if not query or not query.strip():
        raise ValueError(
            "Search query cannot be empty."
        )

    api_key = os.getenv(
        "TAVILY_API_KEY"
    )

    if not api_key:
        raise RuntimeError(
            "TAVILY_API_KEY is not configured."
        )

    client = TavilyClient(
        api_key=api_key
    )

    response = client.search(
        query=query,
        max_results=3,
    )

    results = []

    for result in response.get(
        "results",
        [],
    ):

        results.append({
            "title": result.get(
                "title",
                "",
            ),
            "url": result.get(
                "url",
                "",
            ),
            "snippet": result.get(
                "content",
                "",
            ),
        })

    return results


# ============================================================
# Tool registry
# ============================================================

TOOLS = {
    "list_files": list_files,
    "read_file": read_file,
    "write_file": write_file,
    "edit_file": edit_file,
    "run_command": run_command,
    "start_server": start_server,
    "git_status": git_status,
    "git_diff": git_diff,
    "git_log": git_log,
    "web_search": web_search,
}


# ============================================================
# Dispatcher
# ============================================================

def dispatcher(
    tool_name: str,
    arguments: dict,
):
    """
    Execute a registered ForgeAI tool.
    """

    if tool_name not in TOOLS:
        raise ValueError(
            f"Unknown ForgeAI tool: {tool_name}"
        )

    if not isinstance(arguments, dict):
        raise TypeError(
            "Tool arguments must be a dictionary."
        )

    return TOOLS[tool_name](
        **arguments
    )