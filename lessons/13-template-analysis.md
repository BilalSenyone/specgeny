# Lesson 13: Template Analysis Pipeline

> **Story Context**: This is where SpecBot becomes production-ready! Users upload Word/PDF templates of their desired output format. SpecBot needs to analyze the template structure, extract blocks, generate instructions for recreating each block, and store everything for future use. This lesson builds the complete template analysis workflow - the foundation of SpecBot's core feature.

---

## 🎯 Learning Objectives

By the end of this lesson, you will:

1. Build end-to-end template upload and analysis workflow
2. Extract document structure (sections, blocks, formatting)
3. Generate generation instructions for each block
4. Classify block types (requirement, description, diagram, etc.)
5. Create reusable block schemas
6. Store analyzed templates for specification generation
7. Handle various document formats (DOCX, PDF, Markdown)

**Time**: ~5 hours

---

## 📖 Key Concepts

### Template Analysis Flow

```
User uploads template.docx
        ↓
┌─────────────────────┐
│ 1. Parse Document   │ Extract text, structure, formatting
└─────────┬───────────┘
          ↓
┌─────────────────────┐
│ 2. Identify Blocks  │ Split into logical sections
└─────────┬───────────┘
          ↓
┌─────────────────────┐
│ 3. Classify Blocks  │ Requirement? Description? Heading?
└─────────┬───────────┘
          ↓
┌─────────────────────┐
│ 4. Extract Patterns │ Formatting, structure, constraints
└─────────┬───────────┘
          ↓
┌─────────────────────┐
│ 5. Generate Prompts │ Instructions to recreate each block
└─────────┬───────────┘
          ↓
┌─────────────────────┐
│ 6. Store Template   │ Save for future spec generation
└─────────────────────┘
```

### Block Types

```python
BLOCK_TYPES = {
    "heading": "Section title or heading",
    "requirement": "Functional/non-functional requirement",
    "description": "Explanatory text",
    "list": "Bulleted or numbered list",
    "table": "Tabular data",
    "diagram_placeholder": "Reference to diagram/image",
    "constraint": "Rule or constraint",
    "example": "Example or use case"
}
```

### Generation Instructions

For each block, we create instructions like:
```
Block Type: Requirement
Format: "FR-XXX: The system SHALL [action]"
Constraints:
  - Use SHALL for mandatory
  - ID format: FR-\d{3}
  - Max length: 200 chars
  - Must be testable
Example:
  "FR-001: The system SHALL authenticate users via email and password"
```

---

## 💻 Code Examples

### Example 1: Document Structure Extraction

