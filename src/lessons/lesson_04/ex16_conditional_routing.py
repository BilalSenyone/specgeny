"""
src/examples/ex16_conditional_routing.py

Branching based on state conditions
"""

from typing import TypedDict, List, Literal
from langgraph.graph import StateGraph, START, END
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate

load_dotenv()

class ValidationState(TypedDict):
    text:str
    is_valid:bool
    error_message:str

def validate_input (state: ValidationState) -> ValidationState:
    """ Check if Input is valid"""
    text = state["text"]
    is_valid = len(text) >  10 and not any(char.isdigit() for char in text) # check if text is longer than 10 characters and does not contain any digits

    return {
        "text" : text,
        "is_valid" : is_valid,
        "error_message": "" if is_valid else "Input  too short or contains numbers"
    }

def process_valid_input(state: ValidationState) -> ValidationState:
    """Process valid input"""
    print(f"✓ Processing: {state['text']}")
    return state

def handle_invalid_input (state:ValidationState) -> ValidationState:
    """ Handle invalid input"""
    print (f"✗ Error: {state['error_message']}")
    return state

# Routing function
def route_after_validation(state:ValidationState) -> Literal["process","handle_error"]:
    """ Decide next node based on validation result"""
    if state ["is_valid"]:
        return "process"
    else:
        return "handle_error"

# Build graph with conditional edge

workflow = StateGraph(ValidationState)

workflow.add_node("validate", validate_input)
workflow.add_node("process", process_valid_input)
workflow.add_node("handle_error", handle_invalid_input)

workflow.add_edge(START, "validate")
workflow.add_conditional_edges(
    "validate", # from this node
    route_after_validation, # use this function to decide
    {
        "process": "process", # if returns "process", go to process node
        "handle_error": "handle_error" # if returns "handle_error", go to handle_error node
    }
)
workflow.add_edge("process", END)
workflow.add_edge("handle_error", END)

app = workflow.compile()

# Test
test_cases = [
    {"text": "This is a valid input without numbers", "is_valid": False, "error_message": ""},
    {"text": "Short", "is_valid": False, "error_message": ""},
    {"text": "This has numbers 123", "is_valid": False, "error_message": ""}
]

for test in test_cases:
    print(f"\nTesting: '{test['text']}'")
    result = app.invoke(test)
    print(f"Result: {result}")