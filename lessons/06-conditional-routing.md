# Lesson 6: Conditional Edges & Routing Logic

> **Story Context**: SpecBot needs to make smart decisions - simple requirements go through fast validation, complex ones need deep analysis, and ambiguous ones need clarification. This lesson teaches you to build intelligent routing logic that adapts to different scenarios.

---

## 🎯 Learning Objectives

By the end of this lesson, you will:

1. Implement routing functions that return node names
2. Use conditional edges with multiple branches
3. Create LLM-based routing decisions
4. Build routing tables for complex workflows
5. Handle routing errors and edge cases

**Time**: ~3 hours

---

## 📖 Key Concepts

### Routing Function Pattern

A routing function examines state and returns the name of the next node:

```python
from typing import Literal

def my_router(state: MyState) -> Literal["path_a", "path_b", "path_c"]:
    """Decide which node to execute next"""
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
    "source_node",       # From this node
    my_router,           # Use this function to decide
    {
        "path_a": "node_a",   # Map return value to node
        "path_b": "node_b",
        "path_c": "node_c"
    }
)
```

---

## 💻 Code Examples

### Example 1: Simple Binary Routing

```python
"""
src/examples/ex22_binary_routing.py

Basic yes/no routing decision
"""

from typing import TypedDict, Literal
from langgraph.graph import StateGraph, START, END

class ValidationState(TypedDict):
    text: str
    is_valid: bool
    processed_text: str

def validate(state: ValidationState) -> ValidationState:
    """Check if text is valid"""
    is_valid = len(state["text"]) > 10
    return {"text": state["text"], "is_valid": is_valid, "processed_text": ""}

def process_valid(state: ValidationState) -> ValidationState:
    """Process valid text"""
    return {"processed_text": f"PROCESSED: {state['text'].upper()}"}

def reject_invalid(state: ValidationState) -> ValidationState:
    """Reject invalid text"""
    return {"processed_text": f"REJECTED: {state['text']} (too short)"}

def route_after_validation(state: ValidationState) -> Literal["process", "reject"]:
    """Route based on validation result"""
    return "process" if state["is_valid"] else "reject"

# Build workflow
workflow = StateGraph(ValidationState)
workflow.add_node("validate", validate)
workflow.add_node("process", process_valid)
workflow.add_node("reject", reject_invalid)

workflow.add_edge(START, "validate")
workflow.add_conditional_edges(
    "validate",
    route_after_validation,
    {
        "process": "process",
        "reject": "reject"
    }
)
workflow.add_edge("process", END)
workflow.add_edge("reject", END)

app = workflow.compile()

# Test
print(app.invoke({"text": "This is long enough", "is_valid": False, "processed_text": ""}))
print(app.invoke({"text": "Short", "is_valid": False, "processed_text": ""}))
```

### Example 2: Multi-Way Routing

```python
"""
src/examples/ex23_multiway_routing.py

Route requirements to different validators based on complexity
"""

from typing import TypedDict, Literal, List
from langgraph.graph import StateGraph, START, END

class RequirementState(TypedDict):
    requirement: str
    complexity: float
    needs_clarification: bool
    validation_result: str

def analyze_requirement(state: RequirementState) -> RequirementState:
    """Analyze requirement to determine routing"""
    req = state["requirement"]

    # Calculate complexity score
    complexity = len(req.split()) / 50.0  # Words / 50

    # Check for clarification markers
    needs_clarification = any(marker in req.lower() for marker in ["tbd", "unclear", "???"])

    return {
        "requirement": req,
        "complexity": min(complexity, 1.0),
        "needs_clarification": needs_clarification,
        "validation_result": ""
    }

def simple_validation(state: RequirementState) -> RequirementState:
    """Fast validation for simple requirements"""
    result = "✓ Simple validation passed"
    if len(state["requirement"]) < 20:
        result = "✗ Requirement too short"
    return {"validation_result": result}

def complex_validation(state: RequirementState) -> RequirementState:
    """Deep validation for complex requirements"""
    result = "✓ Complex validation passed"

    # Check for implementation details
    tech_terms = ["database", "api", "react", "aws"]
    if any(term in state["requirement"].lower() for term in tech_terms):
        result = "✗ Contains implementation details"

    return {"validation_result": result}

def request_clarification(state: RequirementState) -> RequirementState:
    """Flag for user clarification"""
    return {"validation_result": "⚠ Requires user clarification"}

def route_requirement(state: RequirementState) -> Literal["simple", "complex", "clarify"]:
    """Route based on complexity and clarity"""
    if state["needs_clarification"]:
        return "clarify"
    elif state["complexity"] < 0.3:
        return "simple"
    else:
        return "complex"

# Build workflow
workflow = StateGraph(RequirementState)
workflow.add_node("analyze", analyze_requirement)
workflow.add_node("simple", simple_validation)
workflow.add_node("complex", complex_validation)
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

# Test different requirements
test_cases = [
    "User can login",  # Simple
    "System SHALL authenticate users using email and password credentials with rate limiting and account lockout after failed attempts",  # Complex
    "User can do something TBD with the system"  # Needs clarification
]

for req in test_cases:
    print(f"\nRequirement: {req[:50]}...")
    result = app.invoke({
        "requirement": req,
        "complexity": 0.0,
        "needs_clarification": False,
        "validation_result": ""
    })
    print(f"Result: {result['validation_result']}")
```

