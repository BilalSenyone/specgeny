# Lesson 5: State Management & Data Flow

> **Story Context**: SpecBot workflows are getting complex. We need to manage requirements, validation errors, user feedback, and metadata across multiple steps. This lesson teaches you advanced state management patterns to build robust, maintainable workflows.

---

## 🎯 Learning Objectives

By the end of this lesson, you will:

1. Master state update strategies (replace, merge, append)
2. Use Annotated types for automatic state reduction
3. Implement state channels for parallel data streams
4. Handle nested state structures efficiently
5. Design data flow patterns (fan-out, fan-in, pipeline)
6. Manage state versions and history

**Time**: ~3 hours

---

## 📖 Concept: State Update Strategies

### The Problem: How Should State Update?

When a node returns new state, how should it merge with existing state?

**Example scenario**:
```python
# Current state
state = {"requirements": ["FR-001"], "count": 1}

# Node returns
return {"requirements": ["FR-002"], "count": 2}

# What should final state be?
# Option 1: Replace everything → {"requirements": ["FR-002"], "count": 2}
# Option 2: Append lists → {"requirements": ["FR-001", "FR-002"], "count": 2}
# Option 3: Merge dicts → depends on field
```

### LangGraph's Solution: Annotated Types

Use `Annotated[Type, reducer_function]` to specify how each field updates.

---

## 💡 Core Patterns

### Pattern 1: Replace (Default)

**Use when**: You want to overwrite the previous value.

```python
from typing import TypedDict

class SimpleState(TypedDict):
    current_step: str  # Default: replace
    iteration: int     # Default: replace

def node(state):
    return {"current_step": "validation"}  # Replaces previous value
```

### Pattern 2: Append (Lists)

**Use when**: You want to accumulate values over time.

```python
from typing import TypedDict, Annotated, List
import operator

class AppendState(TypedDict):
    messages: Annotated[List[str], operator.add]  # Appends to list
    errors: Annotated[List[str], operator.add]     # Appends to list

def node(state):
    return {"messages": ["New message"]}  # Appends to existing messages
```

**How it works**:
```python
# Initial state
{"messages": ["Hello"], "errors": []}

# Node returns
{"messages": ["World"]}

# Final state (operator.add applied)
{"messages": ["Hello", "World"], "errors": []}
```

### Pattern 3: Merge (Dictionaries)

**Use when**: You want to merge dictionary values.

```python
from typing import TypedDict, Annotated, Dict

def merge_dicts(existing: dict, new: dict) -> dict:
    """Merge two dictionaries"""
    return {**existing, **new}

class MergeState(TypedDict):
    metadata: Annotated[Dict, merge_dicts]

def node(state):
    return {"metadata": {"author": "Alice"}}  # Merges with existing metadata
```

### Pattern 4: Custom Reducers

**Use when**: You need custom merge logic.

```python
from typing import List
from pydantic import BaseModel

class Requirement(BaseModel):
    id: str
    description: str
    priority: str

def merge_requirements(
    existing: List[Requirement],
    new: List[Requirement]
) -> List[Requirement]:
    """Merge requirements, avoiding duplicates by ID"""
    existing_ids = {req.id for req in existing}
    merged = existing.copy()

    for req in new:
        if req.id not in existing_ids:
            merged.append(req)
        else:
            # Update existing requirement
            index = next(i for i, r in enumerate(merged) if r.id == req.id)
            merged[index] = req

    return merged

class RequirementState(TypedDict):
    requirements: Annotated[List[Requirement], merge_requirements]
```

---

## 🔧 Code Examples

### Example 1: Message History with Append

