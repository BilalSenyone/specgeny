"""
src/examples/ex06_json_parser.py

Parsing JSON output from LLM
"""

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from dotenv import load_dotenv
import json


load_dotenv()
llm = ChatOpenAI(model="gpt-4", temperature=0)

# Create JSON parser
json_parser = JsonOutputParser()

# Prompt with JSON format instructions
prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a requirements analyst. Extract requirements in JSON format.

Output Format:
{format_instructions}"""),
("user", "Extract requirements from: {description}")
])

# Add format instruction to prompt
prompt = prompt.partial(format_instructions= json_parser.get_format_instructions())

# Build chain
chain = prompt | llm | json_parser

# Test
description = """ Build a user login system with email/password authentication.
Include password reset via email and account locking after 3 failed attempts."""

result = chain.invoke ({"description": description})

print("Result type:", type(result))
print("\nParsed JSON:")
print(json.dumps(result, indent=2))