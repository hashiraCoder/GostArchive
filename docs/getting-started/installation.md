# Installation & Setup Guide

This guide provides step-by-step instructions for installing and running GhostArchive on Windows, macOS, and Linux.

---

## 1. System Requirements

### Hardware
- **Processor:** Modern x86_64 or Apple Silicon ARM64 processor (4+ cores recommended).
- **RAM:** Minimum 8 GB (16 GB recommended for concurrent generation and indexing).
- **Disk Space:** ~3 GB free storage for virtual environments, node modules, and local model weights (`all-MiniLM-L6-v2` ~90 MB, `gemma3:1b` ~800 MB).

### Software
- **Operating System:** Windows 10/11, macOS 12+, or modern Linux (Ubuntu 22.04+).
- **Python:** 3.11, 3.12, or 3.13.
- **Node.js:** Node.js 18 LTS or 20 LTS (with npm).
- **Ollama:** Download and install from [ollama.com](https://ollama.com).

---

## 2. Windows Installation (PowerShell)

### Step 1: Clone Repository
```powershell
git clone https://github.com/your-username/GhostArchive.git
cd GhostArchive
```

### Step 2: Configure Backend
```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### Step 3: Configure Environment Variables
```powershell
Copy-Item ..\.env.example ..\.env
```
Inspect `.env` at the root directory. The default loopback settings (`127.0.0.1:8000`, `127.0.0.1:11434`, `127.0.0.1:5173`) are ready for immediate local use.

### Step 4: Pull Model in Ollama
Make sure the Ollama desktop application is running, then pull the default generation model:
```powershell
ollama pull gemma3:1b
```

### Step 5: Start the Backend Service
```powershell
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
Leave this terminal window open. You can check `http://127.0.0.1:8000/api/health` in your browser to verify it responds `{"status":"ok","app_version":"0.1.0"}`.

### Step 6: Install & Start Frontend
In a new PowerShell terminal:
```powershell
cd GhostArchive\frontend
npm install
npm run dev
```
Navigate to **`http://localhost:5173`** to access the GhostArchive UI.

---

## 3. macOS & Linux Installation (Bash/Zsh)

### Step 1: Clone Repository
```bash
git clone https://github.com/your-username/GhostArchive.git
cd GhostArchive
```

### Step 2: Configure Backend
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### Step 3: Configure Environment Variables
```bash
cp ../.env.example ../.env
```

### Step 4: Pull Model in Ollama
```bash
ollama serve &   # If not already running as a system service
ollama pull gemma3:1b
```

### Step 5: Start Backend Service
```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### Step 6: Install & Start Frontend
In a new terminal:
```bash
cd GhostArchive/frontend
npm install
npm run dev
```
Open **`http://localhost:5173`** in your browser.

---

## 4. Verifying the Installation

1. Look at the top right of the GhostArchive UI header. The **Status Pill** should display **Ready** with a green dot.
2. Click on the **System Status** tab in the navigation bar. You should see all 4 core services reporting operational status:
   - **SQLite Database:** Ready
   - **ChromaDB Vector Store:** Ready
   - **Sentence Transformers Embedding Model:** Ready
   - **Local Ollama Daemon & Gemma 3 Model:** Ready
3. Navigate to **Documents**, upload a sample text file (or one from `data/sample_archive/`), then navigate to **Ask Archive** to ask a question.
