# Technical Implementation Plan: SpecGeny MVP Platform

**Feature**: 001-specgeny-mvp-platform
**Created**: 2025-10-28
**Status**: Draft

## Architecture Overview

### System Architecture (In-Memory State)
```
┌─────────────────────────────────────────────────────┐
│         Frontend (React + shadcn/ui)                │
│  File Upload → Processing Status → Review Editor   │
└──────────────────────┬──────────────────────────────┘
                       │ REST API
┌──────────────────────┴──────────────────────────────┐
│      Backend (FastAPI + LangGraph In-Memory)        │
│                                                     │
│  LangGraph Pipeline (Single Agent, No DB):         │
│  FileReader → ContextBuilder → LLM → Parser →      │
│  ConfidenceCalc → Return JSON                      │
│                                                     │
│  State: Python dict in memory (session-based)      │
│  Files: /tmp/uploads (cleared after response)      │
└──────────────────────┬──────────────────────────────┘
                       │
┌──────────────────────┴──────────────────────────────┐
│  LLM API (DeepSeek-Reasoner OR Claude Sonnet 4.5)  │
│  Pandoc (PDF Export - subprocess)                  │
└─────────────────────────────────────────────────────┘
```

**Key Change**: NO SQLite, NO persistence. Everything is stateless request/response.

## Technology Stack

### Backend

| Component | Technology | Why |
|-----------|-----------|-----|
| Framework | FastAPI 0.104+ | Async-native, auto OpenAPI docs |
| Orchestration | LangGraph 0.0.20+ | State management within request lifecycle, learning investment |
| State Storage | Python dict (in-memory) | No database needed, cleared after response |
| File Storage | /tmp/uploads (temp) | Deleted immediately after generation |
| File Parsing | python-docx, PyPDF2, Pillow, openpyxl | Multi-format support |
| LLM Client | anthropic OR openai SDK | Async API calls |
| PDF Export | Pandoc 3.0+ (subprocess) | Markdown → PDF conversion |
| Validation | Pydantic 2.5+ | Request/response schemas |

### Frontend

| Component | Technology | Why |
|-----------|-----------|-----|
| Framework | React 18.2+ (NOT Next.js) | Simpler for MVP than Next.js SSR |
| Language | TypeScript 5.2+ | Type safety |
| Build Tool | Vite 5.0+ | Fast dev server |
| **UI Components** | **shadcn/ui (exclusive)** | **Primary component library** |
| UI Fallback | Radix UI | Only when shadcn missing component |
| Styling | Tailwind CSS 3.4+ | Utility-first |
| Server State | TanStack Query 5.0+ | API state management |
| Client State | Zustand 4.4+ | Lightweight local state |
| Forms | React Hook Form 7.48+ | Works with shadcn Form |
| Routing | React Router 6.20+ | Client-side only |
| HTTP Client | Axios 1.6+ | Upload progress tracking |

### Infrastructure

| Component | Service |
|-----------|---------|
| Frontend | Vercel (zero-config) |
| Backend | Railway or Render |
| CI/CD | GitHub Actions |
| Logging | Python logging (console only for MVP) |

## shadcn/ui Component Usage

### Required shadcn Components

**File Upload Interface:**
- `Card` - Main upload container
- `Button` - Upload trigger, action buttons
- `Input` - Hidden file input
- `Label` - Upload instructions
- `Badge` - File type indicators
- `Progress` - Upload progress bar
- `Alert` - Error messages

**Generation Status:**
- `Card` - Status container
- `Progress` - Generation progress
- `Spinner` - Loading indicator
- `Badge` - Status indicators (pending/processing/complete)

**Specification Preview:**
- `Tabs` - Section navigation
- `Card` - Section containers
- `Badge` - Confidence scores (green/yellow/red)
- `Separator` - Section dividers
- `ScrollArea` - Long content scrolling

**Section Editor:**
- `Textarea` - Content editing
- `Button` - Save/Cancel actions
- `Label` - Section titles
- `Alert` - Validation errors

**Export Controls:**
- `Button` - Download MD/PDF
- `DropdownMenu` - Export options
- `Toast` (sonner) - Success/error notifications

