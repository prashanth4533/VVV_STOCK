# VVV Stock — Deployment Guide

Production-like hosting: **Netlify** (frontend) + **Railway** (backend) + **existing MySQL**.

> The database is **not** recreated. Point the backend at your existing MySQL
> instance; the schema and data are reused as-is.

---

## 0. Repo layout (monorepo)

```
vvvSTOCK/
├── frontend/   # React/Vite app   → Netlify  (Base directory = frontend)
├── backend/    # Flask API        → Railway  (Root Directory = backend)
└── docs/       # this guide
```

The app is already deployed. Railway and Netlify both deploy from GitHub, so push
changes before redeploying. `.gitignore` keeps secrets (`backend/.env`,
`frontend/.env.production`) and local `*.db` files out of the repo.

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

**Root directory must be set to `backend/`.** Dependencies come from
`backend/requirements.txt`.

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

Deployment files (in `frontend/`):
- `frontend/netlify.toml` — build command `npm run build`, publish `dist`, SPA redirect.
- `frontend/.env.production.example` — template for the one required variable.

### Steps
1. Netlify → **Add new site** → **Import from Git** → select this repo.
2. **Set Base directory = `frontend`.** Build settings are then read from
   `frontend/netlify.toml` (command `npm run build`, publish `dist`).
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

## 4b. WhatsApp EOD report — cron + secrets

The nightly report runs as a **separate one-shot process**, not inside the web
workers (an in-process scheduler would double-fire with `--workers 2`).

**Railway setup:**
1. In the same project, add a **second service** from the same repo (Root
   Directory = `backend`), OR add a **Cron Schedule** to a service.
2. **Cron schedule:** `0 21 * * *` and set the service variable `TZ=Asia/Kolkata`
   so 21:00 means IST.
3. **Start command:** `python -m app.jobs.run_eod`
   (one-shot: it runs once and exits — exactly what cron services expect).
4. Add the secrets below as Railway **Variables** (shared with the web service).

| Variable | Required | Notes |
|---|---|---|
| `WHATSAPP_API_TOKEN` | yes | Meta permanent system-user token. |
| `WHATSAPP_PHONE_NUMBER_ID` | yes | Sender phone-number id from Meta. |
| `WHATSAPP_API_VERSION` | no | Defaults to `v21.0`. |

**Behaviour** (enable/disable, time, recipients, template) is stored in the
`settings` table and managed via `GET`/`PUT /api/v1/eod/settings` — not env vars.

**Before the first live run:**
- [ ] Create + get Meta approval for a UTILITY template (12 body variables — see
      the comment block in `app/services/message_formatter.py`). Put its name in
      `eod.template_name`. *Unsolicited scheduled sends require a template;*
      free-form text only works inside a 24h customer-service window.
- [ ] Set `eod.recipients` to the partners' numbers (country code, digits only, no `+`).
- [ ] Set `eod.enabled = true`.
- [ ] Smoke test without sending: `python -m app.jobs.run_eod --dry-run --force`
- [ ] Test one number from the Admin UI ("Test Send") or
      `POST /api/v1/eod/test-send {"recipient":"9198..."}`.

> Manual run any time: `python -m app.jobs.run_eod --force`
> (`--date=YYYY-MM-DD` to backfill a specific day).

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
