"""
src/examples/ex28_state_history.py

Navigate through workflow state history
"""

from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.postgres import PostgresSaver
import os
import sys
from dotenv import load_dotenv

# Add src directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from src.verify_postgresql import check_postgresql

load_dotenv()

POSTGRESQL_PW = os.getenv('POSTGRESQL_PW')
POSTGRESQL_DB = os.getenv('POSTGRESQL_DB')
POSTGRESQL_CONNECTION_STRING = f"postgresql://postgres:{POSTGRESQL_PW}@localhost:5432/{POSTGRESQL_DB}"

class HistoryState(TypedDict):
    counter: int
    log: str

def increment (state: HistoryState) -> HistoryState:
    """Increment counter"""
    new_count = state ["counter"] + 1 # Add a count to handle next increment
    return {
        "counter": new_count,
        "log": state["log"] + f"\nIncremented to {new_count}"
    }
# ----------------------------------------------------------------

def double (state: HistoryState) -> HistoryState:
    """Double counter"""
    new_count = state["counter"] * 2
    return {
        "counter": new_count,
        "log": state["log"] + f"\nDoubled to {new_count}"
    }
# ----------------------------------------------------------------

def check_continue (state: HistoryState) -> str:
    """Check if counter is less than 10"""
    if state["counter"] >= 10:
        return "done"
    return "continue"
# ----------------------------------------------------------------

# Build workflow
workflow  = StateGraph(HistoryState)
workflow.add_node("increment", increment)
workflow.add_node("double", double)

workflow.add_edge(START, "increment")
workflow.add_edge("increment", "double")
workflow.add_conditional_edges(
      "double",
      check_continue,
      {
          "continue": "increment",
          "done": END
      }
  )

with PostgresSaver.from_conn_string(POSTGRESQL_CONNECTION_STRING) as checkpointer:
# checkpointer = PostgresSaver.from_conn_string(POSTGRESQL_CONNECTION_STRING)
    app = workflow.compile(checkpointer=checkpointer) # Compile with PostgreSQL checkpointer to save state history

    # Run workflow
    config = {"configurable": {"thread_id": "history_demo"}}
    initial = {"counter": 1, "log": "Started"}

    print("=== Running workflow ===")
    result = app.invoke(initial, config=config)

    # Explore history
    print("\n=== State History ===\n")
    history = app.get_state_history(config)

    for i, checkpoint in enumerate (history):
        print(f"Checkpoint {i + 1}:")
        print(f"  Node: {checkpoint.metadata.get('source', 'N/A')}")
        print(f"  Counter: {checkpoint.values.get('counter', 'N/A')}")
        print(f"  Step: {checkpoint.metadata.get('step', 'N/A')}")
        print()

    # Restore to specific checkpoint
    print("=== Restoring to checkpoint 2 ===")
    checkpoints = list(history)
    if len(checkpoints) >= 2:
        old_state = checkpoints[1] # Second checkpoint
        if old_state.values.get('counter', 0) >= 2:
            print (f"Restored counter : {old_state.values['counter']}")
            print (f"Restored log: {old_state.values['log']}")
        else:
            print(f"Skipping: counter ({old_state.values.get('counter')}) is less than 2")