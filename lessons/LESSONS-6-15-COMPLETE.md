# Complete Lessons 6-15 Reference

> **Note**: Due to the comprehensive nature of this curriculum, lessons 6-15 are provided here as detailed templates. Each section can be expanded into a full lesson following the pattern established in lessons 1-5.

---

## How to Use This Document

Each lesson below contains:
- 🎯 Learning objectives
- 📖 Key concepts with explanations
- 💻 Complete code examples
- 🏋️ Exercise outline with starter code
- 🔄 Story progress update

**Recommendation**: Copy each lesson section into its own file (`06-conditional-routing.md`, etc.) as you work through the curriculum.

---

# LESSON 6: Conditional Edges & Routing Logic

**Duration**: 3 hours | **Prerequisites**: Lesson 5

## 🎯 Learning Objectives
- Implement complex routing logic based on state
- Use conditional edges with multiple branches
- Create LLM-based routing decisions
- Build routing tables for complex workflows
- Handle routing errors gracefully

## 📖 Key Concepts

### Routing Function Pattern
```python
from typing import Literal

def route_function(state: State) -> Literal["path_a", "path_b", "path_c"]:
    """Return next node name based on state"""
    if state["score"] > 0.8:
        return "path_a"
    elif state["score"] > 0.5:
        return "path_b"
    else:
        return "path_c"
```

### Adding Conditional Edges
```python
workflow.add_conditional_edges(
    "current_node",      # From this node
    route_function,      # Use this function
    {
        "path_a": "node_a",  # Map return values to nodes
        "path_b": "node_b",
        "path_c": "node_c"
    }
)
```

## 💻 Complete Example

```python
"""Smart Requirement Router"""
from langgraph.graph import StateGraph, START, END
from typing import TypedDict, Literal, List

class RequirementState(TypedDict):
    requirement: str
    complexity_score: float
    requires_clarification: bool
    validation_errors: List[str]

def analyze_complexity(state: RequirementState) -> RequirementState:
    """Analyze requirement complexity"""
    req = state["requirement"]
    score = len(req.split()) / 50.0  # Simple complexity metric
    needs_clarification = "TBD" in req or "unclear" in req.lower()

    return {
        "requirement": req,
        "complexity_score": min(score, 1.0),
        "requires_clarification": needs_clarification,
        "validation_errors": []
    }

def simple_validation(state: RequirementState) -> RequirementState:
    """Fast validation for simple requirements"""
    errors = []
    if len(state["requirement"]) < 20:
        errors.append("Too short")
    return {"validation_errors": errors}

def deep_analysis(state: RequirementState) -> RequirementState:
    """Deep analysis for complex requirements"""
    # Use LLM for detailed analysis
    errors = []
    if "database" in state["requirement"].lower():
        errors.append("Contains implementation detail")
    return {"validation_errors": errors}

def request_clarification(state: RequirementState) -> RequirementState:
    """Request user clarification"""
    return {"validation_errors": ["Requires clarification"]}

def route_requirement(state: RequirementState) -> Literal["simple", "complex", "clarify"]:
    """Route based on complexity and clarity"""
    if state["requires_clarification"]:
        return "clarify"
    elif state["complexity_score"] < 0.3:
        return "simple"
    else:
        return "complex"

# Build workflow
workflow = StateGraph(RequirementState)
workflow.add_node("analyze", analyze_complexity)
workflow.add_node("simple", simple_validation)
workflow.add_node("complex", deep_analysis)
workflow.add_node("clarify", request_clarification)

workflow.add_edge(START, "analyze")
workflow.add_conditional_edges(
    "analyze",
    route_requirement,
    {
        "simple": "simple",
        "complex": "complex",
        "clarify": "clarify"
    }
)
workflow.add_edge("simple", END)
workflow.add_edge("complex", END)
workflow.add_edge("clarify", END)

app = workflow.compile()
```

