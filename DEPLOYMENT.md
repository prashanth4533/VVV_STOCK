# VVV Stock — Deployment Guide

Production-like hosting: **Netlify** (frontend) + **Railway** (backend) + **existing MySQL**.

> The database is **not** recreated. Point the backend at your existing MySQL
> instance; the schema and data are reused as-is.

---

## 0. Prerequisite — push the repo to GitHub (BLOCKER)

The git repository currently contains **only `README.md`**; the application code
is untracked. Railway and Netlify both deploy from a Git provider, so this must be
done first.

```bash
cd vvvSTOCK
git add .
git commit -m "Add application + deployment configuration"
git branch -M main
git remote add origin https://github.com/<you>/vvv-stock.git   # if not already set
git push -u origin main
```

`.gitignore` is configured so secrets (`backend/.env`, `.env.production`) and the
leftover local SQLite files (`*.db`) are **not** committed.

---

## 1. Architecture

```
Browser ──> Netlify (static React/Vite build)
                │  fetch(VITE_API_BASE_URL)
                ▼
        Railway (Flask + Gunicorn)
                │  mysql+pymysql://
                ▼
        Existing MySQL database
```

---

## 2. Backend — Railway

**Root directory must be set to `backend/`.** (The repo-root `requirements.txt` is
an unrelated global pip freeze and must not be used.)

Deployment files (already created):
- `backend/railway.json` — NIXPACKS build + Gunicorn start command.
- `backend/Procfile` — `web: gunicorn run:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120`
- WSGI entry point: `run:app` (`run.py` → `app = create_app()`).

### Steps
1. Railway → **New Project** → **Deploy from GitHub repo** → select this repo.
2. Service **Settings → Root Directory** = `backend`.
3. **Variables** → add the environment variables in section 4.
4. Deploy. Railway runs the `startCommand`; `$PORT` is injected automatically.
5. **Settings → Networking → Generate Domain** to get the public URL.
6. Health check: open `https://<railway-domain>/api/v1/health` → `{"status":"ok"}`.

### Notes
- `--workers 2` is a safe default; raise it for more traffic.
- Schema already exists, so no migration runs on boot. To apply migrations
  manually: `flask db upgrade` (set `FLASK_APP=run.py`).

---

## 3. Frontend — Netlify

Deployment files (already created):
- `netlify.toml` — build command `npm run build`, publish `dist`, SPA redirect.
- `.env.production.example` — template for the one required variable.

### Steps
1. Netlify → **Add new site** → **Import from Git** → select this repo.
2. Build settings are auto-read from `netlify.toml` (command `npm run build`,
   publish `dist`). Leave base directory empty (frontend is at repo root).
3. **Site settings → Environment variables** → add `VITE_API_BASE_URL`
   (section 4) pointing at the Railway domain **with** `/api/v1`.
4. Deploy. Copy the Netlify site URL (e.g. `https://vvv-stock.netlify.app`).
5. Go back to Railway and set `CORS_ORIGINS` to that Netlify URL, then redeploy.

> `VITE_*` variables are inlined at **build time**. After changing
> `VITE_API_BASE_URL`, trigger a fresh Netlify deploy.

---

## 4. Environment variables

### Railway (backend)
| Variable | Required | Example | Notes |
|---|---|---|---|
| `FLASK_ENV` | yes | `production` | Selects `ProductionConfig` (DEBUG off). |
| `SECRET_KEY` | yes | `<random 32+ chars>` | Flask secret. |
| `DATABASE_URL` | yes* | `mysql+pymysql://user:pass@host:3306/vvv_stock?charset=utf8mb4` | Single connection string. A bare `mysql://` scheme is auto-normalized to PyMySQL. |
| `CORS_ORIGINS` | yes | `https://vvv-stock.netlify.app` | Comma-separated; must include the Netlify origin. |

\* Instead of `DATABASE_URL` you may set component vars: `DB_HOST`, `DB_PORT`,
`DB_NAME`, `DB_USER`, `DB_PASSWORD`.

### Netlify (frontend)
| Variable | Required | Example |
|---|---|---|
| `VITE_API_BASE_URL` | yes | `https://<railway-domain>/api/v1` |

---

## 5. Production validation checklist

Backend (hit directly or via browser):
- [ ] `GET /api/v1/health` → `{"status":"ok"}`
- [ ] `GET /api/v1/products` returns existing rows
- [ ] `GET /api/v1/suppliers`, `/categories`, `/purchases`, `/sales`, `/stock-transactions` respond

End-to-end through the deployed UI (Netlify → Railway → MySQL):
- [ ] **Dashboard** — KPI cards, stock-status donut, category table populate
- [ ] **Products** — catalog lists products; Add Product persists
- [ ] **Inventory** — Stock In and Stock Adjustment save; recent transactions update
- [ ] **Purchases** — create a purchase; appears in history; stock increases
- [ ] **Sales** — create a sale; appears in history; stock decreases
- [ ] **Suppliers** — add/edit supplier persists
- [ ] No CORS errors in browser console
- [ ] No `localhost` calls in the Network tab (all hit the Railway domain)

---

## 6. Known blockers / prerequisites

1. **Repo not pushed** — only `README.md` is committed (see section 0).
2. **Root `requirements.txt` is wrong** — it's a global `pip freeze`
   (jupyter/torch/etc.), not app deps. Railway must use root dir `backend`,
   whose `requirements.txt` is correct.
3. **MySQL must be reachable from Railway** — the existing database has to accept
   remote connections from Railway's egress (public host/port, user granted remote
   access, firewall open). A `localhost`-only MySQL will not work.
4. **CORS is environment-driven** — until `CORS_ORIGINS` includes the live Netlify
   URL, the browser will block API responses.
