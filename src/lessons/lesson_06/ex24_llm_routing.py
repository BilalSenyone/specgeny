"""
src/examples/ex24_llm_routing.py

Use LLM to make routing decisions
"""

from typing import TypedDict, Literal
from langgraph.graph import StateGraph, START, END
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv

load_dotenv() # Load environment variables from .env file

class SmartRoutinState(TypedDict):
    user_request: str
    route_decision: str
    processing_result: str

def llm_router(state: SmartRoutinState) -> SmartRoutinState:
    """ Use LLM to make routing decisions """
    
    llm = ChatOpenAI(model="gpt-4", temperature=0)
    prompt = ChatPromptTemplate.from_messages([
        ("system", """Analyze the user request and decide which processing path to take.

        Options:
        - "extract": User wants to extract requirements from description
        - "validate": User wants to validate existing requirements
        - "clarify": User is asking questions about requirements
        - "other": Something else

        Respond with ONLY ONE WORD: extract, validate, clarify, or other"""),
        ("user", "{request}")
    ])

    chain = prompt | llm
    response = chain.invoke({"request": state["user_request"]})
    decision = response.content.strip().lower()

    return {"route_decision": decision}

def extract_path (state: SmartRoutinState) -> SmartRoutinState:
    """Process extraction request"""
    return {"processing_result": "Extracting requirements..."}

def validate_path (state: SmartRoutinState) -> SmartRoutinState:
    """Process validation request"""
    return {"processing_result": "Validating requirements..."}

def clarify_path (state: SmartRoutinState) -> SmartRoutinState:
    """Process clarification request"""
    return {"processing_result": "Answering your question..."}

def other_path (state: SmartRoutinState) -> SmartRoutinState:
    """Handle other requests"""
    return {"processing_result": "I'm not sure how to help with that."}

def route_by_llm_decision(state: SmartRoutinState) -> Literal["extract", "validate", "clarify", "other"]:
    """Route based on LLM's decision"""
    decision = state["route_decision"]
    if decision in ["extract", "validate", "clarify", "other"]:
        return decision
    return "other"  # Default fallback


workflow = StateGraph(SmartRoutinState)
workflow.add_node("router", llm_router)
workflow.add_node("extract", extract_path)
workflow.add_node("validate", validate_path)
workflow.add_node("clarify", clarify_path)
workflow.add_node("other", other_path)

workflow.add_edge(START, "router")
workflow.add_conditional_edges(
    "router", 
    route_by_llm_decision,
    {
        "extract": "extract",
        "validate": "validate",
        "clarify": "clarify",
        "other": "other"
    }
)
workflow.add_edge("extract", END)
workflow.add_edge("validate", END)
workflow.add_edge("clarify", END)
workflow.add_edge("other", END)

app = workflow.compile()

# Test
requests = [
    "Extract requirements from this: Build a login system",
    "Check if FR-001 is valid",
    "What does a functional requirement mean?",
    "Tell me a joke"
]

for req in requests:
    print(f"\nRequest: {req}")
    result = app.invoke({
        "user_request": req,
        "route_decision": "",
        "processing_result": ""
    })
    print(f"Decision: {result['route_decision']}")
    print(f"Result: {result['processing_result']}")

