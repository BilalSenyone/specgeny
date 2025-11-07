# Lesson 10: Context7 & Progressive Disclosure

> **Story Context**: SpecBot needs to analyze massive documents (100+ pages) but LLM context windows have limits. Loading everything upfront is slow and expensive. This lesson teaches Context7 - a pattern for progressively loading context only when needed, making SpecBot fast and efficient even with huge specifications.

---

## 🎯 Learning Objectives

By the end of this lesson, you will:

1. Understand progressive context loading patterns
2. Implement Context7 "levels" of detail
3. Build demand-driven context expansion
4. Create summary-first exploration workflows
5. Optimize token usage for large documents
6. Design efficient multi-document workflows

**Time**: ~3 hours

---

## 📖 Key Concepts

### The Context Problem

**Traditional approach (inefficient)**:
```python
# Load entire 100-page document into context
context = load_entire_document()  # 50,000 tokens
llm.invoke(context + prompt)      # Expensive, slow
```

**Problems**:
- 🐌 Slow: Reading 50k tokens takes time
- 💸 Expensive: Costs 10x more
- 🎯 Unfocused: 90% of context is irrelevant
- 🚫 Limited: Some docs exceed context window

### Context7: Progressive Disclosure

**Smart approach**:
```
Level 0: Metadata only (50 tokens)
Level 1: Summary (500 tokens)
Level 2: Section titles (1000 tokens)
Level 3: Section summaries (5000 tokens)
Level 4: Full sections (20000 tokens)
Level 5: Full sections with examples (40000 tokens)
Level 6: Full document with appendices (80000 tokens)
Level 7: Full document + related docs (150000 tokens)
```

**Load context progressively**:
1. Start with Level 0 (metadata)
2. Agent decides what it needs
3. Expand specific sections to higher levels
4. Stop when sufficient information gathered

### When to Use Context7

✅ **Good for**:
- Large documents (>10 pages)
- Multi-document analysis
- Exploratory workflows
- Cost-sensitive applications

❌ **Not needed for**:
- Small documents (<5 pages)
- When you need full context anyway
- Simple extraction tasks

---

## 💻 Code Examples

### Example 1: Basic Context7 Structure

