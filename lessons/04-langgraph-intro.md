# Lesson 4: Introduction to LangGraph & Simple Workflows

> **Story Context**: SpecBot can extract requirements, but the real power comes from multi-step workflows: extract → validate → clarify → approve. Simple chains aren't enough. This lesson introduces LangGraph, a framework for building stateful, graph-based workflows that can handle complex business logic.

---

## 🎯 Learning Objectives

By the end of this lesson, you will:

1. Understand what LangGraph is and when to use it
2. Build your first state graph
3. Define nodes (processing steps) and edges (transitions)
4. Manage state across workflow steps
5. Create branching logic with conditional edges
6. Debug and visualize workflows

**Time**: ~3 hours

---

## 📖 Concept: What is LangGraph?

### The Problem with Simple Chains

**LangChain chains** are great for linear workflows:
```python
chain = prompt | llm | parser
```

But they struggle with:
- ❌ Conditional logic (if/else branching)
- ❌ Loops and iteration
- ❌ State that persists across steps
- ❌ Human-in-the-loop approvals
- ❌ Error recovery and retries
- ❌ Complex branching workflows

### Enter LangGraph

**LangGraph** is built for:
- ✅ **Stateful workflows**: Data persists between steps
- ✅ **Conditional routing**: Dynamic paths based on state
- ✅ **Cycles and loops**: Iterate until condition met
- ✅ **Human-in-the-loop**: Pause for approval, resume later
- ✅ **Checkpointing**: Save/resume workflows
- ✅ **Parallel execution**: Multiple nodes run concurrently

### Core Architecture

```
┌─────────────────────────────────────────┐
│            STATE GRAPH                  │
│                                         │
│   ┌──────┐      ┌──────┐      ┌─────┐ │
│   │Node 1│─────▶│Node 2│─────▶│ END │ │
│   └──────┘      └──────┘      └─────┘ │
│                    │                   │
│                    ▼                   │
│                 ┌──────┐               │
│                 │Node 3│               │
│                 └──────┘               │
│                                         │
│  State: {...shared data...}            │
└─────────────────────────────────────────┘
```

**Key Concepts**:
1. **Nodes**: Processing functions that transform state
2. **Edges**: Transitions between nodes
3. **State**: Shared data structure (TypedDict)
4. **START/END**: Special nodes marking workflow boundaries

---

## 🏗️ Setup: Install LangGraph

```bash
pip install langgraph
```

Verify installation:
```python
import langgraph
print(f"LangGraph version: {langgraph.__version__}")
```

---

## 💡 Code Examples

### Example 1: Your First State Graph

```python
"""
src/examples/ex14_first_graph.py

Simplest possible LangGraph workflow
"""

from typing import TypedDict
from langgraph.graph import StateGraph, START, END

# Step 1: Define state structure
class SimpleState(TypedDict):
    """State shared across all nodes"""
    message: str
    count: int

# Step 2: Define node functions
def node_a(state: SimpleState) -> SimpleState:
    """First processing step"""
    print(f"Node A: Received message='{state['message']}'")
    return {
        "message": state["message"] + " (processed by A)",
        "count": state["count"] + 1
    }

def node_b(state: SimpleState) -> SimpleState:
    """Second processing step"""
    print(f"Node B: Received message='{state['message']}'")
    return {
        "message": state["message"] + " (processed by B)",
        "count": state["count"] + 1
    }

# Step 3: Build graph
workflow = StateGraph(SimpleState)

# Add nodes
workflow.add_node("node_a", node_a)
workflow.add_node("node_b", node_b)

# Define edges (transitions)
workflow.add_edge(START, "node_a")  # START → node_a
workflow.add_edge("node_a", "node_b")  # node_a → node_b
workflow.add_edge("node_b", END)  # node_b → END

# Compile graph
app = workflow.compile()

# Execute
initial_state = {"message": "Hello", "count": 0}
result = app.invoke(initial_state)

print(f"\nFinal result: {result}")
# Output: {'message': 'Hello (processed by A) (processed by B)', 'count': 2}
```

