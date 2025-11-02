"""
src/examples/ex08_multi_step_chain.py

Complex chain with multiple processing steps
"""

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.runnables import RunnableLambda
from pydantic import BaseModel, Field
from typing import List
from dotenv import load_dotenv

load_dotenv()
llm = ChatOpenAI(model="gpt-4", temperature=0)

# Step 1 : Extract requirements (Pydantic model)


class Requirement (BaseModel):
    id: str
    description: str
    priority : str

class Requirements (BaseModel):
    items: List[Requirement]

req_parser = PydanticOutputParser(pydantic_object=Requirements)

req_prompt = ChatPromptTemplate.from_messages([
    ("system", "Extract requirements.\n\n{format_instructions}"),
    ("user", "{description}")
]).partial(format_instructions=req_parser.get_format_instructions())
# what does the partial mean ? 
"""Partial is
    a partial function is a function that is created by binding some of the arguments to the function.
    In this case, we are binding the format_instructions argument to the req_parser.get_format_instructions() function.
    This means that the format_instructions argument will be pre-filled with the value returned by the req_parser.get_format_instructions() function.
    This is useful because we can then use the partial function as a regular function.
    This is useful because we can then use the partial function as a regular function.
    So does it happen inside the prompt or outside ?
    It happens inside the prompt.
    The partial function is used to pre-fill the format_instructions argument with the value returned by the req_parser.get_format_instructions() function.
    This means that the format_instructions argument will be pre-filled with the value returned by the req_parser.get_format_instructions() function.
    This is useful because we can then use the partial function as a regular function.
    This is useful because we can then use the partial function as a regular function.
    So does it happen inside the prompt or outside ?
    It happens inside the prompt. 
    So how will the prompt really look like when sent to the LLM ?

"""

print("Format instructions:", req_prompt)

# Step 2 : Validate each requirement (separate function)
def validate_requirements(requirements : Requirements) -> Requirements:
    """Custom Validation logic"""
    for req in requirements.items:
        # Example: ensure description is not empty
        if not req.description.strip():
            raise ValueError(f"Empty description for {req.id}")

        #Example : ensure priority is valid
        if req.priority not in ["P1", "P2", "P3"]:
            req.priority = "P2" # Default to P2
    
    return requirements

# Step 3 : Enrich with additional metadata (another LLM call)
enrich_prompt = ChatPromptTemplate.from_messages([
    ("system", "For each requirement, suggest test scenarios."),
    ("user", "Requirements:\n{requirements}\n\nProvide test scenarios in JSON.")
])

# Build multi-step chain
extraction_chain = req_prompt | llm | req_parser
validation_step = RunnableLambda(validate_requirements) # Explain this
"""RunnableLambda is a function that takes a function and returns a Runnable. means that we can use the validate_requirements function as a step in the chain.
"""
enrichment_chain = enrich_prompt | llm

# Compose full pipeline
full_chain = extraction_chain | validation_step

#Execute
result = full_chain.invoke({
    "description": """Build a search feature where users can search by keyword,
    filter by category, and sort results by relevance or date."""
})

print("Extracted & Validated Requirements:")
for req in result.items:
    print(f"  {req.id} [{req.priority}]: {req.description}")