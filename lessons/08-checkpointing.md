# Lesson 8: Persistence & Checkpointing

> **Story Context**: SpecBot is generating complex specifications with 20+ blocks. If the system crashes mid-generation, we lose everything. This lesson teaches you to implement persistent checkpointing so workflows can survive crashes, resume days later, and maintain full state history.

---

## 🎯 Learning Objectives

By the end of this lesson, you will:

1. Implement PostgreSQL checkpointing for persistent state
2. Save and restore workflow state across sessions
3. Handle long-running workflows that span hours/days
4. Implement crash recovery mechanisms
5. Navigate and manage state history
6. Build time-travel debugging capabilities

**Time**: ~4 hours

---

## 📖 Key Concepts

### Why Checkpointing Matters

Without checkpointing, workflows are ephemeral:
- State exists only in memory
- Crashes lose all progress
- No way to pause and resume later
- Can't debug past states

With checkpointing:
- State persists to database after each node
- Workflows survive crashes and restarts
- Users can close browser and resume later
- Full audit trail of all state changes

### Checkpointer Types

**MemorySaver** (Development):
```python
from langgraph.checkpoint import MemorySaver

checkpointer = MemorySaver()
# Stores in memory - lost on restart
```

**PostgresSaver** (Production):
```python
from langgraph.checkpoint.postgres import PostgresSaver

checkpointer = PostgresSaver.from_conn_string(
    "postgresql://user:password@localhost:5432/specbot"
)
# Persists to PostgreSQL - survives restarts
```

### Thread ID Pattern

Every workflow execution needs a unique thread ID:
```python
config = {"configurable": {"thread_id": "spec_12345"}}
```

This ID links all checkpoints for a single execution.

---

## 💻 Code Examples

### Example 1: Basic PostgreSQL Checkpointing

```python
"""
src/examples/ex27_postgres_checkpointing.py

Basic workflow with persistent checkpointing
"""

from typing import TypedDict, List
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.postgres import PostgresSaver
import time

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

# Compile with PostgreSQL checkpointer
checkpointer = PostgresSaver.from_conn_string(
    "postgresql://postgres:postgres@localhost:5432/specbot"
)
app = workflow.compile(checkpointer=checkpointer)

# Start long-running workflow
config = {"configurable": {"thread_id": "spec_large_001"}}
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
```

### Example 2: State History Navigation

```python
"""
src/examples/ex28_state_history.py

Navigate through workflow state history
"""

from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.postgres import PostgresSaver

class HistoryState(TypedDict):
    counter: int
    log: str

def increment(state: HistoryState) -> HistoryState:
    """Increment counter"""
    new_count = state["counter"] + 1
    return {
        "counter": new_count,
        "log": state["log"] + f"\nIncremented to {new_count}"
    }

def double(state: HistoryState) -> HistoryState:
    """Double counter"""
    new_count = state["counter"] * 2
    return {
        "counter": new_count,
        "log": state["log"] + f"\nDoubled to {new_count}"
    }

# Build workflow
workflow = StateGraph(HistoryState)
workflow.add_node("increment", increment)
workflow.add_node("double", double)

workflow.add_edge(START, "increment")
workflow.add_edge("increment", "double")
workflow.add_edge("double", "increment")
workflow.add_edge("increment", END)

checkpointer = PostgresSaver.from_conn_string(
    "postgresql://postgres:postgres@localhost:5432/specbot"
)
app = workflow.compile(checkpointer=checkpointer)

# Run workflow
config = {"configurable": {"thread_id": "history_demo"}}
initial = {"counter": 1, "log": "Started"}

print("=== Running workflow ===\n")
result = app.invoke(initial, config=config)

# Explore history
print("\n=== State History ===\n")
history = app.get_state_history(config)

for i, checkpoint in enumerate(history):
    print(f"Checkpoint {i + 1}:")
    print(f"  Node: {checkpoint.metadata.get('source', 'N/A')}")
    print(f"  Counter: {checkpoint.values.get('counter', 'N/A')}")
    print(f"  Step: {checkpoint.metadata.get('step', 'N/A')}")
    print()

# Restore to specific checkpoint
print("=== Restoring to checkpoint 2 ===\n")
checkpoints = list(history)
if len(checkpoints) >= 2:
    old_state = checkpoints[1]  # Second checkpoint
    print(f"Restored counter: {old_state.values['counter']}")
    print(f"Restored log: {old_state.values['log']}")
```

### Example 3: Crash Recovery Pattern

