"""
src/examples/ex11_chain_of_thought.py

Using CoT for better requirement analysis
"""

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv

load_dotenv()
llm = ChatOpenAI(model="gpt-4", temperature=0)

# COT Prompt
prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a requirements analyst. Extract functional requirements using step-by-step reasoning.

PROCESS:
1. ANALYZE: Read the feature description and identify key user actions
2. CATEGORIZE: Group related actions into logical requirements
3. VALIDATE: Ensure each requirement is testable and specific
4. FORMAT: Output as FR-XXX format

Show your reasoning for ANALYZE and CATEGORIZE steps, then provide the final requirements."""),
    ("user", "{description}")
])

chain = prompt | llm
 
# Test
description = """ Build a comment system where users can post comments,
edit their own comments, delete their own comments, and reply to others' comments.
Show comment count for each post"""

result = chain.invoke({"description": description})
print (result.content)