```python
"""
src/examples/ex33_context7_basic.py

Implement basic Context7 levels
"""

from typing import TypedDict, List, Literal
from langgraph.graph import StateGraph, START, END

class Context7State(TypedDict):
    document_id: str
    current_level: int
    context: dict  # Hierarchical context
    question: str
    answer: str
    needs_more_context: bool

class DocumentContext:
    """Hierarchical document context"""

    def __init__(self, document_path: str):
        self.document_path = document_path
        self.cache = {}

    def get_level_0(self) -> dict:
        """Level 0: Metadata only"""
        return {
            "title": "User Authentication System Specification",
            "version": "2.1",
            "pages": 45,
            "sections": 12,
            "last_modified": "2024-01-15"
        }

    def get_level_1(self) -> dict:
        """Level 1: Executive summary"""
        return {
            **self.get_level_0(),
            "summary": (
                "Specification for user authentication system supporting "
                "email/password, OAuth, and MFA. Covers requirements, "
                "architecture, security, and testing."
            )
        }

    def get_level_2(self) -> dict:
        """Level 2: Section titles"""
        return {
            **self.get_level_1(),
            "sections": [
                {"id": "1", "title": "Introduction"},
                {"id": "2", "title": "Functional Requirements"},
                {"id": "3", "title": "Non-Functional Requirements"},
                {"id": "4", "title": "Security Requirements"},
                {"id": "5", "title": "Architecture"},
                {"id": "6", "title": "Testing Strategy"},
            ]
        }

    def get_level_3(self, section_id: str = None) -> dict:
        """Level 3: Section summaries"""
        level_2 = self.get_level_2()

        # Add summaries to sections
        for section in level_2["sections"]:
            section["summary"] = f"Summary of {section['title']}..."

        if section_id:
            # Return specific section only
            section = next(s for s in level_2["sections"] if s["id"] == section_id)
            return {**level_2, "sections": [section]}

        return level_2

    def get_level_4(self, section_id: str) -> dict:
        """Level 4: Full section content"""
        return {
            "section_id": section_id,
            "title": "Functional Requirements",
            "content": """
                FR-001: The system SHALL authenticate users via email/password
                FR-002: The system SHALL support OAuth 2.0 providers
                FR-003: The system SHALL implement MFA with TOTP
                ...
                [Full section content ~2000 tokens]
            """
        }

def determine_initial_level(state: Context7State) -> Context7State:
    """Start with Level 1 (summary)"""
    doc = DocumentContext(state["document_id"])
    context = doc.get_level_1()

    return {
        "current_level": 1,
        "context": context
    }

def answer_question(state: Context7State) -> Context7State:
    """Try to answer with current context"""
    question = state["question"]
    context = state["context"]

    # Simple heuristic: check if context has relevant info
    if question.lower() in str(context).lower():
        answer = f"Based on Level {state['current_level']} context: [answer]"
        needs_more = False
    else:
        answer = "Need more context to answer"
        needs_more = True

    return {
        "answer": answer,
        "needs_more_context": needs_more
    }

def expand_context(state: Context7State) -> Context7State:
    """Expand to next level"""
    doc = DocumentContext(state["document_id"])
    next_level = state["current_level"] + 1

    print(f"Expanding context to Level {next_level}...")

    if next_level == 2:
        context = doc.get_level_2()
    elif next_level == 3:
        context = doc.get_level_3()
    elif next_level == 4:
        # In production, LLM decides which section to expand
        context = doc.get_level_4(section_id="2")
    else:
        context = state["context"]  # No more levels

    return {
        "current_level": next_level,
        "context": context
    }

def check_if_answered(state: Context7State) -> Literal["answered", "expand", "failed"]:
    """Route based on whether question is answered"""
    if not state["needs_more_context"]:
        return "answered"
    elif state["current_level"] < 4:
        return "expand"
    else:
        return "failed"

# Build workflow
workflow = StateGraph(Context7State)
workflow.add_node("init", determine_initial_level)
workflow.add_node("answer", answer_question)
workflow.add_node("expand", expand_context)

workflow.add_edge(START, "init")
workflow.add_edge("init", "answer")
workflow.add_conditional_edges(
    "answer",
    check_if_answered,
    {
        "answered": END,
        "expand": "expand",
        "failed": END
    }
)
workflow.add_edge("expand", "answer")

app = workflow.compile()

# Test
result = app.invoke({
    "document_id": "spec_001",
    "current_level": 0,
    "context": {},
    "question": "What are the functional requirements?",
    "answer": "",
    "needs_more_context": True
})

print(f"Final level: {result['current_level']}")
print(f"Answer: {result['answer']}")
```

### Example 2: LLM-Driven Context Expansion

```python
"""
src/examples/ex34_llm_context_expansion.py

Let LLM decide what context to load
"""

from typing import TypedDict, List
from langgraph.graph import StateGraph, START, END
from langchain_anthropic import ChatAnthropic
from langchain.prompts import ChatPromptTemplate

class SmartContextState(TypedDict):
    question: str
    available_sections: List[dict]
    loaded_sections: List[str]
    context_data: str
    answer: str
    complete: bool

def show_table_of_contents(state: SmartContextState) -> SmartContextState:
    """Show available sections"""
    sections = [
        {"id": "intro", "title": "Introduction", "pages": 3},
        {"id": "func_req", "title": "Functional Requirements", "pages": 12},
        {"id": "nfr", "title": "Non-Functional Requirements", "pages": 8},
        {"id": "arch", "title": "Architecture", "pages": 15},
        {"id": "security", "title": "Security", "pages": 10},
        {"id": "test", "title": "Testing", "pages": 7},
    ]

    return {"available_sections": sections}

def llm_choose_sections(state: SmartContextState) -> SmartContextState:
    """LLM decides which sections to load"""
    llm = ChatAnthropic(model="claude-3-5-sonnet-20241022", temperature=0)

    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are analyzing a specification document.
        Given a question and table of contents, identify which sections
        are most relevant to answer the question.

        Respond with a JSON array of section IDs to load.
        Example: ["func_req", "security"]

        Be selective - only load sections you actually need."""),
        ("user", """Question: {question}

        Available sections:
        {sections}

        Which sections should I load?""")
    ])

    sections_str = "\n".join(
        f"- {s['id']}: {s['title']} ({s['pages']} pages)"
        for s in state["available_sections"]
    )

    response = llm.invoke(
        prompt.format_messages(
            question=state["question"],
            sections=sections_str
        )
    )

    # Parse response (simplified - use JSON parser in production)
    import json
    sections_to_load = json.loads(response.content)

    return {"loaded_sections": sections_to_load}

def load_section_content(state: SmartContextState) -> SmartContextState:
    """Load actual section content"""
    section_content = {
        "intro": "This document specifies the user authentication system...",
        "func_req": """
            FR-001: System SHALL authenticate via email/password
            FR-002: System SHALL support OAuth 2.0
            FR-003: System SHALL implement MFA with TOTP
            ...[Full functional requirements]
        """,
        "security": """
            SEC-001: Passwords SHALL be hashed with bcrypt
            SEC-002: Session tokens SHALL expire after 24 hours
            ...[Full security requirements]
        """,
    }

    # Load requested sections
    context = "\n\n".join(
        f"=== {section_id.upper()} ===\n{section_content.get(section_id, '[Not available]')}"
        for section_id in state["loaded_sections"]
    )

    return {"context_data": context}

def answer_with_context(state: SmartContextState) -> SmartContextState:
    """Answer question using loaded context"""
    llm = ChatAnthropic(model="claude-3-5-sonnet-20241022", temperature=0)

    prompt = ChatPromptTemplate.from_messages([
        ("system", "Answer the question using only the provided context."),
        ("user", """Context:
        {context}

        Question: {question}

        Answer:""")
    ])

    response = llm.invoke(
        prompt.format_messages(
            context=state["context_data"],
            question=state["question"]
        )
    )

    return {
        "answer": response.content,
        "complete": True
    }

# Build workflow
workflow = StateGraph(SmartContextState)
workflow.add_node("toc", show_table_of_contents)
workflow.add_node("choose", llm_choose_sections)
workflow.add_node("load", load_section_content)
workflow.add_node("answer", answer_with_context)

workflow.add_edge(START, "toc")
workflow.add_edge("toc", "choose")
workflow.add_edge("choose", "load")
workflow.add_edge("load", "answer")
workflow.add_edge("answer", END)

app = workflow.compile()

# Test
result = app.invoke({
    "question": "What are the authentication methods supported?",
    "available_sections": [],
    "loaded_sections": [],
    "context_data": "",
    "answer": "",
    "complete": False
})

print(f"Loaded sections: {result['loaded_sections']}")
print(f"Answer: {result['answer']}")
```

