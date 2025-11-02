# Lesson 2: Chains, Output Parsers & Structured Output

> **Story Context**: SpecBot now extracts requirements, but the output is unstructured text. To build a reliable system, we need structured, machine-readable output that can be validated and stored in a database. This lesson teaches you how to create chains and parse LLM outputs into structured formats.

---

## 🎯 Learning Objectives

By the end of this lesson, you will:

1. Understand LangChain chains and the LCEL syntax
2. Create multi-step processing pipelines
3. Use output parsers for structured data
4. Work with Pydantic models for validation
5. Handle parsing errors gracefully
6. Build SpecBot's structured requirement extractor

**Time**: ~2 hours

---

## 📖 Concept: Chains & LCEL

### What is a Chain?

A **chain** is a sequence of operations where the output of one step becomes the input of the next.

**Simple example**:
```python
# Without chains (manual piping)
prompt_result = prompt.format(input="...")
llm_result = llm.invoke(prompt_result)
parsed_result = parser.parse(llm_result)

# With chains (automatic piping)
chain = prompt | llm | parser
result = chain.invoke({"input": "..."})
```

### LCEL: LangChain Expression Language

**LCEL** is the syntax for composing chains using the pipe operator `|`.

```python
chain = component1 | component2 | component3
```

**Benefits**:
- **Readable**: Clear data flow from left to right
- **Composable**: Mix and match components
- **Async support**: Automatic async execution
- **Streaming**: Built-in streaming support
- **Debugging**: Easy to inspect intermediate steps

---

## 🔧 Core Concept: Output Parsers

### The Problem

LLMs return unstructured text:

```python
response = llm.invoke("Extract requirements")
# Output: "Here are the requirements:\n1. Users can log in\n2. ..."
```

To store in a database, we need structured data:

```python
{
    "requirements": [
        {"id": "FR-001", "description": "...", "priority": "P1"},
        {"id": "FR-002", "description": "...", "priority": "P2"}
    ]
}
```

### Output Parser Types

| Parser | Use Case | Example |
|--------|----------|---------|
| **StringOutputParser** | Simple text extraction | Plain string |
| **JsonOutputParser** | JSON objects | `{"key": "value"}` |
| **PydanticOutputParser** | Validated data models | Type-safe objects |
| **StructuredOutputParser** | Custom structures | Tables, lists |
| **CommaSeparatedListOutputParser** | Lists | `["item1", "item2"]` |

---

## 💡 Code Examples

### Example 1: Basic Chain with LCEL

```python
"""
src/examples/ex05_basic_chain.py

Simple chain: Prompt → LLM → String Parser
"""

from langchain_anthropic import ChatAnthropic
from langchain.prompts import ChatPromptTemplate
from langchain.schema.output_parser import StrOutputParser
from dotenv import load_dotenv

load_dotenv()

llm = ChatAnthropic(model="claude-3-5-sonnet-20241022", temperature=0)

# Create components
prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a concise technical writer."),
    ("user", "Define {term} in one sentence.")
])

output_parser = StrOutputParser()

# Compose chain using LCEL
chain = prompt | llm | output_parser

# Execute
result = chain.invoke({"term": "functional requirement"})
print(f"Result type: {type(result)}")
print(f"Result: {result}")
```

### Example 2: JSON Output Parser

```python
"""
src/examples/ex06_json_parser.py

Parsing JSON output from LLM
"""

from langchain_anthropic import ChatAnthropic
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import JsonOutputParser
from dotenv import load_dotenv
import json

load_dotenv()

llm = ChatAnthropic(model="claude-3-5-sonnet-20241022", temperature=0)

# Create JSON parser
json_parser = JsonOutputParser()

# Prompt with JSON format instructions
prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a requirements analyst. Extract requirements in JSON format.

Output Format:
{format_instructions}"""),
    ("user", "Extract requirements from: {description}")
])

# Add format instructions to prompt
prompt = prompt.partial(format_instructions=json_parser.get_format_instructions())

# Build chain
chain = prompt | llm | json_parser

# Test
description = """Build a user login system with email/password authentication.
Include password reset via email and account locking after 3 failed attempts."""

result = chain.invoke({"description": description})

print("Result type:", type(result))
print("\nParsed JSON:")
print(json.dumps(result, indent=2))
```

### Example 3: Pydantic Output Parser (Type-Safe)

