# Tasks: SpecGeny MVP Platform

**Input**: Design documents from `/specs/001-specgeny-mvp-platform/`
**Prerequisites**: plan.md, spec.md, data-model.md, contracts/openapi.yaml

**Tests**: Tests are OPTIONAL for this MVP - only included where explicitly beneficial for core validation.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

This is a web application with:
- **Backend**: `backend/src/` (Python/FastAPI)
- **Frontend**: `frontend/src/` (React/TypeScript)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create backend project structure per plan.md in backend/
- [ ] T002 Initialize Python project with pyproject.toml (FastAPI 0.104+, LangGraph 0.0.20+, python-docx 1.1+, PyPDF2 3.0+, Pillow 10.0+, openpyxl 3.1+, anthropic/openai SDKs, Pydantic 2.5+, mistralai SDK, PyYAML 6.0+)
- [ ] T003 Create frontend project structure per plan.md in frontend/
- [ ] T004 Initialize React project with Vite 5.0+ and TypeScript 5.2+ in frontend/
- [ ] T005 Install frontend dependencies (React 18.2+, Tailwind CSS 3.4+, TanStack Query 5.0+, Zustand 4.4+, React Hook Form 7.48+, React Router 6.20+, Axios 1.6+) in frontend/package.json
- [ ] T006 Initialize shadcn/ui with components.json configuration in frontend/
- [ ] T007 [P] Create backend/.env.example with LLM_PROVIDER, LLM_API_KEY, OCR_PROVIDER, UPLOAD_DIR, CORS_ORIGINS
- [ ] T008 [P] Create frontend/.env.example with VITE_API_BASE_URL, VITE_MAX_FILE_SIZE_MB, VITE_MAX_FILES
- [ ] T009 [P] Setup Tailwind CSS configuration in frontend/tailwind.config.js
- [ ] T010 [P] Configure TypeScript in frontend/tsconfig.json

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

### Backend Foundation

- [ ] T011 Create config loader in backend/src/config.py (load env variables)
- [ ] T012 Create Pydantic request schemas in backend/src/models/requests.py (GenerationRequest, PDFExportRequest)
- [ ] T013 Create Pydantic response schemas in backend/src/models/responses.py (GenerationResponse, ConfidenceScoreResponse)
- [ ] T014 Create LangGraph state TypedDict in backend/src/graph/state.py (PipelineState with all fields per data-model.md)
- [ ] T015 Create OCR adapter interface in backend/src/services/ocr/adapter.py (extract_text_from_image method signature)
- [ ] T016 Implement Mistral OCR adapter in backend/src/services/ocr/mistral_ocr.py (implements OCR adapter interface)
- [ ] T017 Create template block TypedDict in backend/src/templates/models.py (TemplateBlock, TemplateConfig)
- [ ] T018 Implement YAML template loader in backend/src/templates/loader.py (load_template function)
- [ ] T019 Create UiPath PDD template configuration in backend/config/templates/uipath_pdd.yaml (6-10 blocks: Executive Summary, User Stories, Functional Requirements, Technical Architecture, Error Handling, Testing Strategy)
- [ ] T020 Create LLM client wrapper in backend/src/services/llm_client.py (supports DeepSeek/Claude/OpenAI via env config)
- [ ] T021 Implement text file parsers in backend/src/services/file_parsers.py (parse_txt, parse_md, parse_docx, parse_pdf, parse_xlsx functions)
- [ ] T022 Implement file magic number validator in backend/src/services/validator.py (validate_file_format function)
- [ ] T023 Create FastAPI app in backend/src/api/main.py (CORS, startup/shutdown, health endpoint)
- [ ] T024 Create API dependencies in backend/src/api/dependencies.py (rate limiting middleware)

### Frontend Foundation

- [ ] T025 [P] Install shadcn/ui components (button, card, badge, progress, textarea, alert, tabs, separator, scroll-area, toast) in frontend/src/components/ui/
- [ ] T026 Create TypeScript interfaces in frontend/src/types/index.ts (GenerationResponse, ConfidenceScore, SessionState, CachedSpec)
- [ ] T027 Create Zustand store in frontend/src/stores/specStore.ts (session state, uploaded files, generated spec, confidence scores)
- [ ] T028 Create Axios API client in frontend/src/services/api.ts (generateSpec, exportPDF functions with upload progress)
- [ ] T029 Setup React Router in frontend/src/App.tsx (routes: /, /processing, /review)
- [ ] T030 Create global CSS with Tailwind imports in frontend/src/index.css

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Document Upload and Generation (Priority: P1) 🎯 MVP