```python
"""
src/examples/ex29_crash_recovery.py

Production-ready crash recovery system
"""

from typing import TypedDict, List, Optional
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.postgres import PostgresSaver
import time
import random

class RobustState(TypedDict):
    spec_id: str
    blocks: List[dict]
    current_index: int
    total_blocks: int
    last_checkpoint: str
    errors: List[str]

def generate_block(state: RobustState) -> RobustState:
    """Generate block with potential failures"""
    block_num = state["current_index"] + 1

    # Simulate random failures (10% chance)
    if random.random() < 0.1:
        raise Exception(f"Random failure at block {block_num}")

    block = {
        "id": f"BLK-{block_num:03d}",
        "content": f"Generated content for block {block_num}",
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S")
    }

    print(f"✓ Generated block {block_num}/{state['total_blocks']}")

    return {
        "blocks": state["blocks"] + [block],
        "current_index": block_num,
        "last_checkpoint": time.strftime("%Y-%m-%d %H:%M:%S")
    }

def handle_error(state: RobustState, error: Exception) -> RobustState:
    """Handle errors gracefully"""
    error_msg = f"Error at block {state['current_index'] + 1}: {str(error)}"
    return {
        "errors": state["errors"] + [error_msg]
    }

def check_completion(state: RobustState) -> str:
    """Check if all blocks generated"""
    if state["current_index"] >= state["total_blocks"]:
        return "done"
    return "continue"

# Build workflow with error handling
workflow = StateGraph(RobustState)
workflow.add_node("generate", generate_block)

workflow.add_edge(START, "generate")
workflow.add_conditional_edges(
    "generate",
    check_completion,
    {
        "continue": "generate",
        "done": END
    }
)

checkpointer = PostgresSaver.from_conn_string(
    "postgresql://postgres:postgres@localhost:5432/specbot"
)
app = workflow.compile(checkpointer=checkpointer)

def safe_invoke(app, state, config, max_retries=3):
    """Invoke with automatic retry on failure"""
    for attempt in range(max_retries):
        try:
            return app.invoke(state, config=config)
        except Exception as e:
            print(f"\n⚠ Error on attempt {attempt + 1}: {e}")

            if attempt < max_retries - 1:
                print("Retrying from last checkpoint...")
                # Get last good state
                current = app.get_state(config)
                state = current.values
                time.sleep(2)  # Wait before retry
            else:
                print("Max retries reached. Saving state for manual recovery.")
                raise

# Usage
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
    print(f"\n✓ Successfully generated {len(result['blocks'])} blocks")

    if result["errors"]:
        print(f"\n⚠ Errors encountered: {len(result['errors'])}")
        for error in result["errors"]:
            print(f"  - {error}")
except Exception as e:
    print(f"\n✗ Workflow failed: {e}")
    print("State saved. Resume with:")
    print(f"  current_state = app.get_state(config)")
    print(f"  app.invoke(current_state.values, config=config)")
```

---

## 🏋️ Hands-On Exercise: Resume-Anywhere Specification Generator

**Objective**: Build a specification generator that can be paused at any point and resumed seamlessly.

### Requirements

Create a system that:
1. Generates 15 blocks for a specification
2. Saves checkpoint after each block
3. Can be interrupted at any time
4. Resumes from exact stopping point
5. Displays progress and time elapsed
6. Provides "resume" command that works across sessions

### Starter Code

Create `src/exercises/ex08_resume_anywhere.py`:

```python
"""
Exercise 8: Resume-Anywhere Specification Generator

Build workflow that can pause/resume at any point
"""

from typing import TypedDict, List
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.postgres import PostgresSaver
from datetime import datetime
import time

class ResumeState(TypedDict):
    spec_id: str
    blocks: List[dict]
    current_index: int
    total_blocks: int
    started_at: str
    last_updated: str
    status: str  # "running", "paused", "completed"

# TODO: Implement generate_block_node
def generate_block_node(state: ResumeState) -> ResumeState:
    """Generate one block with progress tracking"""
    # TODO: Generate block content
    # TODO: Simulate processing time (2-3 seconds)
    # TODO: Update timestamps
    # TODO: Print progress
    pass

# TODO: Implement save_checkpoint_node
def save_checkpoint_node(state: ResumeState) -> ResumeState:
    """Explicit checkpoint save (for critical points)"""
    # TODO: Mark checkpoint in state
    pass

# TODO: Implement completion check
def check_completion(state: ResumeState) -> str:
    """Route based on completion status"""
    pass

# TODO: Build workflow with checkpointer

# TODO: Implement CLI interface:
# - start: Start new specification
# - resume: Resume from thread_id
# - status: Show current progress
# - list: List all in-progress specifications

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python ex08_resume_anywhere.py start <spec_id>")
        print("  python ex08_resume_anywhere.py resume <spec_id>")
        print("  python ex08_resume_anywhere.py status <spec_id>")
        sys.exit(1)

    command = sys.argv[1]

    # TODO: Implement commands
```

### Expected Output

