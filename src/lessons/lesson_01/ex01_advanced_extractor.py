"""
src/exercises/ex01_advanced_extractor.py

Advanced requirement extraction with categorization and priorities
"""

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
 #The key advantage of using Pydantic is that the model-generated output will be validated. Pydantic will raise an error if any required fields are missing or if any fields are of the wrong type.
from typing import List, Literal
from dotenv import load_dotenv

load_dotenv()


#Define structured output
class Requirement(BaseModel):
    id: str = Field(description="Requirement ID (e.g., FR-001, NFR-001)")
    type: Literal["functional", "non-functional", "business_rule"]
    priority: Literal["P1", "P2", "P3"]
    description: str = Field(description="Clear, testable requirement description")
    dependencies: List[str] = Field(default=[], description="IDs of requirements this depends on")

class RequirementSet(BaseModel):
    requirements: List[Requirement]

#Todo : Implement advanced extraction with structured output
# Hint : Use PydanticOutputParser for structured responses

llm = ChatOpenAI(model="gpt-4", temperature=0)
structured_llm = llm.with_structured_output(RequirementSet)

# Test cases (user messages)
test_descriptions = [
    """I want to build a user login system where users can sign in with
    their email and password. If they forget their password, they should
    be able to reset it via email. After 3 failed login attempts, their
    account should be temporarily locked for security.""",

    """Create a task management feature where users can create tasks,
    assign them to team members, set due dates, and mark them as complete.
    Users should be able to filter tasks by status and assignee.""",

    """Build a notification system that alerts users when they receive
    a new message, when someone mentions them, or when a task is assigned
    to them. Users should be able to customize which notifications they receive."""
]

# Run the structured LLM on each test case
for i, description in enumerate(test_descriptions, 1):
    print(f"\n{'='*70}")
    print(f"Test Case {i}")
    print(f"{'='*70}")
    print(f"Input: {description[:100]}...")
    response = structured_llm.invoke(description)
    print(f"\nExtracted Requirements:")
    for req in response.requirements:
        print(f"{req.id} [{req.priority}] ({req.type})")
        print(f"  {req.description}")
        print(f"  Dependencies: {req.dependencies}")
        print(f"{'='*70}")
