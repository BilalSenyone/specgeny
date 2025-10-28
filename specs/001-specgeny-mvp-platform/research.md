# Technical Research: SpecGeny MVP Platform

**Feature**: 001-specgeny-mvp-platform
**Created**: 2025-10-28
**Phase**: 0 - Research & Technology Selection

## Purpose

This document consolidates technical research findings and justifies technology choices for the SpecGeny MVP. All decisions align with the project constitution (`.specify/memory/constitution.md`) and technical instructions (`documents/tech-instructions.md`).

## Key Technical Decisions

### 1. LLM Provider Selection

**Decision**: Support both DeepSeek-Reasoner AND Claude Sonnet 4.5 with runtime configuration

**Rationale**:
- **DeepSeek-Reasoner**: Lower cost per API call (~$0.50-1.00 per spec), excellent reasoning capabilities, native multimodal support
- **Claude Sonnet 4.5**: Premium option with superior output quality (~$2-3 per spec), proven track record for document generation
- **Runtime toggle**: Allow MVP benchmarking with real user files to determine best cost/performance ratio

**Implementation**:
```python
# backend/src/config.py
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "deepseek")  # or "claude"
```

**Alternatives Considered**:
- **GPT-4 Vision**: Rejected due to higher cost ($3-5 per spec) with no significant quality improvement over Claude
- **Open-source models (Llama 3, Mistral)**: Rejected due to self-hosting complexity and latency concerns (violates Fast Feedback principle)

**Constitution Alignment**: Principle V (Fast Feedback) - API-based LLMs ensure <5min generation time

---

### 2. LangGraph for Single-Agent Orchestration

**Decision**: Use LangGraph despite single-agent MVP

**Rationale** (as per Constitution Principle VII):
1. **Zero Architectural Rework**: When adding multi-agent in V2.0 (e.g., specialized analyzer, mapper, generator), only add nodes to existing graph
2. **Clean State Management**: Explicit state transitions between file_reader → context_builder → llm → parser → confidence_calculator
3. **Built-in Error Recovery**: Graph handles node failures without try/catch spaghetti
4. **Observable Execution**: Graph tracing for debugging pipeline issues
5. **Team Learning**: Agentic framework skills transferable to future projects

**Cost Accepted**: 3-5 days additional implementation time

**Simpler Alternative Rejected**:
- **Sequential function calls**: Rejected because requires complete rewrite when introducing parallel agents or conditional branching

**Code Example**:
```python
# backend/src/graph/pipeline.py
from langgraph.graph import StateGraph

workflow = StateGraph(dict)
workflow.add_node("file_reader", file_reader_node)
workflow.add_node("context_builder", context_builder_node)
workflow.add_node("llm", llm_node)
workflow.add_node("parser", response_parser_node)
workflow.add_node("confidence", confidence_calculator_node)

workflow.set_entry_point("file_reader")
workflow.add_edge("file_reader", "context_builder")
workflow.add_edge("context_builder", "llm")
workflow.add_edge("llm", "parser")
workflow.add_edge("parser", "confidence")
workflow.set_finish_point("confidence")
```

**Constitution Alignment**: Principle VII (Strategic Learning Investment) explicitly approves this

---

### 3. Stateless Architecture (No SQLite Persistence)

**Decision**: In-memory state during request lifecycle, no database

**Rationale**:
- **Simplicity First** (Principle I): Eliminates database setup, migrations, connection pooling
- **Faster MVP**: Removes 1 week of database work (schema design, ORM setup, testing)
- **Scalability**: Stateless design easier to horizontally scale (add backend instances) than stateful with shared DB
- **User Expectation**: MVP users expect immediate results, not job queue polling

**Implementation**:
```python
# backend/src/api/routes/generate.py
@router.post("/generate")
async def generate_specification(files: List[UploadFile]):
    state = {
        "request_id": str(uuid4()),
        "files": files,
        # ... in-memory only
    }
    result = await pipeline.ainvoke(state)
    cleanup_temp_files(state["request_id"])
    return result  # Response contains full spec JSON
```

**Alternatives Considered**:
- **SQLite with job persistence**: Rejected because adds complexity without MVP value (users complete workflow in one session)
- **Redis for session state**: Rejected because requires external service (violates simplicity)

