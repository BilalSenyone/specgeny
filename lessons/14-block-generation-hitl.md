# Lesson 14: Block-by-Block Generation with HITL

> **Story Context**: SpecBot has analyzed the template and knows how to generate each block. Now we build the core user experience - generating specifications block by block, pausing for user approval, regenerating based on feedback, and assembling the final document. This is where all previous lessons come together into the production SpecBot workflow!

---

## 🎯 Learning Objectives

By the end of this lesson, you will:

1. Build complete block-by-block generation workflow
2. Integrate template analysis with content generation
3. Implement approval gates after each block
4. Handle regeneration with user feedback
5. Track specification progress across sessions
6. Assemble final document from approved blocks
7. Implement real-time updates to frontend via SSE

**Time**: ~5 hours

---

## 📖 Key Concepts

### Block Generation Flow

```
User starts specification
        ↓
Load template + user documents
        ↓
┌──────────────────────┐
│ Generate Block 1     │ ← Use template instructions + RAG
└─────────┬────────────┘
          ↓
┌──────────────────────┐
│ Pause for Approval   │ ← interrupt()
└─────────┬────────────┘
          │
    ┌─────┴─────┐
    │           │
Approved?    Rejected?
    │           │
    │      ┌────▼────────────────┐
    │      │ Regenerate w/       │
    │      │ feedback            │
    │      └────┬────────────────┘
    │           │
    └─────┬─────┘
          ↓
Save approved block
          ↓
More blocks? → Yes: Loop to Generate Block N
          │
          No
          ↓
Assemble final document
```

### State Management

```python
class SpecificationState(TypedDict):
    # Specification metadata
    spec_id: str
    template_id: str
    user_id: str
    title: str

    # Generation context
    user_documents: List[str]  # Uploaded files
    rag_context: str           # Retrieved context

    # Block generation
    current_block_index: int
    total_blocks: int
    current_block: dict
    approved_blocks: Annotated[List[dict], operator.add]

    # User interaction
    user_approved: bool
    user_feedback: str

    # Output
    final_document: str
    status: str  # "generating", "paused", "completed"
```

### Real-Time Updates (SSE)

```python
# Backend sends progress updates
yield {
    "event": "block_generated",
    "data": {
        "block_index": 3,
        "total": 15,
        "content": "FR-003: ..."
    }
}

# Frontend displays in real-time
```

---

## 💻 Code Examples

### Example 1: Complete Generation Workflow

