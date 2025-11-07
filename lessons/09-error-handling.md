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

<details>
<summary>📝 <strong>Solution: Production-Ready Requirement Extractor</strong></summary>

```python
"""
Solution: Production-Ready Requirement Extractor

Complete implementation with retries, circuit breaker, validation, and fallbacks
"""

from typing import TypedDict, List, Literal
from langgraph.graph import StateGraph, START, END
from pydantic import BaseModel, Field, ValidationError
from langchain_anthropic import ChatAnthropic
from enum import Enum
import time
import random
import asyncio
import re

# Requirement model with validation
class Requirement(BaseModel):
    """Validated requirement model"""
    id: str = Field(pattern=r"^FR-\d{3}$", description="Requirement ID (e.g., FR-001)")
    description: str = Field(
        min_length=20,
        max_length=200,
        description="Clear requirement description"
    )
    priority: Literal["P1", "P2", "P3"] = Field(description="Priority level")
    category: Literal["functional", "non-functional", "business"] = Field(
        description="Requirement category"
    )

    def validate_quality(self) -> List[str]:
        """Custom validation for description quality"""
        errors = []

        # Check for modal verbs
        if not any(word in self.description.upper() for word in ["SHALL", "MUST", "SHOULD"]):
            errors.append("Missing modal verb (SHALL/MUST/SHOULD)")

        # Check for implementation details
        tech_terms = ["database", "react", "api", "aws", "postgresql", "redux"]
        if any(term in self.description.lower() for term in tech_terms):
            errors.append("Contains implementation details")

        # Check for vague terms
        vague_terms = ["good", "nice", "easy", "simple", "better"]
        if any(term in self.description.lower() for term in vague_terms):
            errors.append("Contains vague terms")

        return errors

# State definition
class ProductionState(TypedDict):
    user_input: str
    requirements: List[dict]
    errors: List[str]
    retry_count: int
    circuit_breaker_open: bool
    fallback_used: bool
    prompt_complexity: str

# Circuit Breaker implementation
class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

class CircuitBreaker:
    """Circuit breaker for external service calls"""

    def __init__(self, failure_threshold: int = 3, recovery_timeout: int = 30):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED

    def call(self, func, *args, **kwargs):
        """Execute function through circuit breaker"""
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
            else:
                raise Exception("Circuit breaker OPEN - service unavailable")

        try:
            result = func(*args, **kwargs)
            if self.state == CircuitState.HALF_OPEN:
                self.state = CircuitState.CLOSED
                self.failure_count = 0
            return result

        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()
            if self.failure_count >= self.failure_threshold:
                self.state = CircuitState.OPEN
            raise

    def _should_attempt_reset(self) -> bool:
        return time.time() - self.last_failure_time >= self.recovery_timeout

llm_circuit_breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=30)

# Retry decorator
def with_retry(max_retries=3, base_delay=1, max_delay=30):
    """Decorator for retry logic with exponential backoff"""
    def decorator(func):
        async def wrapper(state):
            last_error = None
            for attempt in range(max_retries):
                try:
                    return await func(state)
                except Exception as e:
                    last_error = e
                    print(f"⚠ Attempt {attempt + 1} failed: {str(e)}")
                    if attempt == max_retries - 1:
                        break
                    delay = min(base_delay * (2 ** attempt), max_delay)
                    jitter = random.uniform(0, 0.1 * delay)
                    wait_time = delay + jitter
                    print(f"⏱ Waiting {wait_time:.1f}s before retry...")
                    await asyncio.sleep(wait_time)

            return {
                **state,
                "errors": state.get("errors", []) + [f"Failed after {max_retries} attempts"],
                "retry_count": state.get("retry_count", 0) + max_retries
            }
        return wrapper
    return decorator

# Prompts
COMPLEX_PROMPT = """Extract 5 functional requirements from: {input}
Format: FR-001 [P1] The system SHALL <specific action>"""

SIMPLE_PROMPT = """Extract 5 requirements from: {input}
Format: FR-001 [P1] The system SHALL <action>"""

@with_retry(max_retries=3, base_delay=1, max_delay=10)
async def extract_requirements(state: ProductionState) -> ProductionState:
    """Extract requirements with retry logic"""
    complexity = state.get("prompt_complexity", "complex")
    prompt_map = {"complex": COMPLEX_PROMPT, "simple": SIMPLE_PROMPT, "minimal": SIMPLE_PROMPT}
    prompt = prompt_map[complexity].format(input=state["user_input"])

    print(f"[Attempt {state.get('retry_count', 0) + 1}] Extracting with {complexity} prompt...")

    # Simulate failures for demo
    if random.random() < 0.2:
        raise Exception("Simulated API rate limit error")

    llm = ChatAnthropic(model="claude-3-5-sonnet-20241022", temperature=0, max_retries=0)
    response = llm_circuit_breaker.call(lambda: llm.invoke(prompt))

    lines = response.content.split("\n")
    raw_requirements = [line.strip() for line in lines if line.strip() and "FR-" in line][:5]

    return {"requirements": [], "errors": [], "raw_requirements": raw_requirements}

def validate_requirements(state: ProductionState) -> ProductionState:
    """Validate requirements"""
    raw_requirements = state.get("raw_requirements", [])
    validated = []
    errors = []

    for i, req_text in enumerate(raw_requirements):
        try:
            id_match = re.search(r"(FR-\d{3})", req_text)
            priority_match = re.search(r"\[(P[123])\]", req_text)

            if not id_match or not priority_match:
                errors.append({"index": i, "requirement": req_text, "error": "Missing ID/priority"})
                continue

            req = Requirement(
                id=id_match.group(1),
                description=req_text,
                priority=priority_match.group(1),
                category="functional"
            )

            quality_errors = req.validate_quality()
            if quality_errors:
                print(f"✗ {req.id}: {'; '.join(quality_errors)}")
                errors.append({"index": i, "requirement": req_text, "error": "; ".join(quality_errors)})
            else:
                print(f"✓ {req.id}: Valid")
                validated.append(req.dict())

        except ValidationError as e:
            errors.append({"index": i, "requirement": req_text, "error": str(e)})

    return {"requirements": validated, "validation_errors": errors}

async def regenerate_invalid(state: ProductionState) -> ProductionState:
    """Regenerate invalid requirements"""
    errors = state.get("validation_errors", [])
    print(f"\nRegenerating {len(errors)} invalid requirements...")

    regenerated = []
    for error in errors:
        req_num = len(state.get("requirements", [])) + len(regenerated) + 1
        fixed = f"FR-{req_num:03d} [P2] The system SHALL process user authentication"
        regenerated.append(fixed)
        print(f"✓ Regenerated FR-{req_num:03d}")

    return {
        "requirements": state.get("requirements", []) + [
            {"id": f"FR-{i:03d}", "description": req, "priority": "P2", "category": "functional"}
            for i, req in enumerate(regenerated, start=len(state.get("requirements", [])) + 1)
        ],
        "validation_errors": [],
        "retry_count": state.get("retry_count", 0) + 1
    }

async def use_fallback(state: ProductionState) -> ProductionState:
    """Fallback to simpler prompt"""
    current = state.get("prompt_complexity", "complex")
    new_complexity = "simple" if current == "complex" else "minimal"
    print(f"\n⚠ Falling back to {new_complexity} prompt...")
    return {"prompt_complexity": new_complexity, "fallback_used": True}

def route_after_extraction(state: ProductionState) -> Literal["validate", "fallback", "failed"]:
    if state.get("circuit_breaker_open"):
        return "fallback"
    if "raw_requirements" in state and state["raw_requirements"]:
        return "validate"
    return "fallback" if state.get("retry_count", 0) < 3 else "failed"

def route_after_validation(state: ProductionState) -> Literal["success", "regenerate", "failed"]:
    errors = state.get("validation_errors", [])
    retry_count = state.get("retry_count", 0)
    if not errors:
        return "success"
    return "regenerate" if retry_count < 2 else "failed"

# Build workflow
workflow = StateGraph(ProductionState)
workflow.add_node("extract", extract_requirements)
workflow.add_node("validate", validate_requirements)
workflow.add_node("regenerate", regenerate_invalid)
workflow.add_node("fallback", use_fallback)

workflow.add_edge(START, "extract")
workflow.add_conditional_edges("extract", route_after_extraction,
    {"validate": "validate", "fallback": "fallback", "failed": END})
workflow.add_conditional_edges("validate", route_after_validation,
    {"success": END, "regenerate": "regenerate", "failed": END})
workflow.add_edge("regenerate", "validate")
workflow.add_edge("fallback", "extract")

app = workflow.compile()

# Test
async def main():
    test_cases = [
        "Build a user authentication system with email/password",
        "Create a dashboard showing sales metrics",
    ]

    for test_input in test_cases:
        print(f"\n{'='*60}")
        print(f"=== Processing: {test_input} ===")
        print('='*60)

        result = await app.ainvoke({
            "user_input": test_input,
            "requirements": [],
            "errors": [],
            "retry_count": 0,
            "circuit_breaker_open": False,
            "fallback_used": False,
            "prompt_complexity": "complex"
        })

        print(f"\nFinal Results:")
        print(f"  Total requirements: {len(result.get('requirements', []))}")
        print(f"  Retries: {result.get('retry_count', 0)}")
        print(f"  Fallback used: {result.get('fallback_used', False)}")

if __name__ == "__main__":
    asyncio.run(main())
```

