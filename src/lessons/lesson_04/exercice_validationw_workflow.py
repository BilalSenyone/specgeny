"""
src/examples/exercice_validationw_workflow.py

"""

from typing import TypedDict, List, Literal
from langgraph.graph import StateGraph, START, END
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate

load_dotenv()

class RequirementWorkflowState(TypedDict):
    description: str
    requirements: str
    validation_errors: List[str]
    iteration: int
    max_iterations: int
    formatted_output: str

# TODO: Define nodes
def extract_requirements(state: RequirementWorkflowState) -> RequirementWorkflowState:
    """Extract requirements using LLM"""
    print("🔍 Extracting requirements...")    
    llm = ChatOpenAI(model="gpt-4", temperature=0)

    prompt = ChatPromptTemplate([
        ("system", "Extract 5 functional requirements. One per line. Must be testable and specific. Format: SHALL/MUST/SHOULD [specific capability]. No more than 20 words per requirement."),
        ("user", "{description}")
    ])

    chain = prompt | llm
    response = chain.invoke({"description": state["description"]})

    return {
        "description": state["description"],
        "requirements": response.content,
        "max_iterations":state["max_iterations"],
        "iteration": state["iteration"],
        "validation_errors":state["validation_errors"],
        "formatted_output":state["formatted_output"]
    }

def validate_requirements(state: RequirementWorkflowState) -> RequirementWorkflowState:
    """Validate requirements against quality rules"""
    print(f"✅ Validating requirements... try# {state['iteration'] + 1} / {state['max_iterations']}")
    # TODO: Check for:
    # - Testable (contains SHALL/MUST/SHOULD)
    # - Specific (length > 20 chars)
    # - No tech details (no "database", "API", etc.)
    
    # First let's split this requirements by new line
    requirements = state["requirements"].split("\n") 
    validated = []

    #validate for (contains SHALL/MUST/SHOULD And be more than 20 chars)
    for req in requirements:
        req = req.strip() # Remove whitespace
        req_lower = req.lower()
        if len(req) > 20 and any(kw in req_lower for kw in ["must", "shall", "should"]) and not any(kw in req_lower for kw in ["database", "api", "python", "node", "tech"]):
            validated.append(req)
    
    print (f" Validated {len(validated)}/{len(requirements)} requirements")

    return {
        "description": state["description"],
        "max_iterations": state["max_iterations"], 
        "iteration": state["iteration"], 
        "validation_errors": [req for items in requirements if items not in validated],
        "formatted_output":state["formatted_output"]
    }

def fix_requirements(state: RequirementWorkflowState) -> RequirementWorkflowState:
    """Ask LLM to fix invalid requirements"""
    print("🔍 Fixing requirements...")
    llm = ChatOpenAI(model="gpt-4", temperature=0)
    # If validation_errors exist, we need to fix them
    if state["validation_errors"]:
        iteration = state["iteration"] + 1 # Increment iteration
        prompt = ChatPromptTemplate([
            ("system", "Fix and correct the following requirements. Don't add or remove any requirements. Must be testable and specific. Format: SHALL/MUST/SHOULD [specific capability] No more than 20 words per requirement. Forbidden to have any technical related information. "),
            ("user", "{requirements}")
        ])
        chain = prompt | llm
        response = chain.invoke({"requirements": state["requirements"]})

        return {
            "description": state["description"],
            "requirements": response.content,
            "max_iterations": state["max_iterations"],
            "iteration": iteration,
            "validation_errors": [], # Back to empty, because we'll validate again but now with the fixed requirements
            "formatted_output": state["formatted_output"]
        }

def format_output(state: RequirementWorkflowState) -> RequirementWorkflowState:
    """Format as FR-XXX list"""
    print("📝 Formatting output...")
    
    formatted = []
    requirements = state["requirements"].split("\n")
    for i, req in enumerate(requirements, 1):
        formatted.append(f"FR-{i:03d}: {req}")
    output = "\n".join(formatted)

    return {
        "description": state["description"],
        "requirements": state["requirements"],
        "max_iterations": state["max_iterations"],
        "iteration": state["iteration"],
        "validation_errors": state["validation_errors"],
        "formatted_output": output
    }

# TODO: Routing function
def route_after_validation(state: RequirementWorkflowState) -> Literal["fix", "format"]:
    """Decide whether to fix or format"""
    # If validation_errors exist and iterations < max: "fix"
    # Otherwise: "format"
    validation_errors = state["validation_errors"]
    max_iterations = state["max_iterations"]
    current_iteration = state["iteration"]

    if validation_errors and current_iteration < max_iterations:
        return "fix"
    else : 
        return "format"


# TODO: Build workflow
workflow = StateGraph(RequirementWorkflowState)
workflow.add_node("extract", extract_requirements)
workflow.add_node("validate", validate_requirements)
workflow.add_node("fix", fix_requirements)
workflow.add_node("format", format_output)

workflow.add_edge(START, "extract")
workflow.add_edge("extract", "validate")
workflow.add_conditional_edges(
    "validate",
    route_after_validation,
    {
        "fix":"fix",
        "format":"format"
    }
)
workflow.add_edge("fix", "validate")
workflow.add_edge("format", END) # Everytime format is called, so once we reach here it's the end
app = workflow.compile()

# Test
tests = [
    {"description": "Build a login system with email authentication and password reset", "requirements": "", "validation_errors": [], "iteration": 0, "max_iterations": 3, "formatted_output": ""},
    {"description": "Build a login system with email authentication and password reset with react and python in more than 20 chars", "requirements": "", "validation_errors": [], "iteration": 0, "max_iterations": 3, "formatted_output": ""},
    {"description": "Build a login system with email authentication and password reset with react and python in more than 20 chars and must be testable and specific", "requirements": "", "validation_errors": [], "iteration": 0, "max_iterations": 3, "formatted_output": ""},
]

# TODO: Test with multiple inputs
for test in tests:
    result = app.invoke(test)
    
    print("\n" + "="*70)
    print("FINAL OUTPUT")
    print("="*70)
    print(result["formatted_output"])
    print("\n" + "-"*70)
    print("RAW REQUIREMENTS:")
    print("-"*70)
    print(result["requirements"])
    print("\n" + "-"*70)
    print("VALIDATION ERRORS:")
    print("-"*70)
    print(result["validation_errors"])