```python
"""
src/examples/ex07_pydantic_parser.py

Type-safe parsing with Pydantic models
"""

from langchain_anthropic import ChatAnthropic
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from typing import List, Literal
from dotenv import load_dotenv

load_dotenv()

llm = ChatAnthropic(model="claude-3-5-sonnet-20241022", temperature=0)

# Define Pydantic models
class Requirement(BaseModel):
    id: str = Field(description="Requirement ID (e.g., FR-001)")
    type: Literal["functional", "non-functional"] = Field(description="Requirement type")
    priority: Literal["P1", "P2", "P3"] = Field(description="Priority level")
    description: str = Field(description="Clear, testable requirement statement")
    testable: bool = Field(description="Whether requirement is testable")

class RequirementSet(BaseModel):
    feature_name: str = Field(description="Name of the feature")
    requirements: List[Requirement] = Field(description="List of extracted requirements")
    total_count: int = Field(description="Total number of requirements")

# Create parser
pydantic_parser = PydanticOutputParser(pydantic_object=RequirementSet)

# Prompt with Pydantic schema
prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a requirements analyst. Extract requirements and return structured data.

{format_instructions}

Rules:
- Maximum 5 requirements
- Each must be testable
- Assign appropriate priority (P1=critical, P2=important, P3=nice-to-have)
- Use clear, specific language"""),
    ("user", "Feature: {feature_name}\n\nDescription: {description}")
])

# Add format instructions
prompt = prompt.partial(format_instructions=pydantic_parser.get_format_instructions())

# Build chain
chain = prompt | llm | pydantic_parser

# Test
result = chain.invoke({
    "feature_name": "User Authentication",
    "description": """Build a user login system with email/password authentication.
    Include password reset via email and account locking after 3 failed attempts."""
})

# Access typed data
print(f"Feature: {result.feature_name}")
print(f"Total Requirements: {result.total_count}\n")

for req in result.requirements:
    print(f"{req.id} [{req.priority}] ({req.type})")
    print(f"  {req.description}")
    print(f"  Testable: {req.testable}\n")
```

### Example 4: Multi-Step Chain Pipeline

```python
"""
src/examples/ex08_multi_step_chain.py

Complex chain with multiple processing steps
"""

from langchain_anthropic import ChatAnthropic
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from langchain.schema.runnable import RunnableLambda
from pydantic import BaseModel, Field
from typing import List
from dotenv import load_dotenv

load_dotenv()

llm = ChatAnthropic(model="claude-3-5-sonnet-20241022", temperature=0)

# Step 1: Extract requirements (Pydantic model)
class Requirement(BaseModel):
    id: str
    description: str
    priority: str

class Requirements(BaseModel):
    items: List[Requirement]

req_parser = PydanticOutputParser(pydantic_object=Requirements)

req_prompt = ChatPromptTemplate.from_messages([
    ("system", "Extract requirements.\n\n{format_instructions}"),
    ("user", "{description}")
]).partial(format_instructions=req_parser.get_format_instructions())

# Step 2: Validate each requirement (custom function)
def validate_requirements(requirements: Requirements) -> Requirements:
    """Custom validation logic"""
    for req in requirements.items:
        # Example: ensure description is not empty
        if not req.description.strip():
            raise ValueError(f"Empty description for {req.id}")

        # Example: ensure priority is valid
        if req.priority not in ["P1", "P2", "P3"]:
            req.priority = "P2"  # Default to P2

    return requirements

# Step 3: Enrich with additional metadata (another LLM call)
enrich_prompt = ChatPromptTemplate.from_messages([
    ("system", "For each requirement, suggest test scenarios."),
    ("user", "Requirements:\n{requirements}\n\nProvide test scenarios in JSON.")
])

# Build multi-step chain
extraction_chain = req_prompt | llm | req_parser
validation_step = RunnableLambda(validate_requirements)
enrichment_chain = enrich_prompt | llm

# Compose full pipeline
full_chain = extraction_chain | validation_step

# Execute
result = full_chain.invoke({
    "description": """Build a search feature where users can search by keyword,
    filter by category, and sort results by relevance or date."""
})

print("Extracted & Validated Requirements:")
for req in result.items:
    print(f"  {req.id} [{req.priority}]: {req.description}")
```

### Example 5: Error Handling in Chains

