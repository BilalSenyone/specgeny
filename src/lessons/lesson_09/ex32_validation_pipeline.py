"""
src/examples/ex32_validation_pipeline.py

Multi-layer validation with error recovery
"""

from typing import List, TypedDict, Literal
from langgraph.graph import StateGraph, START, END
from pydantic import BaseModel, Field, ValidationError
from enum import Enum
from dotenv import load_dotenv
import re # import re module to use regex

load_dotenv()

class Requirements(BaseModel):
    """ Validated requirement model """
    id : str = Field(pattern=r"^FR-\d{3}$") # pattern=r"^FR-\d{3}$" is a regular expression that matches the id field. FR-XXX format.
    description : str = Field(min_length=20, max_length=200)
    priority : Literal["P1", "P2", "P3"]
    category : Literal["functional", "non-functional", "business"]

    def validate_description_quality(self) -> List[str]:
        """ Custom validation for description quality """
        errors = []

        # Check for modal 
        if not any (word in self.description for word in ["SHALL", "MUST", "SHOULD"]):
            errors.append("Missing modal verb (SHALL/MUST/SHOULD)")

        # Check for implementation details
        tech_terms = ["database", "React", "API", "AWS", "PostgreSQL"]
        if any (term.lower() in self.description.lower() for term in tech_terms):
            errors.append ("Contains implementation details")

        # Check for vague terms
        vague_terms = ["good", "nice", "easy", "simple", "better"]
        if any (term in self.description.lower() for term in vague_terms):
            errors.append ("Contains vague terms")
        
        return errors
    # ------------------------------------------------------------

class ValidationState(TypedDict):
    raw_requirements : List[str]
    validated_requirements : List[Requirements]
    validation_errors : List[str]
    retry_count : int
    status : str

def parse_requirements(state: ValidationState) -> ValidationState:
    """ Parse and validate requirements """

    errors = []
    validated = []

    for i, req_text in enumerate(state["raw_requirements"]):
        try :
            # Extract components with regex
            id_match = re.search(r"(FR-\d{3})", req_text)
            priority_match = re.search(r"\[(P[123])\]", req_text)

            if not id_match or not priority_match:
                errors.append({
                    "index": i,
                    "requirement": req_text,
                    "error": "Missing ID or priority"
                })
                continue
            
            # Initialize requirement object
            req = Requirements(
                id=id_match.group(1),
                description=req_text,
                priority= priority_match.group(1), 
                category="functional"
            )

            quality_errors = req.validate_description_quality()
            if quality_errors:
                errors.append({
                    "index": i,
                    "requirement": req_text,
                    "error": "; ".join(quality_errors)
                })
            else : 
                validated.append(req)
            
        except ValidationError as e:
            errors.append({
                "index":i,
                "requirement":req_text,
                "error": str(e)
            })
    
    return {
        "validated_requirements": validated,
        "validation_errors": errors,
        "retry_count": state["retry_count"],
        "status": "validated" if not errors else "has_errors",
        "raw_requirements": state["raw_requirements"]
    }
    
# ------------------------------------------------------------


def regenerate_invalid(state: ValidationState) -> ValidationState : 
    """ Regenerate invalid requirements """
    print (f"Regenerating {len(state['validation_errors'])} invalid requirements...")

    regenerated = []
    for error in state["validation_errors"]:
        # Simple regeneration logic (in production, use LLM)
        original = error["requirement"]
        req_num = len(state["validated_requirements"]) + len(regenerated) + 1

        fixed = f"FR-{req_num:03d} [P2] The system SHALL {original.lower()}"
        regenerated.append(fixed)
    
    return {
        "raw_requirements": regenerated,
        "validation_errors": [],
        "retry_count": state["retry_count"] + 1,
        "status": state["status"],
        "validated_requirements": state["validated_requirements"]
    }
# ------------------------------------------------------------

def check_validation_status(state: ValidationState) -> Literal["success", "retry", "failed"] : 
    """ Check validation status """
    if state["status"] == "validated":
        return "success"
    elif state["retry_count"] < 3:
        return "retry"
    else : 
        return "failed"

# ------------------------------------------------------------

# Build workflow
workflow = StateGraph(ValidationState)
workflow.add_node("parse", parse_requirements)
workflow.add_node("regenerate", regenerate_invalid)

workflow.add_edge(START, "parse")
workflow.add_conditional_edges(
    "parse",
    check_validation_status,
    {
        "success": END,
        "retry": "regenerate",
        "failed": END
    }
)
workflow.add_edge("regenerate", "parse")


app = workflow.compile()

# Test
test_requirements = [
    "FR-001 [P1] System should have good security",  # Vague
    "FR-002 [P2] System SHALL authenticate users using PostgreSQL database",  # Implementation detail
    "FR-003 [P1] The system SHALL authenticate users within 2 seconds",  # Valid!
]

result = app.invoke({
    "raw_requirements": test_requirements,
    "validated_requirements": [],
    "validation_errors": [],
    "retry_count": 0,
    "status": "pending"
})

print("=== Validation Results ===\n")
print(f"Valid requirements: {len(result['validated_requirements'])}")
print(f"Validation errors: {len(result['validation_errors'])}")
print(f"Retry count: {result['retry_count']}")

if result['validation_errors']:
    print("\nErrors:")
    for error in result['validation_errors']:
        print(f"  - {error['error']}")
        print(f"    Requirement: {error['requirement'][:60]}...")