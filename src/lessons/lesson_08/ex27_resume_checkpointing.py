"""
src/examples/ex27_resume_checkpointing.py

Resume a workflow from its last checkpoint
"""

from typing import TypedDict
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
    total_blocks: int
    current_block: str
    timestamp: str

def process_block(state: PersistentState) -> PersistentState:
    """Process one block (simulates slow operation)"""
    block_num = state["blocks_processed"] + 1

    print(f"Processing block {block_num}...")
    time.sleep(2)  # Simulate slow processing

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

# Build the same workflow
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

# Check PostgreSQL connection
check_postgresql()

# Connect with the same thread_id to resume
config = {"configurable": {"thread_id": "spec_large_001"}}

print("=== Resuming workflow ===\n")

# Use context manager for checkpointer
with PostgresSaver.from_conn_string(POSTGRESQL_CONNECTION_STRING) as checkpointer:
    app = workflow.compile(checkpointer=checkpointer)

    # Get the current state from checkpoint
    current_state = app.get_state(config)

    if current_state.values:
        blocks_done = current_state.values.get('blocks_processed', 0)
        total = current_state.values.get('total_blocks', 0)

        print(f"Found checkpoint: {blocks_done}/{total} blocks completed")
        print(f"Resuming from block {blocks_done}...\n")

        # Resume from checkpoint
        try:
            result = app.invoke(None, config=config) # None means resume from the last checkpoint using the last state
            print(f"\n✓ Completed all {result['blocks_processed']} blocks")
            print(f"Final timestamp: {result['timestamp']}")
        except KeyboardInterrupt:
            print("\n\n⚠ Interrupted again! State is saved.")
            print("Run this script again to continue...")
    else:
        print("❌ No checkpoint found for thread_id 'spec_large_001'")
        print("Run ex27_postgres_checkpointing.py first to create a workflow.")
