"""
Exercise 7: Multi-Stage Approval System

Build workflow with multiple approval gates
"""

from typing import Literal, TypedDict, List
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from langgraph.types import interrupt, Command
from langgraph.checkpoint.memory import MemorySaver
from dotenv import load_dotenv

load_dotenv()

class MultiStageState(TypedDict):
    feature_description: str
    requirements: List[str]
    success_criteria: List[str]
    full_spec: str
    stage: Literal["requirements", "criteria", "final"]  # "requirements", "criteria", "final"
    feedback: str
    approval_history: List[dict] # List of dictionaries with stage and approved

# TODO: Implement nodes
# 1. generate_requirements
def generate_requirements(state: MultiStageState) -> MultiStageState:
    """ Extract requirements and feature namefor one feature """
    current_feature = state["feature_description"]
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    prompt = ChatPromptTemplate.from_messages([
        ("system", "Extract max 3 functional requirements from the following feature description.. One per line. Must be testable and specific. Less than 15 words per requirement. Format: FR-XXX: System SHALL/MUST/SHOULD [specific capability]. Example: FR-001: System SHALL provide user account creation functionality"),
        ("user", "Feature Description: {current_feature}")
    ])
    
    # Extract requirements
    chain = prompt | llm
    response = chain.invoke({"current_feature": current_feature})

    return {
        "requirements": response.content.split("\n")
    }
# ------------------------------------------------------------

# 2. approve_requirements - Use interrupt() and return resume value
def approve_requirements (state: MultiStageState) -> MultiStageState:
    """ Pause for requirements approval """
    print(f"\n📋 Requirements for {state['feature_description']} ready for review")
    print(f"Requirements to approve : \n{'\n'.join(state['requirements'])}")

    # Pause and send to UI
    user_response = interrupt({
        "type": "requirements_approval_required",
        "requirements": state["requirements"],
        "feature_description": state["feature_description"]
    })

    if user_response.get("approved"):
        print(f"✓ Requirements for {state['feature_description']} approved")
        return {
            "approval_history": state["approval_history"] + [{"stage": "requirements", "approved": True}], # Add approved to approval history
            "stage": "requirements" # Set stage to requirements so we can regenerate
        }
    else:
        print(f"✗ Requirements for {state['feature_description']} rejected")
        print(f"Feedback: {user_response.get('feedback', 'None')}")
        return {"feedback": user_response.get("feedback", ""), "stage": "requirements"} # Set stage to requirements so we can regenerate
# ------------------------------------------------------------

# 3. generate_success_criteria
def generate_success_criteria(state: MultiStageState) -> MultiStageState:
    """ Generate success criteria for one feature """
    current_feature = state["feature_description"]
    requirements = state["requirements"]
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", "Generate 3 success criteria for the following feature. One per line. Must be measurable and specific. Less than 15 words per criterion. Use the following requirements as context: {requirements}"),
        ("user", "Feature Description: {current_feature}")
    ])

    chain = prompt | llm
    response = chain.invoke({"current_feature": current_feature, "requirements": requirements})

    return {
        "success_criteria": response.content.split("\n")
    }
# ------------------------------------------------------------

# 4. approve_criteria - Use interrupt() and return resume value
def approve_criteria(state: MultiStageState) -> MultiStageState:
    """ Pause for criteria approval """
    print(f"\n📋 Success criteria for {state['feature_description']} ready for review")
    print(f"Success criteria to approve : \n{'\n'.join(state['success_criteria'])}")
    
    user_response = interrupt({
        "type": "criteria_approval_required",
        "criteria": state["success_criteria"],
        "feature_description": state["feature_description"]
    })

    if user_response.get("approved"):
        print(f"✓ Success criteria for {state['feature_description']} approved")
        return {
            "approval_history": state["approval_history"] + [{"stage": "criteria", "approved": True}], # Add approved to approval history
            "stage": "criteria" # Set stage to criteria so we can regenerate
        }
    else:
        print(f"✗ Success criteria for {state['feature_description']} rejected")
        print(f"Feedback: {user_response.get('feedback', 'None')}")
        return {"feedback": user_response.get("feedback", ""), "stage": "criteria"} # Set stage to criteria so we can regenerate
# ------------------------------------------------------------

# 5. generate_full_specc
def generate_full_spec(state: MultiStageState) -> MultiStageState:
    """ Generate the full specification for one feature """
    current_feature = state["feature_description"]
    requirements = state["requirements"]
    success_criteria = state["success_criteria"]
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", "Generate the functional specification for the following feature. No technical details. Less than 200 words. Use the following requirements and success criteria as context: \n\n Requirements: {requirements} \n\n Success Criteria: {success_criteria}"),
        ("user", "Feature Description: {current_feature}")
    ])

    chain = prompt | llm
    response = chain.invoke({"current_feature": current_feature, "requirements": requirements, "success_criteria": success_criteria})
    return {
        "full_spec": response.content
    }
# ------------------------------------------------------------