**Goal**: Users can upload up to 10 files (txt, md, docx, pdf, png, jpg, xlsx) totaling 50 MB, generate a UiPath PDD specification using block-by-block LLM generation, and view the result with confidence scores

**Independent Test**: Upload a set of RPA project files, wait for generation to complete, verify a complete PDD is produced with color-coded confidence scores (green/yellow/red)

### Backend Implementation for User Story 1

#### LangGraph Pipeline Nodes

- [ ] T031 [P] [US1] Implement file_reader node in backend/src/graph/nodes/file_reader.py (extract text from uploaded files using file_parsers, update PipelineState.files with FileMetadata)
- [ ] T032 [P] [US1] Implement ocr_processor node in backend/src/graph/nodes/ocr_processor.py (process images via OCR adapter, update FileMetadata.content_text with OCR results)
- [ ] T033 [US1] Implement context_builder node in backend/src/graph/nodes/context_builder.py (build cumulative context: all uploaded files + previously generated blocks, format LLM prompt)
- [ ] T034 [US1] Implement block_generator node in backend/src/graph/nodes/block_generator.py (call LLM client for single template block, store LLM response)
- [ ] T035 [US1] Implement parser node in backend/src/graph/nodes/parser.py (extract Markdown block from LLM response, update PipelineState.parsed_sections)
- [ ] T036 [US1] Implement confidence calculator node in backend/src/graph/nodes/confidence.py (calculate heuristic scores: length check, generic phrases detection, source keyword matching)

#### LangGraph Pipeline Orchestration

- [ ] T037 [US1] Implement LangGraph pipeline in backend/src/graph/pipeline.py (build block-by-block workflow: file_reader → ocr_processor → loop[context_builder → block_generator → parser] → confidence_calculator, return final state)
- [ ] T038 [US1] Add block iteration logic to pipeline (iterate through template blocks from YAML config, generate each block sequentially with cumulative context)

#### API Endpoint

- [ ] T039 [US1] Implement /generate endpoint in backend/src/api/routes/generate.py (validate files per FR-002/003/004, save to /tmp/uploads/{request_id}/, invoke LangGraph pipeline, return GenerationResponse, cleanup temp files)
- [ ] T040 [US1] Add file validation logic to /generate (check file count ≤10, total size ≤50MB, magic number validation, reject unsupported formats with clear error messages)
- [ ] T041 [US1] Add error handling to /generate (catch LLM timeouts, file parsing errors, return appropriate HTTP status codes per openapi.yaml)
- [ ] T042 [US1] Register /generate route in backend/src/api/main.py

### Frontend Implementation for User Story 1

#### Components

- [ ] T043 [P] [US1] Create FileUpload component in frontend/src/components/FileUpload.tsx (drag-drop interface using shadcn Card + Input, file validation, display uploaded files list)
- [ ] T044 [P] [US1] Create GenerationStatus component in frontend/src/components/GenerationStatus.tsx (block-by-block progress indicator using shadcn Progress, display current block being generated)
- [ ] T045 [P] [US1] Create SpecPreview component in frontend/src/components/SpecPreview.tsx (display generated specification blocks with confidence badges: green ≥80%, yellow 50-79%, red <50%)

#### Pages

- [ ] T046 [US1] Create Home page in frontend/src/pages/Home.tsx (template selection defaulting to UiPath PDD, integrate FileUpload component, "Generate Specification" button)
- [ ] T047 [US1] Create Processing page in frontend/src/pages/Processing.tsx (integrate GenerationStatus component, display real-time generation progress, redirect to Review on completion)
- [ ] T048 [US1] Create Review page in frontend/src/pages/Review.tsx (integrate SpecPreview component, display generated specification with confidence scores)

#### API Integration

- [ ] T049 [US1] Implement generateSpec API call in frontend/src/services/api.ts (POST multipart/form-data to /generate, track upload progress, handle timeout/errors)
- [ ] T050 [US1] Integrate generateSpec with Zustand store in frontend/src/stores/specStore.ts (update state with generated spec, confidence scores, generation time)
- [ ] T051 [US1] Add TanStack Query integration for /generate in Home page (loading state, error handling, success redirect to Processing)

