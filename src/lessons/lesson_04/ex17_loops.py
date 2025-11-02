"""
src/examples/ex17_loops.py

Iterative workflow with loops
"""

from typing import TypedDict, List, Literal
from langgraph.graph import StateGraph, START, END
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate

load_dotenv()

class IterativeState(TypedDict):
    current_value:int
    max_value:int
    iteration:int

def increment(state: IterativeState) -> IterativeState:
    """Increment value"""
    new_value = state["current_value"] + 1
    print(f"Iteration {state['iteration']}: {state['current_value']} → {new_value}")
    return {
        "current_value": new_value,
        "max_value": state["max_value"],
        "iteration": state["iteration"] + 1
    }

def check_condition(state: IterativeState) -> Literal["continue", "done"]:
    """Check if we should continue or stop"""
    if state["current_value"] >= state["max_value"]:
        return "done"
    else:
        return "continue"

# Build graph with loop
workflow = StateGraph(IterativeState)

workflow.add_node("increment", increment)

workflow.add_edge(START, "increment")
# Conditional edge that loops back
workflow.add_conditional_edges(
    "increment",
    check_condition,
    {
        "continue": "increment",  # Loop back to same node
        "done": END  # Exit workflow
    }
)

app = workflow.compile()

# Test: count from 0 to 5
result = app.invoke({
    "current_value": 0,
    "max_value": 5,
    "iteration": 1
})

print(f"\nFinal result: {result}")