**Trade-off**: Users lose work if browser closes mid-generation. Accepted for MVP; V1.5 can add optional persistence if user feedback demands it.

**Constitution Alignment**: Principle I (Simplicity First) - filesystem over database

---

### 4. shadcn/ui as Exclusive UI Library

**Decision**: shadcn/ui for all components, Radix UI only as fallback

**Rationale**:
- **Consistency**: Single design system reduces visual inconsistencies
- **Copy-Paste Simplicity**: shadcn components are just TypeScript files in `/src/components/ui/`, not npm packages
- **Customizability**: Full control over component code (not black-box library)
- **Accessibility**: Built on Radix primitives (ARIA compliant)
- **Constitution Mandate**: Non-negotiable per Constitution Technical Constraints

**Required Components**:
```bash
# Install via shadcn CLI
npx shadcn-ui@latest add button card badge progress textarea alert tabs separator scroll-area toast
```

**Fallback to Radix**:
Only if shadcn missing specific component (e.g., Tooltip, Popover):
```bash
npm install @radix-ui/react-tooltip @radix-ui/react-popover
```

**Alternatives Considered**:
- **Material-UI (MUI)**: Rejected due to larger bundle size and opinionated styling
- **Chakra UI**: Rejected due to heavy JavaScript runtime (violates performance goals)

**Constitution Alignment**: Principle I (Simplicity First) - copy-paste components over heavy frameworks

---

### 5. File Parsing Libraries

**Decision**: Native Python libraries for all formats

| Format | Library | Justification |
|--------|---------|---------------|
| .txt, .md | Built-in `open()` | No dependencies needed |
| .docx | python-docx 1.1+ | Industry standard, actively maintained |
| .pdf | PyPDF2 3.0+ | Pure Python (no system deps), good text extraction |
| .png, .jpg | Pillow 10.0+ | Convert to base64 for LLM multimodal input |
| .xlsx | openpyxl 3.1+ | Read-only mode (fast), extracts as CSV-like text |

**Alternatives Considered**:
- **PyMuPDF for PDFs**: Rejected due to complex installation (requires system libraries)
- **Tesseract OCR for images**: Rejected because modern LLMs (DeepSeek, Claude Vision) handle OCR natively
- **pandas for Excel**: Rejected due to large dependency footprint (numpy, etc.) for simple text extraction

**Implementation Note**: Images are sent directly to multimodal LLM (base64-encoded), not pre-processed with OCR.

**Constitution Alignment**: Principle I (Simplicity First) - standard libraries over exotic tools

---

### 6. PDF Export Strategy

**Decision**: Pandoc subprocess for Markdown → PDF conversion

**Rationale**:
- **Proven Tool**: Pandoc is industry-standard for document conversion
- **High Quality**: Professional PDF output with proper formatting
- **Simple Integration**: Single subprocess call, no complex library
- **Lightweight**: Only used on-demand (export endpoint), not during generation

**Installation**:
```dockerfile
# Dockerfile
RUN apt-get update && apt-get install -y pandoc texlive-xetex
```

**Code Example**:
```python
# backend/src/services/pdf_export.py
import subprocess

def markdown_to_pdf(markdown_content: str) -> bytes:
    result = subprocess.run(
        ["pandoc", "-f", "markdown", "-t", "pdf", "--pdf-engine=xelatex"],
        input=markdown_content.encode(),
        capture_output=True,
        timeout=10
    )
    return result.stdout
```

**Alternatives Considered**:
- **WeasyPrint**: Rejected due to CSS complexity (overkill for simple specs)
- **ReportLab**: Rejected because requires manual layout code (Pandoc auto-formats)

**Constitution Alignment**: Principle V (Fast Feedback) - <5s PDF export via subprocess

---

### 7. Context Stuffing Strategy (No RAG)

**Decision**: Concatenate all files into single LLM prompt, no vector database

**Rationale**:
- **Token Budget**: 10 files × 50 MB ~= 150K-180K tokens (well within 200K limit)
- **Simplicity**: No embeddings, no Pinecone, no vector search logic
- **Accuracy**: LLM sees ALL context, no retrieval errors from poor embeddings
- **Cost**: Zero vector DB costs (~$70/month saved)

