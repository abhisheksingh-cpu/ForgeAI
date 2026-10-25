from llm_router import LLMRouter

router = LLMRouter()

tasks = [
    "Create a README file.",
    "Design the architecture for a distributed payment system.",
    "Fix this failing authentication implementation."
]

for task in tasks:
    print(task)
    print(router.route(task))
    print()