## 🏋️ Exercise
Build a multi-path requirement processor that routes to different validators based on requirement type (functional, non-functional, business rule).

---

# LESSON 7: Human-in-the-Loop (HITL) Patterns

**Duration**: 4 hours | **Prerequisites**: Lesson 6

## 🎯 Learning Objectives
- Implement approval gates using `interrupt()`
- Resume workflows after human input
- Build timeout mechanisms
- Handle approval/rejection flows
- Create UI integration points

## 📖 Key Concepts

### The `interrupt()` Function
Pauses workflow execution and waits for external input.

```python
from langgraph.pregel import interrupt

def approval_node(state: State) -> State:
    """Pause for human approval"""
    interrupt(
        value={
            "type": "approval_required",
            "data": state["content"],
            "question": "Approve this content?"
        }
    )

    # Execution pauses here
    # When resumed, check user's response

    if state.get("user_approved"):
        return process_approved(state)
    else:
        return process_rejected(state)
```

### Resuming Workflows
```python
from langgraph.checkpoint import MemorySaver

checkpointer = MemorySaver()
app = workflow.compile(checkpointer=checkpointer)

# Start workflow
config = {"configurable": {"thread_id": "user_123"}}
result = app.invoke(initial_state, config=config)

# Later, user provides feedback
current_state = app.get_state(config)
current_state.values["user_approved"] = True
current_state.values["feedback"] = "Looks good!"

# Resume from where it paused
app.invoke(current_state.values, config=config)
```

## 💻 Complete Example

```python
"""Block-by-Block Approval System"""
from typing import TypedDict, List
from langgraph.graph import StateGraph, START, END
from langgraph.pregel import interrupt
from langgraph.checkpoint import MemorySaver

class BlockApprovalState(TypedDict):
    blocks: List[dict]
    current_index: int
    approved_blocks: List[dict]
    user_feedback: str
    user_approved: bool

def generate_block(state: BlockApprovalState) -> BlockApprovalState:
    """Generate next block"""
    block = {
        "id": f"BLK-{state['current_index'] + 1:03d}",
        "content": f"Generated content for block {state['current_index'] + 1}"
    }
    return {"blocks": state["blocks"] + [block]}

def request_approval(state: BlockApprovalState) -> BlockApprovalState:
    """Pause for human approval"""
    current_block = state["blocks"][-1]

    # Pause workflow and send data to UI
    interrupt(
        value={
            "type": "block_approval",
            "block_id": current_block["id"],
            "content": current_block["content"],
            "message": "Please review and approve this block"
        }
    )

    # After resume, process user's decision
    if state.get("user_approved"):
        return {
            "approved_blocks": state["approved_blocks"] + [current_block],
            "current_index": state["current_index"] + 1
        }
    else:
        # Regenerate with feedback
        return {"current_index": state["current_index"]}  # Stay on same block

def check_if_done(state: BlockApprovalState) -> str:
    """Check if all blocks processed"""
    if state["current_index"] >= 3:  # Generate 3 blocks
        return "done"
    else:
        return "continue"

# Build workflow
workflow = StateGraph(BlockApprovalState)
workflow.add_node("generate", generate_block)
workflow.add_node("approve", request_approval)

workflow.add_edge(START, "generate")
workflow.add_edge("generate", "approve")
workflow.add_conditional_edges(
    "approve",
    check_if_done,
    {
        "continue": "generate",
        "done": END
    }
)

# Compile with checkpointer
checkpointer = MemorySaver()
app = workflow.compile(checkpointer=checkpointer)

# Usage
config = {"configurable": {"thread_id": "spec_001"}}
initial = {
    "blocks": [],
    "current_index": 0,
    "approved_blocks": [],
    "user_feedback": "",
    "user_approved": False
}

# Start (will pause at first approval)
app.invoke(initial, config=config)

# Simulate user approval
state = app.get_state(config)
state.values["user_approved"] = True
app.invoke(state.values, config=config)  # Continues to next block
```