```python
"""
src/examples/ex45_generation_workflow.py

Complete block-by-block generation with HITL
"""

from typing import TypedDict, List, Annotated
from langgraph.graph import StateGraph, START, END
from langgraph.pregel import interrupt
from langgraph.checkpoint.postgres import PostgresSaver
from langchain_anthropic import ChatAnthropic
import operator

class GenerationState(TypedDict):
    spec_id: str
    template_id: str
    blocks_to_generate: List[dict]  # From template analysis
    current_index: int
    generated_content: str
    approved_blocks: Annotated[List[dict], operator.add]
    user_approved: bool
    user_feedback: str
    rag_context: str

def load_template_and_context(state: GenerationState) -> GenerationState:
    """Load template instructions and retrieve context"""
    # Load template from database
    template = get_template(state["template_id"])

    # Retrieve relevant context from user documents
    # (Using RAG from Lesson 11)
    context = retrieve_context_for_spec(state["spec_id"])

    return {
        "blocks_to_generate": template["blocks"],
        "rag_context": context
    }

def generate_block(state: GenerationState) -> GenerationState:
    """Generate one block using template instructions + context"""
    block_schema = state["blocks_to_generate"][state["current_index"]]

    llm = ChatAnthropic(model="claude-3-5-sonnet-20241022", temperature=0.3)

    # Build prompt from template instructions
    generation_instruction = block_schema["generation_instruction"]
    example = block_schema.get("example", "")

    prompt = f"""You are generating a specification block.

Block Type: {block_schema['type']}
Instructions: {generation_instruction}
Example from template: {example}

Context from user documents:
{state['rag_context']}

Generate this block following the template style exactly:"""

    response = llm.invoke(prompt)

    return {
        "generated_content": response.content
    }

def request_user_approval(state: GenerationState) -> GenerationState:
    """Pause and request approval"""
    current_block = {
        "index": state["current_index"],
        "type": state["blocks_to_generate"][state["current_index"]]["type"],
        "content": state["generated_content"]
    }

    # Pause workflow - execution stops here
    interrupt(
        value={
            "type": "block_approval_required",
            "spec_id": state["spec_id"],
            "block": current_block,
            "progress": {
                "current": state["current_index"] + 1,
                "total": len(state["blocks_to_generate"])
            }
        }
    )

    # After resume, check user decision
    if state.get("user_approved"):
        print(f"✓ Block {state['current_index'] + 1} approved")
        return {
            "approved_blocks": [current_block],
            "current_index": state["current_index"] + 1,
            "user_approved": False,  # Reset for next block
            "user_feedback": ""
        }
    else:
        print(f"✗ Block {state['current_index'] + 1} rejected")
        print(f"Feedback: {state.get('user_feedback', 'None')}")
        return {
            "user_approved": False,
            "generated_content": ""  # Will regenerate
        }

def regenerate_with_feedback(state: GenerationState) -> GenerationState:
    """Regenerate block incorporating user feedback"""
    block_schema = state["blocks_to_generate"][state["current_index"]]
    previous_content = state["generated_content"]
    feedback = state["user_feedback"]

    llm = ChatAnthropic(model="claude-3-5-sonnet-20241022", temperature=0.3)

    prompt = f"""You previously generated this block:
{previous_content}

The user provided this feedback:
{feedback}

Regenerate the block incorporating the feedback while maintaining
the template style from these instructions:
{block_schema['generation_instruction']}

Improved block:"""

    response = llm.invoke(prompt)

    return {
        "generated_content": response.content,
        "user_feedback": ""
    }

def assemble_final_document(state: GenerationState) -> GenerationState:
    """Assemble all approved blocks into final document"""
    document_parts = []

    for block in state["approved_blocks"]:
        document_parts.append(block["content"])

    final_doc = "\n\n".join(document_parts)

    return {"final_document": final_doc}

def check_approval_status(state: GenerationState) -> str:
    """Route based on approval"""
    if state.get("user_approved"):
        # Check if done
        if state["current_index"] >= len(state["blocks_to_generate"]):
            return "complete"
        return "next_block"
    else:
        return "regenerate"

def check_if_complete(state: GenerationState) -> str:
    """Check if all blocks generated"""
    if state["current_index"] >= len(state["blocks_to_generate"]):
        return "assemble"
    return "generate"

# Build workflow
workflow = StateGraph(GenerationState)

workflow.add_node("init", load_template_and_context)
workflow.add_node("generate", generate_block)
workflow.add_node("request_approval", request_user_approval)
workflow.add_node("regenerate", regenerate_with_feedback)
workflow.add_node("assemble", assemble_final_document)

workflow.add_edge(START, "init")
workflow.add_edge("init", "generate")
workflow.add_edge("generate", "request_approval")

workflow.add_conditional_edges(
    "request_approval",
    check_approval_status,
    {
        "next_block": "generate",
        "regenerate": "regenerate",
        "complete": "assemble"
    }
)

workflow.add_edge("regenerate", "request_approval")
workflow.add_edge("assemble", END)

# Compile with PostgreSQL checkpointer for persistence
checkpointer = PostgresSaver.from_conn_string(
    "postgresql://localhost/specbot"
)
app = workflow.compile(checkpointer=checkpointer)

# Usage: Start generation
config = {"configurable": {"thread_id": "spec_001"}}
initial_state = {
    "spec_id": "spec_001",
    "template_id": "tmpl_123",
    "blocks_to_generate": [],
    "current_index": 0,
    "generated_content": "",
    "approved_blocks": [],
    "user_approved": False,
    "user_feedback": "",
    "rag_context": "",
    "final_document": ""
}

# Start (will pause at first approval)
app.invoke(initial_state, config=config)

# Later: User approves/rejects
state = app.get_state(config)
state.values["user_approved"] = True  # or False
state.values["user_feedback"] = "Make it more specific"  # if rejected
app.invoke(state.values, config=config)
```

### Example 2: Server-Sent Events (SSE) Integration

