# Lesson 7: Human-in-the-Loop (HITL) Patterns

> **Story Context**: SpecBot generates specifications automatically, but humans need to review and approve them. This lesson teaches you to build workflows that pause for human approval, handle feedback, and resume execution - the core pattern for building SpecBot's approval system.

---

## 🎯 Learning Objectives

By the end of this lesson, you will:

1. Use `interrupt()` to pause workflows for human input
2. Resume workflows after receiving feedback
3. Implement approval/rejection flows
4. Build timeout mechanisms
5. Create UI integration points for approvals

**Time**: ~4 hours

---

## 📖 Key Concepts

### The `interrupt()` Function

`interrupt()` pauses workflow execution and returns control to the caller. The workflow can be resumed later with new state.

```python
from langgraph.types import interrupt

def approval_node(state):
    """Pause for human approval"""
    # interrupt() returns the value provided when resuming
    user_decision = interrupt(
        {
            "type": "approval_required",
            "data": state["content"],
            "message": "Please review"
        }
    )

    # Execution pauses at interrupt()
    # When resumed with Command(resume=value), continues here
    # user_decision will contain the resume value

    if user_decision.get("approved"):
        return handle_approved(state)
    else:
        return handle_rejected(state)
```

### Workflow Lifecycle with HITL

```
1. Start workflow → Execute nodes
2. Hit interrupt() → Pause & return interrupt value
3. User reviews → Provides feedback
4. Resume workflow → Use Command(resume=value) to continue
5. Complete → Return final result
```

**Key APIs:**
- `interrupt(value)` - Pause execution and send `value` to caller
- `Command(resume=value)` - Resume paused workflow with `value`
- Checkpointer - Required to persist state across pause/resume

---

## 💻 Code Examples

### Example 1: Basic Approval Gate

```python
"""
src/examples/ex25_basic_approval.py

Simple approval gate using interrupt()
"""

from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.types import interrupt, Command
from langgraph.checkpoint.memory import MemorySaver

class ApprovalState(TypedDict):
    content: str
    approved: bool
    feedback: str

def generate_content(state: ApprovalState) -> ApprovalState:
    """Generate content that needs approval"""
    return {
        "content": "This is generated content that needs review",
        "approved": False,
        "feedback": ""
    }

def request_approval(state: ApprovalState) -> ApprovalState:
    """Pause for human approval"""
    print(f"Content to review: {state['content']}")

    # Pause workflow here and wait for human decision
    # When resumed, interrupt() returns the value from Command(resume=...)
    user_decision = interrupt(
        {
            "type": "approval_required",
            "content": state["content"],
            "message": "Please review and approve"
        }
    )

    # After resume, check user's decision from the resume value
    if user_decision.get("approved"):
        print("✓ Approved!")
        return {"content": f"APPROVED: {state['content']}"}
    else:
        print("✗ Rejected")
        return {"content": f"REJECTED: {state['content']}"}

# Build workflow
workflow = StateGraph(ApprovalState)
workflow.add_node("generate", generate_content)
workflow.add_node("approve", request_approval)

workflow.add_edge(START, "generate")
workflow.add_edge("generate", "approve")
workflow.add_edge("approve", END)

# IMPORTANT: Must use checkpointer for HITL
checkpointer = MemorySaver()
app = workflow.compile(checkpointer=checkpointer)

# Usage: Start workflow
config = {"configurable": {"thread_id": "approval_001"}}
initial = {"content": "", "approved": False, "feedback": ""}

print("=== Starting workflow ===")
result = app.invoke(initial, config=config)
print(f"Paused at: {result}")
print(f"Interrupt info: {result.get('__interrupt__')}")

# Simulate user approval
print("\n=== User approves ===")
# Resume with Command(resume=...) to pass decision back to interrupt()
final_result = app.invoke(
    Command(resume={"approved": True}),
    config=config
)
print(f"Final result: {final_result}")
```

### Example 2: Block-by-Block Approval with Regeneration

