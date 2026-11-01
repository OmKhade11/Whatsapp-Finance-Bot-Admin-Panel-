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
