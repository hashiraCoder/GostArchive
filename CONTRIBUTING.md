# Contributing to GhostArchive

Thank you for your interest in contributing to GhostArchive! GhostArchive is a local-first, evidence-grounded personal memory archive designed to help users preserve, organize, and query their private documents with absolute privacy.

We welcome issues, feature suggestions, documentation improvements, and pull requests that adhere to our architectural and privacy standards.

---

## 1. Ground Rules & Core Principles

Before opening a pull request, please keep our core tenets in mind:

1. **Local-First & Offline Privacy:** Never introduce dependencies or features that send user documents, raw text, embeddings, or prompts to remote cloud endpoints by default. GhostArchive must function 100% offline once model weights are locally cached.
2. **SQLite is Authoritative:** SQLite is the single source of truth for metadata, chunk text, and source offsets. ChromaDB is strictly an auxiliary, rebuildable index.
3. **Evidence-Grounded RAG:** The assistant must never invent or hallucinate answers. Citations must match retrieved chunks, and the system must abstain with `insufficient_evidence: true` when information is missing.
4. **Zero-Invention Rule:** Tests, documentation, and performance figures must reflect real source code and verified test execution.
5. **No Regressions:** All existing tests (194 backend, 36 frontend) must continue to pass.

---

## 2. Development Setup

### Prerequisites
- Python 3.11+ (Python 3.12 or 3.13 recommended)
- Node.js 18 LTS or 20 LTS
- [Ollama](https://ollama.com/) (installed and running locally)
- Git

### Backend Setup
```bash
# 1. Navigate to backend directory
cd backend

# 2. Create and activate a Python virtual environment
python -m venv venv
# On Windows:
.\venv\Scripts\Activate.ps1
# On macOS / Linux:
source venv/bin/activate

# 3. Install runtime and development dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# 4. Pull the local Gemma 3 model in Ollama
ollama pull gemma3:1b

# 5. Run the backend development server
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### Frontend Setup
```bash
# 1. Navigate to frontend directory
cd frontend

# 2. Install dependencies
npm install

# 3. Start the Vite development server
npm run dev
# The application will be accessible at http://localhost:5173
```

---

## 3. Code Style & Quality Standards

We enforce automated code style checks on every pull request.

### Backend (Python)
- **Tool:** [Ruff](https://github.com/astral-sh/ruff)
- **Line Length:** 100 characters
- **Target Version:** Python 3.11 (`py311`)
- **Commands:**
  ```bash
  # Check lint rules
  ruff check backend

  # Format check
  ruff format --check backend

  # Auto-format
  ruff format backend
  ```

### Frontend (TypeScript / React)
- **Type Checking:** Strict mode enabled. No `any` types allowed in application source code.
- **Commands:**
  ```bash
  cd frontend
  # Type check
  npm run type-check

  # Production build check
  npm run build
  ```

---

## 4. Running the Test Suites

Every code change must include corresponding regression tests.

```bash
# Run backend tests
cd backend
pytest -v

# Run frontend tests
cd frontend
npm test

# Run deterministic evaluation benchmark
cd backend
python app/evaluation/runner.py --questions ../data/evaluation/questions.json --corpus ../data/sample_archive
```

---

## 5. Pull Request Guidelines

1. **Open an Issue First:** For major architecture changes or feature additions, please open an issue to discuss your approach before submitting code.
2. **Branch Naming:** Use clear branch names such as `feat/pdf-support`, `fix/chunk-offset`, or `docs/installation-guide`.
3. **Commit Messages:** Follow conventional commits (e.g., `feat:`, `fix:`, `docs:`, `test:`, `refactor:`).
4. **Documentation Updates:** If you add or modify API routes, configuration options, or UI flows, update the corresponding markdown documentation in `docs/`.
5. **No Secret Commits:** Ensure `.env` or personal documents are never committed.
