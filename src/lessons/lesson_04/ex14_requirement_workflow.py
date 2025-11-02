"""
src/examples/ex14_requirement_workflow.py

SpecBot workflow: Extract → Validate → Format
"""

from typing import TypedDict, List
from langgraph.graph import StateGraph, START, END
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate

load_dotenv()

#State definition
class RequirementState(TypedDict):
    description: str #Input: user's feature description
    raw_requirements : str #Output from extraction
    validated_requirements: List[str] #Output from validation
    formatted_output : str #Final output

# Node 1: Extract requirements using LLM
def extract_requirements(state : RequirementState) -> RequirementState:
    """Extract requirements from user description"""
    print("🔍 Extracting requirements...")

    llm = ChatOpenAI(model="gpt-4", temperature=0)
    prompt = ChatPromptTemplate.from_messages([
        ("system","Extract 3-5 functional requirements. One per line. Must be testable and specific. Format: SHALL/MUST/SHOULD [specific capability]"),
        ("user","{description}")
    ])
    chain = prompt | llm
    response = chain.invoke({"description": state["description"]})

    return {
        "description": state["description"], # No change
        "raw_requirements": response.content, # Extracted requirements
        "validated_requirements": [], # Will be populated by validation
        "formatted_output": "" # Will be populated by formatting
    }

# Node 2 : Validate requirements
def validate_requirements(state: RequirementState) -> RequirementState:
    """ Ensure requirements are testable and specific"""
    print("✅ Validating requirements...")

    #Simple validation : check length and keywords
    requirements = state["raw_requirements"].split("\n") 
    validated = []

    for req in requirements:
        req = req.strip() # Remove whitespace
        if len(req) > 20 and any(kw in req for kw in ["MUST", "SHALL", "SHOULD"]):
            validated.append(req)
    
    print (f" Validated {len(validated)}/{len(requirements)} requirements")

    return {
        "description": state["description"], # No change
        "raw_requirements": state["raw_requirements"], # No change
        "validated_requirements": validated, # Validated requirements
        "formatted_output": "" # Will be populated by formatting
    }

# Node 3 : Format output
def format_output(state : RequirementState) -> RequirementState:
    """ Format requirements as FR-XXX list"""
    print("📝 Formatting output...")

    formatted = []
    for i, req in enumerate(state["validated_requirements"], 1): # Enumerate : index starts at 1
        formatted.append (f"FR-{i:03d}: {req}") # FR-001: Requirement 1

    output = "\n".join(formatted)

    return {
        "description": state["description"], # No change
        "raw_requirements": state["raw_requirements"], # No change
        "validated_requirements": state["validated_requirements"], # No change
        "formatted_output": output # Formatted output
    }

# Build workflow
workflow = StateGraph(RequirementState) # StateGraph : graph of nodes and edges

workflow.add_node("extract", extract_requirements) # LLM call to extract requirements from a user description
workflow.add_node("validate", validate_requirements) # Validate requirements
workflow.add_node("format", format_output) # Format output

workflow.add_edge(START, "extract") # START → extract
workflow.add_edge("extract", "validate") # extract → validate
workflow.add_edge("validate", "format") # validate → format
workflow.add_edge("format", END) # format → END

# Compile the graph
app = workflow.compile()

# Test
initial_state : RequirementState = {
    "description": "Build a login system with email authentication and password reset",
    "raw_requirements": "",
    "validated_requirements": [],
    "formatted_output": ""
}

result = app.invoke(initial_state)

print("\n" + "="*70)
print("FINAL OUTPUT")
print("="*70)
print(result["formatted_output"])
print("\n" + "-"*70)

print("RAW REQUIREMENTS:")
print("-"*70)
print(result["raw_requirements"])
print("\n" + "-"*70)

print("VALIDATED REQUIREMENTS:")
print("="*70)
print(result["validated_requirements"])
print("\n" + "-"*70)

