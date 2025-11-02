# Lesson 9: Error Handling, Retries & Validation

> **Story Context**: SpecBot calls LLMs to generate blocks, but APIs fail, rate limits hit, and responses sometimes violate constraints. Production systems need robust error handling. This lesson teaches you to build fault-tolerant workflows with retries, circuit breakers, and comprehensive validation.

---

## 🎯 Learning Objectives

By the end of this lesson, you will:

1. Implement retry logic with exponential backoff
2. Build circuit breakers to prevent cascading failures
3. Create fallback strategies for degraded operation
4. Validate LLM outputs at each step
5. Handle rate limits and API errors gracefully
6. Design comprehensive error recovery flows

**Time**: ~4 hours

---

## 📖 Key Concepts

### The Error Handling Trinity

**1. Retries** - Try again when transient failures occur
**2. Circuit Breakers** - Stop trying when service is down
**3. Fallbacks** - Degrade gracefully when all else fails

### Common Failure Modes

```
API Failures:
- Network timeouts
- Rate limit exceeded (429)
- Service unavailable (503)
- Authentication errors (401)

LLM Failures:
- Output parsing errors
- Constraint violations
- Incomplete responses
- Hallucinations

System Failures:
- Database connection lost
- Out of memory
- Disk full
- Process killed
```

### Retry Strategy: Exponential Backoff

```python
# Linear backoff (bad)
sleep(2)  # Always wait 2 seconds

# Exponential backoff (good)
wait_time = base_delay * (2 ** attempt)
# Attempt 1: 1s
# Attempt 2: 2s
# Attempt 3: 4s
# Attempt 4: 8s
```

### Circuit Breaker States

```
CLOSED (Normal) → OPEN (Failing) → HALF_OPEN (Testing) → CLOSED
     ↓                ↓                    ↓
  All requests   Block all requests   Allow 1 test request
     pass          (fail fast)        (check if recovered)
```

---

## 💻 Code Examples

### Example 1: Retry with Exponential Backoff

```python
"""
src/examples/ex30_retry_backoff.py

Implement retry logic with exponential backoff
"""

from typing import TypedDict, List
from langgraph.graph import StateGraph, START, END
from langchain_anthropic import ChatAnthropic
import time
import random

class RetryState(TypedDict):
    input_text: str
    requirements: List[str]
    errors: List[str]
    attempt_count: int

def with_retry(max_retries=3, base_delay=1, max_delay=30):
    """Decorator for retry logic with exponential backoff"""
    def decorator(func):
        async def wrapper(state):
            last_error = None

            for attempt in range(max_retries):
                try:
                    # Try the operation
                    return await func(state)

                except Exception as e:
                    last_error = e
                    error_msg = f"Attempt {attempt + 1} failed: {str(e)}"
                    print(f"⚠ {error_msg}")

                    # Update state with error
                    state["errors"] = state.get("errors", []) + [error_msg]
                    state["attempt_count"] = attempt + 1

                    # Don't retry on final attempt
                    if attempt == max_retries - 1:
                        break

                    # Calculate backoff with jitter
                    delay = min(base_delay * (2 ** attempt), max_delay)
                    jitter = random.uniform(0, 0.1 * delay)
                    wait_time = delay + jitter

                    print(f"⏱ Waiting {wait_time:.1f}s before retry...")
                    time.sleep(wait_time)

            # All retries failed
            return {
                **state,
                "errors": state["errors"] + [f"Failed after {max_retries} attempts: {last_error}"]
            }

        return wrapper
    return decorator

@with_retry(max_retries=3, base_delay=1, max_delay=10)
async def extract_requirements(state: RetryState) -> RetryState:
    """Extract requirements with retry logic"""

    # Simulate occasional failures (20% chance)
    if random.random() < 0.2:
        raise Exception("Simulated API failure")

    llm = ChatAnthropic(
        model="claude-3-5-sonnet-20241022",
        temperature=0,
        max_retries=0  # Disable built-in retries, we handle it
    )

    response = await llm.ainvoke(
        f"Extract 3 requirements from: {state['input_text']}"
    )

    # Parse response
    requirements = [
        line.strip()
        for line in response.content.split("\n")
        if line.strip() and not line.startswith("#")
    ][:3]

    return {
        "requirements": requirements,
        "errors": []  # Clear errors on success
    }

# Build workflow
workflow = StateGraph(RetryState)
workflow.add_node("extract", extract_requirements)
workflow.add_edge(START, "extract")
workflow.add_edge("extract", END)

app = workflow.compile()

# Test
import asyncio

async def main():
    result = await app.ainvoke({
        "input_text": "Build a login system with password reset",
        "requirements": [],
        "errors": [],
        "attempt_count": 0
    })

    print("\n=== Results ===")
    print(f"Requirements: {result['requirements']}")
    print(f"Total attempts: {result['attempt_count']}")
    if result['errors']:
        print(f"Errors: {result['errors']}")

asyncio.run(main())
```

