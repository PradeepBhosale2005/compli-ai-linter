# CompliAI Linter

CompliAI Linter is a hybrid AI-powered compliance analysis tool focused on GxP and healthcare regulatory documents. It combines core rule-based checks, user-defined rules, and AI-assisted auditing (via Azure OpenAI) with optional knowledge-base enrichment (RAG) to generate findings and a compliance score.

## Tech stack

- Backend
  - Python 3.11+ (project used Python 3.13 in local dev)
  - FastAPI
  - Uvicorn (ASGI server)
  - SQLite (local DB for history)
  - ChromaDB (optional RAG knowledge base)
  - Azure OpenAI (embeddings & chat completion)
  - python-docx, pypdf (document parsing)

- Frontend
  - React (Vite or CRA) located in `frontend/my-project`
  - JavaScript / TypeScript depending on the project template

- Dev tools
  - pip for Python dependencies (virtualenv recommended)
  - npm / pnpm / yarn for frontend dependencies

---

## Quick start — for a complete beginner

This section will walk you through setting up and running the entire project (backend + frontend) on Windows using PowerShell. Follow each step in order.

### 1) Prerequisites

- Install Python 3.11+ (download from https://www.python.org). Note: your local dev used Python 3.13, but 3.11 or 3.12 should work.
- Install Node.js + npm (https://nodejs.org)
- Optional: Git (https://git-scm.com) to clone the repository

### 2) Clone the repository (if needed)

```powershell
# replace <path> with your desired folder
git clone https://github.com/YourUser/compli-ai-linter.git
cd compli-ai-linter
```

If you already have the code locally, open PowerShell in the repo root.

### 3) Backend setup (Windows PowerShell)

1. Open PowerShell and change into the backend folder:

```powershell
cd .\backend
```

2. Create a Python virtual environment and activate it:

```powershell
python -m venv venv
# Activate the venv (PowerShell)
.\venv\Scripts\Activate.ps1
```

3. Install Python dependencies (a `requirements.txt` is included in `backend/requirements.txt`):

```powershell
pip install -r requirements.txt
```

If you prefer to install packages manually, this project commonly uses:

```powershell
pip install fastapi uvicorn[standard] azure-openai chromadb python-docx pypdf openai pydantic
```

4. Configure environment variables

Create environment variables required for Azure OpenAI and optional RAG. You can set them in PowerShell for the current session:

```powershell
$env:OPENAI_API_KEY = "<your-api-key>"
$env:AZURE_OPENAI_ENDPOINT = "https://your-azure-openai-endpoint"
$env:AZURE_OPENAI_API_VERSION = "2024-06-01"
$env:AZURE_OPENAI_CHAT_DEPLOYMENT = "<chat-deployment-name>"
$env:AZURE_OPENAI_EMBEDDING_DEPLOYMENT = "<embedding-deployment-name>"
```

Note: The project reads settings from `config/settings.py` — inspect that file for exact variable names if you run into issues.

5. For Initialize the croma db and Embedding the pdf's :

```powershell
python create_kb.py
```

This will print table info or create the SQLite file on first run (if the code creates it at startup).

6. Start the backend API

Run the uvicorn server from the `backend` folder (venv active):

```powershell
uvicorn api.main:app --reload
```

If you get `ModuleNotFoundError: No module named 'api'`, ensure you're executing the command from inside the `backend` folder (the folder that contains the `api` package) and the virtualenv is activated. The `backend` folder should contain the `api` directory.

Visit the API docs once the server is running:

- http://localhost:8000/docs
- http://localhost:8000/health

### 4) Frontend setup (React)

1. Open a new PowerShell window and go to the frontend project:

```powershell
cd ..\frontend\my-project
```

2. Install packages:

```powershell
npm install
# or pnpm install
# or yarn install
```

3. Start the dev server (the command depends on the frontend template):

```powershell
npm run dev
# or
npm start
```

By default the app runs on http://localhost:3000 or http://localhost:5173. The frontend is configured to call the backend running at http://localhost:8000 in development.

### 5) Test a full upload & analysis

- From the frontend: use the UI to upload a DOCX or PDF and click analyze.
- From the backend: use `curl` or Postman against the `/analyze-document` endpoint to upload a file.

Example using curl (PowerShell):

```powershell
curl -X POST "http://localhost:8000/analyze-document" -H "accept: application/json" -H "Content-Type: multipart/form-data" -F "file=@C:\path\to\your\document.docx"
```

### 6) Running quick tests & helper scripts

- Run backend test scripts (if present) from the `backend` folder with the venv active:

```powershell
python test_focused_system.py
```

- Populate RAG/KB embeddings (if using the knowledge base):

```powershell
python create_kb.py
```

---

## Files to know in the repo

- `backend/api/main.py` — API endpoints and orchestration
- `backend/services/ai_linter_service.py` — builds prompts and calls Azure OpenAI
- `backend/services/parser_service.py` — DOCX/PDF parsing logic
- `backend/services/rag_service.py` — KB & embeddings (ChromaDB)
- `backend/services/scorer_service.py` — scoring & explanations
- `backend/gxp_rules.json` — global user rules (editable by the UI)
- `backend/check_database.py` — small utility to inspect the SQLite DB
- `frontend/my-project` — React application

## Common troubleshooting

- Module import errors when running `uvicorn api.main:app`:
  - Make sure you run the command inside the `backend` folder (so Python can import the `api` package).
  - Activate the virtualenv before running.
  - If problems persist, try `python -m uvicorn api.main:app --reload`.

- `uvicorn` not found: install `uvicorn` in the active virtualenv: `pip install uvicorn[standard]`.

- Azure OpenAI authentication errors: re-check endpoint and API key. Try a small embeddings call in a short Python script to validate credentials.

- Frontend unable to reach backend: verify the backend URL in the frontend configuration and CORS settings in `api/main.py`.

## Future Scope

- Add a `backend/requirements.txt` (created in the repo) with pinned dependency versions.
- Add `backend/__init__.py` and `backend/api/__init__.py` files if you still see import issues when running from the repo root.
- Add simple PowerShell or npm scripts to start both backend and frontend together.
- Add automated tests and a GitHub Actions CI workflow to run lint/tests on push.

---

If you'd like, I can now:
- create a `backend/requirements.txt` file (I will add one if you confirm),
- add `__init__.py` files to `backend` and `backend/api` to help imports, and
- add a small PowerShell script to start both the backend and frontend in development.


