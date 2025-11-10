"""
Exercise 7: Multi-Stage Approval System

Build workflow with multiple approval gates.

Create a system with three approval stages:

* Requirements approval - User approves extracted requirements
* Success criteria approval - User approves success criteria
*Final specification approval - User approves complete spec
Each stage should:

1. Pause for approval
2. Allow rejection with feedback
3. Regenerate on rejection
4. Track approval history
"""

from typing import TypedDict, List
from langgraph.graph import StateGraph, START, END
from langgraph.types import interrupt, Command
from langgraph.checkpoint.memory import MemorySaver
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv

load_dotenv()

class MultiStageState(TypedDict):
    feature_description: str
    requirements: List[str]
    success_criteria: List[str]
    full_spec: str
    stage: str  # "requirements", "criteria", "final"
    feedback: str
    approval_history: List[dict]

# TODO: Implement nodes
# 1. generate_requirements
# 2. approve_requirements - Use interrupt() and return resume value
# 3. generate_success_criteria
# 4. approve_criteria - Use interrupt() and return resume value
# 5. generate_full_spec
# 6. approve_final - Use interrupt() and return resume value

# Example approval node pattern:
# def approve_requirements(state: MultiStageState) -> MultiStageState:
#     user_response = interrupt({
#         "stage": "requirements",
#         "data": state["requirements"]
#     })
#     if user_response.get("approved"):
#         return {"approval_history": [...]}
#     else:
#         return {"feedback": user_response.get("feedback")}

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

def generate_llm_requirements(state: MultiStageState) -> MultiStageState:
    """Generate requirements for the feature"""

    prompt = ChatPromptTemplate.from_messages([
        ("system", "Extract max 3 functional requirements from the following feature description. One per line. Must be testable and specific. Format: SHALL/MUST/SHOULD [specific capability]. No more than 20 words per requirement."),
        ("user", "Feature: {feature_description}")
    ])
    chain = prompt | llm
    response = chain.invoke({"feature_description": state["feature_description"]})

    return {"requirements": response.content.split("\n")}
#-------------------------------------------------------------------------------------------------

def approve_requirements(state: MultiStageState) -> MultiStageState:
    """Pause for approval of requirements"""
    print(f"Requirements to approve : {state['requirements']}")

    # Interrupt for approval
    user_response = interrupt({
        "type": "approval_required",
        "stage" : "requirements",
        "data" : state["requirements"],
        "message" : "Please review and approve the requirements"
    })

    approval_history = state["approval_history"] or [] # get the approval history or an empty list if it doesn't exist
    if user_response.get("approved"):
        # Add approved for requirement to approval history. First get the approval history and add the new approval
        approval_history.append({
            "stage":"requirements",
            "approved": True,
            "feedback": ""
        })
    else:
        # Add rejected for requirement to approval history. First get the approval history and add the new rejection
        approval_history.append({
            "stage":"requirements",
            "approved": False,
            "feedback": user_response.get("feedback", "")
        })
    
    return {
        "approval_history": approval_history,
        "feedback": user_response.get("feedback", ""),
        "stage": "requirements"
    }
# -------------------------------------------------------------------------------------------------

def generate_llm_success_criteria(state: MultiStageState) -> MultiStageState:
    """Generate success criteria for the feature"""
    prompt = ChatPromptTemplate.from_messages([
        ("system", "From all the following requirements, generate max 10 success criteria. One per line. Must be measurable and specific. Format: MEASURABLE [specific outcome]. No more than 20 words per criterion."),
        ("user", "Requirements: {requirements}")
    ])
    chain = prompt | llm
    response = chain.invoke({"requirements": state["requirements"]})
    return {"success_criteria": response.content.split("\n")}
# -------------------------------------------------------------------------------------------------

def approve_success_criteria(state: MultiStageState) -> MultiStageState:
    """Pause for approval of success criteria"""
    print(f"Success criteria to approve : {state['success_criteria']}")
    
    # Interrupt for approval
    user_response = interrupt({
        "type": "approval_required",
        "stage": "success_criteria",
        "data": state["success_criteria"],
        "message": "Please review and approve the success criteria"
    })
    approval_history = state["approval_history"] or [] # get the approval history or an empty list if it doesn't exist
    if user_response.get("approved"):
        # Add approved for success criteria to approval history. First get the approval history and add the new approval
        approval_history.append({
            "stage":"success_criteria",
            "approved": True,
            "feedback": ""
        })
    else:
        # Add rejected for success criteria to approval history. First get the approval history and add the new rejection
        approval_history.append({
            "stage":"success_criteria",
            "approved": False,
            "feedback": user_response.get("feedback", "")
        })
    return {
        "approval_history": approval_history,
        "feedback": user_response.get("feedback", ""),
        "stage": "success_criteria"
    }
# -------------------------------------------------------------------------------------------------

def generate_llm_full_spec(state: MultiStageState) -> MultiStageState:
    """Generate full specification for the feature"""
    prompt = ChatPromptTemplate.from_messages([
        ("system", "Generate a full specification for the following feature, requirements and success criteria. Use the following requirements and success criteria to generate the specification. No more than 150 words in total."),
        ("user", "Feature: {feature_description}\nRequirements: {requirements}\nSuccess Criteria: {success_criteria}")
    ])


# TODO: Implement routing logic

# TODO: Build workflow with approval gates

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