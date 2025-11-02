"""
src/examples/ex18_append_state.py

Building conversation history with append strategy
"""


from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, START, END
import operator

class ConversationState(TypedDict):
    messages: Annotated[List[str], operator.add] # operator.add is a function that appends to the list everytime there is a new message
    user_input: str # This is the user input that will be appended to the messages list

def user_message_node(state: ConversationState) -> ConversationState:
    """ Add user message to history List and return the new state"""
    return {
        "messages": [f"User: {state['user_input']}"],
        "user_input": state["user_input"]
    }

def ai_response_node(state: ConversationState) -> ConversationState:
    """ Generate and add AI response to history List and return the new state"""
    last_user_message = state["messages"][-1] # -1 means the last element of the list
    response = f"AI: I understand you said '{last_user_message}'"

    return {"messages": [response]}

# Build workflow
workflow = StateGraph(ConversationState)
workflow.add_node("user", user_message_node)
workflow.add_node("ai", ai_response_node)

workflow.add_edge(START, "user")
workflow.add_edge("user", "ai")
workflow.add_edge("ai", END)

app = workflow.compile()

#Test multiple turns
result = app.invoke({"messages": [], "user_input": "Hello"})
print("After turn 1:", result["messages"])

result = app.invoke({"messages": result["messages"], "user_input": "How are you?"})
print("After turn 2:", result["messages"])