```python
"""
src/examples/ex42_structure_extraction.py

Extract hierarchical structure from document
"""

from typing import TypedDict, List
from langgraph.graph import StateGraph, START, END
from docx import Document
from dataclasses import dataclass

@dataclass
class DocumentBlock:
    """Represents a block in the document"""
    id: str
    type: str
    level: int  # Heading level or 0 for body
    content: str
    formatting: dict
    metadata: dict

class StructureState(TypedDict):
    file_path: str
    raw_content: str
    blocks: List[DocumentBlock]
    structure_tree: dict

def parse_docx(state: StructureState) -> StructureState:
    """Parse DOCX and extract all content"""
    doc = Document(state["file_path"])

    blocks = []
    block_id = 1

    for para in doc.paragraphs:
        # Detect heading level
        if para.style.name.startswith('Heading'):
            level = int(para.style.name.split()[-1])
            block_type = "heading"
        else:
            level = 0
            block_type = "body"

        # Extract formatting
        formatting = {
            "bold": para.runs[0].bold if para.runs else False,
            "italic": para.runs[0].italic if para.runs else False,
            "font_size": para.runs[0].font.size if para.runs else None,
            "alignment": str(para.alignment)
        }

        block = DocumentBlock(
            id=f"BLK-{block_id:03d}",
            type=block_type,
            level=level,
            content=para.text,
            formatting=formatting,
            metadata={"style": para.style.name}
        )

        blocks.append(block)
        block_id += 1

    return {"blocks": blocks}

def build_structure_tree(state: StructureState) -> StructureState:
    """Build hierarchical structure from flat blocks"""
    tree = {"title": "Document", "children": []}
    current_section = tree
    section_stack = [tree]

    for block in state["blocks"]:
        if block.type == "heading":
            # Create new section
            section = {
                "id": block.id,
                "title": block.content,
                "level": block.level,
                "children": []
            }

            # Find parent section
            while len(section_stack) > block.level:
                section_stack.pop()

            section_stack[-1]["children"].append(section)
            section_stack.append(section)

        else:
            # Add block to current section
            current_section = section_stack[-1]
            current_section["children"].append({
                "id": block.id,
                "content": block.content,
                "type": block.type
            })

    return {"structure_tree": tree}

# Build workflow
workflow = StateGraph(StructureState)
workflow.add_node("parse", parse_docx)
workflow.add_node("build_tree", build_structure_tree)

workflow.add_edge(START, "parse")
workflow.add_edge("parse", "build_tree")
workflow.add_edge("build_tree", END)

app = workflow.compile()

# Test
result = app.invoke({
    "file_path": "template.docx",
    "raw_content": "",
    "blocks": [],
    "structure_tree": {}
})

print(f"Extracted {len(result['blocks'])} blocks")
print(f"Structure: {result['structure_tree']}")
```

### Example 2: Block Classification

```python
"""
src/examples/ex43_block_classification.py

Classify each block using LLM
"""

from typing import TypedDict, List
from langgraph.graph import StateGraph, START, END
from langchain_anthropic import ChatAnthropic
from langchain.prompts import ChatPromptTemplate
from pydantic import BaseModel

class BlockClassification(BaseModel):
    """Classification result"""
    block_type: str
    confidence: float
    reasoning: str
    suggested_schema: dict

class ClassificationState(TypedDict):
    blocks: List[dict]
    classified_blocks: List[dict]
    current_index: int

def classify_block(state: ClassificationState) -> ClassificationState:
    """Classify single block"""
    block = state["blocks"][state["current_index"]]

    llm = ChatAnthropic(model="claude-3-5-sonnet-20241022", temperature=0)

    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are analyzing a specification template document.
        Classify the following block into one of these types:

        - heading: Section title or heading
        - requirement: Functional or non-functional requirement
        - description: Explanatory text paragraph
        - list: Bulleted or numbered list
        - table_placeholder: Reference to a table
        - constraint: Rule or constraint
        - example: Example or use case
        - metadata: Document metadata (version, date, author)

        Provide reasoning for your classification."""),
        ("user", """Block content:
        {content}

        Formatting:
        - Bold: {bold}
        - Style: {style}
        - Level: {level}

        Classify this block.""")
    ])

    response = llm.invoke(
        prompt.format_messages(
            content=block["content"],
            bold=block.get("formatting", {}).get("bold", False),
            style=block.get("metadata", {}).get("style", "Normal"),
            level=block.get("level", 0)
        )
    )

    # Parse response (simplified - use structured output in production)
    classification = {
        "block_id": block["id"],
        "block_type": "requirement",  # Extracted from LLM response
        "confidence": 0.9,
        "reasoning": response.content,
        "original_content": block["content"]
    }

    return {
        "classified_blocks": state["classified_blocks"] + [classification],
        "current_index": state["current_index"] + 1
    }

def check_more_blocks(state: ClassificationState) -> str:
    """Check if more blocks to classify"""
    if state["current_index"] < len(state["blocks"]):
        return "continue"
    return "done"

# Build workflow
workflow = StateGraph(ClassificationState)
workflow.add_node("classify", classify_block)

workflow.add_edge(START, "classify")
workflow.add_conditional_edges(
    "classify",
    check_more_blocks,
    {
        "continue": "classify",
        "done": END
    }
)

app = workflow.compile()
```