### Example 3: Section-by-Section Progressive Loading

```python
"""
src/examples/ex35_progressive_loading.py

Load document sections progressively based on relevance
"""

from typing import TypedDict, List, Annotated
import operator

class ProgressiveState(TypedDict):
    question: str
    sections_loaded: Annotated[List[str], operator.add]
    context_so_far: str
    confidence: float
    max_sections: int

def load_next_section(state: ProgressiveState) -> ProgressiveState:
    """Load next most relevant section"""
    sections_available = ["intro", "requirements", "architecture", "testing"]
    loaded = state["sections_loaded"]

    # Find next unloaded section
    next_section = next(
        (s for s in sections_available if s not in loaded),
        None
    )

    if not next_section:
        return state

    # Load section content
    section_content = f"[Content of {next_section} section...]"

    return {
        "sections_loaded": [next_section],
        "context_so_far": state["context_so_far"] + "\n" + section_content
    }

def assess_confidence(state: ProgressiveState) -> ProgressiveState:
    """Assess if we have enough context to answer"""
    # In production, use LLM to assess confidence
    # For now, simple heuristic
    confidence = min(len(state["sections_loaded"]) * 0.3, 1.0)

    return {"confidence": confidence}

def should_load_more(state: ProgressiveState) -> str:
    """Decide if we need more context"""
    if state["confidence"] >= 0.8:
        return "sufficient"
    elif len(state["sections_loaded"]) >= state["max_sections"]:
        return "max_reached"
    else:
        return "load_more"

# Build workflow
workflow = StateGraph(ProgressiveState)
workflow.add_node("load", load_next_section)
workflow.add_node("assess", assess_confidence)

workflow.add_edge(START, "load")
workflow.add_edge("load", "assess")
workflow.add_conditional_edges(
    "assess",
    should_load_more,
    {
        "load_more": "load",
        "sufficient": END,
        "max_reached": END
    }
)

app = workflow.compile()

# Test
result = app.invoke({
    "question": "What are the system requirements?",
    "sections_loaded": [],
    "context_so_far": "",
    "confidence": 0.0,
    "max_sections": 3
})

print(f"Sections loaded: {result['sections_loaded']}")
print(f"Final confidence: {result['confidence']}")
```

---

## 🏋️ Hands-On Exercise: Smart Document Explorer

**Objective**: Build a system that intelligently explores large documents, loading only relevant sections.

### Requirements