```python
"""
src/examples/ex09_error_handling.py

Handling parsing errors gracefully
"""

from langchain_anthropic import ChatAnthropic
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser, OutputFixingParser
from pydantic import BaseModel, Field
from typing import List
from dotenv import load_dotenv

load_dotenv()

llm = ChatAnthropic(model="claude-3-5-sonnet-20241022", temperature=0)

class SimpleRequirement(BaseModel):
    id: str = Field(description="Requirement ID")
    description: str = Field(description="Description")

class RequirementList(BaseModel):
    requirements: List[SimpleRequirement]

# Create base parser
base_parser = PydanticOutputParser(pydantic_object=RequirementList)

# Wrap with OutputFixingParser (auto-fixes errors)
fixing_parser = OutputFixingParser.from_llm(parser=base_parser, llm=llm)

prompt = ChatPromptTemplate.from_messages([
    ("system", "Extract requirements.\n\n{format_instructions}"),
    ("user", "{description}")
]).partial(format_instructions=base_parser.get_format_instructions())

# Try with regular parser
try:
    chain_regular = prompt | llm | base_parser
    result_regular = chain_regular.invoke({
        "description": "Build a login system"
    })
    print("✓ Regular parser succeeded")
    print(result_regular)
except Exception as e:
    print(f"✗ Regular parser failed: {e}")

# Try with fixing parser (handles malformed output)
try:
    chain_fixing = prompt | llm | fixing_parser
    result_fixing = chain_fixing.invoke({
        "description": "Build a login system"
    })
    print("\n✓ Fixing parser succeeded")
    print(result_fixing)
except Exception as e:
    print(f"✗ Fixing parser failed: {e}")
```

---

## 🏋️ Hands-On Exercise: Build Structured Requirement Extractor

**Objective**: Create a chain that extracts requirements with full validation and structured output.

### Requirements

Your chain should:
1. Extract requirements from natural language
2. Output structured data using Pydantic models
3. Include validation logic
4. Handle edge cases (empty input, invalid data)
5. Support different requirement types

### Data Models

```python
from pydantic import BaseModel, Field, field_validator
from typing import List, Literal, Optional
from datetime import datetime

class Requirement(BaseModel):
    """Single requirement with validation"""
    id: str = Field(description="Requirement ID (FR-XXX format)")
    type: Literal["functional", "non-functional", "business_rule"]
    priority: Literal["P1", "P2", "P3"]
    description: str = Field(min_length=10, description="Clear requirement statement")
    testable: bool = Field(description="Whether requirement is testable")
    dependencies: List[str] = Field(default=[], description="IDs of dependent requirements")

    @field_validator('id')
    @classmethod
    def validate_id_format(cls, v: str) -> str:
        """Ensure ID follows FR-XXX format"""
        import re
        if not re.match(r'^(FR|NFR|BR)-\d{3}$', v):
            raise ValueError(f"Invalid ID format: {v}. Expected FR-XXX, NFR-XXX, or BR-XXX")
        return v

    @field_validator('description')
    @classmethod
    def validate_description(cls, v: str) -> str:
        """Ensure description starts with System/User/SHALL/MUST"""
        keywords = ['System', 'User', 'SHALL', 'MUST', 'SHOULD']
        if not any(v.startswith(keyword) for keyword in keywords):
            raise ValueError(f"Description must start with one of: {keywords}")
        return v

class RequirementSpecification(BaseModel):
    """Complete requirement specification"""
    feature_name: str = Field(description="Name of the feature being specified")
    description: str = Field(description="Original user description")
    requirements: List[Requirement] = Field(description="Extracted requirements")
    total_count: int = Field(description="Total number of requirements")
    extracted_at: datetime = Field(default_factory=datetime.now)

    @field_validator('requirements')
    @classmethod
    def validate_requirement_count(cls, v: List[Requirement]) -> List[Requirement]:
        """Ensure reasonable number of requirements"""
        if len(v) > 10:
            raise ValueError(f"Too many requirements: {len(v)}. Maximum is 10.")
        if len(v) == 0:
            raise ValueError("No requirements extracted")
        return v
```

### Starter Code

Create `src/exercises/ex02_structured_extractor.py`:

```python
"""
Exercise 2: Structured Requirement Extractor

Build a complete chain with:
1. Structured output using Pydantic
2. Validation logic
3. Error handling
4. Type safety
"""

from langchain_anthropic import ChatAnthropic
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from dotenv import load_dotenv

# TODO: Import your Pydantic models here

load_dotenv()

llm = ChatAnthropic(model="claude-3-5-sonnet-20241022", temperature=0)

# TODO: Create Pydantic parser

# TODO: Create prompt template with format instructions

# TODO: Build chain: prompt | llm | parser

# TODO: Add custom validation step (RunnableLambda)

# TODO: Test with multiple scenarios

test_cases = [
    {
        "feature_name": "User Authentication",
        "description": """Build a secure user authentication system with:
        - Email/password login
        - Password strength validation
        - Account lockout after failed attempts
        - Password reset via email
        - Session management"""
    },
    {
        "feature_name": "Task Management",
        "description": """Create a task tracking system where:
        - Users create tasks with titles and descriptions
        - Tasks have due dates and priorities
        - Tasks can be assigned to team members
        - Users can filter tasks by status, assignee, and priority
        - Users receive notifications for approaching deadlines"""
    },
    {
        "feature_name": "File Upload",
        "description": """Implement file upload with support for images and PDFs.
        Maximum file size 10MB. Validate file types. Show upload progress."""
    }
]

# TODO: Run chain on each test case and display results
```

