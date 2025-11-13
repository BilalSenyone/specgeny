"""
src/examples/ex29_crash_recovery.py

Production-ready crash recovery system
"""

from typing import TypedDict, List
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.postgres import PostgresSaver
from datetime import datetime
import time
import os
import sys
from dotenv import load_dotenv

load_dotenv()

POSTGRESQL_PW = os.getenv('POSTGRESQL_PW')
POSTGRESQL_DB = os.getenv('POSTGRESQL_DB')
POSTGRESQL_CONNECTION_STRING = f"postgresql://postgres:{POSTGRESQL_PW}@localhost:5432/{POSTGRESQL_DB}"
# ----------------------------------------------------------

class ResumeState(TypedDict):
    spec_id: str
    blocks: List[dict]
    current_index: int
    total_blocks: int
    started_at: str
    last_updated: str
    status: str  # "running", "paused", "completed"

# Create a partial for return
class ResumeStateUpdate(TypedDict, total=False):
    spec_id: str
    blocks: List[dict]
    current_index: int
    total_blocks: int
    last_updated: str
    status: str


# TODO: Implement generate_block_node
def generate_block_node(state: ResumeState) -> ResumeStateUpdate:
    """Generate one block with progress tracking"""
    # TODO: Generate block content
    block_num = state["current_index"] + 1
    print(f"[{block_num}/{state['total_blocks']}] Generating block BLK-{block_num:03d}...", end=" ")
    start_time = time.time()
    time.sleep(2) # sleep for 2 seconds 
    elapsed = time.time() - start_time
    block = {
        "id": f"BLK-{block_num:03d}",
        "content": f"Content for block {block_num}",
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    print(f"✓ ({elapsed:.1f}s)")
    return {
        
        "blocks": state["blocks"] + [block],
        "current_index": block_num,
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "status": "running"
    }
# ------------------------------------------------------------

# TODO: Implement save_checkpoint_node
def save_checkpoint_node(state: ResumeState) -> ResumeStateUpdate:
    """Explicit checkpoint save (for critical points)"""
    # TODO: Mark checkpoint in state
    return {
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "status": "paused"
    }
# ------------------------------------------------------------


# TODO: Implement completion check
def check_completion(state: ResumeState) -> str:
    """Route based on completion status"""
    if state["current_index"] >= state["total_blocks"]:
        return "done"
    return "continue"


# ------------------------------------------------------------

# TODO: Build workflow with checkpointer
workflow = StateGraph(ResumeState)
workflow.add_node("generate", generate_block_node)
workflow.add_node("checkpoint", save_checkpoint_node)
workflow.add_edge(START, "generate")
workflow.add_edge("generate", "checkpoint")
workflow.add_conditional_edges("checkpoint", check_completion, {
    "continue": "generate",
    "done": END
})
# ------------------------------------------------------------

# ------------------------------------------------------------

def start_spec(spec_id: str):
    """Start new specification"""
    config = {"configurable": {"thread_id": spec_id}}
    initial = {
        "spec_id": spec_id,
        "blocks": [],
        "current_index": 0,
        "total_blocks": 5,
        "started_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "status": "running"
    }

    print(f"=== Starting Specification {spec_id} ===")
    print(f"Total blocks: {initial['total_blocks']}\n")

    # Keep checkpointer alive during app usage
    with PostgresSaver.from_conn_string(POSTGRESQL_CONNECTION_STRING) as checkpointer:
        app = workflow.compile(checkpointer=checkpointer)

        try:
            result = app.invoke(initial, config=config) # type: ignore

            print(f"\n✓ Specification {spec_id} completed!")
            total_time = (datetime.now() - datetime.strptime(
                result["started_at"], "%Y-%m-%d %H:%M:%S"
            )).total_seconds()
            print(f"Total time: {total_time:.1f} seconds")
            print(f"Total blocks: {len(result['blocks'])}")

        except KeyboardInterrupt:
            current_state = app.get_state(config) # type: ignore
            progress = current_state.values["current_index"]
            total = current_state.values["total_blocks"]

            print(f"\n\n⚠ Interrupted at block {progress}/{total}")
            print("State saved. Resume with:")
            print(f"  python ex08_resume_anywhere.py resume {spec_id}")

def resume_spec(spec_id: str):
    """Resume existing specification"""
    config = {"configurable": {"thread_id": spec_id}}

    # Keep checkpointer alive during app usage
    with PostgresSaver.from_conn_string(POSTGRESQL_CONNECTION_STRING) as checkpointer:
        app = workflow.compile(checkpointer=checkpointer)
        current_state = app.get_state(config) # type: ignore

        if not current_state or not current_state.values:
            print(f"Error: No specification found with ID '{spec_id}'")
            sys.exit(1)

        progress = current_state.values["current_index"]
        total = current_state.values["total_blocks"]

        print(f"=== Resuming Specification {spec_id} ===")
        print(f"Progress: {progress}/{total} blocks completed\n")

        try:
            result = app.invoke(None, config=config) # type: ignore

            print(f"\n✓ Specification {spec_id} completed!")
            total_time = (datetime.now() - datetime.strptime(
                result["started_at"], "%Y-%m-%d %H:%M:%S"
            )).total_seconds()
            print(f"Total time: {total_time:.1f} seconds")
            print(f"Total blocks: {len(result['blocks'])}")

        except KeyboardInterrupt:
            current_state = app.get_state(config) # type: ignore
            progress = current_state.values["current_index"]
            total = current_state.values["total_blocks"]

            print(f"\n\n⚠ Interrupted at block {progress}/{total}")
            print("State saved. Resume with:")
            print(f"  python ex08_resume_anywhere.py resume {spec_id}")

def show_status(spec_id: str):
    """Show specification status"""
    config = {"configurable": {"thread_id": spec_id}}

    # Keep checkpointer alive during app usage
    with PostgresSaver.from_conn_string(POSTGRESQL_CONNECTION_STRING) as checkpointer:
        app = workflow.compile(checkpointer=checkpointer)
        current_state = app.get_state(config) # type: ignore

        if not current_state or not current_state.values:
            print(f"Error: No specification found with ID '{spec_id}'")
            sys.exit(1)

        state = current_state.values
        progress = state["current_index"]
        total = state["total_blocks"]
        percentage = (progress / total) * 100

        print(f"Specification: {state['spec_id']}")

        if progress >= total:
            print("Status: Completed")
        elif progress > 0:
            print("Status: Paused")
        else:
            print("Status: Not Started")

        print(f"Progress: {progress}/{total} blocks ({percentage:.0f}%)")
        print(f"Started: {state['started_at']}")
        print(f"Last updated: {state['last_updated']}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python ex08_resume_anywhere.py start <spec_id>")
        print("  python ex08_resume_anywhere.py resume <spec_id>")
        print("  python ex08_resume_anywhere.py status <spec_id>")
        sys.exit(1)

    command = sys.argv[1]

    if command == "start":
        if len(sys.argv) < 3:
            print("Error: spec_id required")
            sys.exit(1)
        start_spec(sys.argv[2])

    elif command == "resume":
        if len(sys.argv) < 3:
            print("Error: spec_id required")
            sys.exit(1)
        resume_spec(sys.argv[2])

    elif command == "status":
        if len(sys.argv) < 3:
            print("Error: spec_id required")
            sys.exit(1)
        show_status(sys.argv[2])

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)