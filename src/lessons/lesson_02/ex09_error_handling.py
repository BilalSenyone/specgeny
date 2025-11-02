"""
src/examples/ex09_error_handling.py

Handling parsing errors gracefully
"""

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
# from langchain.output_parsers import OutputFixingParser
from pydantic import BaseModel, Field
from typing import List
from dotenv import load_dotenv
load_dotenv()

llm = ChatOpenAI(model="gpt-4", temperature=0)

# Define Pydantic models
class SimpleRequirement(BaseModel):
    id: str = Field(description="Requirement ID")
    description : str = Field(description="Description")

class RequirementList(BaseModel):
    requirements: List[SimpleRequirement]

# Create base parser
base_parser = PydanticOutputParser(pydantic_object=RequirementList)

# Wrap with OutputFixing
# fixing_parser = OutputFixingParser.from_llm(parser=base_parser, llm=llm)

# Prompt with format instructions
prompt = ChatPromptTemplate.from_messages([
    ("system", "Extract requirements.\n\n{format_instructions}"),
    ("user", "{description}")
]).partial(format_instructions=base_parser.get_format_instructions())

# Try with regular parser
try: 
    chain_regular = prompt | llm | base_parser
    result_regular = chain_regular.invoke({"description": "Build a login system"})
    print("✓ Regular parser succeeded")
    print(result_regular)
except Exception as e:
    print(f"✗ Regular parser failed: {e}")

# Try with fixing parser : Now its rather llm.structured_output
try : 
    result_fixing = llm.structured_output(base_parser.get_format_instructions())(description="Build a login system")
    print("✓ Fixing parser succeeded")
    print(result_fixing)
except Exception as e:
    print(f"✗ Fixing parser failed: {e}")

