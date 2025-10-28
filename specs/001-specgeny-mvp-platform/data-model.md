# Data Model: SpecGeny MVP Platform

**Feature**: 001-specgeny-mvp-platform
**Created**: 2025-10-28
**Phase**: 1 - Design & Contracts

## Purpose

This document defines the data structures for the SpecGeny MVP. **Important**: The MVP uses a **stateless architecture** with in-memory state during request lifecycle only. No database persistence is implemented.

## Architecture Context

**State Management Strategy**:
- **Request Lifecycle**: Python dict in memory (LangGraph state)
- **Temporary Files**: `/tmp/uploads/{request_id}/` (deleted after response)
- **Client State**: Browser localStorage (session ID, cached specs)
- **No Persistence**: Zero database, zero job queue

## Core Entities

### 1. GenerationRequest (Request Schema)

**Purpose**: Pydantic model for incoming specification generation requests

**Fields**:
| Field | Type | Required | Validation | Description |
|-------|------|----------|------------|-------------|
| `files` | `List[UploadFile]` | Yes | 1-10 files | Uploaded project files |
| `template_name` | `str` | Yes | Enum: `"uipath_pdd"` | Specification template identifier |

**Validation Rules**:
- **FR-002**: Maximum 10 files
- **FR-003**: Combined file size ≤ 50 MB
- **FR-004**: File extensions must be in `[.txt, .md, .docx, .pdf, .png, .jpg, .xlsx]`
- Magic number validation (not extension-based)

**Pydantic Schema**:
```python
# backend/src/models/requests.py
from fastapi import UploadFile
from pydantic import BaseModel, Field, field_validator
from typing import List

class GenerationRequest(BaseModel):
    template_name: str = Field(
        default="uipath_pdd",
        description="Specification template to use"
    )

    @field_validator('template_name')
    def validate_template(cls, v):
        allowed = ["uipath_pdd"]
        if v not in allowed:
            raise ValueError(f"Template must be one of {allowed}")
        return v
```

---

### 2. FileMetadata (Internal State)

**Purpose**: Represents parsed file information within LangGraph pipeline state

**Fields**:
| Field | Type | Description |
|-------|------|-------------|
| `filename` | `str` | Original uploaded filename |
| `file_type` | `str` | Extension (`.docx`, `.pdf`, etc.) |
| `size_bytes` | `int` | File size in bytes |
| `content_text` | `str` | Extracted text content |
| `content_image` | `Optional[str]` | Base64-encoded image (for .png/.jpg) |
| `extraction_status` | `str` | Enum: `"success"`, `"partial"`, `"failed"` |
| `error_message` | `Optional[str]` | Error details if extraction failed |

**Python TypedDict**:
```python
# backend/src/models/internal.py
from typing import TypedDict, Optional

class FileMetadata(TypedDict):
    filename: str
    file_type: str
    size_bytes: int
    content_text: str
    content_image: Optional[str]
    extraction_status: str
    error_message: Optional[str]
```

---

### 3. PipelineState (LangGraph State)

**Purpose**: In-memory state passed between LangGraph nodes during generation

**Fields**:
| Field | Type | Description |
|-------|------|-------------|
| `request_id` | `str` | UUID for this generation request |
| `session_id` | `str` | Anonymous session ID from client |
| `template_name` | `str` | Template identifier (`"uipath_pdd"`) |
| `files` | `List[FileMetadata]` | Parsed file metadata + content |
| `extracted_content` | `str` | Concatenated text from all files |
| `llm_prompt` | `str` | Built prompt sent to LLM |
| `llm_response` | `str` | Raw Markdown response from LLM |
| `parsed_sections` | `Dict[str, str]` | Section name → content mapping |
| `confidence_scores` | `Dict[str, ConfidenceScore]` | Section name → score |
| `errors` | `List[str]` | Accumulated error messages |
| `start_time` | `float` | Unix timestamp (request start) |
| `generation_time_seconds` | `Optional[float]` | Total time taken |

