# Lesson 12: Multi-Document Synthesis

> **Story Context**: Users don't just upload one document - they upload templates, style guides, example specs, design mockups, and process documents. SpecBot needs to synthesize information from all these sources to generate coherent specifications. This lesson teaches you to build cross-document analysis and synthesis workflows.

---

## 🎯 Learning Objectives

By the end of this lesson, you will:

1. Extract and merge information from multiple documents
2. Resolve conflicts between sources
3. Build hierarchical synthesis workflows
4. Track information provenance (which source said what)
5. Create cross-document references
6. Implement incremental synthesis patterns

**Time**: ~4 hours

---

## 📖 Key Concepts

### The Multi-Document Challenge

**Scenario**:
```
User uploads:
1. Template.docx - Structure of desired output
2. StyleGuide.pdf - Formatting and tone requirements
3. Examples.docx - Previous successful specifications
4. Requirements.txt - Extracted from stakeholder interviews
5. DesignMockups.pdf - UI designs and flows
```

**Challenge**: Generate specification that:
- Follows template structure
- Adheres to style guide
- Matches quality of examples
- Incorporates all requirements
- References design mockups appropriately

### Synthesis Strategies

**1. Sequential Synthesis** (Simple):
```
Doc1 → Extract info → Partial result
Doc2 → Extract info → Merge with partial
Doc3 → Extract info → Merge again
...
Final result
```

**2. Parallel Synthesis** (Fast):
```
Doc1 → Extract info ─┐
Doc2 → Extract info ─┤
Doc3 → Extract info ─┼→ Merge all → Final result
Doc4 → Extract info ─┤
Doc5 → Extract info ─┘
```

**3. Hierarchical Synthesis** (Robust):
```
               ┌─────────────┐
               │   Template  │ (Structure)
               └──────┬──────┘
                      │
        ┌─────────────┼─────────────┐
        │             │             │
┌───────▼──────┐ ┌────▼────┐ ┌─────▼──────┐
│ Requirements │ │  Style  │ │  Examples  │
└───────┬──────┘ └────┬────┘ └─────┬──────┘
        │             │             │
        └─────────────┼─────────────┘
                      │
               ┌──────▼──────┐
               │   Synthesize│
               └─────────────┘
```

### Conflict Resolution

When sources conflict:
```python
Source A: "Requirements SHALL use FR-XXX format"
Source B: "Use REQ-XXX format for requirements"

Resolution strategies:
1. Priority: Template > Style Guide > Examples
2. Recency: Newer documents override older
3. Explicit: Ask user to resolve
4. Context: Use format appropriate for section
```

---

## 💻 Code Examples

### Example 1: Sequential Document Synthesis

