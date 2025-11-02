# Lesson 1: Introduction to LangChain & Basic Prompts

> **Story Context**: Before SpecBot can generate specifications, it needs to understand how to communicate with AI models effectively. In this lesson, you'll learn the foundational concepts of LangChain and create your first intelligent prompts.

---

## 🎯 Learning Objectives

By the end of this lesson, you will:

1. Understand what LangChain is and why it's useful
2. Set up a basic LangChain project
3. Create and execute simple prompts
4. Use prompt templates with variables
5. Work with different AI models (Claude, GPT)
6. Apply prompt engineering best practices

**Time**: ~2 hours

---

## 📖 Concept: What is LangChain?

**LangChain** is a framework for developing applications powered by language models. It provides:

- **Abstraction**: Common interface for different LLM providers (OpenAI, Anthropic, etc.)
- **Components**: Pre-built modules (prompts, chains, agents, memory)
- **Orchestration**: Tools to combine components into complex workflows
- **Utilities**: Parsers, validators, and helpers

### Why LangChain for SpecBot?

Building SpecBot without LangChain would require:
- Writing custom API clients for each LLM provider
- Managing prompt formatting manually
- Handling responses and parsing
- Reinventing common patterns

With LangChain, you get:
- ✅ Unified interface for all models
- ✅ Reusable prompt templates
- ✅ Built-in output parsing
- ✅ Battle-tested patterns

---

## 🏗️ Setup: Your First LangChain Project

### Step 1: Create Project Structure

```bash
mkdir specbot
cd specbot
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Create project structure
mkdir -p src/prompts src/chains src/workflows
touch src/__init__.py
touch .env
```

### Step 2: Install Dependencies

```bash
pip install langchain langchain-anthropic langchain-openai python-dotenv
```

### Step 3: Configure Environment

Create `.env`:
```bash
ANTHROPIC_API_KEY=sk-ant-xxxxx
# OR
OPENAI_API_KEY=sk-xxxxx
```

### Step 4: Test Installation

Create `src/test_setup.py`:

```python
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv()

# Test Anthropic
try:
    claude = ChatAnthropic(model="claude-3-5-sonnet-20241022")
    response = claude.invoke("Say 'LangChain is working!'")
    print("✓ Claude:", response.content)
except Exception as e:
    print("✗ Claude:", str(e))

# Test OpenAI (if you have key)
try:
    gpt = ChatOpenAI(model="gpt-4")
    response = gpt.invoke("Say 'LangChain is working!'")
    print("✓ GPT-4:", response.content)
except Exception as e:
    print("✗ GPT-4:", str(e))
```

Run it:
```bash
python src/test_setup.py
```

---

## 💡 Core Concept: Prompts & Templates

### The Problem with Hardcoded Prompts

**Bad approach**:
```python
# Don't do this!
response = llm.invoke(
    "Extract the requirements from this text: " + user_input
)
```

**Problems**:
- Can't reuse the prompt structure
- Hard to maintain and version control
- No validation or type safety
- Difficult to test

### The LangChain Way: Prompt Templates

**Good approach**:
```python
from langchain.prompts import ChatPromptTemplate

prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a requirements analyst. Extract functional requirements from user descriptions."),
    ("user", "Extract requirements from this: {user_description}")
])

chain = prompt | llm
response = chain.invoke({"user_description": user_input})
```

**Benefits**:
- ✅ Reusable template
- ✅ Variable substitution
- ✅ Version control friendly
- ✅ Testable

---

## 🔧 Code Examples

### Example 1: Basic Prompt Execution

```python
"""
src/examples/ex01_basic_prompt.py

Basic prompt execution with Claude
"""

from langchain_anthropic import ChatAnthropic
from dotenv import load_dotenv

load_dotenv()

# Initialize model
llm = ChatAnthropic(
    model="claude-3-5-sonnet-20241022",
    temperature=0  # Deterministic output
)

# Simple invoke
response = llm.invoke("What is a functional specification?")
print(response.content)
```

**Run it**:
```bash
python src/examples/ex01_basic_prompt.py
```

### Example 2: Prompt Templates with Variables