**Fallback to Radix (only if needed):**
- `Tooltip` - Hover information
- `Popover` - Contextual help

## LangGraph Architecture (In-Memory)

### Why LangGraph for Single Agent?

1. **State Management**: Clean state transitions between pipeline steps
2. **Error Handling**: Built-in error recovery without try/catch spaghetti
3. **Future-Proof**: Zero refactor when adding multi-agent in V2.0
4. **Observability**: Graph execution tracing for debugging
5. **Learning**: Team builds agentic framework skills

**Trade-off Accepted**: 3-5 days additional implementation time vs. future rewrite

### Pipeline Nodes
```python
# LangGraph nodes (simplified)
def file_reader_node(state: dict) -> dict:
    """Parse all uploaded files → extract text/images"""
    return {"extracted_content": "..."}

def context_builder_node(state: dict) -> dict:
    """Template + all file content → single prompt"""
    return {"llm_prompt": "..."}

def llm_node(state: dict) -> dict:
    """Call DeepSeek/Claude API"""
    return {"llm_response": "..."}

def response_parser_node(state: dict) -> dict:
    """Parse Markdown sections from LLM"""
    return {"parsed_sections": {...}}

def confidence_calculator_node(state: dict) -> dict:
    """Apply heuristics to each section"""
    return {"confidence_scores": {...}}
```

**State Schema (Python dict, no persistence):**
```python
{
    "session_id": "uuid4",
    "files": [FileUpload, ...],
    "extracted_content": str,
    "llm_prompt": str,
    "llm_response": str,
    "parsed_sections": dict[str, str],
    "confidence_scores": dict[str, int],
    "errors": list[str]
}
```

## API Endpoints (Simplified - No Jobs)

**Base URL**: `/api/v1`

### Stateless Endpoints

| Method | Endpoint | Purpose | Request | Response |
|--------|----------|---------|---------|----------|
| POST | `/generate` | Upload files + generate spec | Multipart files + template_name | Full spec JSON (sections + scores) |
| POST | `/export/pdf` | Convert MD to PDF | JSON (markdown content) | PDF file download |

**That's it. Two endpoints.**

### Example Flow
```http
# 1. Generate specification (single call)
POST /api/v1/generate
Content-Type: multipart/form-data

files: [file1.docx, file2.pdf, diagram.png]
template_name: "uipath_pdd"

Response 200:
{
  "specification": {
    "Executive Summary": "...",
    "User Stories": "...",
    "Technical Architecture": "..."
  },
  "confidence_scores": {
    "Executive Summary": {"score": 85, "classification": "high"},
    "User Stories": {"score": 72, "classification": "medium"},
    "Technical Architecture": {"score": 45, "classification": "low"}
  },
  "generation_time_seconds": 143
}

# 2. Export to PDF (separate call)
POST /api/v1/export/pdf
Content-Type: application/json

{
  "markdown": "# Executive Summary\n\n..."
}

Response 200:
Content-Type: application/pdf
[PDF binary]
```

## File Processing

### Supported Formats & Extraction

| Format | Library | Method |
|--------|---------|--------|
| .txt, .md | Built-in | Read UTF-8 |
| .docx | python-docx | Extract paragraphs |
| .pdf | PyPDF2 | Extract text per page |
| .png, .jpg | Pillow + LLM | Base64 → multimodal LLM |
| .xlsx | openpyxl | Extract as CSV-like text |

### Context Stuffing (Single Prompt)
```python
# Build single prompt from all files
prompt = f"""
{TEMPLATE_INSTRUCTIONS}

## Uploaded Project Files

### File 1: requirements.docx
{docx_text_content}

### File 2: architecture.pdf
{pdf_text_content}

### File 3: workflow_diagram.png
[Image embedded as base64]

Generate a complete UiPath PDD following the template structure.
"""
```

**Token Limit**: 200K tokens (DeepSeek/Claude)
**If Exceeded**: Truncate oldest files with warning message