```python
"""
src/examples/ex39_sequential_synthesis.py

Synthesize information from multiple documents sequentially
"""

from typing import TypedDict, List, Annotated
from langgraph.graph import StateGraph, START, END
from langchain_anthropic import ChatAnthropic
import operator

class SequentialSynthesisState(TypedDict):
    documents: List[dict]  # Input documents
    current_doc_index: int
    synthesized_info: Annotated[List[dict], operator.add]
    conflicts: Annotated[List[dict], operator.add]
    final_spec: str

def extract_from_document(state: SequentialSynthesisState) -> SequentialSynthesisState:
    """Extract information from current document"""
    doc = state["documents"][state["current_doc_index"]]
    doc_type = doc["type"]

    llm = ChatAnthropic(model="claude-3-5-sonnet-20241022", temperature=0)

    # Extraction prompts based on document type
    extraction_prompts = {
        "template": "Extract the structure and sections from this template document.",
        "style_guide": "Extract formatting rules, tone guidelines, and constraints.",
        "examples": "Extract patterns and best practices from this example.",
        "requirements": "Extract all functional and non-functional requirements."
    }

    prompt = f"""Document type: {doc_type}
    Content: {doc['content']}

    Task: {extraction_prompts.get(doc_type, 'Extract key information.')}

    Provide structured output with clear labels."""

    response = llm.invoke(prompt)

    extracted = {
        "source": doc["title"],
        "type": doc_type,
        "info": response.content,
        "priority": doc.get("priority", 3)  # 1=highest
    }

    return {
        "synthesized_info": [extracted],
        "current_doc_index": state["current_doc_index"] + 1
    }

def check_for_conflicts(state: SequentialSynthesisState) -> SequentialSynthesisState:
    """Detect conflicts between newly extracted info and existing"""
    if len(state["synthesized_info"]) < 2:
        return state  # No conflicts possible yet

    latest = state["synthesized_info"][-1]
    conflicts = []

    # Simple conflict detection (in production, use LLM)
    for existing in state["synthesized_info"][:-1]:
        # Check if same type of information conflicts
        if existing["type"] == latest["type"]:
            conflicts.append({
                "source_a": existing["source"],
                "source_b": latest["source"],
                "type": existing["type"],
                "resolution": "priority"  # Resolve by priority
            })

    return {"conflicts": conflicts}

def merge_information(state: SequentialSynthesisState) -> SequentialSynthesisState:
    """Merge all extracted information with conflict resolution"""
    llm = ChatAnthropic(model="claude-3-5-sonnet-20241022", temperature=0)

    # Sort by priority
    sorted_info = sorted(
        state["synthesized_info"],
        key=lambda x: x["priority"]
    )

    # Build context from all sources
    context_parts = []
    for info in sorted_info:
        context_parts.append(f"""
## {info['source']} ({info['type']})
Priority: {info['priority']}

{info['info']}
        """)

    context = "\n\n".join(context_parts)

    # Conflicts context
    conflicts_text = ""
    if state["conflicts"]:
        conflicts_text = "\n\nConflicts detected:\n"
        for c in state["conflicts"]:
            conflicts_text += f"- {c['source_a']} vs {c['source_b']} ({c['type']})\n"

    prompt = f"""You are synthesizing information from multiple documents to create
    a specification. The documents are ordered by priority (1=highest).

    When there are conflicts, prefer higher priority sources.

    Documents:
    {context}
    {conflicts_text}

    Create a coherent specification that:
    1. Follows the template structure
    2. Adheres to style guide rules
    3. Incorporates all requirements
    4. References examples where appropriate

    Generate the final specification:"""

    response = llm.invoke(prompt)

    return {"final_spec": response.content}

def check_more_documents(state: SequentialSynthesisState) -> str:
    """Check if more documents to process"""
    if state["current_doc_index"] < len(state["documents"]):
        return "continue"
    return "merge"

# Build workflow
workflow = StateGraph(SequentialSynthesisState)
workflow.add_node("extract", extract_from_document)
workflow.add_node("check_conflicts", check_for_conflicts)
workflow.add_node("merge", merge_information)

workflow.add_edge(START, "extract")
workflow.add_edge("extract", "check_conflicts")
workflow.add_conditional_edges(
    "check_conflicts",
    check_more_documents,
    {
        "continue": "extract",
        "merge": "merge"
    }
)
workflow.add_edge("merge", END)

app = workflow.compile()

# Test
test_documents = [
    {
        "title": "Template.docx",
        "type": "template",
        "priority": 1,
        "content": "# Specification Template\n1. Overview\n2. Requirements\n3. Architecture"
    },
    {
        "title": "StyleGuide.pdf",
        "type": "style_guide",
        "priority": 2,
        "content": "Use SHALL for mandatory requirements. Use SHOULD for recommendations."
    },
    {
        "title": "Requirements.txt",
        "type": "requirements",
        "priority": 3,
        "content": "User authentication, password reset, OAuth support, MFA"
    }
]

result = app.invoke({
    "documents": test_documents,
    "current_doc_index": 0,
    "synthesized_info": [],
    "conflicts": [],
    "final_spec": ""
})

print("=== Synthesized Specification ===\n")
print(result["final_spec"])

if result["conflicts"]:
    print("\n\n=== Conflicts Resolved ===\n")
    for conflict in result["conflicts"]:
        print(f"- {conflict['source_a']} vs {conflict['source_b']}")
```

### Example 2: Parallel Synthesis with Map-Reduce

