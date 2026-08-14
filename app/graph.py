from langgraph.graph import StateGraph, START, END

from app.state import AnalystState
from app.nodes.planner import planner_node
from app.nodes.executor import executor_node
from app.nodes.reviewer import reviewer_node

graph = StateGraph(AnalystState)

graph.add_node("Planner", planner_node)
graph.add_node("Executor", executor_node)
graph.add_node("Reviewer", reviewer_node)


graph.add_edge(START, "Planner")
graph.add_edge("Planner", "Executor")
graph.add_edge("Executor", "Reviewer")

def should_end(state: AnalystState):

    if state.get("final_report") or not state.get("plan"):
        return "END"
    return "Executor"


graph.add_conditional_edges(
    "Reviewer",
    should_end,
    {
        "END": END,
        "Executor": "Executor"
    }
)

graph = graph.compile()