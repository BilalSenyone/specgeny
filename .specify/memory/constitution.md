# SpecGeny Constitution

## Core Principles

### I. Simplicity First
Challenge every decision: "Can this be simpler?" 
Examples: Context stuffing over RAG. Single LLM call over multi-agent. Filesystem over cloud storage. Justify complexity or remove it.

### II. Human-in-the-Loop (Non-Negotiable)
AI generates. Humans validate. No autonomous publication. Provide confidence scores (green ≥80%, yellow 50-79%, red <50%) and simple edit interfaces (textareas, not WYSIWYG).


### III. Template-Driven
All outputs conform to structured templates (e.g., UiPath PDD). Templates define mandatory/optional sections. Validate generated content against template before showing users.

### IV. Deterministic Quality
Use rule-based heuristics for confidence scores: section length, generic phrases, keyword matching. Never LLM self-assessment.

### V. Fast Feedback
≤5 minutes generation for 10 files/50MB. Show progress indicators. Fail fast with clear error messages. No silent failures.

### VI. File-First Input
Users upload files (`.txt`, `.md`, `.docx`, `.pdf`, `.png`, `.jpg`, `.xlsx`), not fill forms. Extract intent from artifacts.

### VII. Strategic Learning Investment
The MVP deliberately includes LangGraph (even with single agent) as a learning investment for future multi-agent capabilities. This controlled complexity is justified by:
- Zero architectural rework when scaling to multi-agent (V2.0)
- Team skill development in agentic frameworks
- Graph-based orchestration proves valuable for state management
- Cost: ~3-5 days additional implementation time accepted

## Technical Constraints

### Stack
- **LLM**: Claude/OpenAI any good LLM that can handle tools
- **OCR**: Mistral OCR, Deepseek OCR, any LLM-like OCR
- **Backend**: FastAPI + SQLite + local filesystem
- **Frontend**: React + TypeScript + shadcn/ui (Not Negociable)
- **Deploy**: Vercel (frontend)
- **Auth**: None (anonymous localStorage sessions)

### Limits
- **Max 10 files, 50MB total per session**
- **Sessions expire after 24 hours**
- **LLM budget: <€3/spec, <300s latency**

### Security
- Magic number file validation, not extensions
- Sanitize user inputs against prompt injection

## Quality Standards

### Testing (Selective TDD)
Test critical paths only: file parsing, LLM integration, template validation, confidence calculation. 3-5 end-to-end integration tests with real files.

### Code Quality
- Ruff (Python), ESLint (TypeScript)
- Type hints required (mypy, strict TS)
- No dead code, no commented-out blocks

### Performance
- File upload: <3s (50MB)
- Generation: <5min (P95)
- Preview load: <2s
- PDF export: <5s

### Error Handling
- User errors (4xx): Plain language, actionable
- System errors (5xx): Log, show generic message
- Console + file logging (max 100MB rotating)

## Governance

**Constitution > All Other Practices**

Violations require written justification:
1. Problem statement
2. Simpler alternatives tried
3. Maintenance cost accepted

**Version**: 1.0.0 | **Ratified**: 2025-10-28