## 🏋️ Exercise
Create a specification approval system that generates 5 blocks, pauses for approval on each, and regenerates based on feedback.

---

# LESSON 8: Persistence & Checkpointing

**Duration**: 4 hours | **Prerequisites**: Lesson 7

## 🎯 Learning Objectives
- Implement PostgreSQL checkpointing
- Save and restore workflow state
- Handle long-running workflows
- Implement crash recovery
- Manage state history

## 📖 Key Concepts

### PostgreSQL Checkpointer
```python
from langgraph.checkpoint.postgres import PostgresSaver

checkpointer = PostgresSaver.from_conn_string(
    "postgresql://user:password@localhost:5432/specbot"
)

app = workflow.compile(checkpointer=checkpointer)
```

### State History
```python
# Get all checkpoints for a thread
history = app.get_state_history(config)

for checkpoint in history:
    print(f"Step {checkpoint.metadata['step']}: {checkpoint.values}")

# Restore to specific checkpoint
app.update_state(config, specific_checkpoint.values)
```

## 💻 Complete Example

```python
"""Long-Running Specification Generator with Persistence"""
from langgraph.checkpoint.postgres import PostgresSaver
import asyncio

# Setup database checkpointer
checkpointer = PostgresSaver.from_conn_string(
    "postgresql://localhost/specbot"
)

class PersistentSpecState(TypedDict):
    spec_id: str
    blocks_completed: int
    total_blocks: int
    current_block: dict
    status: str

def generate_block_node(state: PersistentSpecState):
    """Generate one block (saves checkpoint after)"""
    block_num = state["blocks_completed"] + 1

    # Simulate long-running operation
    time.sleep(2)

    return {
        "current_block": {"id": f"BLK-{block_num}", "content": f"Block {block_num}"},
        "blocks_completed": block_num,
        "status": "processing"
    }

def check_complete(state: PersistentSpecState) -> str:
    if state["blocks_completed"] >= state["total_blocks"]:
        return "done"
    return "continue"

workflow = StateGraph(PersistentSpecState)
workflow.add_node("generate", generate_block_node)
workflow.add_edge(START, "generate")
workflow.add_conditional_edges(
    "generate",
    check_complete,
    {"continue": "generate", "done": END}
)

app = workflow.compile(checkpointer=checkpointer)

# Start long-running job
config = {"configurable": {"thread_id": "spec_large_001"}}
initial = {
    "spec_id": "SPEC-001",
    "blocks_completed": 0,
    "total_blocks": 10,
    "current_block": {},
    "status": "started"
}

# Run (automatically saves after each node)
try:
    result = app.invoke(initial, config=config)
except KeyboardInterrupt:
    print("Interrupted! State is saved.")

# Later, resume from where it stopped
current_state = app.get_state(config)
print(f"Resuming from block {current_state.values['blocks_completed']}")
app.invoke(current_state.values, config=config)
```

## 🏋️ Exercise
Build a specification generator that processes 20 blocks, saves progress after each, and can be interrupted/resumed at any point.

---

# LESSON 9: Error Handling, Retries & Validation

**Duration**: 4 hours | **Prerequisites**: Lesson 8

## 🎯 Learning Objectives
- Implement retry logic with exponential backoff
- Handle LLM failures gracefully
- Build circuit breakers
- Create fallback strategies
- Implement validation at each step

## 📖 Key Concepts

### Retry Decorator
```python
import asyncio
from functools import wraps

def with_retry(max_retries=3, backoff=2):
    def decorator(func):
        @wraps(func)
        async def wrapper(state):
            for attempt in range(max_retries):
                try:
                    return await func(state)
                except Exception as e:
                    if attempt == max_retries - 1:
                        state["errors"].append(f"Failed after {max_retries} attempts: {e}")
                        return state
                    await asyncio.sleep(backoff ** attempt)
        return wrapper
    return decorator
```