Create a workflow that:
1. Starts with document table of contents
2. Uses LLM to identify relevant sections for a query
3. Loads sections progressively (most relevant first)
4. Stops loading when confidence threshold reached
5. Tracks tokens loaded vs tokens saved
6. Provides "drill down" capability for subsections

### Starter Code

Create `src/exercises/ex10_smart_explorer.py`:

```python
"""
Exercise 10: Smart Document Explorer

Progressive context loading with relevance scoring
"""

from typing import TypedDict, List, Annotated
from langgraph.graph import StateGraph, START, END
import operator

class ExplorerState(TypedDict):
    query: str
    document_structure: dict
    loaded_sections: Annotated[List[dict], operator.add]
    total_tokens_loaded: int
    confidence_score: float
    exploration_path: Annotated[List[str], operator.add]

# TODO: Implement DocumentStructure class
class DocumentStructure:
    """Hierarchical document structure"""

    def get_toc(self) -> dict:
        """Get table of contents with metadata"""
        pass

    def get_section_summary(self, section_id: str) -> str:
        """Get summary of section (Level 2)"""
        pass

    def get_section_content(self, section_id: str) -> str:
        """Get full section content (Level 3)"""
        pass

    def get_subsection(self, section_id: str, subsection_id: str) -> str:
        """Get specific subsection (Level 4)"""
        pass

# TODO: Implement relevance scoring
def score_section_relevance(section: dict, query: str) -> float:
    """Score how relevant a section is to the query"""
    # Use LLM to score relevance
    pass

# TODO: Implement nodes
# 1. analyze_query - Understand what query is asking
# 2. identify_relevant_sections - Score all sections
# 3. load_top_section - Load most relevant unloaded section
# 4. assess_confidence - Check if we can answer query
# 5. answer_query - Generate answer from loaded context

# TODO: Build workflow

# Test
test_queries = [
    "What authentication methods are supported?",
    "How is the database architected?",
    "What are the performance requirements?"
]
```

<details>
<summary>📝 <strong>Solution: Smart Document Explorer</strong></summary>