### Example 2: Circuit Breaker Pattern

```python
"""
src/examples/ex31_circuit_breaker.py

Implement circuit breaker to prevent cascading failures
"""

from typing import TypedDict
from enum import Enum
import time
from datetime import datetime, timedelta

class CircuitState(Enum):
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, block requests
    HALF_OPEN = "half_open"  # Testing recovery

class CircuitBreaker:
    """Circuit breaker for external service calls"""

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: type = Exception
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception

        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED

    def call(self, func, *args, **kwargs):
        """Execute function through circuit breaker"""

        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
                print("⚡ Circuit breaker: HALF_OPEN (testing recovery)")
            else:
                time_since_failure = time.time() - self.last_failure_time
                wait_time = self.recovery_timeout - time_since_failure
                raise Exception(
                    f"Circuit breaker OPEN. "
                    f"Try again in {wait_time:.0f} seconds."
                )

        try:
            result = func(*args, **kwargs)

            # Success - reset circuit breaker
            if self.state == CircuitState.HALF_OPEN:
                print("✓ Circuit breaker: CLOSED (recovered)")
                self.state = CircuitState.CLOSED
                self.failure_count = 0

            return result

        except self.expected_exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()

            print(f"⚠ Circuit breaker: Failure {self.failure_count}/{self.failure_threshold}")

            if self.failure_count >= self.failure_threshold:
                self.state = CircuitState.OPEN
                print(f"⛔ Circuit breaker: OPEN (too many failures)")

            raise

    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to test recovery"""
        return (
            time.time() - self.last_failure_time >= self.recovery_timeout
        )

# Usage in workflow
class ServiceState(TypedDict):
    data: str
    result: str
    circuit_breaker_status: str

# Create circuit breaker for LLM service
llm_circuit_breaker = CircuitBreaker(
    failure_threshold=3,
    recovery_timeout=30
)

def call_llm_service(state: ServiceState) -> ServiceState:
    """Call LLM service through circuit breaker"""

    try:
        # Simulate flaky service
        if random.random() < 0.5:
            raise Exception("LLM API error")

        result = llm_circuit_breaker.call(
            lambda: "Generated requirements from LLM"
        )

        return {
            "result": result,
            "circuit_breaker_status": llm_circuit_breaker.state.value
        }

    except Exception as e:
        return {
            "result": f"Error: {str(e)}",
            "circuit_breaker_status": llm_circuit_breaker.state.value
        }

# Test circuit breaker
print("=== Testing Circuit Breaker ===\n")

for i in range(10):
    state = {"data": "test", "result": "", "circuit_breaker_status": ""}
    result = call_llm_service(state)

    print(f"Request {i+1}:")
    print(f"  Result: {result['result'][:50]}")
    print(f"  Circuit: {result['circuit_breaker_status']}")
    print()

    time.sleep(2)
```

### Example 3: Comprehensive Validation Pipeline

