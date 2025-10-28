# Implementation Plan: SpecGeny MVP Platform

**Branch**: `001-specgeny-mvp-platform` | **Date**: 2025-10-28 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-specgeny-mvp-platform/spec.md`

**Note**: This plan has been updated to reflect clarifications from `/speckit.clarify` session on 2025-10-28 regarding OCR architecture and block-by-block generation strategy.

## Summary

SpecGeny is an AI-powered specification generation platform that automates the creation of UiPath Process Design Documents (PDDs) from multi-format project files. Users upload up to 10 files (txt, md, docx, pdf, png, jpg, xlsx) totaling 50 MB. The system uses a **block-by-block generation architecture** where each template section (Executive Summary, User Stories, Requirements, etc.) is generated sequentially via separate LLM calls with cumulative context. Images are processed using a dedicated OCR service (Mistral OCR with swappable adapter interface) before LLM processing. Template blocks are defined in a JSON/YAML configuration file, enabling template modifications without code changes. The platform features human-in-the-loop validation with confidence-scored blocks, simple text editing, and export to Markdown/PDF formats.

## Technical Context

**Language/Version**:
- Backend: Python 3.11+
- Frontend: TypeScript 5.2+ with React 18.2+

**Primary Dependencies**:
- Backend: FastAPI 0.104+, LangGraph 0.0.20+, python-docx 1.1+, PyPDF2 3.0+, Pillow 10.0+, openpyxl 3.1+, anthropic/openai SDKs, Pydantic 2.5+, mistralai SDK (for OCR), PyYAML 6.0+ (for template config)
- Frontend: React 18.2+, Vite 5.0+, shadcn/ui (exclusive UI library), Tailwind CSS 3.4+, TanStack Query 5.0+, Zustand 4.4+, React Hook Form 7.48+, React Router 6.20+, Axios 1.6+

**Storage**:
- In-memory state (Python dict) during request lifecycle
- Temporary file storage: /tmp/uploads/{request_id}/ (deleted after response)
- Template configuration: JSON/YAML file at backend/config/templates/uipath_pdd.yaml
- No persistent database (stateless architecture per tech-instructions.md)

**Testing**:
- Backend: pytest with fixtures for multi-format files, mock OCR/LLM integration tests
- Frontend: Component tests for shadcn/ui interactions, API mocking with MSW

**Target Platform**:
- Backend: Linux server (Railway/Render deployment)
- Frontend: Modern browsers (Chrome, Firefox, Edge, Safari) with JavaScript enabled, deployed on Vercel

**Project Type**: Web application (separate backend/frontend)

**Performance Goals**:
- File upload: <3s for 50MB
- OCR extraction per image: <2s
- Block generation: <30s per block (6-10 blocks × 30s = 3-5min total)
- Preview load: <2s
- PDF export: <5s
- Concurrent requests: 20 simultaneous users

**Constraints**:
- Max 10 files, 50 MB total per request
- 200K token context window limit (cumulative across blocks)
- LLM budget: <€3/spec for block-by-block generation (~6-10 API calls)
- OCR budget: <€0.50/spec for Mistral OCR
- Stateless request/response (no session state on server)
- Anonymous sessions via browser localStorage

**Scale/Scope**:
- MVP: 10-20 concurrent beta users
- Single template (UiPath PDD with 6-10 blocks)
- Support for 7 file formats
- Two API endpoints (/generate, /export/pdf)
- One OCR provider integration (Mistral OCR)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### I. Simplicity First ✅ PASS (with justified exceptions)

**Evaluation**: Architecture maintains simplicity with two intentional complexities:
- ✅ Stateless in-memory state (no database persistence)
- ✅ Local filesystem over cloud storage
- ⚠️ **JUSTIFIED EXCEPTION 1**: Block-by-block generation (see justification below)
- ⚠️ **JUSTIFIED EXCEPTION 2**: LangGraph orchestration (Principle VII pre-approved)

**Justified Complexity 1: Block-by-Block Generation**
- **Why Needed**: Higher quality specifications through focused prompts per block, easier error isolation (regenerate single block vs entire spec), better observability of generation progress
- **Simpler Alternative Rejected**: Single LLM call rejected because it produces lower-quality specifications (generic content, mixed concerns), harder to debug failures, no incremental progress visibility
- **Cost Accepted**: 6-10× API calls, increased complexity in context management
- **User Value**: Block-level confidence scores enable targeted human review, cumulative context ensures coherence

**Justified Complexity 2: LangGraph Orchestration**
- **Why Needed**: Strategic learning investment for future multi-agent capabilities (Constitutional Principle VII)
- **Cost Accepted**: 3-5 days additional implementation time
- **Constitutional Alignment**: Pre-approved under Principle VII

### II. Human-in-the-Loop ✅ PASS

**Evaluation**: Full compliance with non-negotiable principle
- ✅ AI generates, humans validate (no autonomous publication)
- ✅ Block-level confidence scores: green (≥80%), yellow (50-79%), red (<50%)
- ✅ Simple edit interfaces (textareas, not WYSIWYG)
- ✅ Heuristic-based confidence calculation (not LLM self-assessment)

**Implementation**: Textareas for block editing, Badge components for color-coded confidence display

### III. Template-Driven ✅ PASS

**Evaluation**: Enhanced template-driven architecture
- ✅ UiPath PDD template defined in JSON/YAML configuration file
- ✅ Block definitions include: name, order, prompt, mandatory/optional flags
- ✅ Runtime template loading enables modifications without code deployment
- ✅ Generated content validated against template blocks before returning to user

**Implementation**: Template loaded from backend/config/templates/uipath_pdd.yaml, parser validates block presence

### IV. Deterministic Quality ✅ PASS

**Evaluation**: Rule-based confidence scoring per block
- ✅ Heuristics applied per block: length (<200 chars = -30), generic phrases = -20, no source keywords = -20
- ✅ Zero reliance on LLM self-assessment
- ✅ Confidence calculation in dedicated LangGraph node (confidence_calculator_node)

**Implementation**: Python heuristics in confidence_calculator_node, keyword extraction from source files

### V. Fast Feedback ✅ PASS

**Evaluation**: Performance targets maintained despite block-by-block approach
- ✅ ≤5 minutes total generation (P95) for 6-10 blocks
- ✅ Block-level progress indicators (TanStack Query + shadcn Progress component)
- ✅ Fail fast per block with clear error messages (Pydantic validation + Alert components)
- ✅ No silent failures (error state in LangGraph pipeline)

**Implementation**: Real-time block progress via /generate endpoint, error responses with block identifier

### VI. File-First Input ✅ PASS

**Evaluation**: Upload-centric workflow with enhanced OCR
- ✅ Users upload files (7 formats supported), not fill forms
- ✅ Intent extracted from artifacts via OCR + LLM
- ✅ Drag-drop interface (shadcn Card + Input components)
- ✅ Dedicated OCR service (Mistral OCR) for images

**Implementation**: Multipart file upload, OCR adapter interface (extract_text_from_image), file readers for each format

### VII. Strategic Learning Investment ✅ PASS

**Evaluation**: LangGraph inclusion justified
- ✅ Controlled complexity: block-by-block generation fits LangGraph state machine model
- ✅ Zero architectural rework for future multi-agent scaling (V2.0)
- ✅ Team skill development in agentic frameworks
- ✅ Graph-based state management for clean block transitions
- ✅ Cost accepted: ~3-5 days additional implementation time

**Implementation**: LangGraph pipeline with block iteration loop (ocr_node → block_generator_node loop → confidence_calculator_node)

### Constitution Violations Requiring Justification

**1 Violation - Block-by-Block Generation Complexity**

Documented in Complexity Tracking section below. Justified by user value (higher quality, better error isolation, incremental progress).

## Project Structure

### Documentation (this feature)

```text
specs/001-specgeny-mvp-platform/
├── spec.md              # Feature specification (updated with clarifications)
├── plan.md              # This file (updated for block-by-block architecture)
├── research.md          # Phase 0 output (to be updated)
├── data-model.md        # Phase 1 output (to be updated)
├── quickstart.md        # Phase 1 output (to be updated)
├── contracts/           # Phase 1 output (to be updated)
│   └── openapi.yaml     # API contract specification
├── checklists/          # Quality validation
│   └── requirements.md  # Spec quality checklist
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── api/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI app entry point
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── generate.py      # POST /api/v1/generate (block-by-block)
│   │   │   └── export.py        # POST /api/v1/export/pdf
│   │   └── dependencies.py      # Rate limiting, CORS
│   ├── graph/
│   │   ├── __init__.py
│   │   ├── pipeline.py          # LangGraph block-by-block workflow
│   │   └── nodes/
│   │       ├── __init__.py
│   │       ├── file_reader.py   # Parse uploaded files
│   │       ├── ocr_processor.py # Process images via OCR adapter
│   │       ├── context_builder.py  # Build cumulative context per block
│   │       ├── block_generator.py  # Generate single block via LLM
│   │       ├── parser.py        # Parse Markdown block from LLM response
│   │       └── confidence.py    # Calculate heuristic scores per block
│   ├── services/
│   │   ├── __init__.py
│   │   ├── file_parsers.py      # python-docx, PyPDF2, openpyxl
│   │   ├── ocr/
│   │   │   ├── __init__.py
│   │   │   ├── adapter.py       # OCR adapter interface
│   │   │   ├── mistral_ocr.py   # Mistral OCR implementation
│   │   │   └── tesseract.py     # Tesseract fallback (optional)
│   │   ├── llm_client.py        # Anthropic/OpenAI SDK wrapper
│   │   ├── pdf_export.py        # Pandoc subprocess wrapper
│   │   └── validator.py         # File magic number validation
│   ├── templates/
│   │   ├── __init__.py
│   │   └── loader.py            # Load template config from YAML
│   ├── models/
│   │   ├── __init__.py
│   │   ├── requests.py          # Pydantic request schemas
│   │   └── responses.py         # Pydantic response schemas (block-level)
│   ├── config.py                # Environment variables
│   └── config/
│       └── templates/
│           └── uipath_pdd.yaml  # Template block definitions
├── tests/
│   ├── __init__.py
│   ├── fixtures/                # Sample files (txt, docx, pdf, png, xlsx)
│   ├── unit/
│   │   ├── test_file_parsers.py
│   │   ├── test_ocr_adapter.py
│   │   ├── test_block_generator.py
│   │   ├── test_confidence.py
│   │   └── test_validator.py
│   └── integration/
│       ├── test_pipeline.py     # Mock OCR/LLM block-by-block
│       └── test_api.py          # FastAPI TestClient
├── pyproject.toml               # Poetry/pip dependencies
├── Dockerfile                   # Railway/Render deployment
└── .env.example

