"""
src/examples/ex14_first_graph.py

Simplest possible LangGraph workflow
"""

from typing import TypedDict
from langgraph.graph import StateGraph, START, END

# Step 1 : Define a state structure
class SimpleState(TypedDict):
    """State shared across all nodes"""
    message:str #message to be processed
    count:int #count of messages processed

# Step 2 :Define  node functions
def node_a(state:SimpleState) -> SimpleState:
    """ First processing step"""
    print(f"Node A: Received message='{state['message']}'")
    return{
        "message":state["message"]  + "(processed by A)",
        "count":state["count"] + 1
    }

def node_b(state:SimpleState) -> SimpleState:
    """ Second processing step"""
    print(f"Node B: Received message='{state['message']}'")
    return{
        "count": state["count"] + 1,
        "message":state["message"] + "(processed by B)"   
    }

# Step 3: Build the graph
workflow = StateGraph(SimpleState)

# Add Nodes
workflow.add_node("node_a", node_a)
workflow.add_node("node_b", node_b)

# Define edges (transitions)
workflow.add_edge(START, "node_a") # START → node_a
workflow.add_edge("node_a", "node_b") # node_a → node_b
workflow.add_edge("node_b", END) # node_b → END

# Compile graph
app = workflow.compile()

#Execute
initial_state = {"message": "Hello", "count":0}
result = app.invoke(initial_state)

print(f"\nFinal result: {result}")	
# Output: {'message': 'Hello (processed by A) (processed by B)', 'count': 2}