```python
"""
src/examples/ex46_sse_integration.py

Real-time updates to frontend using SSE
"""

from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from typing import AsyncGenerator
import asyncio
import json

app = FastAPI()

class SpecificationGenerator:
    """Generator with SSE support"""

    async def generate_with_updates(
        self,
        spec_id: str,
        config: dict
    ) -> AsyncGenerator[str, None]:
        """Generate specification and yield SSE updates"""

        # Start workflow in background
        async for event in self._run_workflow(spec_id, config):
            # Format as SSE
            sse_data = f"data: {json.dumps(event)}\n\n"
            yield sse_data

    async def _run_workflow(self, spec_id: str, config: dict):
        """Run workflow and yield events"""

        # Initialize
        yield {
            "type": "started",
            "spec_id": spec_id,
            "message": "Starting specification generation"
        }

        # Simulate block generation
        total_blocks = 10
        for i in range(total_blocks):
            # Generate block
            await asyncio.sleep(2)  # Simulate generation time

            yield {
                "type": "block_generated",
                "spec_id": spec_id,
                "block_index": i,
                "total_blocks": total_blocks,
                "content": f"Generated content for block {i+1}",
                "progress_percent": ((i+1) / total_blocks) * 100
            }

            # Wait for approval
            yield {
                "type": "approval_required",
                "spec_id": spec_id,
                "block_index": i,
                "message": f"Please review block {i+1}"
            }

            # Simulate waiting for user
            await asyncio.sleep(1)

            yield {
                "type": "block_approved",
                "spec_id": spec_id,
                "block_index": i
            }

        # Complete
        yield {
            "type": "completed",
            "spec_id": spec_id,
            "message": "Specification generation complete",
            "download_url": f"/api/specifications/{spec_id}/download"
        }

generator = SpecificationGenerator()

@app.get("/api/specifications/{spec_id}/generate/stream")
async def generate_specification_stream(spec_id: str, request: Request):
    """SSE endpoint for real-time generation updates"""

    config = {"configurable": {"thread_id": spec_id}}

    return StreamingResponse(
        generator.generate_with_updates(spec_id, config),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )

@app.post("/api/specifications/{spec_id}/blocks/{block_index}/approve")
async def approve_block(spec_id: str, block_index: int, feedback: dict):
    """Approve or reject a block"""
    config = {"configurable": {"thread_id": spec_id}}

    # Get current state
    state = app.get_state(config)

    # Update with user decision
    state.values["user_approved"] = feedback.get("approved", False)
    state.values["user_feedback"] = feedback.get("feedback", "")

    # Resume workflow
    app.invoke(state.values, config=config)

    return {"status": "resumed"}
```

### Example 3: Frontend Integration (React)

```typescript
// src/frontend/SpecificationGenerator.tsx

import { useEffect, useState } from 'react';

interface Block {
  index: number;
  type: string;
  content: string;
}

export function SpecificationGenerator({ specId }: { specId: string }) {
  const [blocks, setBlocks] = useState<Block[]>([]);
  const [currentBlock, setCurrentBlock] = useState<Block | null>(null);
  const [progress, setProgress] = useState(0);
  const [status, setStatus] = useState<'generating' | 'awaiting_approval' | 'completed'>('generating');

  useEffect(() => {
    // Connect to SSE stream
    const eventSource = new EventSource(`/api/specifications/${specId}/generate/stream`);

    eventSource.addEventListener('block_generated', (e) => {
      const data = JSON.parse(e.data);
      setCurrentBlock({
        index: data.block_index,
        type: 'requirement',
        content: data.content
      });
      setProgress(data.progress_percent);
    });

    eventSource.addEventListener('approval_required', (e) => {
      setStatus('awaiting_approval');
    });

    eventSource.addEventListener('block_approved', (e) => {
      const data = JSON.parse(e.data);
      setBlocks(prev => [...prev, currentBlock!]);
      setStatus('generating');
    });

    eventSource.addEventListener('completed', (e) => {
      setStatus('completed');
      eventSource.close();
    });

    return () => eventSource.close();
  }, [specId]);

  const handleApprove = async () => {
    await fetch(`/api/specifications/${specId}/blocks/${currentBlock!.index}/approve`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ approved: true })
    });
  };

  const handleReject = async (feedback: string) => {
    await fetch(`/api/specifications/${specId}/blocks/${currentBlock!.index}/approve`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ approved: false, feedback })
    });
  };

  return (
    <div className="specification-generator">
      <div className="progress-bar">
        <div style={{ width: `${progress}%` }}></div>
        <span>{progress.toFixed(0)}% Complete</span>
      </div>

      <div className="approved-blocks">
        <h3>Approved Blocks</h3>
        {blocks.map(block => (
          <div key={block.index} className="block approved">
            {block.content}
          </div>
        ))}
      </div>

      {status === 'awaiting_approval' && currentBlock && (
        <div className="approval-section">
          <h3>Review Block {currentBlock.index + 1}</h3>
          <div className="block pending">
            {currentBlock.content}
          </div>

          <div className="approval-actions">
            <button onClick={handleApprove} className="approve-btn">
              ✓ Approve
            </button>
            <button onClick={() => {
              const feedback = prompt("What should be changed?");
              if (feedback) handleReject(feedback);
            }} className="reject-btn">
              ✗ Request Changes
            </button>
          </div>
        </div>
      )}

      {status === 'completed' && (
        <div className="completion-message">
          <h3>✓ Specification Complete!</h3>
          <button>Download Document</button>
        </div>
      )}
    </div>
  );
}
```