```python
"""
src/examples/ex26_block_approval.py

Approve blocks one at a time, with regeneration on rejection
"""

from typing import TypedDict, List
from langgraph.graph import StateGraph, START, END
from langgraph.types import interrupt, Command
from langgraph.checkpoint.memory import MemorySaver

class BlockState(TypedDict):
    blocks: List[dict]
    current_index: int
    approved_blocks: List[dict]
    user_approved: bool
    user_feedback: str

def generate_block(state: BlockState) -> BlockState:
    """Generate next block"""
    block_num = state["current_index"] + 1
    block = {
        "id": f"BLK-{block_num:03d}",
        "content": f"Generated content for block {block_num}"
    }

    print(f"Generated: {block['id']}")
    return {"blocks": state["blocks"] + [block]}

def request_block_approval(state: BlockState) -> BlockState:
    """Pause for block approval"""
    current_block = state["blocks"][-1]

    print(f"\n📋 Block {current_block['id']} ready for review")
    print(f"Content: {current_block['content']}")

    # Pause and send to UI
    # When resumed, interrupt() returns the value from Command(resume=...)
    user_response = interrupt(
        {
            "type": "block_approval",
            "block_id": current_block["id"],
            "content": current_block["content"],
            "block_index": state["current_index"]
        }
    )

    # After resume, check user's decision from the resume value
    if user_response.get("approved"):
        print(f"✓ Block {current_block['id']} approved")
        return {
            "approved_blocks": state["approved_blocks"] + [current_block],
            "current_index": state["current_index"] + 1,
            "user_feedback": ""  # Reset feedback
        }
    else:
        print(f"✗ Block {current_block['id']} rejected")
        print(f"Feedback: {user_response.get('feedback', 'None')}")
        # Don't increment index - will regenerate same block
        # Store feedback for regeneration
        return {"user_feedback": user_response.get("feedback", "")}

def regenerate_with_feedback(state: BlockState) -> BlockState:
    """Regenerate block incorporating feedback"""
    block_num = state["current_index"] + 1
    feedback = state.get("user_feedback", "")

    block = {
        "id": f"BLK-{block_num:03d}",
        "content": f"REGENERATED (with feedback: {feedback}): Block {block_num}"
    }

    print(f"Regenerated: {block['id']}")
    # Replace last block with regenerated version
    return {"blocks": state["blocks"][:-1] + [block]}

def check_approval_status(state: BlockState) -> str:
    """Route based on approval"""
    # Check if we have enough approved blocks
    if state["current_index"] >= 3:  # Generated 3 blocks total
        return "done"
    # Check if feedback exists (means rejected)
    elif state.get("user_feedback"):
        return "rejected"
    else:
        return "approved"

# Build workflow
workflow = StateGraph(BlockState)
workflow.add_node("generate", generate_block)
workflow.add_node("request_approval", request_block_approval)
workflow.add_node("regenerate", regenerate_with_feedback)

workflow.add_edge(START, "generate")
workflow.add_edge("generate", "request_approval")
workflow.add_conditional_edges(
    "request_approval",
    check_approval_status,
    {
        "approved": "generate",     # Next block
        "rejected": "regenerate",   # Regenerate current block
        "done": END
    }
)
workflow.add_edge("regenerate", "request_approval")  # Try approval again

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

# User approves block 1
print("User approves block 1")
app.invoke(Command(resume={"approved": True}), config=config)

print("\n=== Block 2 ===")
# Block 2 is generated and waits for approval

# User rejects block 2 with feedback
print("User rejects block 2 with feedback")
result = app.invoke(
    Command(resume={"approved": False, "feedback": "Make it more specific"}),
    config=config
)

print("\n=== Block 2 Regenerated ===")
# Block 2 regenerated with feedback, waits for approval again

# User approves regenerated block 2
print("User approves regenerated block 2")
app.invoke(Command(resume={"approved": True}), config=config)

print("\n=== Block 3 ===")
# Block 3 generated...

# User approves block 3
print("User approves block 3")
final = app.invoke(Command(resume={"approved": True}), config=config)

print(f"\n✓ All blocks approved: {len(final['approved_blocks'])}")
```

---

