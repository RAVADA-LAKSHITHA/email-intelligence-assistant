# AI Email Intelligence Assistant

An AI-powered assistant that connects to Gmail, categorizes and summarizes
incoming email using the Gemini API, extracts action items and deadlines,
and surfaces everything in a dashboard.

## Tech Stack

- **Frontend:** React (Vite), Tailwind CSS
- **Backend:** Python, FastAPI
- **Database:** SQLite (PostgreSQL in production)
- **AI:** Google Gemini API
- **Auth:** Gmail OAuth 2.0

## Status

🚧 In development — Phase 1 (project setup) complete.

## Local Setup

### Backend
```bash
cd backend
python -m venv venv
venv\Scripts\activate        # macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env         # then fill in your keys
fastapi dev app/main.py
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```