# 6. approve_final - Use interrupt() and return resume value
def approve_final(state: MultiStageState) -> MultiStageState:
    """ Pause for final approval """
    print(f"\n📋 Full specification for {state['feature_description']} ready for review")
    print(f"Full specification to approve : \n{state['full_spec']}")
    
    user_response = interrupt({
        "type": "final_approval_required",
        "full_spec": state["full_spec"],
        "feature_description": state["feature_description"]
    })

    if user_response.get("approved"):
        print(f"✓ Full specification for {state['feature_description']} approved")
        return {
            "approval_history": state["approval_history"] + [{"stage": "final", "approved": True}], # Add approved to approval history
            "stage": "final" # Set stage to done so we can end the workflow
        }
    else:
        print(f"✗ Full specification for {state['feature_description']} rejected")
        print(f"Feedback: {user_response.get('feedback', 'None')}")
        return {"feedback": user_response.get("feedback", ""), "stage": "final"} # Set stage to final so we can regenerate

def check_approval_status(state: MultiStageState) -> ["approve", "regenerate", "done"]:
    """ Check if approval is required for the current stage """
    # Check stage AND approval history
    print(f"🔍Checking approval status for {state['stage']}")
    print(f"🧬Approval history: {state['approval_history']}")

    if state["stage"] == "requirements" and any(item["stage"] == "requirements" and item["approved"] for item in state["approval_history"]):
        print("👍 Requirements approved")
        return "approve"
    elif state["stage"] == "criteria" and any(item["stage"] == "criteria" and item["approved"] for item in state["approval_history"]):
        print("👍 Criteria approved")
        return "approve"
    elif state["stage"] == "final" and any(item["stage"] == "final" and item["approved"] for item in state["approval_history"]):
        print("👍 Final approved")
        return "approve"
    else:
        print("👎 Rejected. Regenerating...")
        return "regenerate"


# TODO: Implement routing logic
workflow = StateGraph[MultiStageState, None, MultiStageState, MultiStageState](MultiStageState)
workflow.add_node("generate_requirements", generate_requirements)
workflow.add_node("approve_requirements", approve_requirements)
workflow.add_node("generate_success_criteria", generate_success_criteria)
workflow.add_node("approve_criteria", approve_criteria)
workflow.add_node("generate_full_spec", generate_full_spec)
workflow.add_node("approve_final", approve_final)
workflow.add_node("check_approval_status", check_approval_status)

workflow.add_edge(START, "generate_requirements")
workflow.add_edge("generate_requirements", "approve_requirements")
workflow.add_conditional_edges(
    "approve_requirements", 
    check_approval_status,
    {
        "approve" : "generate_success_criteria",
        "regenerate" : "generate_requirements",
        "done" : END # Should never happen
    }
)
workflow.add_edge("generate_success_criteria", "approve_criteria")
workflow.add_conditional_edges(
    "approve_criteria",
    check_approval_status,
    {
        "approve" : "generate_full_spec",
        "regenerate" : "generate_success_criteria",
        "done" : END # Should never happen
    }
)
workflow.add_edge("generate_full_spec", "approve_final")
workflow.add_conditional_edges(
    "approve_final",
    check_approval_status,
    {
        "approve" : END,
        "regenerate" : "generate_full_spec",
        "done" : END # Should never happen
    }
)

# Test
config = {"configurable": {"thread_id": "multi_stage_001"}}
initial = {
    "feature_description": "User authentication system",
    "requirements": [],
    "success_criteria": [],
    "full_spec": "",
    "stage": "requirements",
    "feedback": "",
    "approval_history": []
}

# Run and resume pattern:
# app.invoke(initial, config=config)
# app.invoke(Command(resume={"approved": True}), config=config)

checkpointer = MemorySaver()
app = workflow.compile(checkpointer=checkpointer)

print("=== Starting workflow ===")
result = app.invoke(initial, config=config)

# Reject requirement 
print("\n🧑‍💼 ❌ User rejects requirement...")
result = app.invoke(Command(resume={"approved":False, "feedback": "Make it more specific"}), config=config)

# Approve requirement (2nd approval)
print("\n🧑‍💼 ✅ User approves requirement (2nd)...")
result = app.invoke(Command(resume={"approved":True}), config=config)

# Reject criteria (1st approval)
print("\n🧑‍💼 ❌ User rejects criteria (1st approval)...")
result = app.invoke(Command(resume={"approved":False, "feedback": "Make it more specific"}), config=config)

# Approve criteria (2nd approval)
print("\n🧑‍💼 ✅ User approves criteria (2nd approval)...")
result = app.invoke(Command(resume={"approved":True}), config=config)

# Reject final (1st approval)
print("\n🧑‍💼 ❌ User rejects final (1st approval)...")
result = app.invoke(Command(resume={"approved":False, "feedback": "Make it more specific"}), config=config)

# Approve final (2nd approval)
print("\n🧑‍💼 ✅User approves final (2nd approval)...")
result = app.invoke(Command(resume={"approved":True}), config=config)