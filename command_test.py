import subprocess
import os

ALLOWED_COMMANDS = {
    "python",
    "pytest"
}

print(os.getcwd())


def run_command(command):

    parts = command.split()

    if not parts:
        raise ValueError("Command cannot be empty")

    executable = parts[0]

    if executable not in ALLOWED_COMMANDS:
        return {
            "exit_code": -1,
            "stdout": "",
            "stderr": "Command not allowed"
        }
    try:
        result = subprocess.run(
            parts,
            capture_output=True,
            text=True,
            cwd="workspace/target_project",
            timeout=10
        )

        return {
            "exit_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr
        }

    except subprocess.TimeoutExpired:
        return {
            "exit_code": -1,
            "stdout": "",
            "stderr": "Command timed out"
        }

    except FileNotFoundError:
        return {
            "exit_code": -1,
            "stdout": "",
            "stderr": "Command executable not found"
        }


print(run_command("python --version"))

print(run_command("powershell"))