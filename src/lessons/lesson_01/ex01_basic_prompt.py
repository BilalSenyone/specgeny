"""
src/examples/ex01_basic_prompt.py

Basic prompt execution with OpenAI
"""

from langchain_openai import ChatOpenAI
from dotenv import load_dotenv


load_dotenv()

# Initialize model
llm = ChatOpenAI (
    model= "gpt-4",
    temperature=0, # Determinictic output, not creative
)

# Simple invoke
response = llm.invoke ("What is a functional specification ? in less than 20 words.")
print (response.content)