```python
"""
src/examples/ex18_append_state.py

Building conversation history with append strategy
"""

from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, START, END
import operator

class ConversationState(TypedDict):
    messages: Annotated[List[str], operator.add]
    user_input: str

def user_message_node(state: ConversationState) -> ConversationState:
    """Add user message to history"""
    return {
        "messages": [f"User: {state['user_input']}"],
        "user_input": state["user_input"]
    }

def ai_response_node(state: ConversationState) -> ConversationState:
    """Generate and add AI response"""
    last_user_message = state["messages"][-1]
    response = f"AI: I understand you said '{last_user_message}'"

    return {"messages": [response]}

# Build workflow
workflow = StateGraph(ConversationState)
workflow.add_node("user", user_message_node)
workflow.add_node("ai", ai_response_node)

workflow.add_edge(START, "user")
workflow.add_edge("user", "ai")
workflow.add_edge("ai", END)

app = workflow.compile()

# Test multiple turns
result = app.invoke({"messages": [], "user_input": "Hello"})
print("After turn 1:", result["messages"])

result = app.invoke({"messages": result["messages"], "user_input": "How are you?"})
print("After turn 2:", result["messages"])
```

### Example 2: Requirement Accumulation with Custom Reducer

```python
"""
src/examples/ex19_custom_reducer.py

Merging requirements without duplicates
"""

from typing import TypedDict, Annotated, List
from pydantic import BaseModel
from langgraph.graph import StateGraph, START, END

class Requirement(BaseModel):
    id: str
    description: str
    priority: str

def merge_requirements(
    existing: List[Requirement],
    new: List[Requirement]
) -> List[Requirement]:
    """Custom merge: update existing or append new"""
    result = {req.id: req for req in existing}  # Use dict for O(1) lookup

    for req in new:
        result[req.id] = req  # Overwrite or add

    return list(result.values())

class RequirementState(TypedDict):
    requirements: Annotated[List[Requirement], merge_requirements]
    source: str

def extract_from_description(state: RequirementState) -> RequirementState:
    """Extract requirements from description"""
    return {
        "requirements": [
            Requirement(id="FR-001", description="User login", priority="P1"),
            Requirement(id="FR-002", description="Password reset", priority="P2")
        ]
    }

def extract_from_examples(state: RequirementState) -> RequirementState:
    """Extract from examples (might overlap)"""
    return {
        "requirements": [
            Requirement(id="FR-001", description="User login (updated)", priority="P1"),  # Update
            Requirement(id="FR-003", description="Account lockout", priority="P1")  # New
        ]
    }

# Build workflow
workflow = StateGraph(RequirementState)
workflow.add_node("from_description", extract_from_description)
workflow.add_node("from_examples", extract_from_examples)

workflow.add_edge(START, "from_description")
workflow.add_edge("from_description", "from_examples")
workflow.add_edge("from_examples", END)

app = workflow.compile()

result = app.invoke({"requirements": [], "source": "test"})

print("Final requirements:")
for req in result["requirements"]:
    print(f"  {req.id}: {req.description} [{req.priority}]")
```

### Example 3: Nested State Structures

```python
"""
src/examples/ex20_nested_state.py

Managing complex nested state
"""

from typing import TypedDict, Annotated, List, Dict
from langgraph.graph import StateGraph, START, END

class ValidationResult(TypedDict):
    is_valid: bool
    errors: List[str]

class BlockState(TypedDict):
    content: str
    validation: ValidationResult
    approved: bool

class SpecificationState(TypedDict):
    spec_id: str
    blocks: Annotated[List[BlockState], lambda x, y: x + y]
    metadata: Annotated[Dict, lambda x, y: {**x, **y}]

def generate_block(state: SpecificationState) -> SpecificationState:
    """Generate a new block"""
    new_block: BlockState = {
        "content": "This is a requirement block",
        "validation": {"is_valid": False, "errors": []},
        "approved": False
    }

    return {"blocks": [new_block]}

def validate_block(state: SpecificationState) -> SpecificationState:
    """Validate the last block"""
    last_block = state["blocks"][-1]

    # Simple validation
    is_valid = len(last_block["content"]) > 10

    # Update last block (need to return full blocks list)
    updated_blocks = state["blocks"][:-1] + [{
        **last_block,
        "validation": {
            "is_valid": is_valid,
            "errors": [] if is_valid else ["Content too short"]
        }
    }]

    # Use replace strategy for blocks when updating
    return {
        "blocks": updated_blocks,
        "metadata": {"last_validation": "completed"}
    }

# Build workflow
workflow = StateGraph(SpecificationState)
workflow.add_node("generate", generate_block)
workflow.add_node("validate", validate_block)

workflow.add_edge(START, "generate")
workflow.add_edge("generate", "validate")
workflow.add_edge("validate", END)

app = workflow.compile()

result = app.invoke({
    "spec_id": "SPEC-001",
    "blocks": [],
    "metadata": {"created": "2024-01-01"}
})

print("Blocks:", result["blocks"])
print("Metadata:", result["metadata"])
```