```python
"""
Solution: Smart Document Explorer

Progressive context loading with relevance scoring and confidence assessment
"""

from typing import TypedDict, List, Annotated, Literal
from langgraph.graph import StateGraph, START, END
from langchain_anthropic import ChatAnthropic
from langchain.prompts import ChatPromptTemplate
import operator
import json

class ExplorerState(TypedDict):
    query: str
    document_structure: dict
    loaded_sections: Annotated[List[dict], operator.add]
    total_tokens_loaded: int
    confidence_score: float
    exploration_path: Annotated[List[str], operator.add]
    answer: str

class DocumentStructure:
    """Hierarchical document structure with token tracking"""

    def __init__(self):
        self.sections = {
            "intro": {
                "id": "intro",
                "title": "Introduction",
                "summary": "Overview of the authentication system and its goals",
                "tokens": 150,
                "subsections": ["overview", "scope", "audience"],
                "content": """
# Introduction

This specification defines a comprehensive user authentication system
supporting multiple authentication methods including email/password,
OAuth 2.0, and multi-factor authentication (MFA).

The system is designed to be secure, scalable, and user-friendly.
                """.strip()
            },
            "auth_methods": {
                "id": "auth_methods",
                "title": "Authentication Methods",
                "summary": "Details on email/password, OAuth, and MFA support",
                "tokens": 2500,
                "subsections": ["email_password", "oauth", "mfa"],
                "content": """
# Authentication Methods

## Email/Password Authentication
- Users can register with email and password
- Passwords must meet complexity requirements
- Passwords hashed with bcrypt (cost factor 12)

## OAuth 2.0 Support
- Support for Google, GitHub, Microsoft providers
- PKCE flow for mobile/SPA applications
- Token refresh and revocation

## Multi-Factor Authentication
- TOTP-based (Time-based One-Time Password)
- SMS backup codes
- Recovery codes (10 single-use codes)
                """.strip()
            },
            "requirements": {
                "id": "requirements",
                "title": "Functional Requirements",
                "summary": "Complete list of functional requirements",
                "tokens": 3000,
                "subsections": ["user_mgmt", "session_mgmt", "security"],
                "content": """
# Functional Requirements

FR-001: The system SHALL authenticate users via email/password
FR-002: The system SHALL support OAuth 2.0 providers (Google, GitHub, Microsoft)
FR-003: The system SHALL implement MFA with TOTP
FR-004: The system SHALL hash passwords with bcrypt (cost factor 12)
FR-005: The system SHALL enforce password complexity requirements
FR-006: The system SHALL implement session management with 24-hour expiry
FR-007: The system SHALL provide password reset functionality
FR-008: The system SHALL log all authentication events
                """.strip()
            },
            "architecture": {
                "id": "architecture",
                "title": "System Architecture",
                "summary": "High-level architecture and component design",
                "tokens": 4000,
                "subsections": ["components", "database", "api"],
                "content": """
# System Architecture

## Components
- Authentication Service (Node.js/Express)
- Token Service (JWT generation/validation)
- User Service (User CRUD operations)
- Session Store (Redis)

## Database Schema
- Users table (id, email, password_hash, created_at)
- OAuth accounts table (user_id, provider, provider_id)
- MFA configs table (user_id, secret, backup_codes)
- Sessions table (session_id, user_id, expires_at)

## API Endpoints
POST /auth/register
POST /auth/login
POST /auth/logout
POST /auth/refresh
GET /auth/oauth/:provider
POST /auth/mfa/enable
POST /auth/mfa/verify
                """.strip()
            },
            "security": {
                "id": "security",
                "title": "Security Requirements",
                "summary": "Security controls and compliance requirements",
                "tokens": 2000,
                "subsections": ["encryption", "compliance", "audit"],
                "content": """
# Security Requirements

SEC-001: All passwords SHALL be hashed with bcrypt
SEC-002: Session tokens SHALL expire after 24 hours
SEC-003: API endpoints SHALL use HTTPS only
SEC-004: Rate limiting SHALL be applied (5 login attempts per minute)
SEC-005: Sensitive data SHALL be encrypted at rest
SEC-006: Audit logs SHALL be retained for 90 days
SEC-007: OAuth tokens SHALL be stored encrypted
                """.strip()
            }
        }

    def get_toc(self) -> dict:
        """Get table of contents with metadata"""
        return {
            "title": "User Authentication System Specification",
            "version": "2.1",
            "total_tokens": sum(s["tokens"] for s in self.sections.values()),
            "sections": [
                {
                    "id": s["id"],
                    "title": s["title"],
                    "summary": s["summary"],
                    "tokens": s["tokens"],
                    "subsections": s["subsections"]
                }
                for s in self.sections.values()
            ]
        }

    def get_section_summary(self, section_id: str) -> str:
        """Get summary of section (Level 2)"""
        if section_id not in self.sections:
            return None
        return self.sections[section_id]["summary"]

    def get_section_content(self, section_id: str) -> str:
        """Get full section content (Level 3)"""
        if section_id not in self.sections:
            return None
        return self.sections[section_id]["content"]

    def get_subsection(self, section_id: str, subsection_id: str) -> str:
        """Get specific subsection (Level 4)"""
        if section_id not in self.sections:
            return None
        # Simplified - in production, would parse actual subsections
        return f"[Detailed content of {subsection_id} subsection]"

    def get_section_tokens(self, section_id: str) -> int:
        """Get token count for section"""
        if section_id not in self.sections:
            return 0
        return self.sections[section_id]["tokens"]

# Document instance
doc = DocumentStructure()

def analyze_query(state: ExplorerState) -> ExplorerState:
    """Understand what the query is asking for"""
    print(f"\nAnalyzing query: {state['query']}")

    # Get table of contents
    toc = doc.get_toc()

    return {
        "document_structure": toc,
        "exploration_path": ["analyze_query"]
    }

def identify_relevant_sections(state: ExplorerState) -> ExplorerState:
    """Score all sections by relevance to query"""
    llm = ChatAnthropic(model="claude-3-5-sonnet-20241022", temperature=0)

    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are analyzing document structure to identify relevant sections.
        Given a user query and document table of contents, score each section's relevance.

        Respond with a JSON array of objects with 'id' and 'relevance_score' (0.0-1.0).
        Order by relevance score descending.

        Example: [{"id": "auth_methods", "score": 0.9}, {"id": "security", "score": 0.6}]"""),
        ("user", """Query: {query}

        Document sections:
        {sections}

        Score each section's relevance:""")
    ])

    sections_str = "\n".join(
        f"- {s['id']}: {s['title']} - {s['summary']} ({s['tokens']} tokens)"
        for s in state["document_structure"]["sections"]
    )

    response = llm.invoke(
        prompt.format_messages(
            query=state["query"],
            sections=sections_str
        )
    )

    # Parse scores
    try:
        scores = json.loads(response.content)
        print(f"\nRelevance scores:")
        for score in scores:
            print(f"  {score['id']}: {score['score']:.2f}")

        return {
            "section_scores": scores,
            "exploration_path": ["identify_relevant_sections"]
        }
    except:
        return {"section_scores": [], "exploration_path": ["identify_relevant_sections"]}

def load_top_section(state: ExplorerState) -> ExplorerState:
    """Load most relevant unloaded section"""
    loaded_ids = [s["id"] for s in state.get("loaded_sections", [])]
    scores = state.get("section_scores", [])

    # Find highest scoring unloaded section
    next_section = next(
        (s for s in scores if s["id"] not in loaded_ids),
        None
    )

    if not next_section:
        print("\nNo more sections to load")
        return {"exploration_path": ["load_top_section_none"]}

    section_id = next_section["id"]
    content = doc.get_section_content(section_id)
    tokens = doc.get_section_tokens(section_id)

    print(f"\nLoading section: {section_id} ({tokens} tokens)")

    section_data = {
        "id": section_id,
        "content": content,
        "tokens": tokens,
        "relevance_score": next_section["score"]
    }

    return {
        "loaded_sections": [section_data],
        "total_tokens_loaded": state.get("total_tokens_loaded", 0) + tokens,
        "exploration_path": [f"load_{section_id}"]
    }

def assess_confidence(state: ExplorerState) -> ExplorerState:
    """Check if we can answer query with loaded context"""
    llm = ChatAnthropic(model="claude-3-5-sonnet-20241022", temperature=0)

    loaded_content = "\n\n".join(
        f"=== {s['id']} ===\n{s['content']}"
        for s in state.get("loaded_sections", [])
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", """Assess if you can answer the query with the provided context.

        Respond with a JSON object:
        {
          "can_answer": true/false,
          "confidence": 0.0-1.0,
          "missing_info": "what additional information is needed (if any)"
        }"""),
        ("user", """Query: {query}

        Loaded context:
        {context}

        Assessment:""")
    ])

    response = llm.invoke(
        prompt.format_messages(
            query=state["query"],
            context=loaded_content
        )
    )

    try:
        assessment = json.loads(response.content)
        confidence = assessment.get("confidence", 0.0)

        print(f"\nConfidence: {confidence:.2f}")
        if not assessment.get("can_answer"):
            print(f"Missing: {assessment.get('missing_info')}")

        return {
            "confidence_score": confidence,
            "can_answer": assessment.get("can_answer", False),
            "exploration_path": ["assess_confidence"]
        }
    except:
        return {
            "confidence_score": 0.5,
            "can_answer": False,
            "exploration_path": ["assess_confidence_error"]
        }

def answer_query(state: ExplorerState) -> ExplorerState:
    """Generate answer from loaded context"""
    llm = ChatAnthropic(model="claude-3-5-sonnet-20241022", temperature=0)

    loaded_content = "\n\n".join(
        f"=== {s['id']} ===\n{s['content']}"
        for s in state.get("loaded_sections", [])
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", "Answer the question using only the provided context. Be specific and cite sections."),
        ("user", """Context:
        {context}

        Question: {query}

        Answer:""")
    ])

    response = llm.invoke(
        prompt.format_messages(
            context=loaded_content,
            query=state["query"]
        )
    )

    return {
        "answer": response.content,
        "exploration_path": ["answer_query"]
    }

def check_progress(state: ExplorerState) -> Literal["answer", "load_more", "max_reached"]:
    """Decide next step"""
    confidence = state.get("confidence_score", 0.0)
    tokens_loaded = state.get("total_tokens_loaded", 0)
    can_answer = state.get("can_answer", False)

    # Confidence threshold reached
    if can_answer or confidence >= 0.8:
        return "answer"

    # Too many tokens loaded
    if tokens_loaded >= 8000:
        print("\nMax token budget reached")
        return "max_reached"

    # Load more context
    return "load_more"

# Build workflow
workflow = StateGraph(ExplorerState)
workflow.add_node("analyze", analyze_query)
workflow.add_node("identify", identify_relevant_sections)
workflow.add_node("load", load_top_section)
workflow.add_node("assess", assess_confidence)
workflow.add_node("answer", answer_query)

workflow.add_edge(START, "analyze")
workflow.add_edge("analyze", "identify")
workflow.add_edge("identify", "load")
workflow.add_edge("load", "assess")
workflow.add_conditional_edges(
    "assess",
    check_progress,
    {
        "answer": "answer",
        "load_more": "load",
        "max_reached": "answer"
    }
)
workflow.add_edge("answer", END)

app = workflow.compile()

# Test
test_queries = [
    "What authentication methods are supported?",
    "How is the database architected?",
    "What are the security requirements?"
]

for query in test_queries:
    print(f"\n{'='*70}")
    print(f"Query: {query}")
    print('='*70)

    result = app.invoke({
        "query": query,
        "document_structure": {},
        "loaded_sections": [],
        "total_tokens_loaded": 0,
        "confidence_score": 0.0,
        "exploration_path": [],
        "answer": ""
    })

    print(f"\n{'='*70}")
    print("Results:")
    print(f"  Sections loaded: {[s['id'] for s in result['loaded_sections']]}")
    print(f"  Total tokens: {result['total_tokens_loaded']}")
    print(f"  Confidence: {result['confidence_score']:.2f}")
    print(f"\nAnswer:\n{result['answer']}")
    print('='*70)
```