---

## 🏋️ Hands-On Exercise: Production-Ready Generation Pipeline

**Objective**: Build the complete production specification generation system.

### Requirements

Create a full system that:
1. Loads template and user documents
2. Generates blocks one by one
3. Pauses for approval after each block
4. Regenerates based on feedback (max 3 attempts per block)
5. Tracks progress and saves state
6. Sends real-time updates via SSE
7. Assembles final document in template format
8. Exports to DOCX/PDF matching original template style

### Starter Code

Create `src/exercises/ex14_production_pipeline.py`:

```python
"""
Exercise 14: Production-Ready Generation Pipeline

Complete specification generation with HITL
"""

from typing import TypedDict, List, Annotated
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.postgres import PostgresSaver
from fastapi import FastAPI
import operator

# TODO: Define complete state
class ProductionGenerationState(TypedDict):
    # Metadata
    spec_id: str
    template_id: str
    user_id: str

    # Context
    template_blocks: List[dict]
    user_documents: List[str]
    rag_retriever: object

    # Generation
    current_block_index: int
    current_block_content: str
    regeneration_count: int
    approved_blocks: Annotated[List[dict], operator.add]

    # User interaction
    user_approved: bool
    user_feedback: str

    # Progress tracking
    started_at: str
    estimated_completion: str
    blocks_per_minute: float

    # Output
    final_document: str
    export_format: str
    status: str

# TODO: Implement nodes
# 1. initialize_generation - Load template, documents, setup RAG
# 2. generate_block - Generate using template + RAG + previous context
# 3. validate_block - Check block meets constraints
# 4. request_approval - Pause for user (with SSE update)
# 5. regenerate_block - Regenerate with feedback
# 6. save_progress - Checkpoint after each block
# 7. assemble_document - Combine all blocks
# 8. export_document - Export to DOCX/PDF matching template
# 9. send_sse_update - Send progress to frontend

# TODO: Implement SSE integration
async def sse_generator(spec_id: str):
    """Yield SSE updates during generation"""
    pass

# TODO: Implement document export
def export_to_docx(blocks: List[dict], template_path: str) -> str:
    """Export blocks to DOCX matching template format"""
    pass

# TODO: Build complete workflow

# TODO: Create FastAPI endpoints
app = FastAPI()

@app.post("/api/specifications/generate")
async def start_generation(spec_request: dict):
    """Start new specification generation"""
    pass

@app.get("/api/specifications/{spec_id}/stream")
async def generation_stream(spec_id: str):
    """SSE stream for real-time updates"""
    pass

@app.post("/api/specifications/{spec_id}/blocks/{block_index}/review")
async def review_block(spec_id: str, block_index: int, review: dict):
    """Approve or reject block"""
    pass
```

<details>
<summary>📝 <strong>Solution: Production-Ready Generation Pipeline</strong></summary>

```python
"""Solution: Production-Ready Block Generation with HITL"""
from typing import TypedDict, List, Literal
from langgraph.graph import StateGraph, START, END
from langchain_anthropic import ChatAnthropic

class GenState(TypedDict):
    user_input: str
    generated_blocks: List[dict]
    approved_blocks: List[dict]
    current_block: dict
    user_feedback: str
    status: str

def generate_block(state: GenState) -> GenState:
    llm = ChatAnthropic(model="claude-3-5-sonnet-20241022")
    response = llm.invoke(f"Generate requirement based on: {state['user_input']}")
    block = {"id": f"FR-{len(state['generated_blocks'])+1:03d}", "content": response.content}
    return {"generated_blocks": state["generated_blocks"] + [block], "current_block": block}

def request_approval(state: GenState) -> GenState:
    print(f"Block: {state['current_block']}")
    feedback = input("Approve? (y/n/edit): ")
    return {"user_feedback": feedback}

def check_approval(state: GenState) -> Literal["approved", "edit", "reject"]:
    if state["user_feedback"] == "y":
        return "approved"
    elif state["user_feedback"] == "edit":
        return "edit"
    return "reject"

def approve_block(state: GenState) -> GenState:
    return {"approved_blocks": state["approved_blocks"] + [state["current_block"]]}

workflow = StateGraph(GenState)
workflow.add_node("generate", generate_block)
workflow.add_node("request", request_approval)
workflow.add_node("approve", approve_block)

workflow.add_edge(START, "generate")
workflow.add_edge("generate", "request")
workflow.add_conditional_edges("request", check_approval, {"approved": "approve", "edit": "generate", "reject": END})
workflow.add_edge("approve", END)

app = workflow.compile()
print("Production-ready generation with HITL approval")
```