### Example 2: SpecBot - Simple Requirement Workflow

```python
"""
src/examples/ex15_requirement_workflow.py

SpecBot workflow: Extract → Validate → Format
"""

from typing import TypedDict, List
from langgraph.graph import StateGraph, START, END
from langchain_anthropic import ChatAnthropic
from langchain.prompts import ChatPromptTemplate
from dotenv import load_dotenv

load_dotenv()

# State definition
class RequirementState(TypedDict):
    description: str  # Input: user's feature description
    raw_requirements: str  # Output from extraction
    validated_requirements: List[str]  # Output from validation
    formatted_output: str  # Final output

# Node 1: Extract requirements using LLM
def extract_requirements(state: RequirementState) -> RequirementState:
    """Extract requirements from description"""
    print("🔍 Extracting requirements...")

    llm = ChatAnthropic(model="claude-3-5-sonnet-20241022", temperature=0)
    prompt = ChatPromptTemplate.from_messages([
        ("system", "Extract 3-5 functional requirements. One per line."),
        ("user", "{description}")
    ])

    chain = prompt | llm
    response = chain.invoke({"description": state["description"]})

    return {
        "description": state["description"],
        "raw_requirements": response.content,
        "validated_requirements": [],
        "formatted_output": ""
    }

# Node 2: Validate requirements
def validate_requirements(state: RequirementState) -> RequirementState:
    """Ensure requirements are testable and specific"""
    print("✅ Validating requirements...")

    # Simple validation: check length and keywords
    requirements = state["raw_requirements"].split("\n")
    validated = []

    for req in requirements:
        req = req.strip()
        if len(req) > 20 and any(kw in req for kw in ["MUST", "SHALL", "SHOULD"]):
            validated.append(req)

    print(f"   Validated {len(validated)}/{len(requirements)} requirements")

    return {
        "description": state["description"],
        "raw_requirements": state["raw_requirements"],
        "validated_requirements": validated,
        "formatted_output": ""
    }

# Node 3: Format output
def format_output(state: RequirementState) -> RequirementState:
    """Format requirements as FR-XXX list"""
    print("📝 Formatting output...")

    formatted = []
    for i, req in enumerate(state["validated_requirements"], 1):
        formatted.append(f"FR-{i:03d}: {req}")

    output = "\n".join(formatted)

    return {
        "description": state["description"],
        "raw_requirements": state["raw_requirements"],
        "validated_requirements": state["validated_requirements"],
        "formatted_output": output
    }

# Build workflow
workflow = StateGraph(RequirementState)

workflow.add_node("extract", extract_requirements)
workflow.add_node("validate", validate_requirements)
workflow.add_node("format", format_output)

workflow.add_edge(START, "extract")
workflow.add_edge("extract", "validate")
workflow.add_edge("validate", "format")
workflow.add_edge("format", END)

app = workflow.compile()

# Test
initial_state = {
    "description": "Build a login system with email authentication and password reset",
    "raw_requirements": "",
    "validated_requirements": [],
    "formatted_output": ""
}

result = app.invoke(initial_state)

print("\n" + "="*70)
print("FINAL OUTPUT")
print("="*70)
print(result["formatted_output"])
```

### Example 3: Conditional Routing