**Checkpoint**: At this point, User Story 1 should be fully functional - users can upload files, generate specs with block-by-block LLM, and view results with confidence scores

---

## Phase 4: User Story 2 - Specification Review and Editing (Priority: P2)

**Goal**: Users can see confidence scores for each section (green/yellow/red) and make corrections using simple text editing tools before finalizing the document

**Independent Test**: Generate a specification, edit specific sections through the text editing interface, verify changes are preserved

### Frontend Implementation for User Story 2

- [ ] T052 [P] [US2] Create BlockEditor component in frontend/src/components/BlockEditor.tsx (textarea for editing single block content, save/cancel buttons using shadcn Button + Textarea)
- [ ] T053 [US2] Add edit mode to SpecPreview component in frontend/src/components/SpecPreview.tsx (click on section to open BlockEditor, toggle between view/edit modes)
- [ ] T054 [US2] Add edit state management to Zustand store in frontend/src/stores/specStore.ts (track edited blocks, preserve edits during session)
- [ ] T055 [US2] Update Review page in frontend/src/pages/Review.tsx (integrate BlockEditor, display edit indicators, allow editing any section)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently - users can generate and edit specifications

---

## Phase 5: User Story 3 - Document Export (Priority: P2)

**Goal**: Users can download specifications in Markdown (.md) or PDF format with all edits included

**Independent Test**: Complete generation and editing, click export buttons, verify files download in correct formats with all content intact

### Backend Implementation for User Story 3

- [ ] T056 [US3] Implement Pandoc subprocess wrapper in backend/src/services/pdf_export.py (convert_markdown_to_pdf function, handle XeLaTeX engine)
- [ ] T057 [US3] Implement /export/pdf endpoint in backend/src/api/routes/export.py (accept PDFExportRequest, call pdf_export service, return PDF file with Content-Disposition header)
- [ ] T058 [US3] Add error handling to /export/pdf (catch Pandoc errors, validate markdown content, return appropriate HTTP status codes)
- [ ] T059 [US3] Register /export/pdf route in backend/src/api/main.py

### Frontend Implementation for User Story 3

- [ ] T060 [P] [US3] Create ExportButtons component in frontend/src/components/ExportButtons.tsx (Download Markdown button, Export PDF button using shadcn Button)
- [ ] T061 [US3] Implement Markdown download in ExportButtons (client-side download of concatenated specification content as .md file)
- [ ] T062 [US3] Implement exportPDF API call in frontend/src/services/api.ts (POST to /export/pdf, handle binary response, trigger file download)
- [ ] T063 [US3] Integrate ExportButtons into Review page in frontend/src/pages/Review.tsx (position after SpecPreview, pass edited content)

**Checkpoint**: All user stories 1, 2, AND 3 should now work independently - users can generate, edit, and export specifications

---

## Phase 6: User Story 4 - Multi-Format File Processing (Priority: P3)

**Goal**: System can accept and process all supported formats (txt, md, docx, pdf, png, jpg, xlsx), including extracting text from images via OCR

**Independent Test**: Upload a mixed set of file types (all 7 formats), verify generated specification incorporates content from all sources

### Backend Implementation for User Story 4

- [ ] T064 [US4] Add image preprocessing to ocr_processor node in backend/src/graph/nodes/ocr_processor.py (PIL image enhancement before OCR, handle low-resolution images)
- [ ] T065 [US4] Add Excel cell parsing to file_parsers in backend/src/services/file_parsers.py (extract structured data from spreadsheets, format as text for LLM context)

### Frontend Implementation for User Story 4

- [ ] T066 [US4] Add file type indicators to FileUpload component in frontend/src/components/FileUpload.tsx (show icons for each file type, validate extensions match allowed list)
- [ ] T067 [US4] Add format-specific validation to FileUpload (display clear error messages for unsupported formats, show format requirements)

**Checkpoint**: All formats should be processable - users can upload any combination of 7 supported file types

---

## Phase 7: User Story 5 - Session Persistence (Priority: P3)

**Goal**: Users can close their browser and return to find their completed specification available (no data loss)

**Independent Test**: Start generation, close browser, reopen, verify user can access previously generated specification

### Frontend Implementation for User Story 5