### Expected Output

```
Feature: User Authentication
================================================================================
Total Requirements: 5
Extracted at: 2024-01-15 10:30:00

FR-001 [P1] (functional) ✓ Testable
  System MUST authenticate users using email and password credentials

FR-002 [P1] (functional) ✓ Testable
  System MUST validate password strength according to defined criteria
  Dependencies: []

FR-003 [P1] (functional) ✓ Testable
  System MUST lock user accounts after 3 consecutive failed login attempts
  Dependencies: [FR-001]

FR-004 [P2] (functional) ✓ Testable
  System MUST provide password reset functionality via email verification
  Dependencies: [FR-001]

NFR-001 [P1] (non-functional) ✓ Testable
  System MUST maintain user sessions for a configurable timeout period
  Dependencies: [FR-001]

Validation: PASSED ✓
```

---

## 🚀 Challenge: Requirement Dependency Analyzer

**Advanced**: Build a chain that not only extracts requirements but also:

1. **Analyzes dependencies** between requirements
2. **Builds a dependency graph** (which requirements block others)
3. **Suggests implementation order** based on dependencies
4. **Detects circular dependencies** and warns the user

### Challenge Template

```python
"""
src/exercises/ex02_dependency_analyzer.py

Advanced: Analyze requirement dependencies and suggest order
"""

from pydantic import BaseModel
from typing import List, Dict, Set
import networkx as nx  # pip install networkx

class RequirementGraph(BaseModel):
    """Requirement dependency graph"""
    requirements: List[Requirement]
    adjacency_list: Dict[str, List[str]]  # req_id -> [dependent_req_ids]
    implementation_order: List[str]  # Topologically sorted
    circular_dependencies: List[List[str]]  # Any cycles detected

def build_dependency_graph(requirements: List[Requirement]) -> RequirementGraph:
    """Build graph and detect issues"""
    # TODO: Implement graph building
    # TODO: Use topological sort for implementation order
    # TODO: Detect cycles using DFS
    pass

# TODO: Integrate into your extraction chain
```

---

## 🎓 Key Takeaways

### LCEL Syntax

```python
# Simple chain
chain = prompt | llm | parser

# With custom logic
chain = prompt | llm | parser | RunnableLambda(custom_function)

# Parallel execution
chain = {
    "requirements": extraction_chain,
    "test_scenarios": test_chain
} | combiner_chain
```

### Output Parser Selection

- **Simple text**: `StrOutputParser()`
- **JSON objects**: `JsonOutputParser()`
- **Type-safe models**: `PydanticOutputParser(pydantic_object=Model)`
- **Auto-fixing**: `OutputFixingParser.from_llm()`
- **Custom parsing**: Implement `BaseOutputParser`

### Validation Best Practices

✅ **DO**:
- Use Pydantic field validators for constraints
- Provide clear error messages
- Use `OutputFixingParser` for production
- Test edge cases thoroughly
- Handle missing/malformed data gracefully

❌ **DON'T**:
- Trust LLM output without validation
- Ignore parsing errors
- Use overly complex nested models
- Forget to set `temperature=0` for consistency

---

## 🔄 Story Progress: SpecBot v0.2

**What we built**: SpecBot now returns structured, validated requirements!

```python
# SpecBot v0.2 - Structured Output
specbot = StructuredRequirementExtractor()
spec = specbot.extract("Build a login system")

# Access typed data
print(spec.feature_name)  # "User Authentication"
print(spec.requirements[0].id)  # "FR-001"
print(spec.requirements[0].priority)  # "P1"
print(spec.total_count)  # 5

# Store in database
db.save_specification(spec.model_dump())
```

**Next Step**: Lesson 3 will teach advanced prompt engineering techniques including few-shot learning, chain-of-thought, and constitutional AI principles.

---

## 📚 Additional Resources

- [LangChain LCEL Documentation](https://python.langchain.com/docs/expression_language/)
- [Output Parsers Guide](https://python.langchain.com/docs/modules/model_io/output_parsers/)
- [Pydantic Documentation](https://docs.pydantic.dev/)

---

**Continue to [Lesson 3: Advanced Prompt Engineering & Few-Shot Learning →](./03-advanced-prompts.md)**