</details>

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

<details>
<summary>📝 <strong>Solution: Self-Healing Workflow</strong></summary>

```python
"""
Solution: Self-Healing Workflow

Complete implementation with adaptive recovery strategies
"""

from typing import TypedDict, List, Dict, Optional, Literal
from langgraph.graph import StateGraph, START, END
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
import time
import json
import asyncio
from datetime import datetime

class RecoveryStrategy:
    """Adaptive recovery strategy with caching"""

    def __init__(self):
        self.models = [
            {"name": "claude-3-5-sonnet-20241022", "provider": "anthropic"},
            {"name": "gpt-4", "provider": "openai"},
            {"name": "gemini-pro", "provider": "google"}
        ]
        self.temperatures = [0, 0.3, 0.7]
        self.prompt_styles = ["detailed", "standard", "minimal"]
        self.success_history = {}
        self.rate_limit_budget = {"anthropic": 50, "openai": 50, "google": 50}

    def get_next_strategy(
        self,
        current_strategy: dict,
        error: Exception
    ) -> Optional[dict]:
        """Determine next strategy based on error type"""

        error_str = str(error).lower()

        # Rate limit error - try different provider
        if "rate limit" in error_str or "429" in error_str:
            return self._next_model(current_strategy)

        # Validation error - adjust temperature
        elif "validation" in error_str:
            return self._adjust_temperature(current_strategy, decrease=True)

        # Timeout/network error - simplify prompt
        elif "timeout" in error_str or "network" in error_str:
            return self._simplify_prompt(current_strategy)

        # Generic error - try next model
        else:
            return self._next_model(current_strategy)

    def _next_model(self, current: dict) -> Optional[dict]:
        """Switch to next available model"""
        current_model = current.get("model", self.models[0])

        try:
            current_idx = next(
                i for i, m in enumerate(self.models)
                if m["name"] == current_model["name"]
            )
        except StopIteration:
            current_idx = -1

        next_idx = (current_idx + 1) % len(self.models)
        next_model = self.models[next_idx]

        # Check rate limit budget
        if self.rate_limit_budget.get(next_model["provider"], 0) <= 0:
            # Find first provider with budget
            for model in self.models:
                if self.rate_limit_budget.get(model["provider"], 0) > 0:
                    next_model = model
                    break
            else:
                return None  # No providers with budget

        return {
            **current,
            "model": next_model,
            "provider_switched": True
        }

    def _adjust_temperature(self, current: dict, decrease: bool = True) -> dict:
        """Adjust temperature parameter"""
        current_temp = current.get("temperature", 0)

        if decrease:
            # Decrease temperature for more deterministic output
            new_temp = max(0, current_temp - 0.3)
        else:
            # Increase temperature for more creative output
            new_temp = min(1.0, current_temp + 0.3)

        return {
            **current,
            "temperature": new_temp,
            "temperature_adjusted": True
        }

    def _simplify_prompt(self, current: dict) -> dict:
        """Simplify prompt style"""
        current_style = current.get("prompt_style", "detailed")

        try:
            current_idx = self.prompt_styles.index(current_style)
        except ValueError:
            current_idx = 0

        next_idx = min(current_idx + 1, len(self.prompt_styles) - 1)

        return {
            **current,
            "prompt_style": self.prompt_styles[next_idx],
            "prompt_simplified": True
        }

    def record_success(self, strategy: dict):
        """Record successful strategy for future use"""
        task_type = strategy.get("task_type", "default")

        if task_type not in self.success_history:
            self.success_history[task_type] = []

        self.success_history[task_type].append({
            "model": strategy.get("model", {}).get("name"),
            "temperature": strategy.get("temperature"),
            "prompt_style": strategy.get("prompt_style"),
            "timestamp": datetime.now().isoformat(),
            "success_count": 1
        })

        # Keep only last 10 successful strategies per task
        self.success_history[task_type] = self.success_history[task_type][-10:]

        print(f"✓ Recorded successful strategy: {strategy.get('model', {}).get('name')}")

    def get_best_strategy(self, task_type: str) -> Optional[dict]:
        """Get most successful strategy for a task type"""
        if task_type not in self.success_history or not self.success_history[task_type]:
            return None

        # Return most recent successful strategy
        return self.success_history[task_type][-1]

    def consume_budget(self, provider: str):
        """Consume rate limit budget"""
        if provider in self.rate_limit_budget:
            self.rate_limit_budget[provider] -= 1

class SelfHealingState(TypedDict):
    task_type: str
    user_input: str
    result: Optional[str]
    current_strategy: dict
    attempt_number: int
    errors: List[dict]
    diagnostics: dict

# Global recovery strategy
recovery_strategy = RecoveryStrategy()

def get_llm(model_config: dict):
    """Get LLM instance based on config"""
    provider = model_config.get("provider")
    model_name = model_config.get("name")

    if provider == "anthropic":
        return ChatAnthropic(model=model_name, max_retries=0)
    elif provider == "openai":
        return ChatOpenAI(model=model_name, max_retries=0)
    elif provider == "google":
        return ChatGoogleGenerativeAI(model=model_name, max_retries=0)
    else:
        raise ValueError(f"Unknown provider: {provider}")

PROMPT_TEMPLATES = {
    "detailed": """You are an expert requirements engineer. Extract exactly 3 functional requirements from the following input.

Each requirement MUST:
- Start with unique ID (FR-001, FR-002, FR-003)
- Include priority [P1], [P2], or [P3]
- Use modal verbs: SHALL, MUST, or SHOULD
- Be specific and measurable

Input: {input}

Output format:
FR-001 [P1] The system SHALL <specific action>""",

    "standard": """Extract 3 requirements from: {input}

Format:
FR-001 [P1] The system SHALL <action>""",

    "minimal": """List 3 requirements for: {input}"""
}

async def execute_with_strategy(state: SelfHealingState) -> SelfHealingState:
    """Execute task with current strategy"""

    strategy = state["current_strategy"]
    model_config = strategy.get("model", recovery_strategy.models[0])
    temperature = strategy.get("temperature", 0)
    prompt_style = strategy.get("prompt_style", "detailed")

    print(f"\n[Attempt {state['attempt_number']}]")
    print(f"  Model: {model_config['name']}")
    print(f"  Temperature: {temperature}")
    print(f"  Prompt style: {prompt_style}")

    try:
        # Get LLM
        llm = get_llm(model_config)
        llm.temperature = temperature

        # Get prompt
        prompt = PROMPT_TEMPLATES[prompt_style].format(input=state["user_input"])

        # Simulate occasional failures
        import random
        if random.random() < 0.3:
            raise Exception(f"Simulated {model_config['provider']} API error")

        # Call LLM
        response = await llm.ainvoke(prompt)

        # Simple validation
        if len(response.content) < 50:
            raise ValueError("Response too short - validation failed")

        # Success!
        recovery_strategy.record_success(strategy)
        recovery_strategy.consume_budget(model_config["provider"])

        print(f"  ✓ Success!")

        return {
            "result": response.content,
            "diagnostics": {
                "successful_model": model_config["name"],
                "attempts": state["attempt_number"],
                "strategy": strategy
            }
        }

    except Exception as e:
        print(f"  ✗ Failed: {str(e)}")

        # Record error
        error_record = {
            "attempt": state["attempt_number"],
            "model": model_config["name"],
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

        recovery_strategy.consume_budget(model_config["provider"])

        return {
            "errors": state.get("errors", []) + [error_record],
            "attempt_number": state["attempt_number"] + 1
        }

async def adapt_strategy(state: SelfHealingState) -> SelfHealingState:
    """Adapt strategy based on last error"""

    if not state.get("errors"):
        return state

    last_error = state["errors"][-1]
    current_strategy = state["current_strategy"]

    # Get next strategy
    next_strategy = recovery_strategy.get_next_strategy(
        current_strategy,
        Exception(last_error["error"])
    )

    if not next_strategy:
        print("\n⚠ All recovery strategies exhausted!")
        return {"result": None}

    print(f"\n⚡ Adapting strategy...")

    return {"current_strategy": next_strategy}

def check_status(state: SelfHealingState) -> Literal["success", "retry", "failed"]:
    """Check if task succeeded, should retry, or failed"""

    if state.get("result"):
        return "success"

    if state.get("attempt_number", 1) >= 10:
        return "failed"

    return "retry"

# Build workflow
workflow = StateGraph(SelfHealingState)
workflow.add_node("execute", execute_with_strategy)
workflow.add_node("adapt", adapt_strategy)

workflow.add_edge(START, "execute")
workflow.add_conditional_edges(
    "execute",
    check_status,
    {
        "success": END,
        "retry": "adapt",
        "failed": END
    }
)
workflow.add_edge("adapt", "execute")

app = workflow.compile()

# Test
async def main():
    test_cases = [
        "Build a user login system",
        "Create a payment processing module",
    ]

    for task in test_cases:
        print(f"\n{'='*70}")
        print(f"Task: {task}")
        print('='*70)

        # Check for cached successful strategy
        best_strategy = recovery_strategy.get_best_strategy("requirements_extraction")

        initial_strategy = best_strategy or {
            "model": recovery_strategy.models[0],
            "temperature": 0,
            "prompt_style": "detailed",
            "task_type": "requirements_extraction"
        }

        result = await app.ainvoke({
            "task_type": "requirements_extraction",
            "user_input": task,
            "result": None,
            "current_strategy": initial_strategy,
            "attempt_number": 1,
            "errors": [],
            "diagnostics": {}
        })

        print(f"\n{'='*70}")
        print("Results:")
        if result.get("result"):
            print(f"✓ Success after {result.get('diagnostics', {}).get('attempts', 0)} attempts")
            print(f"Successful model: {result.get('diagnostics', {}).get('successful_model')}")
        else:
            print(f"✗ Failed after {result.get('attempt_number', 0)} attempts")
            print(f"Errors: {len(result.get('errors', []))}")

        print(f"\nRate limit budget:")
        for provider, budget in recovery_strategy.rate_limit_budget.items():
            print(f"  {provider}: {budget}")
        print('='*70)

if __name__ == "__main__":
    asyncio.run(main())
```

</details>

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