- [ ] T068 [US5] Add localStorage integration to Zustand store in frontend/src/stores/specStore.ts (persist session_id, cached_specs to localStorage on state changes)
- [ ] T069 [US5] Implement session recovery on app load in frontend/src/App.tsx (read from localStorage on mount, restore cached specifications)
- [ ] T070 [US5] Add session ID generation to Zustand store (generate UUID on first visit, persist in localStorage)
- [ ] T071 [US5] Update Home page to show cached specifications in frontend/src/pages/Home.tsx (display list of previous generations, allow loading cached spec)

**Checkpoint**: All user stories should now be independently functional - complete MVP feature set

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T072 [P] Add comprehensive error handling across all API routes in backend/src/api/routes/ (standardize error responses per openapi.yaml, add request validation)
- [ ] T073 [P] Add logging infrastructure in backend/src/api/main.py (structured logging for generation pipeline, OCR operations, LLM calls)
- [ ] T074 [P] Add request/response logging middleware in backend/src/api/dependencies.py (log all API calls with timing)
- [ ] T075 [P] Add loading states and error boundaries to frontend pages (shadcn Alert for errors, loading spinners)
- [ ] T076 [P] Add toast notifications for user feedback in frontend/src/App.tsx (shadcn Toast for success/error messages)
- [ ] T077 [P] Improve confidence score visualization in SpecPreview (add tooltips explaining scores, show heuristic reasons)
- [ ] T078 Add edge case handling for empty files in file_reader node (warn when no extractable content, skip empty files)
- [ ] T079 Add edge case handling for LLM timeouts in block_generator node (retry logic with exponential backoff, fail gracefully after 3 retries)
- [ ] T080 Add edge case handling for file size validation (prevent >50MB uploads, show progress for large files)
- [ ] T081 [P] Code cleanup and refactoring (remove console.logs, add JSDoc comments, extract magic numbers to constants)
- [ ] T082 Run quickstart.md validation (verify all setup steps work, test sample files from quickstart.md)
- [ ] T083 [P] Update README.md with project overview and quick start link

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-7)**: All depend on Foundational phase completion
  - User stories can proceed in parallel (if staffed)
  - Or sequentially in priority order: US1 (P1) → US2 (P2) → US3 (P2) → US4 (P3) → US5 (P3)
- **Polish (Phase 8)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Integrates with US1 but independently testable (can edit any spec, not just generated ones)
- **User Story 3 (P2)**: Can start after Foundational (Phase 2) - Integrates with US1/US2 but independently testable (can export any markdown content)
- **User Story 4 (P3)**: Can start after Foundational (Phase 2) - Enhances US1 but independently testable (file processing can be tested separately)
- **User Story 5 (P3)**: Can start after Foundational (Phase 2) - Enhances US1/US2/US3 but independently testable (localStorage persistence works independently)

### Within Each User Story

#### User Story 1 Task Dependencies
- T031-T032 (file_reader, ocr_processor) can run in parallel
- T033-T036 (context_builder, block_generator, parser, confidence) must run after T031-T032
- T037-T038 (pipeline orchestration) must run after T033-T036
- T039-T042 (API endpoint) must run after T037-T038
- T043-T045 (components) can run in parallel
- T046-T048 (pages) must run after T043-T045
- T049-T051 (API integration) must run after T046-T048

#### User Story 2 Task Dependencies
- T052 (BlockEditor) can start immediately after Foundational
- T053-T054 can run in parallel after T052
- T055 must run after T053-T054

#### User Story 3 Task Dependencies
- T056-T059 (backend) can run in parallel
- T060 (ExportButtons) can start after Foundational
- T061-T062 can run in parallel after T060
- T063 must run after T061-T062

#### User Story 4 Task Dependencies
- T064-T065 (backend enhancements) can run in parallel
- T066-T067 (frontend validation) can run in parallel

#### User Story 5 Task Dependencies
- T068-T070 can run sequentially (each depends on previous)
- T071 must run after T068-T070

### Parallel Opportunities

**Setup Phase (Phase 1)**:
- T007-T010 can run in parallel (different config files)

**Foundational Phase (Phase 2)**:
- Backend: T012-T013 can run in parallel (different model files)
- Backend: T015-T016 can run in parallel (adapter interface + implementation)
- Backend: T020-T022 can run in parallel (different service files)
- Frontend: T025-T030 can run in parallel (all different files)

**User Story 1 (Phase 3)**:
- T031-T032 can run in parallel (different node files)
- T043-T045 can run in parallel (different component files)