</details>

---

## 🚀 Challenge: Adaptive Context Budget

**Advanced**: Implement a system that adapts context loading based on available token budget.

### Challenge Requirements

Build a system that:
1. **Tracks token budget** (e.g., 10k tokens available)
2. **Prioritizes sections** by relevance score
3. **Loads sections** until budget exhausted
4. **Summarizes** sections if too large
5. **Caches** loaded sections across queries
6. **Reports** token efficiency metrics

<details>
<summary>📝 <strong>Solution: Adaptive Context Budget</strong></summary>

```python
"""
Solution: Adaptive Context Budget

Token-aware context loading with caching and summarization
"""

from typing import TypedDict, List, Dict, Annotated
from langgraph.graph import StateGraph, START, END
from langchain_anthropic import ChatAnthropic
import operator

class BudgetState(TypedDict):
    query: str
    token_budget: int
    tokens_used: int
    cached_sections: Dict[str, str]
    loaded_sections: Annotated[List[dict], operator.add]
    answer: str
    metrics: dict

class TokenBudgetManager:
    """Manages token budget and caching"""

    def __init__(self, budget: int = 10000):
        self.budget = budget
        self.cache = {}  # section_id -> content
        self.section_metadata = {
            "intro": {"tokens": 150, "priority": 0.3},
            "auth": {"tokens": 2500, "priority": 0.9},
            "requirements": {"tokens": 3000, "priority": 0.8},
            "architecture": {"tokens": 4000, "priority": 0.7},
            "testing": {"tokens": 1500, "priority": 0.5}
        }

    def can_load(self, section_id: str, tokens_used: int) -> bool:
        """Check if section fits in budget"""
        section_tokens = self.section_metadata.get(section_id, {}).get("tokens", 0)
        return tokens_used + section_tokens <= self.budget

    def get_summary(self, section_id: str) -> tuple:
        """Get summarized version (1/3 tokens)"""
        full_tokens = self.section_metadata.get(section_id, {}).get("tokens", 0)
        summary_tokens = full_tokens // 3
        return f"[Summary of {section_id}]", summary_tokens

    def prioritize_sections(self, relevance_scores: Dict[str, float]) -> List[tuple]:
        """Prioritize by relevance * priority"""
        scored = []
        for section_id, relevance in relevance_scores.items():
            if section_id in self.section_metadata:
                priority = self.section_metadata[section_id]["priority"]
                combined_score = relevance * priority
                scored.append((section_id, combined_score))

        return sorted(scored, key=lambda x: x[1], reverse=True)

budget_mgr = TokenBudgetManager(budget=8000)

def load_with_budget(state: BudgetState) -> BudgetState:
    """Load sections within token budget"""

    # Simulate relevance scores
    relevance = {
        "intro": 0.3,
        "auth": 0.95,
        "requirements": 0.8,
        "architecture": 0.6,
        "testing": 0.4
    }

    prioritized = budget_mgr.prioritize_sections(relevance)
    tokens_used = state.get("tokens_used", 0)
    loaded = []
    cached = state.get("cached_sections", {})

    print(f"\nToken budget: {budget_mgr.budget}")
    print(f"Tokens used: {tokens_used}\n")

    for section_id, score in prioritized:
        # Check cache first
        if section_id in cached:
            print(f"  ✓ {section_id}: Using cached (0 tokens)")
            loaded.append({"id": section_id, "content": cached[section_id], "tokens": 0, "cached": True})
            continue

        # Try to load full section
        if budget_mgr.can_load(section_id, tokens_used):
            tokens = budget_mgr.section_metadata[section_id]["tokens"]
            content = f"[Full content of {section_id}]"
            print(f"  ✓ {section_id}: Loaded full ({tokens} tokens)")
            loaded.append({"id": section_id, "content": content, "tokens": tokens, "cached": False})
            cached[section_id] = content
            tokens_used += tokens
        else:
            # Try summary instead
            summary, summary_tokens = budget_mgr.get_summary(section_id)
            if tokens_used + summary_tokens <= budget_mgr.budget:
                print(f"  ~ {section_id}: Loaded summary ({summary_tokens} tokens)")
                loaded.append({"id": section_id, "content": summary, "tokens": summary_tokens, "summarized": True})
                tokens_used += summary_tokens
            else:
                print(f"  ✗ {section_id}: Budget exhausted")
                break

    return {
        "loaded_sections": loaded,
        "tokens_used": tokens_used,
        "cached_sections": cached
    }

def generate_answer(state: BudgetState) -> BudgetState:
    """Generate answer with loaded context"""

    content = "\n\n".join(s["content"] for s in state.get("loaded_sections", []))
    answer = f"Answer based on {len(state.get('loaded_sections', []))} sections"

    # Calculate metrics
    total_sections = len(state.get("loaded_sections", []))
    cached_sections = sum(1 for s in state.get("loaded_sections", []) if s.get("cached", False))
    summarized_sections = sum(1 for s in state.get("loaded_sections", []) if s.get("summarized", False))

    metrics = {
        "tokens_used": state.get("tokens_used", 0),
        "tokens_budget": budget_mgr.budget,
        "efficiency": 1 - (state.get("tokens_used", 0) / budget_mgr.budget),
        "sections_loaded": total_sections,
        "sections_cached": cached_sections,
        "sections_summarized": summarized_sections
    }

    return {"answer": answer, "metrics": metrics}

# Build workflow
workflow = StateGraph(BudgetState)
workflow.add_node("load", load_with_budget)
workflow.add_node("answer", generate_answer)

workflow.add_edge(START, "load")
workflow.add_edge("load", "answer")
workflow.add_edge("answer", END)

app = workflow.compile()

# Test with multiple queries (showing caching effect)
queries = ["Query 1", "Query 2", "Query 3"]

for i, query in enumerate(queries):
    print(f"\n{'='*60}")
    print(f"Query {i+1}: {query}")
    print('='*60)

    result = app.invoke({
        "query": query,
        "token_budget": 8000,
        "tokens_used": 0,
        "cached_sections": result.get("cached_sections", {}) if i > 0 else {},
        "loaded_sections": [],
        "answer": "",
        "metrics": {}
    })

    print(f"\n{'='*60}")
    print("Metrics:")
    for key, value in result["metrics"].items():
        if isinstance(value, float):
            print(f"  {key}: {value:.2%}" if "efficiency" in key else f"  {key}: {value:.2f}")
        else:
            print(f"  {key}: {value}")
    print('='*60)
```