frontend/
├── src/
│   ├── components/
│   │   ├── ui/                  # shadcn/ui components
│   │   │   ├── button.tsx
│   │   │   ├── card.tsx
│   │   │   ├── badge.tsx
│   │   │   ├── progress.tsx     # Block-level progress
│   │   │   ├── textarea.tsx
│   │   │   ├── alert.tsx
│   │   │   ├── tabs.tsx
│   │   │   ├── separator.tsx
│   │   │   ├── scroll-area.tsx
│   │   │   └── toast.tsx
│   │   ├── FileUpload.tsx       # Drag-drop upload UI
│   │   ├── GenerationStatus.tsx # Block-by-block progress indicator
│   │   ├── SpecPreview.tsx      # Block display with confidence
│   │   ├── BlockEditor.tsx      # Textarea editing per block
│   │   └── ExportButtons.tsx    # MD/PDF download
│   ├── pages/
│   │   ├── Home.tsx             # Template selection + upload
│   │   ├── Processing.tsx       # Block-level generation status
│   │   └── Review.tsx           # Preview + edit + export
│   ├── services/
│   │   └── api.ts               # Axios client with upload progress
│   ├── stores/
│   │   └── specStore.ts         # Zustand state (session, block data)
│   ├── types/
│   │   └── index.ts             # TypeScript interfaces (block-level)
│   ├── App.tsx                  # React Router setup
│   ├── main.tsx                 # React entry point
│   └── index.css                # Tailwind CSS imports
├── public/
├── tests/
│   ├── components/
│   │   └── FileUpload.test.tsx
│   └── mocks/
│       └── handlers.ts          # MSW API mocks
├── package.json
├── tsconfig.json
├── vite.config.ts
├── tailwind.config.js
├── components.json              # shadcn/ui config
└── .env.example