---

## 📊 Data Flow Patterns

### Pattern 1: Fan-Out (Parallel Processing)

**Use case**: Process multiple items in parallel.

```python
"""
src/examples/ex21_fan_out.py

Parallel requirement extraction
"""

from typing import TypedDict, List
from langgraph.graph import StateGraph, START, END

class FanOutState(TypedDict):
    features: List[str]
    results: List[dict]

def process_feature_1(state: FanOutState) -> FanOutState:
    """Process first feature"""
    feature = state["features"][0]
    return {"results": [{"feature": feature, "requirements": ["FR-001", "FR-002"]}]}

def process_feature_2(state: FanOutState) -> FanOutState:
    """Process second feature"""
    feature = state["features"][1]
    return {"results": [{"feature": feature, "requirements": ["FR-003"]}]}

# These nodes run in parallel
# (LangGraph detects no dependencies and executes concurrently)
```

### Pattern 2: Fan-In (Aggregation)

**Use case**: Combine results from parallel processing.

```python
def aggregate_results(state: FanOutState) -> FanOutState:
    """Combine all results"""
    all_requirements = []
    for result in state["results"]:
        all_requirements.extend(result["requirements"])

    return {
        "results": [{
            "summary": f"Total requirements: {len(all_requirements)}",
            "all_requirements": all_requirements
        }]
    }
```

### Pattern 3: Pipeline (Sequential Transformation)

**Use case**: Chain of transformations.

```python
def extract(state) -> state:
    """Extract raw requirements"""
    pass

def validate(state) -> state:
    """Validate extracted requirements"""
    pass

def format(state) -> state:
    """Format validated requirements"""
    pass

# Pipeline: extract → validate → format
```

---

## 🏋️ Hands-On Exercise: Multi-Feature Processor

**Objective**: Build a workflow that processes multiple features in parallel with proper state management.

### Requirements

Create a system that:
1. Accepts list of feature descriptions
2. Processes each feature in parallel (extract requirements)
3. Validates each feature's requirements independently
4. Aggregates all results into final specification
5. Tracks progress and errors per feature

### State Design

```python
from typing import TypedDict, Annotated, List, Dict
import operator

class FeatureResult(TypedDict):
    feature_name: str
    requirements: List[str]
    validation_errors: List[str]
    status: str  # "pending", "processing", "completed", "failed"

class MultiFeatureState(TypedDict):
    features: List[str]  # Input feature descriptions
    results: Annotated[List[FeatureResult], operator.add]
    current_feature_index: int
    total_requirements: int
    errors: Annotated[List[str], operator.add]
```

### Starter Code

Create `src/exercises/ex05_multi_feature.py`:

```python
"""
Exercise 5: Multi-Feature Processor

Build a workflow that processes multiple features in parallel
"""

from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, START, END
import operator

# TODO: Define state

# TODO: Create nodes for:
# 1. Initialize - prepare feature processing
# 2. Extract - extract requirements for one feature
# 3. Validate - validate one feature's requirements
# 4. Aggregate - combine all results

# TODO: Build workflow with proper state management

# Test with multiple features
test_features = [
    "User authentication with email and password",
    "Task management with assignment and due dates",
    "File upload with drag-and-drop support"
]
```