```python
"""
src/examples/ex02_prompt_template.py

Using prompt templates for reusable prompts
"""

from langchain_anthropic import ChatAnthropic
from langchain.prompts import ChatPromptTemplate
from dotenv import load_dotenv

load_dotenv()

llm = ChatAnthropic(model="claude-3-5-sonnet-20241022", temperature=0)

# Create a reusable template
template = ChatPromptTemplate.from_messages([
    ("system", """You are a technical writer specializing in {domain}.
    Your task is to create clear, concise documentation."""),
    ("user", "{task}")
])

# Use the template multiple times
scenarios = [
    {"domain": "API documentation", "task": "Explain what a REST API endpoint is"},
    {"domain": "user guides", "task": "Explain how to reset a password"},
    {"domain": "functional specifications", "task": "Explain what a user story is"}
]

for scenario in scenarios:
    chain = template | llm
    response = chain.invoke(scenario)
    print(f"\n{'='*60}")
    print(f"Domain: {scenario['domain']}")
    print(f"Task: {scenario['task']}")
    print(f"{'='*60}")
    print(response.content)
```

### Example 3: Multi-Turn Conversations

```python
"""
src/examples/ex03_multi_turn.py

Multi-turn conversations with message history
"""

from langchain_anthropic import ChatAnthropic
from langchain.schema import HumanMessage, AIMessage, SystemMessage
from dotenv import load_dotenv

load_dotenv()

llm = ChatAnthropic(model="claude-3-5-sonnet-20241022", temperature=0.7)

# Build conversation history
messages = [
    SystemMessage(content="You are a helpful specification assistant."),
    HumanMessage(content="I need to build a user authentication system."),
]

# First response
response1 = llm.invoke(messages)
print("Assistant:", response1.content)

# Add to history and continue
messages.extend([
    AIMessage(content=response1.content),
    HumanMessage(content="What functional requirements should I include?")
])

response2 = llm.invoke(messages)
print("\nAssistant:", response2.content)

# Add to history and continue
messages.extend([
    AIMessage(content=response2.content),
    HumanMessage(content="Format the first three as FR-001, FR-002, FR-003")
])

response3 = llm.invoke(messages)
print("\nAssistant:", response3.content)
```

### Example 4: System Prompts for Behavior Control

```python
"""
src/examples/ex04_system_prompts.py

Using system prompts to control AI behavior
"""

from langchain_anthropic import ChatAnthropic
from langchain.prompts import ChatPromptTemplate
from dotenv import load_dotenv

load_dotenv()

llm = ChatAnthropic(model="claude-3-5-sonnet-20241022", temperature=0)

# Different system prompts for different behaviors
behaviors = {
    "concise": """You are a concise technical writer.
    Respond in 1-2 sentences maximum. Be direct and precise.""",

    "detailed": """You are a detailed technical writer.
    Provide comprehensive explanations with examples and context.
    Break down complex concepts into digestible parts.""",

    "structured": """You are a structured technical writer.
    Always format your response as:
    1. Definition
    2. Key Components
    3. Example
    4. Best Practices"""
}

user_question = "What is a functional requirement?"

for style, system_prompt in behaviors.items():
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("user", "{question}")
    ])

    chain = prompt | llm
    response = chain.invoke({"question": user_question})

    print(f"\n{'='*60}")
    print(f"Style: {style}")
    print(f"{'='*60}")
    print(response.content)
```

---

## 🏋️ Hands-On Exercise: Build SpecBot's First Prompt

**Objective**: Create a reusable prompt template that extracts functional requirements from natural language descriptions.

### Requirements

Create a prompt template that:
1. Takes a user's natural language feature description
2. Extracts functional requirements in FR-XXX format
3. Makes requirements testable and specific
4. Limits output to 5 requirements maximum
5. Avoids implementation details (no tech stack mentions)

### Starter Code

Create `src/exercises/ex01_requirement_extractor.py`:

