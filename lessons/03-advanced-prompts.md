# Lesson 3: Advanced Prompt Engineering & Few-Shot Learning

> **Story Context**: SpecBot can extract requirements, but output quality varies. Sometimes requirements are vague, sometimes too technical. In this lesson, you'll learn advanced prompt engineering techniques inspired by Spec-Kit's instruction templates to create consistent, high-quality outputs.

---

## 🎯 Learning Objectives

By the end of this lesson, you will:

1. Master few-shot learning techniques
2. Implement chain-of-thought prompting
3. Create constraint-based generation
4. Use constitutional AI principles
5. Build reusable prompt libraries
6. Apply Spec-Kit's prompt patterns

**Time**: ~2 hours

---

## 📖 Core Concepts

### 1. Few-Shot Learning

**Definition**: Providing examples in the prompt to guide the model's output format and style.

**Pattern**:
```
System: Your role and rules
Examples: 2-5 high-quality examples
User: The actual task
```

**When to use**:
- Complex output formats
- Domain-specific terminology
- Consistent style requirements
- Edge case handling

### 2. Chain-of-Thought (CoT)

**Definition**: Asking the model to show its reasoning before the final answer.

**Pattern**:
```
"Let's approach this step-by-step:
1. First, analyze...
2. Then, identify...
3. Finally, conclude..."
```

**Benefits**:
- Improved accuracy
- Transparent reasoning
- Better handling of complex tasks
- Easier debugging

### 3. Constraint-Based Generation

