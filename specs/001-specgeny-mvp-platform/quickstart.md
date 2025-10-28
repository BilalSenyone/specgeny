# Quickstart Guide: SpecGeny MVP Platform

**Feature**: 001-specgeny-mvp-platform
**Version**: 1.0.0
**Last Updated**: 2025-10-28

## Prerequisites

### Required Software

- **Python**: 3.11 or higher
- **Node.js**: 18.x or higher
- **pnpm**: 8.x or higher (recommended) or npm 9.x
- **Pandoc**: 3.0 or higher (for PDF export)
- **Git**: For version control

### LLM API Access

You need **one** of the following:
- **DeepSeek API key** (recommended for MVP): [https://platform.deepseek.com](https://platform.deepseek.com)
- **Anthropic Claude API key**: [https://console.anthropic.com](https://console.anthropic.com)
- **OpenAI API key**: [https://platform.openai.com](https://platform.openai.com)

### Install Pandoc

**macOS**:
```bash
brew install pandoc
```

**Ubuntu/Debian**:
```bash
sudo apt-get update
sudo apt-get install pandoc texlive-xetex
```

**Windows**:
Download installer from [https://pandoc.org/installing.html](https://pandoc.org/installing.html)

Verify installation:
```bash
pandoc --version
```

---

## Project Setup

### 1. Clone Repository

```bash
git clone https://github.com/your-org/specgeny.git
cd specgeny
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
# OR if using Poetry:
poetry install

# Copy environment template
cp .env.example .env
```

**Edit `.env` file**:
```bash
# LLM Configuration
LLM_PROVIDER=deepseek  # or 'claude' or 'openai'
LLM_API_KEY=your_api_key_here

# Upload Configuration
UPLOAD_DIR=/tmp/uploads
MAX_FILE_SIZE_MB=50
MAX_FILES=10

# CORS (for local development)
CORS_ORIGINS=http://localhost:5173
```

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
pnpm install
# OR
npm install

# Install shadcn/ui components
npx shadcn-ui@latest add button card badge progress textarea alert tabs separator scroll-area toast

# Copy environment template
cp .env.example .env
```

**Edit `.env` file**:
```bash
VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_MAX_FILE_SIZE_MB=50
VITE_MAX_FILES=10
```

---

## Running Locally

### Start Backend (Terminal 1)

```bash
cd backend
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Run FastAPI server
uvicorn src.api.main:app --reload --port 8000
```

**Expected output**:
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [12345] using StatReload
INFO:     Started server process [12346]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

**Test backend**:
```bash
curl http://localhost:8000/health
# Expected: {"status":"ok"}
```

**API Documentation**:
- Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
- ReDoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)

### Start Frontend (Terminal 2)

```bash
cd frontend

# Run Vite dev server
pnpm dev
# OR
npm run dev
```

**Expected output**:
```
  VITE v5.0.0  ready in 523 ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
  ➜  press h to show help
```

**Access app**: [http://localhost:5173](http://localhost:5173)

---

## Testing the Application

### 1. Prepare Test Files

Create a test directory with sample project files:

```bash
mkdir test-files
cd test-files

# Create sample text file
cat > requirements.txt << 'EOF'
Project: Invoice Processing Automation

Requirements:
1. Extract invoice data from PDF invoices
2. Validate invoice numbers against SAP
3. Route to appropriate approvers based on amount
4. Send notifications on approval/rejection
EOF

# Create sample markdown file
cat > architecture.md << 'EOF'
# System Architecture

## Components
- UiPath Orchestrator
- ReFramework template
- SAP connector
- Email notifications (SMTP)

## Data Flow
1. Monitor email inbox for invoice PDFs
2. Extract data using Document Understanding
3. Validate against SAP BAPI
4. Route to approver queue
5. Update SAP on approval
EOF
```

### 2. Test Generation Flow

1. **Open browser**: [http://localhost:5173](http://localhost:5173)

2. **Upload files**:
   - Drag and drop `requirements.txt` and `architecture.md`
   - Verify file preview shows both files

3. **Generate specification**:
   - Click "Generate Specification" button
   - Watch progress indicator (should take 2-5 minutes)

4. **Review specification**:
   - Check confidence scores (green/yellow/red badges)
   - Review generated sections (Executive Summary, User Stories, etc.)

5. **Edit sections** (optional):
   - Click on any section to edit
   - Make changes in textarea
   - Click "Save"

6. **Export specification**:
   - Click "Download Markdown" → verify `.md` file downloads
   - Click "Export PDF" → verify `.pdf` file downloads

### 3. Test API Directly (cURL)

**Generate specification**:
```bash
curl -X POST http://localhost:8000/api/v1/generate \
  -F "files=@test-files/requirements.txt" \
  -F "files=@test-files/architecture.md" \
  -F "template_name=uipath_pdd"
```

**Export to PDF**:
```bash
curl -X POST http://localhost:8000/api/v1/export/pdf \
  -H "Content-Type: application/json" \
  -d '{
    "markdown": "# Test Specification\n\nThis is a test.",
    "filename": "test.pdf"
  }' \
  --output test.pdf
```

---

## Project Structure

```
specgeny/
├── backend/
│   ├── src/
│   │   ├── api/          # FastAPI routes
│   │   ├── graph/        # LangGraph pipeline
│   │   ├── services/     # File parsers, LLM client, PDF export
│   │   ├── templates/    # UiPath PDD template
│   │   ├── models/       # Pydantic schemas
│   │   └── config.py     # Environment variables
│   ├── tests/            # pytest tests
│   ├── requirements.txt  # Python dependencies
│   └── .env.example      # Environment template
│
├── frontend/
│   ├── src/
│   │   ├── components/   # React components (shadcn/ui)
│   │   ├── pages/        # Route pages
│   │   ├── services/     # API client (Axios)
│   │   ├── stores/       # Zustand state
│   │   └── types/        # TypeScript interfaces
│   ├── package.json      # Node dependencies
│   └── .env.example      # Environment template
│
└── specs/
    └── 001-specgeny-mvp-platform/
        ├── spec.md       # Feature specification
        ├── plan.md       # Implementation plan
        ├── research.md   # Technical research
        ├── data-model.md # Data structures
        ├── quickstart.md # This file
        └── contracts/    # API contracts
            └── openapi.yaml
```

---

## Common Issues

### Backend Issues

**Issue**: `ModuleNotFoundError: No module named 'langgraph'`
```bash
# Solution: Reinstall dependencies
pip install -r requirements.txt
```

**Issue**: `FileNotFoundError: [Errno 2] No such file or directory: 'pandoc'`
```bash
# Solution: Install Pandoc (see Prerequisites section)
brew install pandoc  # macOS
sudo apt-get install pandoc  # Linux
```

**Issue**: `HTTPException: LLM API key not configured`
```bash
# Solution: Set LLM_API_KEY in .env file
echo "LLM_API_KEY=your_key_here" >> backend/.env
```

**Issue**: `CORS error in browser console`
```bash
# Solution: Update CORS_ORIGINS in backend/.env
CORS_ORIGINS=http://localhost:5173
```

### Frontend Issues

**Issue**: `Failed to fetch from http://localhost:8000`
```bash
# Solution: Ensure backend is running on port 8000
# Check: curl http://localhost:8000/health
```

**Issue**: `Module not found: @/components/ui/button`
```bash
# Solution: Install shadcn/ui components
npx shadcn-ui@latest add button card badge progress textarea alert
```

**Issue**: `VITE_API_BASE_URL is undefined`
```bash
# Solution: Create frontend/.env file
echo "VITE_API_BASE_URL=http://localhost:8000/api/v1" > frontend/.env
```

---

## Development Workflow

### 1. Backend Development

**Run tests**:
```bash
cd backend
pytest tests/ -v
```

**Run with live reload**:
```bash
uvicorn src.api.main:app --reload --port 8000
```

**Check code quality**:
```bash
# Format with ruff
ruff format src/

# Lint with ruff
ruff check src/

# Type check with mypy
mypy src/
```

### 2. Frontend Development

**Run tests**:
```bash
cd frontend
pnpm test
# OR
npm test
```

**Run with hot reload** (default):
```bash
pnpm dev
```

**Check code quality**:
```bash
# Lint with ESLint
pnpm lint

# Type check with TypeScript
pnpm type-check
# OR
tsc --noEmit
```

### 3. Adding shadcn/ui Components

When you need a new shadcn component:

```bash
cd frontend

# Install specific component
npx shadcn-ui@latest add <component-name>

# Example: Add dropdown-menu
npx shadcn-ui@latest add dropdown-menu
```

This adds the component to `src/components/ui/<component-name>.tsx`

---

## Next Steps

### For Implementation

1. **Review artifacts**:
   - [ ] `spec.md` - Feature requirements
   - [ ] `data-model.md` - Data structures
   - [ ] `contracts/openapi.yaml` - API contract
   - [ ] `research.md` - Technology decisions

2. **Generate tasks**:
   ```bash
   # Run the tasks generation command
   /speckit.tasks
   ```

3. **Start implementation**:
   - Follow task order in `tasks.md`
   - Backend first (API + LangGraph pipeline)
   - Frontend second (React + shadcn/ui)

### For Testing

1. **Prepare test data**:
   - Collect real RPA project files (docx, pdf, png, xlsx)
   - Create diverse test cases (10 files, 50 MB, edge cases)

2. **Test scenarios**:
   - [ ] File upload validation (10 files, 50 MB limits)
   - [ ] Multi-format processing (all 7 formats)
   - [ ] LLM integration (DeepSeek vs Claude)
   - [ ] Confidence scoring (heuristics)
   - [ ] PDF export (Pandoc)
   - [ ] Error handling (corrupted files, API failures)

3. **Performance testing**:
   - Measure generation time (target: <5 min for P95)
   - Test concurrent requests (target: 20 simultaneous users)

---

## Deployment

### Production Build

**Backend**:
```bash
cd backend

# Build Docker image
docker build -t specgeny-backend .

# Run container
docker run -p 8000:8000 \
  -e LLM_PROVIDER=deepseek \
  -e LLM_API_KEY=your_key \
  specgeny-backend
```

**Frontend**:
```bash
cd frontend

# Build for production
pnpm build

# Preview production build
pnpm preview
```

### Deploy to Platforms

**Backend** → Railway or Render:
- Connect GitHub repo
- Set environment variables (LLM_PROVIDER, LLM_API_KEY)
- Auto-deploy from `main` branch

**Frontend** → Vercel:
- Connect GitHub repo
- Set environment variable: `VITE_API_BASE_URL=https://api.specgeny.com/api/v1`
- Auto-deploy from `main` branch

---

## Support

**Documentation**:
- Feature spec: `specs/001-specgeny-mvp-platform/spec.md`
- API contract: `specs/001-specgeny-mvp-platform/contracts/openapi.yaml`
- Data model: `specs/001-specgeny-mvp-platform/data-model.md`

**API Documentation** (local):
- Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
- OpenAPI JSON: [http://localhost:8000/openapi.json](http://localhost:8000/openapi.json)

**Constitution**: `.specify/memory/constitution.md` - Project principles and constraints

---

**Version**: 1.0.0 | **Created**: 2025-10-28