```
$ python ex08_resume_anywhere.py start SPEC-001
=== Starting Specification SPEC-001 ===
Total blocks: 15

[1/15] Generating block BLK-001... ✓ (2.1s)
[2/15] Generating block BLK-002... ✓ (2.3s)
[3/15] Generating block BLK-003... ^C

⚠ Interrupted at block 3/15
State saved. Resume with:
  python ex08_resume_anywhere.py resume SPEC-001

$ python ex08_resume_anywhere.py status SPEC-001
Specification: SPEC-001
Status: Paused
Progress: 3/15 blocks (20%)
Started: 2024-01-15 14:30:00
Last updated: 2024-01-15 14:30:06

$ python ex08_resume_anywhere.py resume SPEC-001
=== Resuming Specification SPEC-001 ===
Progress: 3/15 blocks completed

[4/15] Generating block BLK-004... ✓ (2.2s)
[5/15] Generating block BLK-005... ✓ (2.0s)
...
[15/15] Generating block BLK-015... ✓ (2.1s)

✓ Specification SPEC-001 completed!
Total time: 32.4 seconds
Total blocks: 15
```

---

## 🚀 Challenge: Time-Travel Debugger

**Advanced**: Build a debugging interface that lets you "rewind" workflow execution to any previous state.

### Challenge Requirements

Create a system that:
1. Records every state change with metadata
2. Displays timeline of execution
3. Allows jumping to any previous state
4. Can "fork" execution from past state (create alternate timeline)
5. Compares state differences between checkpoints
6. Exports state history as JSON

### Template

```python
"""
src/exercises/ex08_time_travel.py

Time-travel debugging for LangGraph workflows
"""

from langgraph.checkpoint.postgres import PostgresSaver
import json
from datetime import datetime

class TimeTravel:
    """Navigate workflow state history"""

    def __init__(self, app, config):
        self.app = app
        self.config = config

    def list_checkpoints(self):
        """List all checkpoints with metadata"""
        history = self.app.get_state_history(self.config)

        checkpoints = []
        for i, checkpoint in enumerate(history):
            checkpoints.append({
                "index": i,
                "node": checkpoint.metadata.get("source"),
                "step": checkpoint.metadata.get("step"),
                "timestamp": checkpoint.metadata.get("timestamp"),
                "state_preview": str(checkpoint.values)[:100]
            })

        return checkpoints

    def restore_to(self, checkpoint_index: int):
        """Restore to specific checkpoint"""
        # TODO: Get checkpoint at index
        # TODO: Update workflow state
        # TODO: Return restored state
        pass

    def diff(self, checkpoint_a: int, checkpoint_b: int):
        """Show differences between two checkpoints"""
        # TODO: Get both checkpoints
        # TODO: Compare state values
        # TODO: Return formatted diff
        pass

    def fork_from(self, checkpoint_index: int, new_thread_id: str):
        """Create alternate timeline from checkpoint"""
        # TODO: Get checkpoint state
        # TODO: Create new thread with that state
        # TODO: Return new config
        pass

    def export_history(self, output_file: str):
        """Export full state history to JSON"""
        # TODO: Get all checkpoints
        # TODO: Format as JSON
        # TODO: Write to file
        pass

# TODO: Implement CLI interface for time-travel commands
```

---

## 🎓 Key Takeaways

### Checkpointing Best Practices

✅ **DO**:
- Always use checkpointer for production workflows
- Use unique, meaningful thread IDs
- Save critical state before risky operations
- Implement resume capability in your UI
- Test crash recovery regularly
- Monitor checkpoint storage size

❌ **DON'T**:
- Store sensitive data in checkpoints without encryption
- Use same thread_id for different workflow runs
- Forget to clean up old checkpoints
- Rely on MemorySaver in production
- Checkpoint too frequently (performance impact)
- Ignore checkpoint database maintenance

### When to Use Checkpointing

**Always use for**:
- Long-running workflows (>1 minute)
- User-facing applications
- Workflows with human-in-the-loop
- Production systems
- Workflows with expensive operations

**Optional for**:
- Quick test scripts
- Stateless operations
- Pure data transformations

---

## 🔄 Story Progress: SpecBot v0.8

**What we built**: SpecBot now survives crashes and resumes seamlessly!

```python
# SpecBot v0.8 - Persistent Checkpointing
checkpointer = PostgresSaver.from_conn_string(DATABASE_URL)
app = workflow.compile(checkpointer=checkpointer)

# Generate 50-block specification
config = {"configurable": {"thread_id": f"spec_{spec_id}"}}
app.invoke(initial_state, config=config)

# If interrupted, resume exactly where it stopped
current_state = app.get_state(config)
app.invoke(current_state.values, config=config)

# Users can close browser and resume days later!
```

**Next Step**: Lesson 9 adds production-grade error handling with retries, circuit breakers, and fallback strategies.

---

**Continue to [Lesson 9: Error Handling, Retries & Validation →](./09-error-handling.md)**