```python
"""
src/examples/ex40_parallel_synthesis.py

Process multiple documents in parallel, then merge
"""

from typing import TypedDict, List, Annotated
from langgraph.graph import StateGraph, START, END
import operator

class ParallelSynthesisState(TypedDict):
    documents: List[dict]
    extracted_data: Annotated[List[dict], operator.add]
    merged_result: str

def extract_template_structure(state: ParallelSynthesisState) -> ParallelSynthesisState:
    """Extract structure from template (parallel task 1)"""
    template = next(d for d in state["documents"] if d["type"] == "template")

    # Simulate extraction
    structure = {
        "type": "structure",
        "sections": ["Overview", "Requirements", "Architecture", "Testing"],
        "format": "hierarchical"
    }

    return {"extracted_data": [structure]}

def extract_style_rules(state: ParallelSynthesisState) -> ParallelSynthesisState:
    """Extract style rules (parallel task 2)"""
    style_guide = next(d for d in state["documents"] if d["type"] == "style_guide")

    rules = {
        "type": "style",
        "modal_verbs": {"mandatory": "SHALL", "recommended": "SHOULD"},
        "id_format": "FR-XXX",
        "tone": "formal"
    }

    return {"extracted_data": [rules]}

def extract_requirements(state: ParallelSynthesisState) -> ParallelSynthesisState:
    """Extract requirements (parallel task 3)"""
    req_doc = next(d for d in state["documents"] if d["type"] == "requirements")

    requirements = {
        "type": "requirements",
        "items": [
            "User authentication via email/password",
            "OAuth 2.0 support",
            "Multi-factor authentication",
            "Password reset flow"
        ]
    }

    return {"extracted_data": [requirements]}

def merge_all_extractions(state: ParallelSynthesisState) -> ParallelSynthesisState:
    """Merge all parallel extractions into final spec"""
    llm = ChatAnthropic(model="claude-3-5-sonnet-20241022", temperature=0)

    # Organize extracted data by type
    data_by_type = {}
    for item in state["extracted_data"]:
        data_by_type[item["type"]] = item

    structure = data_by_type.get("structure", {})
    style = data_by_type.get("style", {})
    requirements = data_by_type.get("requirements", {})

    prompt = f"""Create a specification using:

Structure: {structure.get('sections', [])}
Style: {style.get('modal_verbs', {})} for requirements, ID format: {style.get('id_format', 'XXX')}
Requirements to include: {requirements.get('items', [])}

Generate a well-formatted specification following the structure and style."""

    response = llm.invoke(prompt)

    return {"merged_result": response.content}

# Build parallel workflow
workflow = StateGraph(ParallelSynthesisState)

# These nodes run in parallel
workflow.add_node("extract_structure", extract_template_structure)
workflow.add_node("extract_style", extract_style_rules)
workflow.add_node("extract_requirements", extract_requirements)
workflow.add_node("merge", merge_all_extractions)

# All extraction nodes start from START
workflow.add_edge(START, "extract_structure")
workflow.add_edge(START, "extract_style")
workflow.add_edge(START, "extract_requirements")

# All converge to merge
workflow.add_edge("extract_structure", "merge")
workflow.add_edge("extract_style", "merge")
workflow.add_edge("extract_requirements", "merge")

workflow.add_edge("merge", END)

app = workflow.compile()

# Test
result = app.invoke({
    "documents": [
        {"type": "template", "content": "..."},
        {"type": "style_guide", "content": "..."},
        {"type": "requirements", "content": "..."}
    ],
    "extracted_data": [],
    "merged_result": ""
})

print(result["merged_result"])
```

### Example 3: Provenance Tracking

```python
"""
src/examples/ex41_provenance_tracking.py

Track which source each piece of information came from
"""

from typing import TypedDict, List
from dataclasses import dataclass

@dataclass
class ProvenanceInfo:
    """Track source of information"""
    content: str
    source_document: str
    source_section: str
    confidence: float
    extraction_timestamp: str

class ProvenanceState(TypedDict):
    documents: List[dict]
    extracted_requirements: List[ProvenanceInfo]
    final_spec_with_citations: str

def extract_with_provenance(state: ProvenanceState) -> ProvenanceState:
    """Extract requirements with full provenance tracking"""
    requirements = []

    for doc in state["documents"]:
        # Simulate extraction with provenance
        if "authentication" in doc["content"].lower():
            req = ProvenanceInfo(
                content="The system SHALL authenticate users via email and password",
                source_document=doc["title"],
                source_section=doc.get("section", "General"),
                confidence=0.95,
                extraction_timestamp="2024-01-15T10:30:00"
            )
            requirements.append(req)

    return {"extracted_requirements": requirements}

def generate_with_citations(state: ProvenanceState) -> ProvenanceState:
    """Generate specification with source citations"""
    spec_parts = []

    spec_parts.append("# User Authentication Specification\n")
    spec_parts.append("## Functional Requirements\n")

    for i, req in enumerate(state["extracted_requirements"], 1):
        # Format requirement with citation
        req_text = f"\nFR-{i:03d}: {req.content}"

        # Add citation
        citation = f"\n*Source: {req.source_document}, {req.source_section} (confidence: {req.confidence:.0%})*"

        spec_parts.append(req_text)
        spec_parts.append(citation)

    spec_parts.append("\n\n## References\n")
    sources = set(req.source_document for req in state["extracted_requirements"])
    for source in sources:
        spec_parts.append(f"- {source}\n")

    return {"final_spec_with_citations": "".join(spec_parts)}

# Build workflow
workflow = StateGraph(ProvenanceState)
workflow.add_node("extract", extract_with_provenance)
workflow.add_node("generate", generate_with_citations)

workflow.add_edge(START, "extract")
workflow.add_edge("extract", "generate")
workflow.add_edge("generate", END)

app = workflow.compile()

# Test
result = app.invoke({
    "documents": [
        {"title": "Requirements.docx", "content": "Need user authentication system"},
        {"title": "StyleGuide.pdf", "content": "Use SHALL for requirements"}
    ],
    "extracted_requirements": [],
    "final_spec_with_citations": ""
})

print(result["final_spec_with_citations"])
```