```python
"""
Exercise 1: Requirement Extractor

Create a prompt template that extracts functional requirements
from natural language descriptions.
"""

from langchain_anthropic import ChatAnthropic
from langchain.prompts import ChatPromptTemplate
from dotenv import load_dotenv

load_dotenv()

llm = ChatAnthropic(model="claude-3-5-sonnet-20241022", temperature=0)

# TODO: Create your prompt template here
# Hints:
# - Use ChatPromptTemplate.from_messages()
# - Include a system message that defines the AI's role
# - Include a user message with a {description} variable
# - Specify constraints (max 5 requirements, testable, no tech details)

prompt = ChatPromptTemplate.from_messages([
    ("system", """TODO: Your system prompt here

    Rules:
    - Extract maximum 5 functional requirements
    - Format as FR-001, FR-002, etc.
    - Each requirement must be testable
    - Focus on WHAT, not HOW (no implementation details)
    - Use clear, specific language
    """),
    ("user", "{description}")
])

# Test cases
test_descriptions = [
    """I want to build a user login system where users can sign in with
    their email and password. If they forget their password, they should
    be able to reset it via email. After 3 failed login attempts, their
    account should be temporarily locked for security.""",

    """Create a task management feature where users can create tasks,
    assign them to team members, set due dates, and mark them as complete.
    Users should be able to filter tasks by status and assignee.""",

    """Build a notification system that alerts users when they receive
    a new message, when someone mentions them, or when a task is assigned
    to them. Users should be able to customize which notifications they receive."""
]

# TODO: Run your prompt template on each test case
for i, description in enumerate(test_descriptions, 1):
    print(f"\n{'='*70}")
    print(f"Test Case {i}")
    print(f"{'='*70}")
    print(f"Input: {description[:100]}...")
    print(f"\nExtracted Requirements:")

    chain = prompt | llm
    response = chain.invoke({"description": description})
    print(response.content)
```

### Expected Output Format

```
Test Case 1
======================================================================
Input: I want to build a user login system where users can sign in...

Extracted Requirements:
FR-001: System MUST authenticate users using email and password
FR-002: System MUST provide password reset functionality via email
FR-003: System MUST lock accounts after 3 consecutive failed login attempts
FR-004: System MUST send password reset link to user's registered email
FR-005: System MUST unlock accounts after a specified time period or admin action
```

### Validation Checklist

Your solution should:
- [ ] Extract exactly 5 requirements (or fewer if fewer valid requirements exist)
- [ ] Format requirements as FR-XXX
- [ ] Make requirements testable (no vague language like "good", "nice", "user-friendly")
- [ ] Avoid implementation details (no mention of "database", "API", "React", etc.)
- [ ] Use clear, specific language ("MUST", "SHALL", "SHOULD")

---

## 🚀 Challenge: Advanced Requirement Extraction

**For advanced learners**: Extend your extractor to also:

1. **Categorize requirements** by type:
   - Functional (FR-XXX)
   - Non-functional (NFR-XXX) - performance, security, usability
   - Business Rules (BR-XXX)

2. **Assign priority** (P1, P2, P3) based on:
   - Security-related: P1
   - Core functionality: P1
   - User convenience: P2
   - Optional features: P3

3. **Identify dependencies** between requirements

### Challenge Solution Structure

```python
"""
src/exercises/ex01_advanced_extractor.py

Advanced requirement extraction with categorization and priorities
"""

from langchain_anthropic import ChatAnthropic
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from typing import List, Literal
from dotenv import load_dotenv

load_dotenv()

# Define structured output
class Requirement(BaseModel):
    id: str = Field(description="Requirement ID (e.g., FR-001, NFR-001)")
    type: Literal["functional", "non-functional", "business_rule"]
    priority: Literal["P1", "P2", "P3"]
    description: str = Field(description="Clear, testable requirement description")
    dependencies: List[str] = Field(default=[], description="IDs of requirements this depends on")

class RequirementSet(BaseModel):
    requirements: List[Requirement]

# TODO: Implement advanced extraction with structured output
# Hint: Use PydanticOutputParser for structured responses
```

---

## 🎓 Key Takeaways

1. **LangChain provides abstraction** over different LLM providers
2. **Prompt templates** make prompts reusable and maintainable
3. **System prompts** control AI behavior and output format
4. **Temperature controls** determinism vs creativity
5. **Message history** enables multi-turn conversations

### Prompt Engineering Best Practices

