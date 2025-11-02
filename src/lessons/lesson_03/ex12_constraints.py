"""
src/examples/ex12_constraints.py

Strict constraint enforcement like Spec-Kit
"""

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field, field_validator
from typing import List, Literal
from dotenv import load_dotenv

load_dotenv()
llm = ChatOpenAI(model="gpt-4", temperature=0)

# Strict Pydantic model with validators
class StrictRequirement(BaseModel):
    id: str = Field(pattern=r"^FR-\d{3}$") #Must match FR-XXX format
    type : Literal["SHALL", "MUST", "SHOULD"]
    subject : Literal["System", "User", "Administrator"]
    action : str = Field(min_length=10, max_length=100)
    testable : bool = Field(default=True)

    @field_validator('action') # Explanation : This is a validator for the action field. It is a class method that is used to validate the action field. It is a class method because it is used to validate the action field for all instances of the StrictRequirement class.
    @classmethod # Explanation : This is a class method. It is a method that is used to validate the action field for all instances of the StrictRequirement class.

    def validate_no_tech_terms(cls, v: str) -> str:
        """ Ensure no implementation details"""
        tech_terms = ['database', 'api', 'react', 'postgres', 'mongodb', 'aws', 'docker']
        lower_action = v.lower()
        for term in tech_terms:
            if term in lower_action:
                raise ValueError(f"Implementation detail detected: '{term}' in requirement")
        return v

class StrictRequirementSet(BaseModel):
    requirements: List[StrictRequirement] = Field(min_length=1, max_length=5) 
# explanation : cannot contain more than 5 requirements

# Create parser
parser = PydanticOutputParser(pydantic_object=StrictRequirementSet)

# Strict prompt with validation
prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a requirements analyst with STRICT formatting rules
    {format_instructions}
    CRITICAL CONSTRAINTS:
1. IDs: MUST be FR-001 through FR-005 (sequential, zero-padded)
2. Type: Only SHALL (mandatory), MUST (required), or SHOULD (optional)
3. Subject: Only "System", "User", or "Administrator"
4. Action: 10-100 characters, describes WHAT not HOW
5. NO technology terms: database, API, React, PostgreSQL, MongoDB, AWS, Docker, etc.
6. Total: Maximum 5 requirements

VALIDATION BEFORE OUTPUT:
✓ Each ID follows FR-XXX pattern?
✓ Each uses SHALL/MUST/SHOULD?
✓ Each starts with System/User/Administrator?
✓ No tech terms in action?
✓ Total count ≤ 5?

If validation fails, revise until all constraints met."""),
    ("user", "Extract requirements:\n\n{description}")
])

prompt = prompt.partial(format_instructions=parser.get_format_instructions())

chain = prompt | llm | parser

# Test
description = """Build a user authentication system with login and password reset"""

try : 
    result = chain.invoke({"description": description})
    print("✓ All constraints satisfied!")
    for req in result.requirements:
        print(f"\n{req.id}: {req.subject} {req.type} {req.action}")
except Exception as e:
    print(f"✗ Constraint violation: {e}")