</details>

---

## 🎓 Key Takeaways

### Context7 Best Practices

✅ **DO**:
- Start with summaries, drill down as needed
- Let LLM decide what context to load
- Track token usage and costs
- Cache loaded sections
- Set maximum context limits
- Test with real large documents

❌ **DON'T**:
- Load full document by default
- Ignore token costs
- Load context you don't use
- Forget to implement fallbacks
- Skip relevance scoring

### Token Efficiency Gains

**Example savings**:
```
Traditional: Load 50k tokens every query
Context7: Load 5k tokens on average

Queries: 100
Traditional cost: 100 × $0.05 = $5.00
Context7 cost: 100 × $0.005 = $0.50

Savings: 90%
```

---

## 🔄 Story Progress: SpecBot v0.10

**What we built**: SpecBot now handles huge documents efficiently!

```python
# SpecBot v0.10 - Context7 Integration
def analyze_template(template_path):
    # Start with Level 1 (summary)
    context = get_level_1(template_path)

    # LLM decides what sections to expand
    relevant_sections = llm_identify_sections(context, question)

    # Load only relevant sections to Level 3
    for section in relevant_sections:
        context += get_level_3(template_path, section)

    # 90% reduction in tokens loaded!
    return analyze_with_context(context)
```

**Next Step**: Lesson 11 combines Context7 with RAG (Retrieval-Augmented Generation) for intelligent document understanding.

---

**Continue to [Lesson 11: RAG for Document Understanding →](./11-rag-document-understanding.md)**