**Python TypedDict**:
```python
# backend/src/graph/state.py
from typing import TypedDict, List, Dict, Optional

class PipelineState(TypedDict):
    request_id: str
    session_id: str
    template_name: str
    files: List[FileMetadata]
    extracted_content: str
    llm_prompt: str
    llm_response: str
    parsed_sections: Dict[str, str]
    confidence_scores: Dict[str, 'ConfidenceScore']
    errors: List[str]
    start_time: float
    generation_time_seconds: Optional[float]
```

**Lifecycle**: Exists only during single HTTP request, destroyed after response

---

### 4. ConfidenceScore (Internal State)

**Purpose**: Heuristic confidence score for a specification section

**Fields**:
| Field | Type | Description |
|-------|------|-------------|
| `score` | `int` | Confidence value (0-100) |
| `classification` | `str` | Enum: `"high"`, `"medium"`, `"low"` |
| `reasons` | `List[str]` | Applied heuristics |

**Classification**:
- **High (green)**: `score >= 80`
- **Medium (yellow)**: `50 <= score < 80`
- **Low (red)**: `score < 50`

**Python TypedDict**:
```python
# backend/src/models/internal.py
class ConfidenceScore(TypedDict):
    score: int
    classification: str
    reasons: List[str]
```

---

### 5. GenerationResponse (Response Schema)

**Purpose**: Pydantic model for specification generation response

**Fields**:
| Field | Type | Description |
|-------|------|-------------|
| `specification` | `Dict[str, str]` | Section name → Markdown content |
| `confidence_scores` | `Dict[str, ConfidenceScoreResponse]` | Section name → score details |
| `generation_time_seconds` | `float` | Total processing time |
| `warnings` | `List[str]` | Non-fatal issues |

**Pydantic Schema**:
```python
# backend/src/models/responses.py
from pydantic import BaseModel, Field
from typing import Dict, List

class ConfidenceScoreResponse(BaseModel):
    score: int = Field(ge=0, le=100)
    classification: str
    reasons: List[str]

class GenerationResponse(BaseModel):
    specification: Dict[str, str]
    confidence_scores: Dict[str, ConfidenceScoreResponse]
    generation_time_seconds: float
    warnings: List[str] = Field(default_factory=list)
```

---

### 6. PDFExportRequest (Request Schema)

**Purpose**: Pydantic model for PDF export requests

**Fields**:
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `markdown` | `str` | Yes | Full Markdown specification content |
| `filename` | `str` | No | Desired PDF filename |

**Pydantic Schema**:
```python
# backend/src/models/requests.py
class PDFExportRequest(BaseModel):
    markdown: str = Field(min_length=1)
    filename: str = Field(
        default="specification.pdf",
        pattern=r"^[a-zA-Z0-9_-]+\.pdf$"
    )
```

---

### 7. SessionState (Client-Side, Browser localStorage)

**Purpose**: Anonymous session persistence in browser

**TypeScript Interface**:
```typescript
// frontend/src/types/index.ts
interface SessionState {
  session_id: string;
  cached_specs: CachedSpec[];
  created_at: number;
}

interface CachedSpec {
  id: string;
  template_name: string;
  specification: Record<string, string>;
  confidence_scores: Record<string, ConfidenceScore>;
  generated_at: number;
}
```

---

## Entity Relationships

```
Client (Browser)
  SessionState (localStorage)
    └── cached_specs: CachedSpec[]

Backend (In-Memory, Request Lifecycle)
  GenerationRequest
    ├── files: UploadFile[]
    └── template_name: str
         ↓
  PipelineState (LangGraph)
    ├── files: FileMetadata[]
    ├── parsed_sections: Dict[str, str]
    └── confidence_scores: Dict[str, ConfidenceScore]
         ↓
  GenerationResponse
    ├── specification: Dict[str, str]
    └── confidence_scores: Dict[str, ConfidenceScore]

[State destroyed after response sent]
```

**Version**: 1.0.0 | **Created**: 2025-10-28