---

## 🏋️ Hands-On Exercise: Cross-Document Reference System

**Objective**: Build a system that creates cross-references between multiple documents.

### Requirements

Create a system that:
1. Processes multiple related documents
2. Identifies connections between documents (references, dependencies)
3. Creates a knowledge graph of relationships
4. Generates specifications with cross-document links
5. Detects inconsistencies across documents
6. Suggests harmonization of conflicting information

### Starter Code

Create `src/exercises/ex12_cross_document.py`:

```python
"""
Exercise 12: Cross-Document Reference System

Build system that synthesizes and cross-references multiple documents
"""

from typing import TypedDict, List, Dict, Annotated
from langgraph.graph import StateGraph, START, END
import operator

class CrossDocState(TypedDict):
    documents: List[dict]
    entity_mentions: Dict[str, List[dict]]  # entity -> [{doc, context}]
    relationships: Annotated[List[dict], operator.add]
    inconsistencies: Annotated[List[dict], operator.add]
    synthesized_spec: str

# TODO: Implement entity extraction
def extract_entities(state: CrossDocState) -> CrossDocState:
    """Extract entities (requirements, features, components) from all docs"""
    # TODO: Use NER or LLM to extract entities
    # TODO: Track which doc each entity appears in
    pass

# TODO: Implement relationship detection
def find_relationships(state: CrossDocState) -> CrossDocState:
    """Find relationships between entities across documents"""
    # TODO: Detect references (A mentions B)
    # TODO: Detect dependencies (A requires B)
    # TODO: Detect conflicts (A contradicts B)
    pass

# TODO: Implement inconsistency detection
def detect_inconsistencies(state: CrossDocState) -> CrossDocState:
    """Find inconsistencies across documents"""
    # TODO: Compare same entity across docs
    # TODO: Flag contradictions
    # TODO: Suggest resolutions
    pass

# TODO: Implement synthesis with cross-references
def synthesize_with_links(state: CrossDocState) -> CrossDocState:
    """Generate spec with cross-document references"""
    # TODO: Create unified spec
    # TODO: Add cross-references
    # TODO: Include relationship diagram
    pass

# TODO: Build workflow

# Test with interconnected documents
test_docs = [
    {
        "id": "requirements",
        "title": "Requirements Document",
        "content": "FR-001: User authentication is required. See security-spec for details."
    },
    {
        "id": "security",
        "title": "Security Specification",
        "content": "SEC-001: Authentication SHALL use bcrypt. Implements FR-001 from requirements doc."
    },
    {
        "id": "architecture",
        "title": "Architecture Design",
        "content": "AuthService handles FR-001. Uses algorithm specified in SEC-001."
    }
]
```

<details>
<summary>📝 <strong>Solution: Cross-Document Reference System</strong></summary>

```python
"""Solution: Cross-Document Reference System"""
from typing import TypedDict, List
from langgraph.graph import StateGraph, START, END
from langchain_anthropic import ChatAnthropic
import re

class RefState(TypedDict):
    documents: List[dict]
    references: List[dict]
    synthesis: str

def extract_references(state: RefState) -> RefState:
    refs = []
    for doc in state["documents"]:
        found = re.findall(r'(FR-\d{3}|SEC-\d{3})', doc["content"])
        refs.extend([{"from": doc["id"], "to": ref} for ref in found])
    return {"references": refs}

def synthesize_documents(state: RefState) -> RefState:
    llm = ChatAnthropic(model="claude-3-5-sonnet-20241022")
    content = "\n\n".join(f"[{d['title']}]: {d['content']}" for d in state["documents"])
    response = llm.invoke(f"Synthesize:\n{content}\n\nReferences: {state['references']}")
    return {"synthesis": response.content}

workflow = StateGraph(RefState)
workflow.add_node("extract", extract_references)
workflow.add_node("synthesize", synthesize_documents)
workflow.add_edge(START, "extract")
workflow.add_edge("extract", "synthesize")
workflow.add_edge("synthesize", END)

app = workflow.compile()
result = app.invoke({"documents": [{"id": "req", "title": "Req", "content": "FR-001: Auth"}], "references": [], "synthesis": ""})
print(f"Synthesis: {result['synthesis']}")
```

