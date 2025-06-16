# 🔍 Figbox Matcher


An intelligent people matching platform that uses SBERT embeddings and FAISS for semantic search to connect users based on their profiles, expertise, and intent. (WIP)

## 🛠️ Tech Stack

**Backend:**
- FastAPI + Python
- SBERT (Sentence Transformers)
- FAISS vector search
- Pydantic models

**Frontend:**
- React + TypeScript

## Quick Start


### Backend
```bash
# Create virtual environment in project root
python3 -m venv venv
source venv/bin/activate

# Install dependencies and start server
pip install -r backend/requirements.txt
python backend/setup.py  # Generate embeddings
python backend/main.py   # Start FastAPI server

### Frontend
```bash
cd frontend
npm install
npm start
