"""
src/examples/ex30_retry_backoff.py

Implement retry logic with exponential backoff
"""

from typing import TypedDict, List
from langgraph.graph import StateGraph, START, END
# from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
import time
import random
from dotenv import load_dotenv

load_dotenv()


class RetryState(TypedDict):
    input_text: str
    requirements: List[str]
    errors: List[str]
    attempt_count: int

class RetryStateUpdate(TypedDict, total=False):
    input_text: str
    requirements: List[str]
    errors: List[str]
    attempt_count: int


def with_retry(max_retries=3, base_delay=1, max_delay=30):
    """Decorator for retry logic with exponential backoff"""
    def decorator(func):
        # explain that : async def wrapper(state) is a coroutine function that returns a coroutine object. A coroutine is a function that can be paused and resumed.
        async def wrapper(state):
            last_error= None

            for attempt in range(max_retries):
                try:
                    # Try the operation
                    return await func(state) # explain that : return await func(state) is a coroutine function that returns a coroutine object

                except Exception as e :
                    last_error = e
                    error_msg= f"Attempt {attempt + 1} failed: {str(e)}"
                    print(f"⚠ {error_msg}")

                    # Update state with error
                    state["errors"] = state.get("errors", []) + [error_msg] # explain that : state.get("errors", []) is a dictionary that returns the value of the key "errors" if it exists, otherwise it returns an empty list
                    state["attempt_count"] = attempt + 1

                    # Don't retry on final attempt
                    if attempt == max_retries -1:
                        break

                    # Calculate backoff with jitter
                    delay = min(base_delay * (2 ** attempt), max_delay) # delay calculation using exponential backoff formula
                    jitter = random.uniform(0, 0.1 * delay) # jitter calculation using random.uniform function, which does not return a value but a random number between 0 and 0.1 * delay
                    wait_time = delay + jitter # wait time calculation using delay and jitter

                    print (f"⏱ Waiting {wait_time:.1f}s before retry...")
                    time.sleep(wait_time)

                # All retries failed
                return {
                    **state, # **state is a dictionary that returns the value of the key "state" if it exists, otherwise it returns an empty dictionary
                    "errors": state["errors"] + [f"Failed after {max_retries} attempts : {last_error}"] # explain that : state["errors"] + [f"Failed after {max_retries} attempts : {last_error}"] is a list that returns the value of the key "errors" if it exists, otherwise it returns an empty list
                }

        return wrapper # explain that : return wrapper is a function that returns the value of the key "wrapper" if it exists, otherwise it returns an empty function. It is a decorator that wraps the function with the retry logic.

    return decorator # explain that : return decorator is a function that returns the value of the key "decorator" if it exists, otherwise it returns an empty function. It is a decorator that wraps the function with the retry logic.

# ------------------------------------------------------------

@with_retry(max_retries=3, base_delay=1, max_delay=10)
async def extract_requirements(state:RetryState) -> RetryStateUpdate:
    """Extract requirements with retry logic"""

    # Simulate occasional failures
    if random.random() < 0.2:
        raise Exception("Simulated API failure")

    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, max_retries=0)
    response = await llm.ainvoke(f"Extract 3 requirements from: {state['input_text']}. Max 20 words per requirement.")

    # Parse respoinse
    requirements = [
        line.strip()
        for line in response.content.split("\n")
        if line.strip() and not line.startswith("#")
    ][:3] # explain that : [:3] is a list that returns the first 3 elements of the list

    return {
        "requirements": requirements,
        "errors": [], # clear errors on success
    }
# ------------------------------------------------------------


# Build workflow
workflow = StateGraph(RetryState)
workflow.add_node("extract", extract_requirements)
workflow.add_edge(START, "extract")
workflow.add_edge("extract", END)

app = workflow.compile()

# Test
import asyncio # import asyncio module to run the async function

async def main():
    result = await app.ainvoke({
        "input_text": "Build a login system with password reset",
        "requirements": [],
        "errors": [],
        "attempt_count": 0
    })

    print("\n=== Results ===")
    print(f"Requirements: {result['requirements']}")
    print(f"Total attempts: {result['attempt_count']}")
    if result['errors']:
        print(f"Errors: {result['errors']}")

asyncio.run(main())
# ------------------------------------------------------------