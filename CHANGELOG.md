# Changelog

All notable changes to VVV Stock are documented here.
Format loosely follows [Keep a Changelog](https://keepachangelog.com/);
versioning is [SemVer](https://semver.org/).

## [Unreleased]
- Repo reorganized into a `frontend/` + `backend/` monorepo; added `docs/`,
  this changelog, and a rewritten README. Removed stray root files
  (global `requirements.txt`, leftover `*.db`, temp scripts).

## [1.0.0] — 2026-06-16
Initial production release.

### Added
- Product catalog, purchases, sales, stock-in/adjustment, suppliers, dashboard,
  and reports — all backed by the Flask API and MySQL.
- Deployment: Netlify (frontend) + Railway (backend + MySQL).

### Notes
- Backend is MySQL-only; API base URL on the frontend is environment-driven
  via `VITE_API_BASE_URL`.