</details>

---

## 🚀 Challenge: Advanced Features

**Advanced**: Add production-grade features to the generation pipeline.

### Challenge Requirements

1. **Parallel block generation**: Generate multiple blocks simultaneously when possible
2. **Smart context selection**: Use only relevant parts of RAG context per block
3. **Quality scoring**: Automatically score each generated block
4. **Auto-approval**: Approve high-confidence blocks automatically
5. **A/B testing**: Generate 2 variants, let user choose
6. **Undo/redo**: Allow users to revert to previous versions
7. **Collaborative editing**: Multiple users can review simultaneously

<details>
<summary>📝 <strong>Solution: Advanced Features</strong></summary>

```python
"""Solution: Advanced features with parallel generation and quality scoring"""
from typing import TypedDict, List
from langgraph.graph import StateGraph, START, END
from langchain_anthropic import ChatAnthropic
import asyncio

class AdvancedState(TypedDict):
    blocks_to_generate: int
    generated_blocks: List[dict]
    quality_scores: List[float]

async def parallel_generate(state: AdvancedState) -> AdvancedState:
    llm = ChatAnthropic(model="claude-3-5-sonnet-20241022")

    async def gen_block(i):
        response = await llm.ainvoke(f"Generate block {i}")
        return {"id": f"FR-{i:03d}", "content": response.content}

    blocks = await asyncio.gather(*[gen_block(i) for i in range(state["blocks_to_generate"])])
    return {"generated_blocks": list(blocks)}

def score_quality(state: AdvancedState) -> AdvancedState:
    scores = [0.95 if "SHALL" in b["content"] else 0.7 for b in state["generated_blocks"]]
    return {"quality_scores": scores}

workflow = StateGraph(AdvancedState)
workflow.add_node("generate", parallel_generate)
workflow.add_node("score", score_quality)
workflow.add_edge(START, "generate")
workflow.add_edge("generate", "score")
workflow.add_edge("score", END)

app = workflow.compile()
result = asyncio.run(app.ainvoke({"blocks_to_generate": 5, "generated_blocks": [], "quality_scores": []}))
print(f"Generated {len(result['generated_blocks'])} blocks, avg quality: {sum(result['quality_scores'])/len(result['quality_scores']):.2f}")
```

</details>

---

## 🎓 Key Takeaways

### Production Generation Best Practices

✅ **DO**:
- Save state after every block
- Send real-time progress updates
- Limit regeneration attempts (3 max)
- Provide clear approval UI
- Track quality metrics
- Handle errors gracefully
- Test with real templates

❌ **DON'T**:
- Generate all blocks before approval
- Lose progress on errors
- Skip validation
- Assume LLM always generates valid blocks
- Forget to handle edge cases
- Skip user feedback loop

---

## 🔄 Story Progress: SpecBot v0.14

**What we built**: SpecBot's complete generation workflow!

```python
# SpecBot v0.14 - Complete Generation Pipeline

# User starts new specification
spec = create_specification(
    template_id="tmpl_123",
    title="User Authentication System",
    documents=["requirements.pdf", "designs.pdf"]
)

# Generation runs block-by-block
# Frontend shows real-time progress via SSE
# User approves/rejects each block
# Regenerates based on feedback
# Saves progress continuously

# After 15 blocks approved...
final_doc = download_specification(spec.id)
# → Perfect DOCX matching template format!
```

**Next Step**: Lesson 15 wraps everything up with deployment, monitoring, and productionization!

---

**Continue to [Lesson 15: Final Integration & Deployment →](./15-final-integration.md)**