### Example 3: LLM-Based Routing

```python
"""
src/examples/ex24_llm_routing.py

Use LLM to make routing decisions
"""

from typing import TypedDict, Literal
from langgraph.graph import StateGraph, START, END
from langchain_anthropic import ChatAnthropic
from langchain.prompts import ChatPromptTemplate
from dotenv import load_dotenv

load_dotenv()

class SmartRoutingState(TypedDict):
    user_request: str
    route_decision: str
    processing_result: str

def llm_router(state: SmartRoutingState) -> SmartRoutingState:
    """Use LLM to decide routing"""
    llm = ChatAnthropic(model="claude-3-5-sonnet-20241022", temperature=0)

    prompt = ChatPromptTemplate.from_messages([
        ("system", """Analyze the user request and decide which processing path to take.

        Options:
        - "extract": User wants to extract requirements from description
        - "validate": User wants to validate existing requirements
        - "clarify": User is asking questions about requirements
        - "other": Something else

        Respond with ONLY ONE WORD: extract, validate, clarify, or other"""),
        ("user", "{request}")
    ])

    chain = prompt | llm
    response = chain.invoke({"request": state["user_request"]})
    decision = response.content.strip().lower()

    return {"route_decision": decision}

def extract_path(state: SmartRoutingState) -> SmartRoutingState:
    """Process extraction request"""
    return {"processing_result": "Extracting requirements..."}

def validate_path(state: SmartRoutingState) -> SmartRoutingState:
    """Process validation request"""
    return {"processing_result": "Validating requirements..."}

def clarify_path(state: SmartRoutingState) -> SmartRoutingState:
    """Process clarification request"""
    return {"processing_result": "Answering your question..."}

def other_path(state: SmartRoutingState) -> SmartRoutingState:
    """Handle other requests"""
    return {"processing_result": "I'm not sure how to help with that."}

def route_by_llm_decision(state: SmartRoutingState) -> Literal["extract", "validate", "clarify", "other"]:
    """Route based on LLM's decision"""
    decision = state["route_decision"]
    if decision in ["extract", "validate", "clarify", "other"]:
        return decision
    return "other"  # Default fallback

# Build workflow
workflow = StateGraph(SmartRoutingState)
workflow.add_node("router", llm_router)
workflow.add_node("extract", extract_path)
workflow.add_node("validate", validate_path)
workflow.add_node("clarify", clarify_path)
workflow.add_node("other", other_path)

workflow.add_edge(START, "router")
workflow.add_conditional_edges(
    "router",
    route_by_llm_decision,
    {
        "extract": "extract",
        "validate": "validate",
        "clarify": "clarify",
        "other": "other"
    }
)
workflow.add_edge("extract", END)
workflow.add_edge("validate", END)
workflow.add_edge("clarify", END)
workflow.add_edge("other", END)

app = workflow.compile()

# Test
requests = [
    "Extract requirements from this: Build a login system",
    "Check if FR-001 is valid",
    "What does a functional requirement mean?",
    "Tell me a joke"
]

for req in requests:
    print(f"\nRequest: {req}")
    result = app.invoke({
        "user_request": req,
        "route_decision": "",
        "processing_result": ""
    })
    print(f"Decision: {result['route_decision']}")
    print(f"Result: {result['processing_result']}")
```