</details>

---

## 🚀 Challenge: Conflict Resolution Engine

**Advanced**: Build an intelligent system that automatically resolves conflicts between documents.

### Challenge Requirements

Create a system that:
1. **Detects conflicts** across multiple documents
2. **Classifies conflict types** (factual, stylistic, priority)
3. **Applies resolution strategies** based on conflict type
4. **Generates explanations** for each resolution
5. **Flags unresolvable conflicts** for human review
6. **Learns from user decisions** to improve future resolutions

<details>
<summary>📝 <strong>Solution: Conflict Resolution Engine</strong></summary>

```python
"""Solution: Conflict Resolution with conflict detection"""
from typing import TypedDict, List
from langgraph.graph import StateGraph, START, END
from langchain_anthropic import ChatAnthropic

class ConflictState(TypedDict):
    documents: List[dict]
    conflicts: List[dict]
    resolution: str

def detect_conflicts(state: ConflictState) -> ConflictState:
    conflicts = []
    for i, doc1 in enumerate(state["documents"]):
        for doc2 in state["documents"][i+1:]:
            if "SHALL NOT" in doc1["content"] and "SHALL" in doc2["content"]:
                conflicts.append({"doc1": doc1["id"], "doc2": doc2["id"], "type": "contradiction"})
    return {"conflicts": conflicts}

def resolve_conflicts(state: ConflictState) -> ConflictState:
    if not state["conflicts"]:
        return {"resolution": "No conflicts detected"}
    llm = ChatAnthropic(model="claude-3-5-sonnet-20241022")
    response = llm.invoke(f"Resolve: {state['conflicts']}")
    return {"resolution": response.content}

workflow = StateGraph(ConflictState)
workflow.add_node("detect", detect_conflicts)
workflow.add_node("resolve", resolve_conflicts)
workflow.add_edge(START, "detect")
workflow.add_edge("detect", "resolve")
workflow.add_edge("resolve", END)

app = workflow.compile()
result = app.invoke({"documents": [{"id": "d1", "content": "SHALL use X"}, {"id": "d2", "content": "SHALL NOT use X"}], "conflicts": [], "resolution": ""})
print(f"Resolution: {result['resolution']}")
```

</details>

---

## 🎓 Key Takeaways

### Multi-Document Synthesis Best Practices

✅ **DO**:
- Establish clear document priority hierarchy
- Track provenance of all information
- Detect and resolve conflicts explicitly
- Maintain audit trail of decisions
- Use parallel processing for speed
- Validate synthesized output

❌ **DON'T**:
- Assume documents won't conflict
- Lose track of information sources
- Merge blindly without conflict detection
- Ignore document metadata (dates, versions)
- Skip validation of synthesized output

### Synthesis Patterns

| Pattern | Use When | Pros | Cons |
|---------|----------|------|------|
| Sequential | Few documents, order matters | Simple, maintainable | Slow, can accumulate errors |
| Parallel | Many independent documents | Fast, scalable | Complex merging required |
| Hierarchical | Clear document hierarchy | Handles conflicts well | Requires structure design |

---

## 🔄 Story Progress: SpecBot v0.12

**What we built**: SpecBot now synthesizes information from multiple sources!

```python
# SpecBot v0.12 - Multi-Document Synthesis

# User uploads multiple documents
documents = [
    upload_template(),      # Structure
    upload_style_guide(),   # Formatting rules
    upload_requirements(),  # Content
    upload_examples()       # Quality reference
]

# Parallel extraction
template_structure = extract_structure(documents[0])
style_rules = extract_style(documents[1])
requirements = extract_requirements(documents[2])
patterns = extract_patterns(documents[3])

# Intelligent synthesis
spec = synthesize(
    structure=template_structure,
    style=style_rules,
    content=requirements,
    quality_reference=patterns
)

# Result: Specification that perfectly combines all sources!
```

**Next Step**: Lesson 13 brings it all together - building the complete template analysis pipeline that powers SpecBot's template upload feature.

---

**Continue to [Lesson 13: Template Analysis Pipeline →](./13-template-analysis.md)**