## 🏋️ Hands-On Exercise: Multi-Stage Approval System

**Objective**: Build a specification generator with multiple approval stages.

### Requirements

Create a system with three approval stages:
1. **Requirements approval** - User approves extracted requirements
2. **Success criteria approval** - User approves success criteria
3. **Final specification approval** - User approves complete spec

Each stage should:
- Pause for approval
- Allow rejection with feedback
- Regenerate on rejection
- Track approval history

### Starter Code

Create `src/exercises/ex07_multi_stage_approval.py`:

```python
"""
Exercise 7: Multi-Stage Approval System

Build workflow with multiple approval gates
"""

from typing import TypedDict, List
from langgraph.graph import StateGraph, START, END
from langgraph.types import interrupt, Command
from langgraph.checkpoint.memory import MemorySaver

class MultiStageState(TypedDict):
    feature_description: str
    requirements: List[str]
    success_criteria: List[str]
    full_spec: str
    stage: str  # "requirements", "criteria", "final"
    feedback: str
    approval_history: List[dict]

# TODO: Implement nodes
# 1. generate_requirements
# 2. approve_requirements - Use interrupt() and return resume value
# 3. generate_success_criteria
# 4. approve_criteria - Use interrupt() and return resume value
# 5. generate_full_spec
# 6. approve_final - Use interrupt() and return resume value

# Example approval node pattern:
# def approve_requirements(state: MultiStageState) -> MultiStageState:
#     user_response = interrupt({
#         "stage": "requirements",
#         "data": state["requirements"]
#     })
#     if user_response.get("approved"):
#         return {"approval_history": [...]}
#     else:
#         return {"feedback": user_response.get("feedback")}

# TODO: Implement routing logic

# TODO: Build workflow with approval gates

# Test
config = {"configurable": {"thread_id": "multi_stage_001"}}
initial = {
    "feature_description": "User authentication system",
    "requirements": [],
    "success_criteria": [],
    "full_spec": "",
    "stage": "requirements",
    "feedback": "",
    "approval_history": []
}

# Run and resume pattern:
# app.invoke(initial, config=config)
# app.invoke(Command(resume={"approved": True}), config=config)
```

---

## 🚀 Challenge: Timeout Handling

**Advanced**: Add timeout mechanisms that automatically approve/reject after a certain time period.

```python
import time
from datetime import datetime, timedelta

class TimeoutState(TypedDict):
    content: str
    approval_requested_at: datetime
    timeout_seconds: int
    approved: bool

def check_timeout(state: TimeoutState) -> bool:
    """Check if approval timed out"""
    if not state.get("approval_requested_at"):
        return False

    elapsed = (datetime.now() - state["approval_requested_at"]).total_seconds()
    return elapsed > state["timeout_seconds"]

# TODO: Implement timeout handling
```

---

## 🎓 Key Takeaways

### HITL Best Practices

✅ **DO**:
- Always use checkpointer with HITL workflows
- Use `Command(resume=value)` to resume paused workflows
- Capture the return value from `interrupt()` to get user input
- Provide clear context for approval decisions
- Handle both approval and rejection
- Track approval history

❌ **DON'T**:
- Forget to use checkpointer (HITL won't work)
- Manually update state values instead of using `Command(resume=)`
- Ignore the return value from `interrupt()`
- Assume user will always approve
- Skip validation after user feedback
- Create infinite approval loops
- Store sensitive data in interrupt values

---

## 🔄 Story Progress: SpecBot v0.7

**What we built**: SpecBot now pauses for human approval!

```python
# SpecBot v0.7 - HITL Integration
for block in blocks:
    generate_block(block)
    interrupt({"type": "approval_required", "block": block})
    # Workflow pauses here
    # User reviews in UI
    # User approves/rejects
    # Workflow resumes
    if approved:
        continue
    else:
        regenerate_with_feedback(block, feedback)
```

**Next Step**: Lesson 8 adds persistence with PostgreSQL checkpointing, allowing long-running workflows to survive crashes and resume days later.

---

**Continue to [Lesson 8: Persistence & Checkpointing →](./08-checkpointing.md)**
