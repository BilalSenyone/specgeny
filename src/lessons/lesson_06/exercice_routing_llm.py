"""
Exercise 6: Smart Requirement Classifier

Build intelligent routing based on requirement characteristics
"""


from typing import TypedDict, Literal
from langgraph.graph import StateGraph, START, END
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()

class Requirement(BaseModel):
    requirement: str  # <- ADD THIS
    req_type: Literal["FR", "NFR", "BR"]  # "FR", "NFR", "BR"
    priority: Literal["P1", "P2", "P3"]  # "P1", "P2", "P3"
    is_clear: bool

class ClassifierState(TypedDict):
    description: str
    requirement: str
    req_type: Literal["FR", "NFR", "BR"]  # "FR", "NFR", "BR"
    priority: Literal["P1", "P2", "P3"]  # "P1", "P2", "P3"
    is_clear: bool
    validation_path: str
    final_result: str


def get_requirement (state: ClassifierState) -> ClassifierState:
    """Get requirements from the user using LLM"""
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    prompt = ChatPromptTemplate.from_messages([
        ("system", "Extract the requirement from the user's description. Return the requirement type (FR = Functional Requirement, NFR = Non-Functional Requirement, BR = Business Rule), the priority (P1 = High, P2 = Medium, P3 = Low) and if the requirement is clear (True = Clear, False = Unclear)."),
        ("user", "{description}")
    ])

    structured_llm = llm.with_structured_output(Requirement)
    # response = chain.invoke({"description": state["description"]})
    chain = prompt | structured_llm
    response = chain.invoke({"description": state["description"]})

    return{
        "requirement": response.requirement,
        "req_type": response.req_type,
        "priority": response.priority,
        "is_clear": response.is_clear,
    }
# ----------------------------------------------------------------


# TODO: Implement classify_requirement node
def classify_requirement(state: ClassifierState) -> ClassifierState:
    """Analyze and classify the requirement"""
    # TODO: Determine type (FR/NFR/BR)


    # TODO: Assess priority
    # TODO: Check clarity
    #1. Determine type (FR/NFR/BR)
    #2. Assess priority
    #3. Check clarity

# TODO: Implement routing function
def route_by_classification(state: ClassifierState) -> Literal[...]:
    """Route based on type, priority, clarity"""
    # TODO: Create routing logic
    # High priority functional: "p1_fr"
    # Standard functional: "standard_fr"
    # Non-functional: "nfr"
    # Business rule: "br"
    # Unclear: "clarify"
    pass

# TODO: Implement validator nodes for each path

# TODO: Build workflow with conditional edges

# Test cases
test_requirements = [
    "System SHALL authenticate users within 2 seconds (P1)",
    "User should be able to change theme color (P3)",
    "System must comply with GDPR regulations",
    "Something needs to happen with the data TBD"
]

workflow = StateGraph(ClassifierState)
workflow.add_node("get_requirement", get_requirement)
# workflow.add_node("classify_requirement", classify_requirement)
# workflow.add_node("route_by_classification", route_by_classification)
workflow.add_edge(START, "get_requirement")
workflow.add_edge("get_requirement", END)

app = workflow.compile()

# Test
for req in test_requirements:
    result = app.invoke({"description": req})
    print(f"Result: {result}")
