"""
src/examples/ex27_postgres_checkpointing.py

Basic workflow with persistent checkpointing
"""

from typing import TypedDict, List
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.postgres import PostgresSaver
import time
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

class PersistentState(TypedDict):
    blocks_processed: int
    total_blocks:int
    current_block:str
    timestamp:str

def process_block(state: PersistentState) -> PersistentState:
    """ Process one block (simulates slow operation)"""
    block_num = state["blocks_processed"] + 1

    print(f"Processing block {block_num}...")
    time.sleep(2) # Simulate slow processing

    return {
        "blocks_processed": block_num,
        "current_block": f"Block {block_num} content",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }

def check_completion(state: PersistentState) -> str:
    """Route to continue or complete"""
    if state["blocks_processed"] >= state["total_blocks"]:
        return "done"
    return "continue"

# Build workflow
workflow = StateGraph(PersistentState)
workflow.add_node("process", process_block)
workflow.add_edge(START, "process")
workflow.add_conditional_edges(
    "process",
    check_completion,
    {
        "continue": "process",
        "done": END
    }
)

# Check if the connection string is valid
#call verify_postgresql.py
check_postgresql()

# Compile with PostgreSQL checkpointer
with PostgresSaver.from_conn_string(POSTGRESQL_CONNECTION_STRING) as checkpointer:
    app = workflow.compile(checkpointer=checkpointer)
    # Start long-running workflow
    config = {"configurable": {"thread_id": "spec_large_001"}
            }
    initial = {
        "blocks_processed": 0,
        "total_blocks": 10,
        "current_block": "",
        "timestamp": ""
    }
    print("=== Starting workflow ===")
    print("(Press Ctrl+C to interrupt)\n")
    try:
        result = app.invoke(initial, config=config)
        print(f"\n✓ Completed all {result['blocks_processed']} blocks")
    except KeyboardInterrupt:
        print("\n\n⚠ Interrupted! State is saved to database.")
        print("Run the resume script to continue...")

# To resume (run this separately):
"""
# resume_workflow.py
current_state = app.get_state(config)
print(f"Resuming from block {current_state.values['blocks_processed']}")
result = app.invoke(current_state.values, config=config)
"""