"""
src/examples/ex02_prompt_template.py

Using prompt templates for reusable prompts
"""

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv


load_dotenv()

# Initialize model
llm = ChatOpenAI (
    model= "gpt-4",
    temperature=0, # Determinictic output, not creative
)

# Create a reusable template
template = ChatPromptTemplate.from_messages([
    ("system", """You are a technical writer specializing in {domain}.
    Your task is to create clear, concise documentation."""),
    ("user", "{task}")
])

#Use the template multiple times
scenarios = [
    {"domain": "API documentation", "task":"Explain what a REST API endpoint is"},
    {"domain": "user guides", "task":"Explain how to reset a password"},
    {"domain": "functional specifications", "task":"Explain what a user story is"}
]



for scenario in scenarios:
    chain = template | llm
    response = chain.invoke(scenario)
    print(f"\n{'='*60}")
    print(f"Domain: {scenario['domain']}")
    print(f"Task: {scenario['task']}")
    print(f"{'='*60}")
    print(response.content)