**Definition**: Explicit rules and limits in prompts (inspired by Spec-Kit's approach).

**Examples from Spec-Kit**:
- "Maximum 3 [NEEDS CLARIFICATION] markers total"
- "Branch name: 2-4 words, lowercase, hyphens only"
- "Success criteria must be measurable and technology-agnostic"

---

## 💡 Spec-Kit's Prompt Patterns

### Pattern 1: Procedural Instructions

**From Spec-Kit's `specify.md`**:

```markdown
1. Generate a concise short name (2-4 words)
2. Check for existing branches
3. Load templates/spec-template.md
4. Follow this execution flow:
   1. Parse user description
   2. Extract key concepts
   3. Fill template sections
```

**Why it works**:
- AI models follow sequences well
- Reduces ambiguity
- Makes debugging easier

### Pattern 2: Explicit Constraints

**From Spec-Kit**:

```markdown
Rules:
- Maximum 5 requirements
- Format as FR-001, FR-002, etc.
- Each requirement must be testable
- Focus on WHAT, not HOW
```

**Application to SpecBot**:

```python
system_prompt = """You are a requirements analyst.

STRICT RULES:
1. Extract EXACTLY 5 functional requirements (no more, no less)
2. Format: FR-XXX where XXX is 001-999
3. Each requirement MUST start with "System SHALL/MUST/SHOULD"
4. Each requirement MUST be independently testable
5. NEVER mention implementation details (technologies, frameworks, databases)
6. Use active voice and present tense

VALIDATION:
Before outputting, verify each requirement passes ALL rules above."""
```

### Pattern 3: Few-Shot Examples (Good vs Bad)

**From Spec-Kit's `checklist.md`**:

```markdown
❌ WRONG (Testing implementation):
- "Verify landing page displays 3 episode cards"

✅ CORRECT (Testing requirements quality):
- "Are the number and layout of featured episodes explicitly specified?"
```

**Application**:

```python
examples = """
EXAMPLE 1 - Vague (BAD):
Input: "Users can log in"
Output: FR-001: System should let users log in ❌

EXAMPLE 1 - Clear (GOOD):
Input: "Users can log in"
Output: FR-001: System SHALL authenticate users using email and password credentials ✓

EXAMPLE 2 - Too Technical (BAD):
Input: "Save user data"
Output: FR-002: System must persist user data to PostgreSQL database ❌

EXAMPLE 2 - Technology-Agnostic (GOOD):
Input: "Save user data"
Output: FR-002: System SHALL store user profile information persistently ✓
"""
```

---

## 🔧 Code Examples

### Example 1: Few-Shot Learning for Consistent Output

```python
"""
src/examples/ex10_few_shot.py

Using few-shot learning for consistent requirement extraction
"""

from langchain_anthropic import ChatAnthropic
from langchain.prompts import ChatPromptTemplate, FewShotChatMessagePromptTemplate
from dotenv import load_dotenv

load_dotenv()

llm = ChatAnthropic(model="claude-3-5-sonnet-20241022", temperature=0)

# Define examples (few-shot learning)
examples = [
    {
        "input": "Users can create accounts with email and password",
        "output": """FR-001: System SHALL provide user account creation functionality
FR-002: System SHALL validate email address format during registration
FR-003: System SHALL enforce minimum password length of 8 characters"""
    },
    {
        "input": "Show a list of all products with images and prices",
        "output": """FR-001: System SHALL display product catalog as a paginated list
FR-002: System SHALL show product image thumbnail for each item
FR-003: System SHALL display current price for each product"""
    },
    {
        "input": "Users receive email notifications when someone comments",
        "output": """FR-001: System SHALL send email notification when new comment is posted
FR-002: System SHALL include comment content in notification email
FR-003: System SHALL provide unsubscribe link in notification emails"""
    }
]

# Create few-shot template
example_prompt = ChatPromptTemplate.from_messages([
    ("human", "{input}"),
    ("ai", "{output}")
])

few_shot_prompt = FewShotChatMessagePromptTemplate(
    example_prompt=example_prompt,
    examples=examples
)

# Build final prompt with examples
final_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a requirements analyst. Extract functional requirements from user descriptions.

FORMAT: FR-XXX: System SHALL [specific capability]
RULES:
- Maximum 3 requirements per feature
- Each requirement must be testable
- No implementation details
- Use SHALL for mandatory requirements"""),
    few_shot_prompt,
    ("human", "{input}")
])

chain = final_prompt | llm

# Test with new input
test_input = "Users can search products by name and filter by category"
result = chain.invoke({"input": test_input})

print("Input:", test_input)
print("\nOutput:")
print(result.content)
```

### Example 2: Chain-of-Thought Reasoning

```python
"""
src/examples/ex11_chain_of_thought.py

Using CoT for better requirement analysis
"""

from langchain_anthropic import ChatAnthropic
from langchain.prompts import ChatPromptTemplate
from dotenv import load_dotenv

load_dotenv()

llm = ChatAnthropic(model="claude-3-5-sonnet-20241022", temperature=0)

# CoT Prompt
prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a requirements analyst. Extract functional requirements using step-by-step reasoning.

PROCESS:
1. ANALYZE: Read the feature description and identify key user actions
2. CATEGORIZE: Group related actions into logical requirements
3. VALIDATE: Ensure each requirement is testable and specific
4. FORMAT: Output as FR-XXX format

Show your reasoning for ANALYZE and CATEGORIZE steps, then provide the final requirements."""),
    ("user", "{description}")
])

chain = prompt | llm

# Test
description = """Build a comment system where users can post comments,
edit their own comments, delete their own comments, and reply to others' comments.
Show comment count for each post."""

result = chain.invoke({"description": description})
print(result.content)
```

### Example 3: Constraint-Based Generation (Spec-Kit Style)

```python
"""
src/examples/ex12_constraints.py

Strict constraint enforcement like Spec-Kit
"""

from langchain_anthropic import ChatAnthropic
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field, field_validator
from typing import List, Literal
from dotenv import load_dotenv

load_dotenv()

llm = ChatAnthropic(model="claude-3-5-sonnet-20241022", temperature=0)

# Strict Pydantic model with validators
class StrictRequirement(BaseModel):
    id: str = Field(pattern=r"^FR-\d{3}$")  # Must match FR-XXX
    type: Literal["SHALL", "MUST", "SHOULD"]
    subject: Literal["System", "User", "Administrator"]
    action: str = Field(min_length=10, max_length=100)
    testable: bool = Field(default=True)

    @field_validator('action')
    @classmethod
    def validate_no_tech_terms(cls, v: str) -> str:
        """Ensure no implementation details"""
        tech_terms = ['database', 'api', 'react', 'postgres', 'mongodb', 'aws', 'docker']
        lower_action = v.lower()
        for term in tech_terms:
            if term in lower_action:
                raise ValueError(f"Implementation detail detected: '{term}' in requirement")
        return v

class StrictRequirementSet(BaseModel):
    requirements: List[StrictRequirement] = Field(min_length=1, max_length=5)

# Create parser
parser = PydanticOutputParser(pydantic_object=StrictRequirementSet)

# Strict prompt with validation
prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a requirements analyst with STRICT formatting rules.

{format_instructions}

CRITICAL CONSTRAINTS:
1. IDs: MUST be FR-001 through FR-005 (sequential, zero-padded)
2. Type: Only SHALL (mandatory), MUST (required), or SHOULD (optional)
3. Subject: Only "System", "User", or "Administrator"
4. Action: 10-100 characters, describes WHAT not HOW
5. NO technology terms: database, API, React, PostgreSQL, MongoDB, AWS, Docker, etc.
6. Total: Maximum 5 requirements

VALIDATION BEFORE OUTPUT:
✓ Each ID follows FR-XXX pattern?
✓ Each uses SHALL/MUST/SHOULD?
✓ Each starts with System/User/Administrator?
✓ No tech terms in action?
✓ Total count ≤ 5?

If validation fails, revise until all constraints met."""),
    ("user", "Extract requirements:\n\n{description}")
])

prompt = prompt.partial(format_instructions=parser.get_format_instructions())

chain = prompt | llm | parser

# Test
description = "Build a user authentication system with login and password reset"

try:
    result = chain.invoke({"description": description})
    print("✓ All constraints satisfied!")
    for req in result.requirements:
        print(f"\n{req.id}: {req.subject} {req.type} {req.action}")
except Exception as e:
    print(f"✗ Constraint violation: {e}")
```

### Example 4: Constitutional AI Principles

```python
"""
src/examples/ex13_constitutional_ai.py

Applying constitutional principles (like Spec-Kit's constitution.md)
"""

from langchain_anthropic import ChatAnthropic
from langchain.prompts import ChatPromptTemplate
from dotenv import load_dotenv

load_dotenv()

llm = ChatAnthropic(model="claude-3-5-sonnet-20241022", temperature=0)

# Constitution (project principles)
constitution = """
PROJECT CONSTITUTION: SpecBot Requirements Standards

I. CLARITY PRINCIPLE
   All requirements MUST be unambiguous and specific.
   Vague terms ("good", "fast", "user-friendly") are PROHIBITED.

II. TESTABILITY PRINCIPLE
   All requirements MUST be independently testable.
   Requirements without clear acceptance criteria are INVALID.

III. TECHNOLOGY AGNOSTICISM
   Requirements MUST focus on WHAT, never HOW.
   Technology stack decisions belong in technical design, not requirements.

IV. USER-CENTRIC LANGUAGE
   Requirements MUST use user-focused language.
   System behavior described from user perspective.

V. TRACEABILITY
   All requirements MUST be uniquely identifiable (FR-XXX).
   Dependencies between requirements MUST be explicit.
"""

# Prompt with constitutional checking
prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a requirements analyst governed by strict principles.

{constitution}

PROCESS:
1. Extract requirements from user description
2. Validate each requirement against ALL constitutional principles
3. If any requirement violates a principle, revise it
4. Output only requirements that pass constitutional validation

FORMAT: FR-XXX: [Subject] [SHALL/MUST/SHOULD] [specific action]"""),
    ("user", "{description}")
])

prompt = prompt.partial(constitution=constitution)

chain = prompt | llm

# Test with intentionally problematic description
description = """Build a nice user authentication system that works fast.
Users should be able to log in easily using a React frontend with JWT tokens
stored in a PostgreSQL database."""

result = chain.invoke({"description": description})

print("Input (with violations):")
print(description)
print("\n" + "="*70)
print("Output (constitutionally compliant):")
print(result.content)
```

---

## 🏋️ Hands-On Exercise: Build SpecBot's Prompt Library

**Objective**: Create a reusable library of prompts following Spec-Kit patterns.

### Requirements

Build a prompt library with:
1. **Base requirement extractor** with few-shot examples
2. **Clarification question generator** (max 3 questions)
3. **Success criteria generator** (measurable, tech-agnostic)
4. **Validation checker** (ensures quality)

### Starter Code

Create `src/exercises/ex03_prompt_library.py`:

```python
"""
Exercise 3: SpecBot Prompt Library

Create reusable, high-quality prompts following Spec-Kit patterns
"""

from langchain_anthropic import ChatAnthropic
from langchain.prompts import ChatPromptTemplate, FewShotChatMessagePromptTemplate
from pydantic import BaseModel, Field
from typing import List
from dotenv import load_dotenv

load_dotenv()

llm = ChatAnthropic(model="claude-3-5-sonnet-20241022", temperature=0)

# TODO: Define Pydantic models for structured output

class Requirement(BaseModel):
    pass  # TODO: Complete

class ClarificationQuestion(BaseModel):
    pass  # TODO: Complete

class SuccessCriterion(BaseModel):
    pass  # TODO: Complete

# TODO: Create few-shot examples
requirement_examples = [
    # Add 3-5 high-quality examples
]

# TODO: Build RequirementExtractor prompt
requirement_prompt = ChatPromptTemplate.from_messages([
    ("system", """TODO: Your system prompt following Spec-Kit patterns

    RULES (from Spec-Kit):
    - Maximum 5 requirements
    - Format: FR-XXX
    - Testable and specific
    - No implementation details
    - Clear language

    EXAMPLES:
    {examples}
    """),
    ("user", "{description}")
])

# TODO: Build ClarificationGenerator prompt (like Spec-Kit's clarify.md)
clarification_prompt = ChatPromptTemplate.from_messages([
    ("system", """TODO: Generate clarification questions

    RULES (from Spec-Kit):
    - Maximum 3 questions total
    - Only high-impact questions
    - Present as multiple choice with suggested answer
    - Focus on scope, security, UX (in that priority)
    """),
    ("user", "Requirements:\n{requirements}\n\nGenerate clarification questions.")
])

# TODO: Build SuccessCriteriaGenerator (like Spec-Kit's success criteria)
success_criteria_prompt = ChatPromptTemplate.from_messages([
    ("system", """TODO: Generate success criteria

    RULES (from Spec-Kit):
    - Measurable outcomes
    - Technology-agnostic
    - User-focused
    - Objectively verifiable

    BAD: "API response time under 200ms"
    GOOD: "Users see search results in under 1 second"
    """),
    ("user", "Feature: {feature}\n\nRequirements:\n{requirements}\n\nGenerate success criteria.")
])

# TODO: Test your prompt library

test_input = """Build a file upload feature for images and PDFs.
Users should be able to drag and drop files, see upload progress,
and receive confirmation when upload completes."""

print("="*70)
print("TESTING PROMPT LIBRARY")
print("="*70)

# Test 1: Extract requirements
print("\n1. REQUIREMENT EXTRACTION")
print("-"*70)
# TODO: Run requirement extraction

# Test 2: Generate clarification questions
print("\n2. CLARIFICATION QUESTIONS")
print("-"*70)
# TODO: Run clarification generation

# Test 3: Generate success criteria
print("\n3. SUCCESS CRITERIA")
print("-"*70)
# TODO: Run success criteria generation
```

---

## 🚀 Challenge: Self-Improving Prompts

**Advanced**: Build a system that uses LLMs to improve their own prompts.

**Concept**:
1. Run prompt on test cases
2. Evaluate output quality
3. Ask LLM to suggest prompt improvements
4. Apply improvements
5. Re-test and measure improvement

### Challenge Template

```python
"""
src/exercises/ex03_self_improving.py

Meta-prompting: LLMs improving their own prompts
"""

from typing import List, Dict
import json

class PromptOptimizer:
    """Optimize prompts through iterative evaluation"""

    def __init__(self, llm):
        self.llm = llm
        self.history = []

    def evaluate_prompt(self, prompt: str, test_cases: List[Dict]) -> float:
        """Run prompt on test cases and score output quality"""
        # TODO: Implement evaluation logic
        pass

    def suggest_improvements(self, prompt: str, failures: List[Dict]) -> str:
        """Ask LLM to improve prompt based on failures"""
        # TODO: Implement meta-prompting
        pass

    def optimize(self, initial_prompt: str, test_cases: List[Dict], iterations: int = 3):
        """Iteratively improve prompt"""
        current_prompt = initial_prompt
        current_score = self.evaluate_prompt(current_prompt, test_cases)

        for i in range(iterations):
            print(f"\nIteration {i+1}")
            print(f"Current score: {current_score}")

            # Get failures
            failures = self.get_failures(current_prompt, test_cases)

            # Suggest improvements
            improved_prompt = self.suggest_improvements(current_prompt, failures)

            # Evaluate
            new_score = self.evaluate_prompt(improved_prompt, test_cases)

            if new_score > current_score:
                current_prompt = improved_prompt
                current_score = new_score
                print(f"✓ Improved to {new_score}")
            else:
                print("✗ No improvement, keeping previous prompt")

        return current_prompt, current_score

# TODO: Implement optimization loop
```

---

## 🎓 Key Takeaways

### Few-Shot Learning

**When to use**: Complex formats, domain-specific output, consistent style

**Best practices**:
- Use 3-5 examples (more isn't always better)
- Show diverse edge cases
- Include both good and bad examples
- Keep examples relevant to the task

### Chain-of-Thought

**When to use**: Complex analysis, multi-step reasoning, debugging

**Best practices**:
- Ask for explicit reasoning steps
- Use "Let's think step-by-step"
- Review reasoning before trusting output
- Combine with few-shot for best results

### Constraint-Based Generation

**When to use**: Strict format requirements, validation needs, production systems

**Best practices from Spec-Kit**:
- State constraints explicitly
- Use validation rules
- Provide examples of rule violations
- Build validation into Pydantic models

---

## 🔄 Story Progress: SpecBot v0.3

**What we built**: SpecBot now produces consistent, high-quality requirements using advanced prompt techniques!

```python
# SpecBot v0.3 - Advanced Prompting
from specbot import PromptLibrary

library = PromptLibrary()

# Extract with few-shot learning
requirements = library.extract_requirements(
    description="Build file upload feature",
    examples=few_shot_examples
)

# Generate clarification questions (max 3)
questions = library.generate_clarifications(
    requirements=requirements,
    max_questions=3
)

# Generate success criteria (measurable, tech-agnostic)
criteria = library.generate_success_criteria(
    feature="File Upload",
    requirements=requirements
)
```

**Quality Improvements**:
- ✅ Consistent output format
- ✅ Higher quality requirements
- ✅ Better edge case handling
- ✅ Constitutional compliance

**Next Step**: Lesson 4 introduces LangGraph for building multi-step workflows with state management!

---

## 📚 Additional Resources

- [Anthropic Prompt Engineering Guide](https://docs.anthropic.com/claude/docs/prompt-engineering)
- [OpenAI Prompt Engineering Best Practices](https://platform.openai.com/docs/guides/prompt-engineering)
- [Few-Shot Learning Paper](https://arxiv.org/abs/2005.14165)
- [Chain-of-Thought Prompting](https://arxiv.org/abs/2201.11903)

---

**Continue to [Lesson 4: Introduction to LangGraph & Simple Workflows →](./04-langgraph-intro.md)**
