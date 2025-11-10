"""
src/examples/ex29_crash_recovery.py

Production-ready crash recovery system
"""

from typing import TypedDict, List
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.postgres import PostgresSaver
import os
import time
import random
from dotenv import load_dotenv

load_dotenv()

POSTGRESQL_PW = os.getenv('POSTGRESQL_PW')
POSTGRESQL_DB = os.getenv('POSTGRESQL_DB')
POSTGRESQL_CONNECTION_STRING = f"postgresql://postgres:{POSTGRESQL_PW}@localhost:5432/{POSTGRESQL_DB}"
# ----------------------------------------------------------

class RobustState(TypedDict):
    spec_id : str
    blocks : List[dict]
    current_index: int
    total_blocks : int
    last_checkpoint: str
    errors: List[str]

# Partial update type - for function returns (not all fields required)
class RobustStateUpdate(TypedDict, total=False):
    spec_id : str
    blocks : List[dict]
    current_index: int
    total_blocks : int
    last_checkpoint: str
    errors: List[str]

def generate_block (state: RobustState) -> RobustStateUpdate:
    """ Generate a new block """
    block_num = state["current_index"] + 1

    # Simulate random failures (10% chance)
    if random.random() < 0.1:
        raise Exception(f"Random failure at block {block_num}") 
    
    block = {
        "id": f"BLK-{block_num:03d}", # 
        "content": f"Generated content for block {block_num}",
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S")
    }

    print (f"✓ Generated block {block_num}/{state['total_blocks']}")

    return {
        "blocks": state["blocks"] + [block],
        "current_index": block_num,
        "last_checkpoint": time.strftime("%Y-%m-%d %H:%M:%S")
    }
# ----------------------------------------------------------

def handle_error(state: RobustState) -> RobustStateUpdate:
    """ Handle errors gracefully, add it to the error list """
    # Note: In production, you'd pass error info through state
    error_msg = f"❌ Error encountered at block {state['current_index'] + 1}"
    return {
        "errors": state["errors"] + [error_msg]
    }
# ----------------------------------------------------------

def check_completion(state: RobustState) -> str:
    """ Check if all blocks have been generated """
    if state["current_index"] >= state["total_blocks"]:
        return "done"
    return "continue"
# ----------------------------------------------------------

# Build workflow with error handling
workflow= StateGraph(RobustState)
workflow.add_node("generate", generate_block)
workflow.add_node("handle_error", handle_error)

workflow.add_edge(START, "generate")
workflow.add_conditional_edges(
    "generate",
    check_completion,
    {
        "continue": "generate",
        "done": END
    }
)

def safe_invoke(app, state, config, max_retries=3):
    """ Invoke with automatic retry on failure"""
    for attempt in range(max_retries):
        try:
            return app.invoke(state, config=config)
        except Exception as e:
            print(f"❌ Error on attempt {attempt + 1}: {e}")
            if attempt < max_retries - 1:
                print("Retrying from last checkpoint...")
                # Get last good state
                current = app.get_state(config)
                state = current.values
                time.sleep(2)
            else:
                print("Max retries reached. Saving state for manual recovery.")
                raise
    return None  # Explicit return if loop completes without success

# Usage
with PostgresSaver.from_conn_string(POSTGRESQL_CONNECTION_STRING) as checkpointer:
    app = workflow.compile(checkpointer=checkpointer)
    
    config = {"configurable": {"thread_id": "robust_spec_001"}}
    initial = {
        "spec_id": "SPEC-001",
        "blocks": [],
        "current_index": 0,
        "total_blocks": 20,
        "last_checkpoint": "",
        "errors": []
    }

    print("=== Starting robust workflow ===")
    print("(Automatic retry on failures)\n")

    try:
        result = safe_invoke(app, initial, config)
        if result:
            print(f"\n✓ Completed all {result['current_index']} blocks")

            if result["errors"]:
                print(f"\n⚠ Errors encountered: {len(result['errors'])}")
                for error in result["errors"]:
                    print(f"  {error}")
        else:
            print("\n❌ Workflow failed to complete")

    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        print("State saved for manual recovery.")
        print(f"\n✗ Workflow failed: {e}")
        print("State saved. Resume with:")
        print(f"  current_state = app.get_state(config)")
        print(f"  app.invoke(current_state.values, config=config)")
