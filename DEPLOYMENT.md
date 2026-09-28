# StartupOps AI — Deployment & Operations Guide

## 1. Local Development Quickstart

### Prerequisites
- Python 3.11+
- Node.js 18+
- SQLite (default for development) or PostgreSQL with `pgvector`
- Redis (optional, in-memory fallback enabled by default)

### Backend Setup
```bash
cd backend
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
cp ../.env.example .env
uvicorn app.main:app --reload --port 8000
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

The application will be accessible at:
- Web UI: `http://localhost:3000`
- API Docs (Swagger): `http://localhost:8000/docs`

---

## 2. Docker & Containerized Deployment

Run the complete multi-service stack with Docker Compose:
```bash
docker-compose -f infra/docker-compose.yml up --build -d
```

### Stack Components:
- `frontend`: Next.js production server (`:3000`)
- `backend`: FastAPI Uvicorn ASGI server (`:8000`)
- `db`: PostgreSQL 16 with pgvector extension (`:5432`)
- `redis`: Redis cache & event broker (`:6379`)

---

## 3. Deploy to Render (render.com)

The codebase is pre-configured with a Render Blueprint [`render.yaml`](file:///render.yaml) for zero-configuration, 1-click deployment.

### Option A: 1-Click Blueprint Deployment (Recommended)
1. Push your repository to **GitHub** or **GitLab**.
2. Go to your **[Render Dashboard](https://dashboard.render.com/)** -> Click **New +** -> **Blueprint**.
3. Connect your repository.
4. Render will automatically detect [`render.yaml`](file:///render.yaml) and provision:
   - `startupops-db`: Managed PostgreSQL database (free tier).
   - `startupops-backend`: Python FastAPI Web Service running on `$PORT`.
   - `startupops-frontend`: Next.js Web Service automatically connected to the backend.
5. In the backend settings, set your `GOOGLE_AI_STUDIO_API_KEY` (Gemini API key).
6. Click **Apply**!

---

### Option B: Manual Service Creation on Render

#### 1. Database (Render PostgreSQL)
- **New +** -> **PostgreSQL**
- Name: `startupops-db`
- Copy the **Internal Database URL** (e.g., `postgres://...`).

#### 2. Backend Web Service
- **New +** -> **Web Service** -> Connect repo
- **Root Directory**: `backend`
- **Runtime**: `Python 3`
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- **Environment Variables**:
  - `DATABASE_URL`: Your Render PostgreSQL URL or leave unset to use SQLite.
  - `GOOGLE_AI_STUDIO_API_KEY`: Your Gemini API Key.
  - `APP_SECRET_KEY`: Random 32+ character string.
  - `ENCRYPTION_KEY`: 64-char hex string (e.g., `0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef`).
  - `PYTHON_VERSION`: `3.11.9`

#### 3. Frontend Web Service
- **New +** -> **Web Service** -> Connect repo
- **Root Directory**: `frontend`
- **Runtime**: `Node`
- **Build Command**: `npm install && npm run build`
- **Start Command**: `npm start`
- **Environment Variables**:
  - `BACKEND_URL`: `https://<your-backend-name>.onrender.com`
  - `NEXT_PUBLIC_API_URL`: `https://<your-backend-name>.onrender.com`
  - `NODE_VERSION`: `18.20.4`

