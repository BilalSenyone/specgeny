"""
src/examples/ex03_multi_turn.py

Multi-turn conversations with message history
"""

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from dotenv import load_dotenv


load_dotenv()

llm = ChatOpenAI(model="gpt-4", temperature=0.7) # quite creative

# Build conversation history
messages = [
    SystemMessage(content="You are a helpful specification assistant. Your answer are never more than 2 sentences."),
    HumanMessage(content= "I need to build a user authentication system")
    ]

# First response
response1 = llm.invoke(messages)
print("Assistant:", response1.content)

# Add to history and continue
messages.extend ([
    AIMessage(content = response1.content),
    HumanMessage(content= "What functional requirements should I include ?")
])

response2= llm.invoke (messages)
print ("\nAssistant:", response2.content)

# Add to history and continue
messages.extend([
    AIMessage(content=response2.content),
    HumanMessage(content="Format the first three asFR-001, FR-002, FR-003")
]) 

response3 = llm.invoke (messages)
print ("\nAssistant:", response3.content)