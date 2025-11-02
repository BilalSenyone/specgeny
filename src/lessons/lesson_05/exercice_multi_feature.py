"""
Exercise 5: Multi-Feature Processor

Build a workflow that processes multiple features in parallel
"""

"""
Requirements
Create a system that:

Accepts list of feature descriptions
Processes each feature in parallel (extract requirements)
Validates each feature's requirements independently
Aggregates all results into final specification
Tracks progress and errors per feature

"""

from typing import TypedDict, Annotated, List, Literal
from langgraph.graph import StateGraph, START, END
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
import operator
from dotenv import load_dotenv

load_dotenv()


class FeatureResult (TypedDict):
    feature_name: str
    requirements: List[str]
    validation_errors: Annotated[List[str], operator.add]
    status: Literal["pending", "processing", "completed", "failed"]
    total_retries: int = 3 # default is 3 retries
    current_retry: int = 0 # 0 is the first retry

class MultiFeatureState(TypedDict):
    features: List[str] # Input feature descriptions
    results : List[FeatureResult] # operator.add is a function that appends to the list everytime there is a new feature result
    current_feature_index: int
    total_requirements: int
    errors: Annotated[List[str], operator.add] # operator.add is a function that appends to the list everytime there is a new error



def initialize_processing(state: MultiFeatureState) -> MultiFeatureState:
    """ Prepare feature processing """

    return {
        "features": state["features"],
        "results": [],
        "current_feature_index": 0,
        "total_requirements": 0,
        "errors": []
    }

def extract_requirements(state: MultiFeatureState) -> MultiFeatureState:
    """ Extract requirements and feature namefor one feature """
    current_feature = state["features"][state["current_feature_index"]]
    llm = ChatOpenAI(model="gpt-4", temperature=0)

    prompt = ChatPromptTemplate.from_messages([
        ("system", "Extract max 3 functional requirements from the following feature description.. One per line. Must be testable and specific. Less than 15 words per requirement. Format: FR-XXX: System SHALL/MUST/SHOULD [specific capability]. Example: FR-001: System SHALL provide user account creation functionality"),
        ("user", "Feature: {current_feature}")
    ])
    
    # Extract requirements
    chain = prompt | llm
    response = chain.invoke({"current_feature": current_feature})

    # Get existing results
    results = state["results"].copy()
    current_index = state["current_feature_index"]

    # Create new feature 
    new_result: FeatureResult= {
         "feature_name": current_feature,
         "requirements":response.content.split("\n"),
         "validation_errors": [],
         "status": "pending",
         "total_retries": 2,
         "current_retry": 0
         
    }

    # Check if result already exists (retry scenario)
    if current_index < len(results) :
        # Update existing result
        results[current_index] = {
            **new_result,
            "current_retry": results[current_index]["current_retry"] + 1            
        }
    else:
        # Add new result
        results.append(new_result)

    return {
        "results": results,
    }

def validate_requirements(state: MultiFeatureState) -> MultiFeatureState:
        """ Validate the requirements for the current feature """

        results = state["results"].copy()
        current_feature_result = results[state["current_feature_index"]]
        requirements = current_feature_result["requirements"]
        validation_errors = []

        #Validate
        for req in requirements:
             req = req.strip() # Remove whitespace
             req_lower = req.lower() # Convert to lowercase
             word_count = len(req.split())

             if word_count> 20 or not any(kw in req_lower for kw in ["must", "shall", "should"]):
                  validation_errors.append(req)
            
        current_feature_result["validation_errors"] = validation_errors
        current_feature_result["status"] = "completed" if not validation_errors else "failed"

        

        return {
            "results": results,
            "current_feature_index": state["current_feature_index"] , # Keep same
            "total_requirements": state["total_requirements"],
            "errors": validation_errors
        }

def route_after_validation(state: MultiFeatureState) -> Literal["done", "retry", "next_feature"]:
    """ Route based on validation result and remaining features """
    current_index = state["current_feature_index"]
    current_result = state["results"][current_index] # ✅ Safe now!

    # If failed and retries lefts - retry same feature
    if (current_result["status"] == "failed" and 
        current_result["current_retry"] < current_result["total_retries"]):
         return "retry"
    
    # If completed or max retries - check if more features
    if current_index +1 < len(state["features"]) :
         return "next_feature"
    else : 
         return "done"

def move_to_next_feature(state: MultiFeatureState) -> MultiFeatureState:
     """ Increment feature index and reset retry count"""
     return {
         "current_feature_index": state["current_feature_index"] + 1,
     }

def aggregate_results (state: MultiFeatureState) -> MultiFeatureState:
    """ Aggregate all results """
    total_requirements = 0
    total_errors = 0
    features = state["features"]
    results = state["results"]
    errors = state["errors"]

    #1. Calculate total features
    total_features = len(features)

    #2. Calculate total requirements
    for result in results:
         total_requirements += len(result["requirements"])
    
    #3. Calculate total errors by getting all errors in results state
    for result in results:
         errors.extend(result["validation_errors"])
         total_errors += len(result["validation_errors"])

    return {
       "total_requirements": total_requirements,
       "errors": errors,       
    }

# TODO: Create nodes for:
# 1. Initialize - prepare feature processing
# 2 Get LLM response - get the LLM response for the current feature
# 3. Validate - validate the LLM response for the current feature
# 4. Aggregate - combine all results

# TODO: Build workflow with proper state management

# Test with multiple features
test_features = [
    "User authentication with email and password",
    "Task management with assignment and due dates",
    "File upload with drag-and-drop support"
]

"""
Expected Output: 
'''
Processing 3 features...

Feature 1: User authentication
  Requirements: FR-001, FR-002, FR-003
  Status: ✓ Completed

Feature 2: Task management
  Requirements: FR-004, FR-005, FR-006, FR-007
  Status: ✓ Completed

Feature 3: File upload
  Requirements: FR-008, FR-009
  Status: ✓ Completed

Summary:
  Total features: 3
  Total requirements: 9
  Errors: 0
  '''
"""

# Build workflow
workflow = StateGraph(MultiFeatureState)
workflow.add_node("initialize", initialize_processing)
workflow.add_node("extract", extract_requirements)
workflow.add_node("validate", validate_requirements)
workflow.add_node("aggregate", aggregate_results)
workflow.add_node("move_next", move_to_next_feature)

workflow.add_edge(START, "initialize")
workflow.add_edge("initialize", "extract")
workflow.add_edge("extract", "validate")
workflow.add_conditional_edges(
    "validate",
    route_after_validation,
    {
        "next_feature": "move_next",
        "retry": "extract",
        "done": "aggregate"
    }
)
workflow.add_edge("move_next", "extract")
workflow.add_edge("aggregate", END)

app = workflow.compile()

# Test
print("="*70)
print("Processing features...")


result = app.invoke({"features": test_features})
    


print("Summary :")
print(f"Total features: {len(test_features)}")
print(f"Total requirements: {result['total_requirements']}")
print(f"Total errors: {len(result['errors'])}")
print("="*70)