### Expected Output

```
Processing 3 features...

Feature 1: User authentication
  Requirements: FR-001, FR-002, FR-003
  Status: ✓ Completed

Feature 2: Task management
  Requirements: FR-004, FR-005, FR-006, FR-007
  Status: ✓ Completed

Feature 3: File upload
  Requirements: FR-008, FR-009
  Status: ✓ Completed

Summary:
  Total features: 3
  Total requirements: 9
  Errors: 0
```

---

## 🚀 Challenge: State Versioning System

**Advanced**: Implement a state versioning system that tracks all state changes.

### Challenge Requirements

Build a workflow that:
1. Saves state snapshot after each node
2. Allows rollback to any previous version
3. Shows diff between versions
4. Implements branching (try different paths from same state)

### Template

```python
"""
src/exercises/ex05_state_versioning.py

Advanced state versioning and time travel
"""

from typing import TypedDict, List
import copy
from datetime import datetime

class VersionedState(TypedDict):
    data: dict
    version: int
    history: List[dict]  # List of all previous states

class StateVersionManager:
    """Manage state versions"""

    def __init__(self):
        self.versions = []

    def save_version(self, state: dict, node_name: str):
        """Save current state as new version"""
        version = {
            "version_id": len(self.versions) + 1,
            "timestamp": datetime.now(),
            "node": node_name,
            "state": copy.deepcopy(state)
        }
        self.versions.append(version)

    def get_version(self, version_id: int) -> dict:
        """Retrieve specific version"""
        return self.versions[version_id - 1]["state"]

    def rollback(self, version_id: int) -> dict:
        """Rollback to specific version"""
        return copy.deepcopy(self.get_version(version_id))

    def diff(self, version_a: int, version_b: int) -> dict:
        """Show differences between versions"""
        # TODO: Implement diff logic
        pass

# TODO: Integrate with LangGraph workflow
# TODO: Add versioning to each node
```

---

## 🎓 Key Takeaways

### State Update Strategies

| Strategy | Annotation | Use Case |
|----------|------------|----------|
| Replace | No annotation | Simple values that change |
| Append | `Annotated[List, operator.add]` | Accumulating lists |
| Merge | `Annotated[Dict, merge_func]` | Combining dictionaries |
| Custom | `Annotated[Type, custom_func]` | Complex merge logic |

### Best Practices

✅ **DO**:
- Use Annotated types for clarity
- Keep state flat when possible
- Document reducer functions
- Test reducers independently
- Use immutable operations

❌ **DON'T**:
- Mutate state directly
- Create deeply nested state
- Use complex reducer logic
- Forget to handle None values
- Mix update strategies without clear reason

---

## 🔄 Story Progress: SpecBot v0.5

**What we built**: SpecBot now properly manages complex state across workflows!

```python
# SpecBot v0.5 - Advanced State Management
class SpecBotState(TypedDict):
    # Append strategy for accumulation
    requirements: Annotated[List[Requirement], merge_requirements]
    errors: Annotated[List[str], operator.add]
    messages: Annotated[List[str], operator.add]

    # Merge strategy for metadata
    metadata: Annotated[Dict, lambda x, y: {**x, **y}]

    # Replace strategy for current values
    current_block: str
    iteration: int

# State updates correctly across complex workflows!
```

**Next Step**: Lesson 6 will teach conditional routing based on state values, enabling smart workflows that adapt to different scenarios.

---

## 📚 Additional Resources

- [LangGraph State Documentation](https://langchain-ai.github.io/langgraph/concepts/#state)
- [Python operator Module](https://docs.python.org/3/library/operator.html)
- [Pydantic Models](https://docs.pydantic.dev/)

---

**Continue to [Lesson 6: Conditional Edges & Routing Logic →](./06-conditional-routing.md)**
