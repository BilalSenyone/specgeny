"""
src/examples/ex19_custom_reducer.py

Merging requirements without duplicates
"""


from typing import TypedDict, Annotated, List
from pydantic import BaseModel
from langgraph.graph import StateGraph, START, END

class Requirement(BaseModel):
    id: str
    description: str
    priority: str

def merge_requirements(
    existing : List[Requirement],
    new : List[Requirement]
) -> List[Requirement]:
    """
    Custom merge without operator.add, update existing or append new
    
    This function is automatically called by LangGraph whenever a node returns
    a value for the 'requirements' field. LangGraph passes:
    - existing: The current value of requirements in the state
    - new: The value returned by the node for requirements
    
    Example:
        State has: existing = [FR-001, FR-002]
        Node returns: new = [FR-001 (updated), FR-003]
        LangGraph calls: merge_requirements(existing, new)
        Result: [FR-001 (updated), FR-002, FR-003]
    """
    # First we create a dictionary of the existing requirements
    result = {req.id : req for req in existing} # Use dict for O(1) lookup

    for req in new:
        result[req.id] = req # Overwrite or add
    
    return list(result.values()) # Convert back to list
# ------------------------------------------------------------

class RequirementState(TypedDict):
    requirements: Annotated [List[Requirement], merge_requirements] # This is the custom reducer function that will be used to merge the requirements everytime there is a new requirement
    source: str
# ------------------------------------------------------------

def extract_from_description(state: RequirementState) -> RequirementState:
    """Extract requirements from description"""

    return {
        "requirements" : [
            Requirement(id="FR-001", description="User login", priority="P1"),
            Requirement(id="FR-002", description="Password reset", priority="P2"),
        ]
    }
# ------------------------------------------------------------

def extract_from_examples(state: RequirementState) -> RequirementState:
    """ Extract from examples (might overlap)"""
    return {
        "requirements" : [
            Requirement(id="FR-001", description="User login (updated)", priority="P1"),
            Requirement(id="FR-003", description="Account lockout", priority="P1"),
        ]
    }
# ------------------------------------------------------------

# Build workflow
workflow = StateGraph(RequirementState)
workflow.add_node("from_description", extract_from_description)
workflow.add_node("from_examples", extract_from_examples)

workflow.add_edge(START, "from_description")
workflow.add_edge("from_description", "from_examples")
workflow.add_edge("from_examples", END)

# Test

app = workflow.compile()
result = app.invoke({"requirements": [], "source": "description"})
print("Final requirements:")

for req in result["requirements"]:
    print(f"  {req.id}: {req.description} [{req.priority}]")    
