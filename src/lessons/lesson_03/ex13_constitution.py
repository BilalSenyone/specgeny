"""
src/examples/ex13_constitutional_ai.py

Applying constitutional principles (like Spec-Kit's constitution.md)
"""

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field, field_validator
from typing import List, Literal
from dotenv import load_dotenv

load_dotenv()
llm = ChatOpenAI(model="gpt-4", temperature=0)


#Constituion (projet principles)
constitution = """
PROJECT CONSTITUTION : SpecBot Requirements Standards

I. CLARITY PRINCIPLE
    All requirements MUST be unambiguous and specific.
    Vague terms ("good, "fast", "user-friendly") are PROHIBITED.

II. TESTABILITY PRINCIPLE
    All requirements MUST be independantly testable.
    Requirements without clear acceptance criteria are INVALID.

III. TECHNOLOGY AGNOSTICISM
    Requirements MUST focus on WHAT, never HOW.
    Technology stack decisions belong in technical design, not requirements.

IV. USER-CENTRIC LANGUAGE
    Requirements MUST use user-focused language.
    System behavior described from user perspective, without technical details.

V. TRACEABILITY
    All Requirements MUST be uniquely identifiable (FR-XXX).
    Dependencies between requirements MUST be explicit.
"""

#Prompt with constitutional checking
prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a requirements analyst governed by strict principles.
    
    {constitution}

    PROCESS : 
    1. Extract requirements from user description
    2. Validate each requirement against ALL constitutional principles
    3. If any requirement violates a principle, revise it
    4. Output only requirements that pass constitutional validation

    FORMAT :
    FR-XXX: [Subject] [SHALL/MUST/SHOULD] [specific action]

    OUTPUT FORMAT:
    ## Analysis
    [Your reasoning here]

    ## Final Requirements
    [Only compliant requirements here]     

    """),
    ("user", "{description}")
])

prompt = prompt.partial(constitution=constitution)

chain = prompt | llm

#Test with intentionally problematic description
description = """Build a nice user authentication system that works fast. Users should be able to log in easily using a React Frontend NextJS with JWT tokens stored in a postgreSQL database"""

result = chain.invoke({"description": description})

print("Input (with violations):")
print(description)
print("\n" + "="*70)
print("Output (constitutionally compliant):")
print(result.content)