✅ **DO**:
- Use clear, specific language
- Provide examples (few-shot learning - covered in Lesson 3)
- Set explicit constraints (length, format, style)
- Use system prompts to define role and behavior
- Version control your prompts

❌ **DON'T**:
- Use vague language ("good", "nice", "better")
- Assume the model knows your context
- Forget to test with edge cases
- Hardcode prompts in application logic

---

## 🔄 Story Progress: SpecBot v0.1

**What we built**: SpecBot can now understand natural language and extract functional requirements!

```python
# SpecBot v0.1 - Requirement Extraction
specbot = RequirementExtractor()
requirements = specbot.extract("Build a login system with password reset")
# Output: [FR-001, FR-002, FR-003, ...]
```

**Next Step**: In Lesson 2, we'll learn to structure this output using output parsers and chains, making SpecBot's responses more reliable and machine-readable.

---

## 📝 Solution: Exercise 1

<details>
<summary>Click to reveal solution</summary>

```python
"""
Solution: src/exercises/ex01_requirement_extractor_solution.py
"""

from langchain_anthropic import ChatAnthropic
from langchain.prompts import ChatPromptTemplate
from dotenv import load_dotenv

load_dotenv()

llm = ChatAnthropic(model="claude-3-5-sonnet-20241022", temperature=0)

prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a requirements analyst specializing in functional specifications.

Your task: Extract functional requirements from natural language feature descriptions.

Rules:
1. Extract maximum 5 functional requirements
2. Format each as: FR-XXX: System MUST/SHALL/SHOULD [specific capability]
3. Each requirement MUST be testable and verifiable
4. Focus on WHAT the system must do, NOT HOW it's implemented
5. Avoid technology-specific details (no "database", "API", "React", etc.)
6. Use clear, unambiguous language
7. Each requirement should be independently understandable

Example:
Input: "Users can log in with email and password"
Output: FR-001: System MUST authenticate users using email and password credentials

Start numbering from FR-001 for each new feature description."""),
    ("user", "Extract functional requirements from this feature description:\n\n{description}")
])

# Test cases
test_descriptions = [
    """I want to build a user login system where users can sign in with
    their email and password. If they forget their password, they should
    be able to reset it via email. After 3 failed login attempts, their
    account should be temporarily locked for security.""",

    """Create a task management feature where users can create tasks,
    assign them to team members, set due dates, and mark them as complete.
    Users should be able to filter tasks by status and assignee.""",

    """Build a notification system that alerts users when they receive
    a new message, when someone mentions them, or when a task is assigned
    to them. Users should be able to customize which notifications they receive."""
]

for i, description in enumerate(test_descriptions, 1):
    print(f"\n{'='*70}")
    print(f"Test Case {i}")
    print(f"{'='*70}")
    print(f"Input: {description[:100]}...")
    print(f"\nExtracted Requirements:")

    chain = prompt | llm
    response = chain.invoke({"description": description})
    print(response.content)
```

</details>

---

## 📚 Additional Resources

- [LangChain Prompt Templates Documentation](https://python.langchain.com/docs/modules/model_io/prompts/)
- [Anthropic Prompt Engineering Guide](https://docs.anthropic.com/claude/docs/prompt-engineering)
- [OpenAI Prompt Engineering Guide](https://platform.openai.com/docs/guides/prompt-engineering)

---

## ✅ Self-Check Quiz

Before moving to Lesson 2, ensure you can answer:

1. What are the three types of messages in a ChatPromptTemplate?
2. What's the difference between temperature 0 and temperature 1?
3. How do you pass variables to a prompt template?
4. Why use prompt templates instead of string concatenation?
5. What's the purpose of a system message?

<details>
<summary>Click for answers</summary>

1. **SystemMessage** (defines behavior), **HumanMessage** (user input), **AIMessage** (assistant response)
2. **Temperature 0** = deterministic, same input → same output. **Temperature 1** = creative, varied outputs
3. Use `chain.invoke({"variable_name": value})` with `{variable_name}` in the template
4. Reusability, version control, testability, maintainability, separation of concerns
5. System messages define the AI's role, behavior, constraints, and output format

</details>

---

**Ready for more? Continue to [Lesson 2: Chains, Output Parsers & Structured Output →](./02-chains-output-parsers.md)**