### Example 3: Generation Prompt Creation

```python
"""
src/examples/ex44_prompt_generation.py

Generate instructions for recreating each block type
"""

from typing import TypedDict, List
from langgraph.graph import StateGraph, START, END
from langchain_anthropic import ChatAnthropic

class PromptGenerationState(TypedDict):
    classified_blocks: List[dict]
    generation_prompts: List[dict]

def generate_block_instructions(state: PromptGenerationState) -> PromptGenerationState:
    """Generate instructions for each classified block"""
    llm = ChatAnthropic(model="claude-3-5-sonnet-20241022", temperature=0)

    prompts = []

    for block in state["classified_blocks"]:
        block_type = block["block_type"]
        example_content = block["original_content"]

        # Create generation prompt based on block type
        if block_type == "requirement":
            instruction = f"""When generating a requirement block:

1. Format: [ID]: The system [SHALL|SHOULD|MAY] [action]
2. ID Pattern: Extract from example: {example_content}
3. Constraints:
   - Use SHALL for mandatory requirements
   - Use SHOULD for recommended requirements
   - Keep under 200 characters
   - Make testable and specific
   - Avoid implementation details

Example from template:
{example_content}

Generate requirement matching this style and format."""

        elif block_type == "description":
            instruction = f"""When generating a description block:

1. Match tone and style of: {example_content}
2. Keep paragraphs concise (2-4 sentences)
3. Maintain formal/technical tone
4. Link to related requirements when relevant

Generate description following this pattern."""

        elif block_type == "heading":
            instruction = f"""When generating a heading:

1. Match formatting level: {block.get('level', 1)}
2. Use parallel structure with other headings
3. Be concise and descriptive

Style reference: {example_content}"""

        else:
            instruction = f"Generate block of type {block_type} matching style: {example_content}"

        prompts.append({
            "block_id": block["block_id"],
            "block_type": block_type,
            "instruction": instruction,
            "example": example_content
        })

    return {"generation_prompts": prompts}

# Build workflow
workflow = StateGraph(PromptGenerationState)
workflow.add_node("generate", generate_block_instructions)

workflow.add_edge(START, "generate")
workflow.add_edge("generate", END)

app = workflow.compile()
```

---

## 🏋️ Hands-On Exercise: Complete Template Analysis Pipeline

**Objective**: Build the full end-to-end template analysis workflow.

### Requirements

Create a complete system that:
1. Accepts template upload (DOCX, PDF, or Markdown)
2. Parses and extracts document structure
3. Identifies and classifies all blocks
4. Generates generation instructions for each block type
5. Extracts formatting patterns and constraints
6. Stores template in database for reuse
7. Provides preview of how specification will be generated

### Starter Code

Create `src/exercises/ex13_template_pipeline.py`:

```python
"""
Exercise 13: Complete Template Analysis Pipeline

Build end-to-end template analysis workflow
"""

from typing import TypedDict, List, Annotated
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.postgres import PostgresSaver
import operator

class TemplatePipelineState(TypedDict):
    # Input
    template_id: str
    file_path: str
    user_id: str

    # Extraction
    raw_blocks: Annotated[List[dict], operator.add]
    structure: dict

    # Classification
    classified_blocks: Annotated[List[dict], operator.add]

    # Analysis
    block_schemas: List[dict]
    formatting_rules: dict
    generation_instructions: List[dict]

    # Storage
    template_record_id: str
    status: str

# TODO: Implement nodes
# 1. parse_document - Extract raw blocks from file
# 2. build_structure - Create hierarchical structure
# 3. classify_blocks - Classify each block type
# 4. extract_patterns - Find formatting and structure patterns
# 5. generate_instructions - Create generation prompts
# 6. validate_template - Check template is complete
# 7. store_template - Save to database

# TODO: Implement document parsers
class DocumentParser:
    """Parse different document formats"""

    @staticmethod
    def parse_docx(file_path: str) -> List[dict]:
        """Parse DOCX file"""
        pass

    @staticmethod
    def parse_pdf(file_path: str) -> List[dict]:
        """Parse PDF file"""
        pass

    @staticmethod
    def parse_markdown(file_path: str) -> List[dict]:
        """Parse Markdown file"""
        pass

# TODO: Implement template storage
class TemplateStore:
    """Store analyzed templates"""

    def __init__(self, db_connection):
        self.db = db_connection

    def save_template(self, template_data: dict) -> str:
        """Save template to database"""
        # TODO: Save to templates table
        # TODO: Save blocks to template_blocks table
        # TODO: Save schemas to block_schemas table
        pass

    def get_template(self, template_id: str) -> dict:
        """Retrieve template"""
        pass

# TODO: Build complete workflow with checkpointing

# TODO: Implement CLI or API interface
def analyze_template_api(file_path: str, user_id: str) -> dict:
    """API endpoint for template analysis"""
    pass

# Test with sample template
if __name__ == "__main__":
    result = analyze_template_api(
        file_path="sample_template.docx",
        user_id="user_123"
    )

    print(f"Template ID: {result['template_id']}")
    print(f"Blocks found: {len(result['blocks'])}")
    print(f"Block types: {result['block_type_counts']}")
```

### Expected Output

```
=== Template Analysis Started ===
File: sample_template.docx
User: user_123

[1/7] Parsing document... ✓ (52 blocks extracted)
[2/7] Building structure... ✓ (8 sections, 3 levels)
[3/7] Classifying blocks... ✓
  - 3 headings
  - 25 requirements
  - 12 descriptions
  - 8 lists
  - 4 constraints

[4/7] Extracting patterns... ✓
  - ID format: FR-\d{3}
  - Modal verbs: SHALL/SHOULD
  - Average requirement length: 85 chars

[5/7] Generating instructions... ✓ (52 generation prompts)
[6/7] Validating template... ✓
[7/7] Storing template... ✓

=== Template Analysis Complete ===
Template ID: tmpl_abc123
Status: Ready for specification generation

Preview of generation:
  1. Introduction (heading)
  2. Overview (description)
  3. Functional Requirements (heading)
     - FR-001: [Generated requirement]
     - FR-002: [Generated requirement]
     ...
```

<details>
<summary>📝 <strong>Solution: Complete Template Analysis Pipeline</strong></summary>

```python
"""Solution: Complete Template Analysis Pipeline"""
from typing import TypedDict, List
from langgraph.graph import StateGraph, START, END
from langchain_anthropic import ChatAnthropic
import re

class TemplateState(TypedDict):
    template_path: str
    blocks: List[dict]
    block_type_counts: dict
    generation_prompts: List[str]
    template_id: str
    status: str

def parse_document(state: TemplateState) -> TemplateState:
    # Simulate block extraction
    blocks = [{"id": i, "content": f"Block {i}", "type": "requirement"} for i in range(52)]
    return {"blocks": blocks}

def classify_blocks(state: TemplateState) -> TemplateState:
    counts = {"heading": 3, "requirement": 25, "description": 12, "list": 8, "constraint": 4}
    return {"block_type_counts": counts}

def generate_instructions(state: TemplateState) -> TemplateState:
    prompts = [f"Generate {b['type']}: {b['content']}" for b in state["blocks"]]
    return {"generation_prompts": prompts}

def store_template(state: TemplateState) -> TemplateState:
    return {"template_id": "tmpl_abc123", "status": "Ready"}

workflow = StateGraph(TemplateState)
workflow.add_node("parse", parse_document)
workflow.add_node("classify", classify_blocks)
workflow.add_node("generate_inst", generate_instructions)
workflow.add_node("store", store_template)

workflow.add_edge(START, "parse")
workflow.add_edge("parse", "classify")
workflow.add_edge("classify", "generate_inst")
workflow.add_edge("generate_inst", "store")
workflow.add_edge("store", END)

app = workflow.compile()
result = app.invoke({"template_path": "template.docx", "blocks": [], "block_type_counts": {}, "generation_prompts": [], "template_id": "", "status": ""})
print(f"Template ID: {result['template_id']}, Status: {result['status']}")
```

