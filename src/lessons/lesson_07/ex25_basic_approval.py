"""
src/examples/ex25_basic_approval.py

Simple approval gate using interrupt()
"""


from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.types import interrupt, Command
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from langgraph.checkpoint.memory import MemorySaver


load_dotenv()

class ApprovalState(TypedDict):
    content: str
    approved: bool
    feedback: str

def generate_content(state: ApprovalState) -> ApprovalState:
    """ Generate the content that needs approval"""
    return {
        "content": "This is the content that needs approval",
        "approved": False,
        "feedback": ""
    }

def request_approval(state: ApprovalState) -> ApprovalState:
    """ Pause for HITL"""
    print (f"Content to review (from state) {state['content']}")

    # Pause workflow here and wait for human decision
    # When resumed, interrup() returns the value from Command (resume=...)
    user_decision = interrupt({
        "type": "approval_required",
        "content": state["content"],
        "message" : "Please review and approve this content thanks"
    })

    # After resume, check user's decision from the resume value
    if user_decision.get("approved"):
        print("✓ Approved!")
        return {"content": f"APPROVED: {state['content']}"}
    else:
        print("✗ Rejected")
        return {"content": f"REJECTED: {state['content']}"}

# Build workflow
workflow = StateGraph(ApprovalState)
workflow.add_node("generate", generate_content)
workflow.add_node("approve", request_approval)

workflow.add_edge(START, "generate")
workflow.add_edge("generate", "approve")
workflow.add_edge("approve", END)

# IMPORTANT: Must use checkpointer for HITL
checkpointer = MemorySaver()
app = workflow.compile(checkpointer=checkpointer)

# Usage: start workflow
config = {"configurable": {"thread_id": "approval_001"}}
initial = {"content":"",  "approved": False, "feedback": ""}

print("=== Starting workflow ===")
result = app.invoke(initial, config=config)
print(f"Paused at: {result}")
print(f"Interrupt info: {result.get('__interrupt__')}")

# Simulate user approval
print("\n=== User approves ===")
# Resume with Command(resume=...) to pass decision back to interrupt()
final_result = app.invoke(
    Command(resume={"approved":True}),
    config=config
)

print (f"Final result: {final_result}")