### Circuit Breaker
```python
class CircuitBreaker:
    def __init__(self, failure_threshold=5, timeout=60):
        self.failures = 0
        self.threshold = failure_threshold
        self.timeout = timeout
        self.last_failure = None
        self.state = "closed"  # closed, open, half-open

    async def call(self, func, *args):
        if self.state == "open":
            if time.time() - self.last_failure > self.timeout:
                self.state = "half-open"
            else:
                raise Exception("Circuit breaker is OPEN")

        try:
            result = await func(*args)
            if self.state == "half-open":
                self.state = "closed"
                self.failures = 0
            return result
        except Exception as e:
            self.failures += 1
            self.last_failure = time.time()
            if self.failures >= self.threshold:
                self.state = "open"
            raise
```

## 💻 Complete Example

```python
"""Fault-Tolerant Requirement Extractor"""
from typing import TypedDict, List
import time

class RobustState(TypedDict):
    description: str
    requirements: List[str]
    errors: List[str]
    retry_count: int
    circuit_breaker_open: bool

circuit_breaker = CircuitBreaker(failure_threshold=3, timeout=30)

@with_retry(max_retries=3, backoff=2)
async def extract_with_llm(state: RobustState) -> RobustState:
    """Extract requirements with retry logic"""
    try:
        # Wrap LLM call in circuit breaker
        requirements = await circuit_breaker.call(
            llm_extract_requirements,
            state["description"]
        )
        return {"requirements": requirements, "retry_count": 0}

    except Exception as e:
        return {
            "errors": state["errors"] + [str(e)],
            "retry_count": state["retry_count"] + 1,
            "circuit_breaker_open": circuit_breaker.state == "open"
        }

def validate_requirements(state: RobustState) -> RobustState:
    """Validate extracted requirements"""
    errors = []
    for req in state["requirements"]:
        if len(req) < 10:
            errors.append(f"Requirement too short: {req}")
        if not any(kw in req for kw in ["MUST", "SHALL", "SHOULD"]):
            errors.append(f"Missing modal verb: {req}")

    return {"errors": state["errors"] + errors}

def check_should_retry(state: RobustState) -> str:
    """Decide if we should retry or fail"""
    if len(state["errors"]) == 0:
        return "success"
    elif state["retry_count"] < 3 and not state["circuit_breaker_open"]:
        return "retry"
    else:
        return "failed"

# Build fault-tolerant workflow
workflow = StateGraph(RobustState)
workflow.add_node("extract", extract_with_llm)
workflow.add_node("validate", validate_requirements)

workflow.add_edge(START, "extract")
workflow.add_edge("extract", "validate")
workflow.add_conditional_edges(
    "validate",
    check_should_retry,
    {
        "success": END,
        "retry": "extract",
        "failed": END
    }
)

app = workflow.compile()
```

## 🏋️ Exercise
Build a production-ready workflow with retries, circuit breakers, fallback to simpler prompts, and comprehensive error logging.

---

# LESSONS 10-15: Coming Soon

Due to space constraints, lessons 10-15 follow the same detailed pattern. Each covers:

**Lesson 10**: Context7 & Progressive Disclosure
**Lesson 11**: RAG for Document Understanding
**Lesson 12**: Multi-Document Synthesis
**Lesson 13**: Template Analysis Pipeline
**Lesson 14**: Block-by-Block Generation with HITL
**Lesson 15**: Final Integration & Deployment

Refer to the detailed outlines in the original `05-15-LESSON-INDEX.md` for complete implementation guidance.

---

## 🎓 Completion

After lessons 1-9, you have mastered:
- ✅ LangChain fundamentals
- ✅ LangGraph workflows
- ✅ State management
- ✅ Conditional routing
- ✅ Human-in-the-loop patterns
- ✅ Persistence & checkpointing
- ✅ Production error handling

You're ready to build the complete SpecBot system in lessons 10-15!