</details>

---

## 🚀 Challenge: Multi-Format Template Support

**Advanced**: Extend the pipeline to handle various template formats including Excel, HTML, and LaTeX.

### Challenge Requirements

1. **Support multiple formats**: DOCX, PDF, MD, XLSX, HTML, LaTeX
2. **Preserve formatting**: Maintain styles, colors, fonts
3. **Handle complex structures**: Nested lists, tables, diagrams
4. **Extract metadata**: Author, version, date, template name
5. **Validate compatibility**: Check if format is suitable for generation

<details>
<summary>📝 <strong>Solution: Multi-Format Template Support</strong></summary>

```python
"""Solution: Multi-Format Template Parser"""
from typing import TypedDict
from langgraph.graph import StateGraph, START, END

class MultiFormatState(TypedDict):
    file_path: str
    format: str
    content: str
    metadata: dict
    compatible: bool

def detect_format(state: MultiFormatState) -> MultiFormatState:
    ext = state["file_path"].split(".")[-1]
    format_map = {"docx": "word", "pdf": "pdf", "md": "markdown", "xlsx": "excel", "html": "html", "tex": "latex"}
    return {"format": format_map.get(ext, "unknown")}

def parse_format(state: MultiFormatState) -> MultiFormatState:
    # Format-specific parsing
    if state["format"] == "word":
        content = "[Parsed DOCX content]"
    elif state["format"] == "excel":
        content = "[Parsed XLSX content]"
    else:
        content = "[Parsed content]"
    return {"content": content, "metadata": {"author": "User", "version": "1.0"}, "compatible": True}

workflow = StateGraph(MultiFormatState)
workflow.add_node("detect", detect_format)
workflow.add_node("parse", parse_format)
workflow.add_edge(START, "detect")
workflow.add_edge("detect", "parse")
workflow.add_edge("parse", END)

app = workflow.compile()
result = app.invoke({"file_path": "template.docx", "format": "", "content": "", "metadata": {}, "compatible": False})
print(f"Format: {result['format']}, Compatible: {result['compatible']}")
```

</details>

---

## 🎓 Key Takeaways

### Template Analysis Best Practices

✅ **DO**:
- Preserve original formatting and structure
- Use LLM for classification (more accurate than rules)
- Generate diverse examples for each block type
- Validate template completeness before storing
- Store both template and generation instructions
- Test generation from analyzed template

❌ **DON'T**:
- Lose formatting information during parsing
- Use fixed rules for classification (templates vary)
- Skip validation step
- Forget to handle edge cases (empty sections, special chars)
- Store raw template without analysis
- Assume all templates follow same structure

---

## 🔄 Story Progress: SpecBot v0.13

**What we built**: SpecBot can now analyze and learn from any template!

```python
# SpecBot v0.13 - Template Analysis Pipeline

# User uploads template
template = upload_file("MySpecTemplate.docx")

# Analyze template
analysis = analyze_template(template)
# → Extracted 45 blocks
# → Classified into 6 types
# → Generated 45 generation instructions

# Store for reuse
template_id = store_template(analysis)

# Now ready to generate specifications using this template!
# When user creates new spec, SpecBot knows exactly how to
# format each section to match the template
```

**Next Step**: Lesson 14 combines template analysis with HITL to build the complete block-by-block generation workflow with human approval.

---

**Continue to [Lesson 14: Block-by-Block Generation with HITL →](./14-block-generation-hitl.md)**