**User Story 3 (Phase 5)**:
- T056-T059 (backend) can run in parallel
- T061-T062 (frontend API + download) can run in parallel

**User Story 4 (Phase 6)**:
- T064-T065 (backend) can run in parallel
- T066-T067 (frontend) can run in parallel

**Polish (Phase 8)**:
- T072-T077 can run in parallel (different concerns)
- T081-T083 can run in parallel (different files)

**Cross-Story Parallelization**:
- Once Phase 2 completes, all user stories (US1-US5) can start in parallel by different team members
- Example: Developer A works on US1, Developer B works on US2, Developer C works on US3

---

## Parallel Example: User Story 1 Backend Nodes

```bash
# Launch parallel tasks for LangGraph nodes:
Task T031: "Implement file_reader node in backend/src/graph/nodes/file_reader.py"
Task T032: "Implement ocr_processor node in backend/src/graph/nodes/ocr_processor.py"

# Then launch next set in parallel after above complete:
Task T033: "Implement context_builder node in backend/src/graph/nodes/context_builder.py"
Task T034: "Implement block_generator node in backend/src/graph/nodes/block_generator.py"
Task T035: "Implement parser node in backend/src/graph/nodes/parser.py"
Task T036: "Implement confidence calculator node in backend/src/graph/nodes/confidence.py"
```

---

## Parallel Example: User Story 1 Frontend Components

```bash
# Launch all components in parallel (different files, no dependencies):
Task T043: "Create FileUpload component in frontend/src/components/FileUpload.tsx"
Task T044: "Create GenerationStatus component in frontend/src/components/GenerationStatus.tsx"
Task T045: "Create SpecPreview component in frontend/src/components/SpecPreview.tsx"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup → Project structure ready
2. Complete Phase 2: Foundational → Core infrastructure ready (CRITICAL CHECKPOINT)
3. Complete Phase 3: User Story 1 → File upload + block-by-block generation + preview working
4. **STOP and VALIDATE**: Test User Story 1 independently with real RPA files
5. Deploy/demo if ready (this is a functional MVP!)

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready (CRITICAL CHECKPOINT)
2. Add User Story 1 → Test independently → Deploy/Demo (MVP with core generation!)
3. Add User Story 2 → Test independently → Deploy/Demo (MVP + editing!)
4. Add User Story 3 → Test independently → Deploy/Demo (MVP + export!)
5. Add User Story 4 → Test independently → Deploy/Demo (MVP + multi-format!)
6. Add User Story 5 → Test independently → Deploy/Demo (Complete MVP!)
7. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together (MUST complete before splitting)
2. Once Foundational is done:
   - Developer A: User Story 1 (backend + frontend)
   - Developer B: User Story 2 + User Story 3 (frontend-heavy)
   - Developer C: User Story 4 + User Story 5 (enhancements)
3. Stories complete and integrate independently
4. Integration testing after each story completes

---

## Notes

- **[P] tasks**: Different files, no dependencies - can run in parallel
- **[Story] label**: Maps task to specific user story for traceability
- **Each user story**: Independently completable and testable
- **Commit strategy**: Commit after each task or logical group
- **Validation**: Stop at any checkpoint to validate story independently
- **Architecture**: Block-by-block generation with cumulative context (6-10 LLM calls per spec)
- **OCR**: Dedicated Mistral OCR service with adapter interface for swappability
- **Templates**: YAML-based configuration at backend/config/templates/uipath_pdd.yaml
- **UI Library**: shadcn/ui exclusively (non-negotiable per constitution)
- **Stateless**: No database - in-memory state during request lifecycle only
- **Tests**: Optional for MVP (not explicitly required in spec.md)

---

**Total Tasks**: 83
**Phases**: 8
**User Stories**: 5 (P1: 1, P2: 2, P3: 2)
**Estimated Duration**:
- Phase 1 (Setup): 1-2 days
- Phase 2 (Foundational): 3-5 days
- Phase 3 (US1 - Core MVP): 5-7 days
- Phase 4 (US2 - Editing): 2-3 days
- Phase 5 (US3 - Export): 2-3 days
- Phase 6 (US4 - Multi-format): 1-2 days
- Phase 7 (US5 - Persistence): 1-2 days
- Phase 8 (Polish): 2-3 days
- **Total**: ~17-27 days (single developer, sequential)
- **Total**: ~10-15 days (3 developers, parallel after foundational)