```python
"""
src/examples/ex32_validation_pipeline.py

Multi-layer validation with error recovery
"""

from typing import TypedDict, List, Literal
from langgraph.graph import StateGraph, START, END
from pydantic import BaseModel, Field, ValidationError
import re

class Requirement(BaseModel):
    """Validated requirement model"""
    id: str = Field(pattern=r"^FR-\d{3}$")
    description: str = Field(min_length=20, max_length=200)
    priority: Literal["P1", "P2", "P3"]
    category: Literal["functional", "non-functional", "business"]

    def validate_description_quality(self) -> List[str]:
        """Custom validation for description quality"""
        errors = []

        # Check for modal verbs
        if not any(word in self.description for word in ["SHALL", "MUST", "SHOULD"]):
            errors.append("Missing modal verb (SHALL/MUST/SHOULD)")

        # Check for implementation details
        tech_terms = ["database", "React", "API", "AWS", "PostgreSQL"]
        if any(term.lower() in self.description.lower() for term in tech_terms):
            errors.append("Contains implementation details")

        # Check for vague terms
        vague_terms = ["good", "nice", "easy", "simple", "better"]
        if any(term in self.description.lower() for term in vague_terms):
            errors.append("Contains vague terms")

        return errors

class ValidationState(TypedDict):
    raw_requirements: List[str]
    validated_requirements: List[Requirement]
    validation_errors: List[dict]
    retry_count: int
    status: str

def parse_requirements(state: ValidationState) -> ValidationState:
    """Parse and validate requirements"""
    errors = []
    validated = []

    for i, req_text in enumerate(state["raw_requirements"]):
        try:
            # Extract components with regex
            id_match = re.search(r"(FR-\d{3})", req_text)
            priority_match = re.search(r"\[(P[123])\]", req_text)

            if not id_match or not priority_match:
                errors.append({
                    "index": i,
                    "requirement": req_text,
                    "error": "Missing ID or priority"
                })
                continue

            # Create requirement object
            req = Requirement(
                id=id_match.group(1),
                description=req_text,
                priority=priority_match.group(1),
                category="functional"
            )

            # Custom validation
            quality_errors = req.validate_description_quality()
            if quality_errors:
                errors.append({
                    "index": i,
                    "requirement": req_text,
                    "error": "; ".join(quality_errors)
                })
            else:
                validated.append(req)

        except ValidationError as e:
            errors.append({
                "index": i,
                "requirement": req_text,
                "error": str(e)
            })

    return {
        "validated_requirements": validated,
        "validation_errors": errors,
        "status": "validated" if not errors else "has_errors"
    }

def regenerate_invalid(state: ValidationState) -> ValidationState:
    """Regenerate requirements that failed validation"""
    print(f"Regenerating {len(state['validation_errors'])} invalid requirements...")

    regenerated = []
    for error in state["validation_errors"]:
        # Simple regeneration logic (in production, use LLM)
        original = error["requirement"]
        req_num = len(state["validated_requirements"]) + len(regenerated) + 1

        fixed = f"FR-{req_num:03d} [P2] The system SHALL {original.lower()}"
        regenerated.append(fixed)

    return {
        "raw_requirements": regenerated,
        "validation_errors": [],
        "retry_count": state["retry_count"] + 1
    }

def check_validation_status(state: ValidationState) -> Literal["success", "retry", "failed"]:
    """Route based on validation results"""
    if state["status"] == "validated":
        return "success"
    elif state["retry_count"] < 3:
        return "retry"
    else:
        return "failed"

# Build workflow
workflow = StateGraph(ValidationState)
workflow.add_node("parse", parse_requirements)
workflow.add_node("regenerate", regenerate_invalid)

workflow.add_edge(START, "parse")
workflow.add_conditional_edges(
    "parse",
    check_validation_status,
    {
        "success": END,
        "retry": "regenerate",
        "failed": END
    }
)
workflow.add_edge("regenerate", "parse")

app = workflow.compile()

# Test
test_requirements = [
    "FR-001 [P1] System should have good security",  # Vague
    "FR-002 [P2] System SHALL authenticate users using PostgreSQL database",  # Implementation detail
    "FR-003 [P1] The system SHALL authenticate users within 2 seconds",  # Valid!
]

result = app.invoke({
    "raw_requirements": test_requirements,
    "validated_requirements": [],
    "validation_errors": [],
    "retry_count": 0,
    "status": "pending"
})

print("=== Validation Results ===\n")
print(f"Valid requirements: {len(result['validated_requirements'])}")
print(f"Validation errors: {len(result['validation_errors'])}")
print(f"Retry count: {result['retry_count']}")

if result['validation_errors']:
    print("\nErrors:")
    for error in result['validation_errors']:
        print(f"  - {error['error']}")
        print(f"    Requirement: {error['requirement'][:60]}...")
```

---

## 🏋️ Hands-On Exercise: Production-Ready Requirement Extractor

**Objective**: Build a fault-tolerant requirement extraction system with retries, circuit breakers, validation, and fallbacks.

### Requirements

Create a system that:
1. Extracts requirements from user input
2. Retries on API failures (max 3 attempts, exponential backoff)
3. Uses circuit breaker to prevent overload
4. Validates all outputs with Pydantic
5. Regenerates invalid requirements
6. Falls back to simpler prompts if complex ones fail
7. Logs all errors and recovery actions

### Starter Code

Create `src/exercises/ex09_production_extractor.py`:

