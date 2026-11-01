# Techspot Financial Assistant

Self-contained FastAPI baseline for the Techspot personal and business financial assistant. Production persistence is Supabase Postgres; the SQLite fallback exists only for credential-free local tests.

## Run

Create a private `.env` from `.env.example` and set `SUPABASE_DB_URL` to the Session pooler connection string from the Supabase project’s **Connect** dialog. Then run:

```powershell
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Run `supabase/migrations/001_initial_schema.sql` in the Supabase SQL Editor before starting the API. The application will then use Supabase Postgres instead of SQLite.

Open `http://127.0.0.1:8000/docs`. Protected endpoints currently use `X-User-ID` as a development identity adapter. Replace it with verified Supabase Auth JWT identity before production. Admin endpoints additionally require `X-Admin: true`.

## Test

```powershell
pytest -q
```

## Admin dashboard

The React/Vite admin workspace is under `admin/`. From that directory, install dependencies with `npm install` and run `npm run dev`. It currently consumes the protected `/api/v1/admin/dashboard` endpoint and intentionally displays unavailable states for modules whose tables are not present in the verified local schema.

## Configuration

Copy `.env.example` to `.env` and provide the Supabase database URL. Keep `.env` private and out of Git. AI, WhatsApp, and payment settings remain optional until those providers are connected.


## Vercel multi-service deployment

This repository is configured as one Vercel project with two services:

- `app`: FastAPI from the repository root (`app.main:app`).
- `admin`: Vite/React from `admin/`, published under `/admin/`.

Public routing:

- `/` -> FastAPI status response.
- `/api` and `/api/*` -> FastAPI.
- `/docs`, `/openapi.json`, and `/health` -> FastAPI.
- `/admin` and `/admin/*` -> Vite admin dashboard.

The admin dashboard calls the API through same-origin `/api/...` URLs, so no
internal service binding is required. The Vite development proxy remains for
local development only.

### Vercel environment variables

Set these in the Vercel project's Environment Variables for Production (and
Preview/Development if needed):

- `SUPABASE_URL`: Supabase project URL.
- `SUPABASE_ANON_KEY` or `SUPABASE_PUBLISHABLE_KEY`: browser-safe Supabase
  publishable/anon key.
- `SUPABASE_DB_URL` (or `DATABASE_URL`): backend PostgreSQL connection string.
- Add other backend secrets only when the corresponding integration is enabled.

Never expose `SUPABASE_SERVICE_ROLE_KEY`, database credentials, WhatsApp access
tokens, payment secrets, or AI provider keys through `VITE_*` variables or
frontend build-time definitions. Do not commit `.env`.

After pushing these changes to the connected Git branch, Vercel should build
both services as one deployment. Test `/`, `/admin`, `/docs`, and `/health`.
