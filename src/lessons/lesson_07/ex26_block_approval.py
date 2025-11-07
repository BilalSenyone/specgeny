"""
src/examples/ex26_block_approval.py

Approve blocks one at a time, with regeneration on rejection
"""

from typing import TypedDict, List
from langgraph.graph import StateGraph, START, END
from langgraph.types import interrupt, Command
from langgraph.checkpoint.memory import MemorySaver
from dotenv import load_dotenv

load_dotenv()


class BlockState(TypedDict):
    blocks: List[dict]
    current_index: int
    approved_blocks: List[dict]
    user_approved: bool
    user_feedback: str


def generate_block(state: BlockState) -> BlockState:
    """Generate next block"""
    block_num = state["current_index"] + 1  # get the current index and add 1 to it
    block = {
        "id": f"BLK-{block_num:03d}",  # format the block number to be 3 digits long
        "content": f"Generated content for block {block_num}",
    }

    print(f"Generated: {block['id']}")
    return {
        "blocks": state["blocks"] + [block]
    }  # return the new block in a list, but other values (current_index, approved_blocks, user_approved, user_feedback) are not changed
# ------------------------------------------------------------


def request_block_approval (state : BlockState) -> BlockState:
    """ Pause for block approval"""
    current_block = state["blocks"][-1]
    
    print (f"\n📋 Block {current_block['id']} ready for review")
    print (f"Content: {current_block['content']}")

    # Pause and send to UI
    # When resumed, interrupt() returns the values from Command(resume=...)
    user_response = interrupt(
        {
            "type": "block_approval_required",
            "block_id": current_block["id"],
            "content": current_block["content"],
            "block_index": state["current_index"]
        }
    )

    # After resume; check user's decision from the resume value
    if user_response.get("approved"):
        print(f"✓ Block {current_block['id']} approved")
        return {
            "approved_blocks": state["approved_blocks"] + [current_block],
            "current_index": state["current_index"] + 1
        }
    else:
        print(f"✗ Block {current_block['id']} rejected")
        print(f"Feedback: {user_response.get('feedback', 'None')}")
        # Don't increment index - will regenerate same block
        # Store feedback for regeneration
        return {"user_feedback": user_response.get("feedback", "")}

# ------------------------------------------------------------

def regenerate_with_feedback (state: BlockState) -> BlockState:
    """ Regenerate block incorporating feedback"""
    block_num = state["current_index"] + 1
    feedback = state.get("user_feedback", "")

    block = {
        "id": f"BLK-{block_num:03d}",
        "content": f"REGENERATED (with feedback: {feedback}): Block {block_num}"
    }

    print(f"Regenerated: {block['id']}")
    # Replace last block with regenerated version
    return {"blocks": state["blocks"][:-1] + [block]}

# ------------------------------------------------------------

def check_approval_status (state : BlockState) -> str : 
    """ Route based on approval"""
    # Check if we have enough approved blocks
    if state ["current_index"] >= 3:  # Generated 3 blocks total 
        return "done"
    #Check if feedback exists (means rejected)
    elif state.get("user_feedback") :
        return "rejected"
    else:
        return "approved"

# ------------------------------------------------------------

# Build workflow
workflow = StateGraph(BlockState)
workflow.add_node("generate", generate_block)
workflow.add_node("request_approval", request_block_approval)
workflow.add_node("regenerate", regenerate_with_feedback)

workflow.add_edge(START, "generate")
workflow.add_edge("generate", "request_approval")
workflow.add_conditional_edges(
    "request_approval", 
    check_approval_status, {
        "approved": "generate", 
        "rejected": "regenerate",
        "done": END
    }
)
workflow.add_edge("regenerate", "request_approval") # Try approval again

checkpointer = MemorySaver()
app = workflow.compile(checkpointer=checkpointer)

# Usage
config = {"configurable": {"thread_id": "spec_blocks_001"}}
initial = {
    "blocks": [],
    "current_index": 0,
    "approved_blocks": [],
    "user_feedback": ""
}

print("=== Block 1 ===")
app.invoke(initial, config=config)

# User approves Block 1
print("User approves block 1...")
app.invoke(Command(resume={"approved":True}), config=config)

# User rejects block 2 with feedback
print("\n=== Block 2 ===")
result = app.invoke(
    Command(resume={"approved":False, "feedback":"Make it more specific"}), 
    config=config)

print(f"\n=== Block 2 Regenerated ===")
# Block 2 regenerated with feedback, waits for approval again

# User approves regenerated block 2
print("User approves regenerated block 2...")
app.invoke(Command(resume={"approved":True}), config=config)

print("\n=== Block 3 ===")
# Block 3 generated...

# User approves block 3
print("User approves block 3...")
app.invoke(Command(resume={"approved":True}), config=config)

print(f"\n✓ All blocks approved: {len(result['approved_blocks'])}")