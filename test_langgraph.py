from langgraph.graph import StateGraph, START, END
from typing import TypedDict


class State(TypedDict):
    message: str


def agent_node(state):
    print("Agent received:", state["message"])

    return {
        "message": state["message"] + " → processed"
    }


graph = StateGraph(State)

graph.add_node("agent", agent_node)

graph.add_edge(START, "agent")
graph.add_edge("agent", END)

app = graph.compile()

result = app.invoke({
    "message": "Hello ForgeAI"
})

print(result)