---

## 🏋️ Hands-On Exercise: Smart Requirement Classifier

**Objective**: Build a workflow that intelligently routes requirements to appropriate validators.

### Requirements

Create a system that routes requirements based on:
1. **Type**: Functional (FR), Non-Functional (NFR), or Business Rule (BR)
2. **Priority**: P1 (critical), P2 (important), P3 (nice-to-have)
3. **Clarity**: Clear vs Ambiguous

### Routing Logic

```
                    ┌─────────────┐
                    │  Classify   │
                    └──────┬──────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
         Functional   Non-Functional  Business
              │            │            │
         ┌────┴────┐  ┌────┴────┐     │
         │         │  │         │     │
       P1-FR     P2-FR NFR    Other   BR
         │         │  │         │     │
         └────┬────┘  └────┬────┘     │
              │            │          │
         ┌────┴────────────┴──────────┴────┐
         │         Aggregator               │
         └──────────────────────────────────┘
```

### Starter Code

Create `src/exercises/ex06_smart_classifier.py`:

```python
"""
Exercise 6: Smart Requirement Classifier

Build intelligent routing based on requirement characteristics
"""

from typing import TypedDict, Literal
from langgraph.graph import StateGraph, START, END

class ClassifierState(TypedDict):
    requirement: str
    req_type: str  # "FR", "NFR", "BR"
    priority: str  # "P1", "P2", "P3"
    is_clear: bool
    validation_path: str
    final_result: str

# TODO: Implement classify_requirement node
def classify_requirement(state: ClassifierState) -> ClassifierState:
    """Analyze and classify the requirement"""
    # TODO: Determine type (FR/NFR/BR)
    # TODO: Assess priority
    # TODO: Check clarity
    pass

# TODO: Implement routing function
def route_by_classification(state: ClassifierState) -> Literal[...]:
    """Route based on type, priority, clarity"""
    # TODO: Create routing logic
    # High priority functional: "p1_fr"
    # Standard functional: "standard_fr"
    # Non-functional: "nfr"
    # Business rule: "br"
    # Unclear: "clarify"
    pass

# TODO: Implement validator nodes for each path

# TODO: Build workflow with conditional edges

# Test cases
test_requirements = [
    "System SHALL authenticate users within 2 seconds (P1)",
    "User should be able to change theme color (P3)",
    "System must comply with GDPR regulations",
    "Something needs to happen with the data TBD"
]
```

---

## 🚀 Challenge: Dynamic Routing with Learning

**Advanced**: Build a routing system that learns from past decisions to improve routing accuracy.

### Challenge Concept

1. Track routing decisions and outcomes
2. Use historical data to improve routing
3. Implement A/B testing for routing strategies
4. Measure and optimize routing performance

---

## 🎓 Key Takeaways

### Routing Best Practices

✅ **DO**:
- Keep routing logic simple and clear
- Handle all possible return values
- Provide default fallback routes
- Test edge cases thoroughly
- Document routing decisions

❌ **DON'T**:
- Put business logic in routing functions
- Create circular routes without exit conditions
- Forget to handle unexpected states
- Make routing decisions based on external calls (do that in nodes)

---

## 🔄 Story Progress: SpecBot v0.6

**What we built**: SpecBot now intelligently routes requirements!

```python
# SpecBot v0.6 - Smart Routing
workflow.add_conditional_edges(
    "analyze",
    route_requirement,
    {
        "simple": "fast_validation",
        "complex": "deep_analysis",
        "ambiguous": "clarification_needed"
    }
)

# Requirements automatically routed to appropriate validators!
```

**Next Step**: Lesson 7 introduces Human-in-the-Loop patterns, allowing SpecBot to pause for user approval and feedback.

---

**Continue to [Lesson 7: Human-in-the-Loop (HITL) Patterns →](./07-hitl-patterns.md)**