**Implementation**:
```python
# backend/src/graph/nodes/context_builder.py
def build_prompt(files: List[FileContent], template: str) -> str:
    file_sections = []
    for file in files:
        file_sections.append(f"### File: {file.name}\n{file.content}")

    return f"{template}\n\n## Uploaded Files\n" + "\n\n".join(file_sections)
```

**Overflow Handling**: If files exceed 200K tokens, truncate oldest files with warning message to user.

**Alternatives Considered**:
- **RAG with Pinecone**: Rejected per Constitution (Principle I) - unnecessary complexity for 10 files
- **Chunking + summarization**: Rejected because loses detailed context (specs need specifics)

**Constitution Alignment**: Principle I (Simplicity First) - context stuffing over RAG

---

### 8. Confidence Score Heuristics

**Decision**: Rule-based Python heuristics, zero LLM self-assessment

**Rationale** (as per Constitution Principle IV):
1. **Deterministic**: Same input → same scores (reproducible)
2. **Fast**: No additional LLM calls (saves cost + latency)
3. **Reliable**: LLM self-scores are notoriously unreliable (overconfident or underconfident)

**Heuristics**:
```python
def calculate_confidence(section_text: str, source_files: List[str]) -> int:
    score = 100

    # Section too short (<200 chars)
    if len(section_text) < 200:
        score -= 30

    # Generic/placeholder phrases detected
    generic = ["tbd", "to be determined", "n/a", "not specified",
               "will be defined", "unclear", "unknown"]
    if any(phrase in section_text.lower() for phrase in generic):
        score -= 20

    # No keywords from source files (indicates hallucination)
    keywords = extract_keywords_from_files(source_files)
    if not any(kw in section_text.lower() for kw in keywords):
        score -= 20

    # Empty section
    if not section_text.strip():
        score = 0

    return max(0, score)
```

**Classification**:
- **Green (≥80%)**: High confidence, likely accurate
- **Yellow (50-79%)**: Medium confidence, review recommended
- **Red (<50%)**: Low confidence, likely needs editing

**Alternatives Considered**:
- **LLM self-assessment**: Rejected per Constitution Principle IV (unreliable)
- **Similarity scoring**: Rejected due to complexity (requires embeddings)

**Constitution Alignment**: Principle IV (Deterministic Quality) - rule-based heuristics

---

### 9. Frontend State Management

**Decision**: TanStack Query for server state + Zustand for client state

**Rationale**:
- **TanStack Query**: Perfect for API state (caching, refetching, loading states)
- **Zustand**: Minimal boilerplate for localStorage session management
- **Separation**: Server state (spec data) separate from client state (UI preferences)

**Code Example**:
```typescript
// src/services/api.ts (TanStack Query)
export const useGenerateSpec = () => {
  return useMutation({
    mutationFn: (files: File[]) => axios.post('/api/v1/generate', files),
    onSuccess: (data) => {
      specStore.setState({ currentSpec: data.specification })
    }
  })
}

// src/stores/specStore.ts (Zustand)
export const specStore = create<SpecStore>((set) => ({
  sessionId: localStorage.getItem('session_id') || uuidv4(),
  currentSpec: null,
  setSpec: (spec) => set({ currentSpec: spec })
}))
```

**Alternatives Considered**:
- **Redux**: Rejected due to boilerplate (violates simplicity)
- **Context API**: Rejected because lacks built-in caching (TanStack Query superior)

**Constitution Alignment**: Principle I (Simplicity First) - minimal state libraries

---

### 10. Testing Strategy (Selective TDD)

**Decision**: Test critical paths only, per Constitution Quality Standards

**Critical Paths**:
1. **File parsing** (unit): Each format (docx, pdf, xlsx, images) with real fixtures
2. **LLM integration** (integration): Mock API responses, test prompt building + parsing
3. **Template validation** (unit): Ensure parser extracts all required sections
4. **Confidence calculation** (unit): Verify heuristics work correctly
5. **End-to-end** (integration): 3-5 tests with real multi-format files

**Not Tested** (to save time):
- Pandoc PDF export (proven external tool)
- shadcn/ui components (library responsibility)
- Trivial functions (getters/setters)

