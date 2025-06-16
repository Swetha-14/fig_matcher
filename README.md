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
cd backend
pip install -r requirements.txt
python setup.py  # Generate embeddings
python main.py   # Start FastAPI server

### Frontend
```bash
cd frontend
npm install
npm start