```python
"""
Exercise 9: Production-Ready Requirement Extractor

Build fault-tolerant extraction with comprehensive error handling
"""

from typing import TypedDict, List, Literal
from langgraph.graph import StateGraph, START, END
from pydantic import BaseModel, Field, ValidationError

# TODO: Define Requirement model with validation

# TODO: Define state
class ProductionState(TypedDict):
    user_input: str
    requirements: List[dict]
    errors: List[str]
    retry_count: int
    circuit_breaker_open: bool
    fallback_used: bool
    prompt_complexity: str  # "complex", "simple", "minimal"

# TODO: Implement circuit breaker class

# TODO: Implement retry decorator

# TODO: Implement extraction node with:
# - Retry logic
# - Circuit breaker
# - Prompt complexity management

# TODO: Implement validation node

# TODO: Implement regeneration node

# TODO: Implement fallback node (use simpler prompt)

# TODO: Build workflow with conditional routing

# Test cases
test_cases = [
    "Build a user authentication system with email/password",
    "Create a dashboard showing sales metrics",
    "Implement file upload with drag and drop"
]
```

### Expected Output

```
=== Processing: Build a user authentication system ===

[Attempt 1] Extracting with complex prompt...
⚠ API error: Rate limit exceeded
⏱ Waiting 1.2s before retry...

[Attempt 2] Extracting with complex prompt...
✓ Extracted 5 requirements

Validating requirements...
✓ FR-001: Valid
✓ FR-002: Valid
✗ FR-003: Missing modal verb
✗ FR-004: Contains implementation details
✓ FR-005: Valid

Regenerating 2 invalid requirements...
✓ Regenerated FR-003
✓ Regenerated FR-004

Final Results:
  Total requirements: 5
  Valid: 5
  Retries: 1
  Fallback used: No
  Errors: 1 (recovered)
```

---

## 🚀 Challenge: Self-Healing Workflow

**Advanced**: Build a workflow that automatically recovers from failures by trying different strategies.

### Challenge Requirements

Create a system that:
1. **Tries multiple LLM models** (Claude → GPT-4 → Gemini)
2. **Adjusts parameters** (temperature, max_tokens) on failure
3. **Simplifies prompts** progressively
4. **Caches successful strategies** for future use
5. **Reports detailed diagnostics** on failures
6. **Implements rate limit budget** tracking

### Template

```python
"""
src/exercises/ex09_self_healing.py

Self-healing workflow with adaptive error recovery
"""

class RecoveryStrategy:
    """Adaptive recovery strategy"""

    def __init__(self):
        self.models = ["claude-3-5-sonnet", "gpt-4", "gemini-pro"]
        self.temperatures = [0, 0.3, 0.7]
        self.prompt_styles = ["detailed", "standard", "minimal"]
        self.success_history = {}

    def get_next_strategy(self, current_strategy: dict, error: Exception):
        """Determine next strategy based on error type"""
        # TODO: Implement adaptive strategy selection
        pass

    def record_success(self, strategy: dict):
        """Record successful strategy for future use"""
        # TODO: Cache successful configurations
        pass

# TODO: Implement self-healing workflow
```

---

## 🎓 Key Takeaways

### Error Handling Best Practices

✅ **DO**:
- Always validate LLM outputs
- Use exponential backoff for retries
- Implement circuit breakers for external services
- Log errors with full context
- Have fallback strategies
- Test failure scenarios regularly
- Monitor error rates in production

❌ **DON'T**:
- Retry forever without limits
- Ignore specific error types
- Retry on non-retryable errors (401, 400)
- Hide errors from users
- Skip validation for "trusted" outputs
- Assume APIs are always available

### When to Retry vs Fail Fast

**Retry**:
- Network timeouts
- Rate limits (429)
- Service unavailable (503)
- Transient database errors

**Fail Fast**:
- Authentication errors (401)
- Invalid input (400)
- Resource not found (404)
- Validation failures
- Business logic violations

---

## 🔄 Story Progress: SpecBot v0.9

**What we built**: SpecBot now handles failures gracefully!

```python
# SpecBot v0.9 - Production Error Handling
@with_retry(max_retries=3, base_delay=1)
async def generate_block(state):
    try:
        # Try to generate with circuit breaker
        result = circuit_breaker.call(llm_generate, state)

        # Validate output
        validated = validate_requirement(result)

        return {"block": validated}

    except ValidationError as e:
        # Regenerate with feedback
        return regenerate_with_constraints(state, e)

    except CircuitBreakerOpen:
        # Fall back to cached template
        return use_fallback_template(state)

# Handles API failures, validates outputs, recovers automatically!
```

**Next Step**: Lesson 10 introduces Context7 patterns for progressive context loading, enabling efficient handling of large documents.

---

**Continue to [Lesson 10: Context7 & Progressive Disclosure →](./10-context7-fundamentals.md)**