```python
"""
src/examples/ex16_conditional_routing.py

Branching based on state conditions
"""

from typing import TypedDict, Literal
from langgraph.graph import StateGraph, START, END

class ValidationState(TypedDict):
    text: str
    is_valid: bool
    error_message: str

def validate_input(state: ValidationState) -> ValidationState:
    """Check if input is valid"""
    text = state["text"]
    is_valid = len(text) > 10 and not any(char.isdigit() for char in text)

    return {
        "text": text,
        "is_valid": is_valid,
        "error_message": "" if is_valid else "Input too short or contains numbers"
    }

def process_valid_input(state: ValidationState) -> ValidationState:
    """Process valid input"""
    print(f"✓ Processing: {state['text']}")
    return state

def handle_invalid_input(state: ValidationState) -> ValidationState:
    """Handle invalid input"""
    print(f"✗ Error: {state['error_message']}")
    return state

# Routing function
def route_after_validation(state: ValidationState) -> Literal["process", "handle_error"]:
    """Decide next node based on validation result"""
    if state["is_valid"]:
        return "process"
    else:
        return "handle_error"

# Build graph with conditional edge
workflow = StateGraph(ValidationState)

workflow.add_node("validate", validate_input)
workflow.add_node("process", process_valid_input)
workflow.add_node("handle_error", handle_invalid_input)

workflow.add_edge(START, "validate")

# Conditional edge: route based on state
workflow.add_conditional_edges(
    "validate",  # From this node
    route_after_validation,  # Use this function to decide
    {
        "process": "process",  # If returns "process", go to process node
        "handle_error": "handle_error"  # If returns "handle_error", go there
    }
)

workflow.add_edge("process", END)
workflow.add_edge("handle_error", END)

app = workflow.compile()

# Test cases
test_cases = [
    {"text": "This is a valid input without numbers", "is_valid": False, "error_message": ""},
    {"text": "Short", "is_valid": False, "error_message": ""},
    {"text": "This has numbers 123", "is_valid": False, "error_message": ""}
]

for test in test_cases:
    print(f"\nTesting: '{test['text']}'")
    result = app.invoke(test)
```

### Example 4: Loops and Iteration

```python
"""
src/examples/ex17_loops.py

Iterative workflow with loops
"""

from typing import TypedDict
from langgraph.graph import StateGraph, START, END

class IterativeState(TypedDict):
    current_value: int
    max_value: int
    iteration: int

def increment(state: IterativeState) -> IterativeState:
    """Increment value"""
    new_value = state["current_value"] + 1
    print(f"Iteration {state['iteration']}: {state['current_value']} → {new_value}")

    return {
        "current_value": new_value,
        "max_value": state["max_value"],
        "iteration": state["iteration"] + 1
    }

def check_condition(state: IterativeState) -> str:
    """Check if we should continue or stop"""
    if state["current_value"] >= state["max_value"]:
        return "done"
    else:
        return "continue"

# Build graph with loop
workflow = StateGraph(IterativeState)

workflow.add_node("increment", increment)

workflow.add_edge(START, "increment")

# Conditional edge that loops back
workflow.add_conditional_edges(
    "increment",
    check_condition,
    {
        "continue": "increment",  # Loop back to same node
        "done": END  # Exit workflow
    }
)

app = workflow.compile()

# Test: count from 0 to 5
result = app.invoke({
    "current_value": 0,
    "max_value": 5,
    "iteration": 1
})

print(f"\nFinal result: {result}")
```

---

## 🏋️ Hands-On Exercise: Build SpecBot's Validation Workflow

**Objective**: Create a workflow that extracts requirements, validates them, and iterates until all pass validation.

### Requirements

Build a workflow with these nodes:
1. **Extract**: Get requirements from LLM
2. **Validate**: Check quality (testable, specific, no tech details)
3. **Route**: If validation fails, fix and retry. If passes, format output.
4. **Fix**: Ask LLM to fix invalid requirements
5. **Format**: Create final FR-XXX output

### State Structure

```python
from typing import TypedDict, List

class RequirementWorkflowState(TypedDict):
    description: str
    requirements: List[str]
    validation_errors: List[str]
    iteration: int
    max_iterations: int
    formatted_output: str
```

### Workflow Graph

```
START → Extract → Validate → Route ──[valid]──→ Format → END
                                │
                                └─[invalid]──→ Fix ──┘
                                               (loop back)
```