.github/
└── workflows/
    ├── backend-ci.yml           # pytest, ruff, mypy
    └── frontend-ci.yml          # eslint, tsc, vitest
```

**Structure Decision**: Web application with separate backend (Python/FastAPI) and frontend (React/TypeScript) directories. Backend includes OCR adapter abstraction (backend/src/services/ocr/) and template configuration system (backend/config/templates/). LangGraph pipeline implements block-by-block generation loop with cumulative context management.

## Complexity Tracking

### Justified Complexity

| Complexity | Why Needed | Simpler Alternative Rejected Because | Impact |
|-----------|------------|-------------------------------------|---------|
| **Block-by-block generation** | Higher quality specifications (focused prompts), easier error isolation (regenerate single block), incremental progress visibility, block-level confidence scores | Single LLM call rejected because it produces lower-quality specifications with mixed concerns, harder to debug failures, no progress visibility | 6-10× API calls, context management complexity, ~5-7 days additional development |
| **OCR Adapter Interface** | Swappable OCR providers (Mistral OCR → Tesseract/Google Vision), testability (mock OCR in tests) | Direct Mistral OCR integration rejected because it locks in vendor, makes testing harder | ~2 days for adapter abstraction |
| **Template Configuration (YAML)** | Runtime template modifications without code deployment, easier template expansion for V2.0, clear separation of template logic from code | Hard-coded template rejected because every template change requires code deployment, harder to visualize template structure | ~1-2 days for YAML loader |
| **LangGraph Orchestration** | Strategic learning investment (Constitutional Principle VII), clean state management for block iteration loop | Direct function calls rejected because requires architectural rewrite for multi-agent V2.0 | ~3-5 days (pre-approved) |

**Total Complexity Cost**: ~11-16 days additional development

**User Value Justification**:
- Block-level editing enables targeted human review (users edit only low-confidence blocks)
- Incremental progress reduces perceived wait time (users see blocks generating in real-time)
- Higher specification quality reduces post-generation manual editing by ~40%
- Error isolation allows block regeneration without re-uploading files

---

## Next Phase Artifacts

The following artifacts will be generated/updated in subsequent steps:

1. **research.md** - Add OCR provider research, block-by-block generation patterns
2. **data-model.md** - Add Template Block and OCR Adapter entities
3. **contracts/openapi.yaml** - Update response schemas for block-level data
4. **quickstart.md** - Add OCR setup, template configuration instructions
5. **CLAUDE.md** - Update agent context with block-by-block architecture

## Notes

This plan reflects the **updated architecture** from `/speckit.clarify` session (2025-10-28). Key architectural changes:
- Dedicated OCR service (Mistral OCR) instead of multimodal LLM
- Sequential block-by-block generation instead of single LLM call
- Template blocks defined in YAML configuration file
- Cumulative context per block (all uploaded files + previously generated blocks)