## Confidence Score Heuristics
```python
def calculate_confidence(section_text: str, source_files: list) -> int:
    score = 100
    
    # Section too short
    if len(section_text) < 200:
        score -= 30
    
    # Generic phrases detected
    generic = ["tbd", "to be determined", "n/a", "not specified", 
               "will be defined", "unclear", "unknown"]
    if any(phrase in section_text.lower() for phrase in generic):
        score -= 20
    
    # No keywords from source files
    keywords = extract_keywords_from_files(source_files)
    if not any(kw in section_text.lower() for kw in keywords):
        score -= 20
    
    # Empty section
    if not section_text.strip():
        score = 0
    
    return max(0, score)

# Classification
# ≥80: "high" (green)
# 50-79: "medium" (yellow)
# <50: "low" (red)
```

## Security

### File Upload
- **Client**: Validate type + size before upload
- **Server**: Magic number validation (not extension)
- **Storage**: `/tmp/uploads/{request_id}/` (deleted after response)
- **Size Limits**: 50MB total, 10 files max

### API
- **Rate Limiting**: 10 req/min per IP (simple middleware)
- **CORS**: Whitelist frontend origin
- **Input Validation**: Pydantic models
- **Path Traversal**: No user-supplied file paths

## Performance Targets

| Metric | Target |
|--------|--------|
| File Upload | < 3s (50MB) |
| Total Generation | < 5min (P95) |
| PDF Export | < 5s |
| Concurrent Requests | 20 simultaneous |

## Deployment

### Development
```bash
# Backend
cd backend
uvicorn main:app --reload --port 8000

# Frontend
cd frontend
npm run dev  # Vite on port 5173
```

### Production
- **Frontend**: Vercel (auto-deploy from `main`)
- **Backend**: Railway Docker container
- **Pandoc**: Installed in Dockerfile

### Environment Variables

**Backend:**
```bash
LLM_PROVIDER=deepseek  # or 'claude'
LLM_API_KEY=xxxxx
UPLOAD_DIR=/tmp/uploads
MAX_FILE_SIZE_MB=50
MAX_FILES=10
CORS_ORIGINS=https://specgeny.com
```

**Frontend:**
```bash
VITE_API_BASE_URL=https://api.specgeny.com/api/v1
VITE_MAX_FILE_SIZE_MB=50
VITE_MAX_FILES=10
```

## Testing Strategy

### Backend
- **Unit**: File parsing, confidence calculation
- **Integration**: Full generation with mock LLM
- **Fixtures**: Sample files in all formats

### Frontend
- **Component**: shadcn component interactions
- **Integration**: API mocking with MSW

## Dependencies

### Backend (pyproject.toml)
```toml
fastapi = ">=0.104"
uvicorn[standard] = ">=0.24"
pydantic = ">=2.5"
python-docx = ">=1.1"
pypdf2 = ">=3.0"
pillow = ">=10.0"
openpyxl = ">=3.1"
langgraph = ">=0.0.20"
anthropic = ">=0.8"  # or openai
python-multipart = ">=0.0.6"
```

### Frontend (package.json)
```json
{
  "react": "^18.2",
  "typescript": "^5.2",
  "vite": "^5.0",
  "@tanstack/react-query": "^5.0",
  "zustand": "^4.4",
  "react-hook-form": "^7.48",
  "react-router-dom": "^6.20",
  "axios": "^1.6",
  "tailwindcss": "^3.4"
}
```

## Implementation Phases

**Week 1-2: Backend Core**
- FastAPI + file upload endpoints
- File parsers (python-docx, PyPDF2, PIL, openpyxl)
- LangGraph pipeline (without LLM)

**Week 3: LLM Integration**
- UiPath PDD template prompt
- DeepSeek/Claude API integration
- Context builder + response parser

**Week 4: Frontend Core**
- React + shadcn/ui setup
- File upload UI (Card + Button + Progress)
- Generation status display

**Week 5: Editor & Export**
- Section editing (Textarea + Button)
- Confidence display (Badge with colors)
- Markdown download + PDF export

**Week 6: Polish & Deploy**
- Error handling (Alert components)
- Loading states (Spinner + Progress)
- Production deployment

**Version**: 1.0.0 | **Created**: 2025-10-28