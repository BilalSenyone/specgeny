"""
src/examples/ex20_nested_state.py

Managing complex nested state
"""

from typing import TypedDict, Annotated, List, Dict
from langgraph.graph import StateGraph, START, END

class ValidationResult(TypedDict):
    is_valid:bool
    errors: List[str]

class BlockState(TypedDict):
    content: str
    validation : ValidationResult
    approved: bool

class SpecificationState(TypedDict):
    spec_id: str
    blocks: Annotated[List[BlockState], lambda x, y: x + y] # lambda x, y: x + y is a function that appends to the list everytime there is a new block
    metadata: Annotated[Dict, lambda x,y : {**x, **y}] # lambda x, y: {**x, **y} is a function that merges the two dictionaries

def generate_block(state: SpecificationState) -> SpecificationState:
    """ Generate a new block """
    new_block : BlockState = {
        'content': "This is a requirement block",
        'validation': {'is_valid': False, 'errors': []},
        'approved': False
    } # initialize a new block with default values

    return {'blocks': [new_block]} # return the new block in a list, but other values (spec_id, metadata) are not changed

def validate_block (state: SpecificationState) -> SpecificationState:
    """ Validate the last block """
    last_block : BlockState= state["blocks"][-1]

    # Simple validation
    is_valid = len(last_block['content']) > 10 # if the content is longer than 10 characters, it is valid

    # Update the last block with the new validation result
    updated_blocks = state["blocks"][:-1] + [{
        **last_block,
        'validation': {
            'is_valid': is_valid,
            'errors': [] if is_valid else ['Content too short']
        }
    }]

    # Use replace strategy for block when updating
    return {
        "blocks": updated_blocks,
        "metadata": {"last_validation": "completed"}
    }

# Build workflow
workflow = StateGraph(SpecificationState)
workflow.add_node("generate", generate_block)
workflow.add_node("validate", validate_block)

workflow.add_edge(START, "generate")
workflow.add_edge("generate", "validate")
workflow.add_edge("validate", END)

app = workflow.compile()

result = app.invoke({
    "spec_id": "SPEC-001",
    "blocks": [],
    "metadata": {"created": "2024-01-01"}
})

print("Blocks:", result["blocks"])
print("Metadata:", result["metadata"])

