import sys
from forgeai_graph import app


def main():

    print("\nForgeAI — Autonomous AI Engineering Platform\n")

    requirement = input("> ")

    if not requirement.strip():
        print("Requirement cannot be empty.")
        return

    print("\nForgeAI")
    print("├── Analyzing requirements...")
    print("├── Planning architecture...")
    print("├── Inspecting project...")
    print("├── Executing changes...")
    print("├── Running tests...")
    print("├── Repairing if necessary...")
    print("└── Retesting...\n")

    initial_state = {
        "messages": [
            {
                "role": "user",
                "content": requirement
            }
        ],
        "status": "pending",
        "current_step": "start",
        "plan": "",
        "impact_report": "",
        "approval": "",
        "tool_calls": [],
        "tool_results": [],
        "errors": [],
        "changed_files": [],
        "test_result": {},
        "iterations": 0,
        "retry_attempts": 0
    }

    try:

        result = app.invoke(
            initial_state,
            config={"configurable": {"thread_id": "forgeai-demo"}}
        )

        print("\n└── Build completed.")
        print("\nApplication ready.")

        if result.get("changed_files"):
            print("\nChanged files:")
            for file in result["changed_files"]:
                print(f"  - {file}")

    except Exception as e:

        print("\nForgeAI failed.")
        print(f"Error: {e}")


if __name__ == "__main__":
    main()