**Tools**:
- Backend: pytest with fixtures in `/tests/fixtures/`
- Frontend: Vitest + React Testing Library + MSW for API mocking

**Constitution Alignment**: Quality Standards (Selective TDD) - test critical paths only

---

## Research Outcomes

### Resolved Clarifications

All technical decisions are now resolved. No NEEDS CLARIFICATION markers remain.

### Technology Matrix

| Category | Technology | Version | Justification Reference |
|----------|-----------|---------|------------------------|
| Backend Language | Python | 3.11+ | Constitution stack requirement |
| Backend Framework | FastAPI | 0.104+ | Async-native, auto docs |
| Orchestration | LangGraph | 0.0.20+ | Decision #2 (Strategic learning) |
| LLM Provider | DeepSeek/Claude | Latest | Decision #1 (Runtime toggle) |
| File Parsing | python-docx, PyPDF2, PIL, openpyxl | Latest stable | Decision #5 (Native libraries) |
| PDF Export | Pandoc | 3.0+ | Decision #6 (Subprocess) |
| Frontend Language | TypeScript | 5.2+ | Type safety |
| Frontend Framework | React | 18.2+ | Constitution requirement |
| Build Tool | Vite | 5.0+ | Fast dev server |
| UI Library | shadcn/ui | Latest | Decision #4 (Exclusive use) |
| Styling | Tailwind CSS | 3.4+ | Utility-first |
| Server State | TanStack Query | 5.0+ | Decision #9 (API state) |
| Client State | Zustand | 4.4+ | Decision #9 (localStorage) |
| Testing (Backend) | pytest | Latest | Constitution requirement |
| Testing (Frontend) | Vitest | Latest | Vite-native |

### Dependencies Finalized

**Backend (`pyproject.toml`)**:
```toml
[tool.poetry.dependencies]
python = "^3.11"
fastapi = ">=0.104"
uvicorn = {extras = ["standard"], version = ">=0.24"}
pydantic = ">=2.5"
python-multipart = ">=0.0.6"
langgraph = ">=0.0.20"
anthropic = ">=0.8"
openai = ">=1.3"  # Alternative LLM
python-docx = ">=1.1"
pypdf2 = ">=3.0"
pillow = ">=10.0"
openpyxl = ">=3.1"

[tool.poetry.group.dev.dependencies]
pytest = ">=7.4"
pytest-asyncio = ">=0.21"
ruff = ">=0.1"
mypy = ">=1.7"
```

**Frontend (`package.json`)**:
```json
{
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "typescript": "^5.2.0",
    "@tanstack/react-query": "^5.0.0",
    "zustand": "^4.4.0",
    "react-hook-form": "^7.48.0",
    "react-router-dom": "^6.20.0",
    "axios": "^1.6.0",
    "tailwindcss": "^3.4.0",
    "class-variance-authority": "^0.7.0",
    "clsx": "^2.0.0",
    "tailwind-merge": "^2.0.0"
  },
  "devDependencies": {
    "@vitejs/plugin-react": "^4.2.0",
    "vite": "^5.0.0",
    "vitest": "^1.0.0",
    "@testing-library/react": "^14.0.0",
    "msw": "^2.0.0",
    "eslint": "^8.55.0",
    "@typescript-eslint/parser": "^6.15.0"
  }
}
```

### Best Practices Identified

1. **LangGraph Patterns**: Use `StateGraph` with explicit edges, not `MessageGraph` (less flexible)
2. **Multimodal LLM**: Send images as base64 in `image_url` content blocks (Anthropic/OpenAI format)
3. **File Validation**: Use `python-magic` for magic number validation (not file extensions)
4. **Rate Limiting**: Simple IP-based middleware (10 req/min) via `slowapi` library
5. **CORS**: Whitelist only frontend origin, not `allow_origins=["*"]`
6. **Environment Variables**: Use `pydantic-settings` for type-safe config

---

## Next Steps

Research phase complete. Proceed to:
- **Phase 1**: Generate `data-model.md`, API contracts (`contracts/openapi.yaml`), and `quickstart.md`

**Version**: 1.0.0 | **Created**: 2025-10-28
