"""
src/examples/ex05_basic_chain.py

Simple chain: Prompt → LLM → String Parser
"""

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv

load_dotenv()

llm = ChatOpenAI(model="gpt-4", temperature=0)

prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a concise technical writer."),
    ("user", "Define {term} in one sentence.")
])


output_parser = StrOutputParser()

# Compose chain using LCEL
chain = prompt | llm | output_parser

# Execute
result = chain.invoke({"term" : "functional requirement"})
print (f"Result type: {type(result)}")
print (f"Result: {result}")
