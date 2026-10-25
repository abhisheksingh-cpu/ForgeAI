LIST_FILES_TOOL = {
    "type": "function",
    "function": {
        "name": "list_files",
        "description": (
            "List all visible files in the target project workspace. "
            "Use this before modifying an unfamiliar existing project."
        ),
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
            "additionalProperties": False,
        },
    },
}


READ_FILE_TOOL = {
    "type": "function",
    "function": {
        "name": "read_file",
        "description": (
            "Read the complete contents of an existing file "
            "inside the target project workspace."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": (
                        "Workspace-relative file path, "
                        "for example: src/main.py"
                    ),
                },
                "encoding": {
                    "type": "string",
                    "description": "Text encoding.",
                    "default": "utf-8",
                },
            },
            "required": ["path"],
            "additionalProperties": False,
        },
    },
}


WRITE_FILE_TOOL = {
    "type": "function",
    "function": {
        "name": "write_file",
        "description": (
            "Create a new file or completely replace a file "
            "inside the target project workspace."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": (
                        "Workspace-relative file path."
                    ),
                },
                "content": {
                    "type": "string",
                    "description": (
                        "Complete file contents to write."
                    ),
                },
            },
            "required": ["path", "content"],
            "additionalProperties": False,
        },
    },
}


EDIT_FILE_TOOL = {
    "type": "function",
    "function": {
        "name": "edit_file",
        "description": (
            "Replace the complete contents of an existing file. "
            "Read the file first when modifying existing functionality."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": (
                        "Workspace-relative file path."
                    ),
                },
                "content": {
                    "type": "string",
                    "description": (
                        "Complete updated file contents."
                    ),
                },
            },
            "required": ["path", "content"],
            "additionalProperties": False,
        },
    },
}


RUN_COMMAND_TOOL = {
    "type": "function",
    "function": {
        "name": "run_command",
        "description": (
            "Run an allowed development or validation command "
            "inside the target project workspace. Use this for "
            "tests, syntax checks, builds, package installation, "
            "and other permitted project commands."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": (
                        "Command to execute, such as "
                        "'python -m pytest' or 'npm test'."
                    ),
                },
            },
            "required": ["command"],
            "additionalProperties": False,
        },
    },
}


START_SERVER_TOOL = {
    "type": "function",
    "function": {
        "name": "start_server",
        "description": (
            "Start an allowed development server for the generated "
            "application. Use this only after implementation and "
            "validation are complete."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": (
                        "Allowed server command, such as "
                        "'npm run dev'."
                    ),
                },
            },
            "required": ["command"],
            "additionalProperties": False,
        },
    },
}


GIT_STATUS_TOOL = {
    "type": "function",
    "function": {
        "name": "git_status",
        "description": (
            "Inspect the Git working-tree status of the target project."
        ),
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
            "additionalProperties": False,
        },
    },
}


GIT_DIFF_TOOL = {
    "type": "function",
    "function": {
        "name": "git_diff",
        "description": (
            "Inspect the current Git diff of the target project."
        ),
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
            "additionalProperties": False,
        },
    },
}


GIT_LOG_TOOL = {
    "type": "function",
    "function": {
        "name": "git_log",
        "description": (
            "Inspect recent Git commit history of the target project."
        ),
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
            "additionalProperties": False,
        },
    },
}


WEB_SEARCH_TOOL = {
    "type": "function",
    "function": {
        "name": "web_search",
        "description": (
            "Search the web for external technical information "
            "when the required information cannot reasonably be "
            "determined from the project or existing context."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": (
                        "Technical search query."
                    ),
                },
            },
            "required": ["query"],
            "additionalProperties": False,
        },
    },
}


TOOLS_SCHEMA = [
    LIST_FILES_TOOL,
    READ_FILE_TOOL,
    WRITE_FILE_TOOL,
    EDIT_FILE_TOOL,
    RUN_COMMAND_TOOL,
    START_SERVER_TOOL,
    GIT_STATUS_TOOL,
    GIT_DIFF_TOOL,
    GIT_LOG_TOOL,
    WEB_SEARCH_TOOL,
]