### Starter Code

Create `src/exercises/ex04_validation_workflow.py`:

```python
"""
Exercise 4: Requirement Validation Workflow

Build an iterative workflow with validation and fixing
"""

from typing import TypedDict, List, Literal
from langgraph.graph import StateGraph, START, END
from langchain_anthropic import ChatAnthropic
from langchain.prompts import ChatPromptTemplate
from dotenv import load_dotenv

load_dotenv()

# TODO: Define state
class RequirementWorkflowState(TypedDict):
    pass  # Complete this

# TODO: Define nodes

def extract_requirements(state: RequirementWorkflowState) -> RequirementWorkflowState:
    """Extract requirements using LLM"""
    # TODO: Implement
    pass

def validate_requirements(state: RequirementWorkflowState) -> RequirementWorkflowState:
    """Validate requirements against quality rules"""
    # TODO: Check for:
    # - Testable (contains SHALL/MUST/SHOULD)
    # - Specific (length > 20 chars)
    # - No tech details (no "database", "API", etc.)
    pass

def fix_requirements(state: RequirementWorkflowState) -> RequirementWorkflowState:
    """Ask LLM to fix invalid requirements"""
    # TODO: Implement
    pass

def format_output(state: RequirementWorkflowState) -> RequirementWorkflowState:
    """Format as FR-XXX list"""
    # TODO: Implement
    pass

# TODO: Routing function
def route_after_validation(state: RequirementWorkflowState) -> Literal["fix", "format"]:
    """Decide whether to fix or format"""
    # If validation_errors exist and iterations < max: "fix"
    # Otherwise: "format"
    pass

# TODO: Build workflow

# TODO: Test with multiple inputs
```

---

## 🚀 Challenge: Parallel Processing

**Advanced**: Modify the workflow to process multiple features in parallel.

**Concept**: Use LangGraph's parallel execution to analyze multiple requirements simultaneously.

```python
from langgraph.graph import StateGraph

def process_feature_parallel(features: List[str]) -> List[dict]:
    """Process multiple features in parallel"""
    # TODO: Create subgraph for each feature
    # TODO: Execute all subgraphs in parallel
    # TODO: Collect and return results
    pass
```

---

## 🎓 Key Takeaways

### When to Use LangGraph

**Use LangGraph when you need**:
- Conditional branching (if/else logic)
- Loops and iteration
- State that persists across steps
- Human-in-the-loop workflows
- Complex business logic
- Error handling and retries

**Use simple chains when**:
- Linear, single-path workflow
- No state management needed
- No branching or loops
- Stateless transformations

### LangGraph Best Practices

✅ **DO**:
- Keep state structure simple and flat
- Use TypedDict for type safety
- Make nodes pure functions (input state → output state)
- Use descriptive node names
- Visualize complex graphs
- Test individual nodes before connecting

❌ **DON'T**:
- Mutate state directly (return new state)
- Create deeply nested state structures
- Add business logic to routing functions
- Create circular dependencies without exit conditions
- Skip node name validation

---

## 🔄 Story Progress: SpecBot v0.4

**What we built**: SpecBot now has a proper workflow with validation and iteration!

```python
# SpecBot v0.4 - Workflow Architecture
from specbot import RequirementWorkflow

workflow = RequirementWorkflow()
result = workflow.process("Build a login system")

# Workflow automatically:
# 1. Extracts requirements
# 2. Validates quality
# 3. Fixes invalid requirements (iterates if needed)
# 4. Formats output
```

**Next Step**: Lesson 5 will dive deeper into state management and data flow patterns.

---

## 📚 Additional Resources

- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [LangGraph How-To Guides](https://langchain-ai.github.io/langgraph/how-tos/)
- [State Management Patterns](https://langchain-ai.github.io/langgraph/concepts/#state)

---

**Continue to [Lesson 5: State Management & Data Flow →](./05-state-management.md)**
