---
name: replit-to-vercel
description: >-
  End-to-end zero-downtime migration playbook for moving a full-stack web application
  (especially React + Vite + Express + Drizzle + PostgreSQL/Neon) from Replit to
  Vercel hosting and local/agent-driven GitHub development. Use when the user asks to
  migrate, move, or decouple a Replit-hosted app or database to Vercel.
---

# Replit → Vercel Zero-Downtime Migration

Move a Replit-hosted full-stack app to **Vercel + Neon PostgreSQL** (or another managed Postgres) and GitHub-driven local/agent development **without touching or taking down the live Replit site until final DNS cutover**.

For detailed failure modes and fixes (Node 26 ESM `.js` imports, Neon idle disconnects, 4.5 MB uploads, DNS authority checks), see [references/replit-gotchas.md](./references/replit-gotchas.md).

---

## Core Safety Rules

1. **Read-only on Replit:** Never edit, stop, or redeploy the live Replit app during migration. Only read secrets, inspect config, and snapshot the **Production** database (not Development).
2. **Preview-first cutover:** Refactor on a feature branch (e.g. `migrate-to-vercel`), verify every route/API/auth flow on the Vercel Preview URL first, then merge to `main`, then flip DNS.
3. **Never leak secrets:** Keep raw API keys, passwords, and connection strings out of git, commit messages, and field notes. Put local secrets only in gitignored `.env.local`, and clean up any temporary scratch env files immediately after DB migration.
4. **Live Field Notes (when requested or for multi-step migrations):** Maintain a redacted `field_notes.md` log recording milestones, DB row-count parity tables, DNS records, and safe screenshots (always re-hide revealed secrets before capturing).

---

## Phase 1 — Audit & Upfront Dependency Plan (Before Touching Cloud Resources)

1. Clone the GitHub repository locally (use `gh repo clone` if private).
2. Audit the codebase before proposing a plan:
   - Inspect `package.json`, `.replit`, `vite.config.*`, `drizzle.config.*`, `server/`, `shared/`, `client/index.html`, and `client/public/favicon.*`.
   - Grep every `process.env.` reference across the repo to build a complete environment variable table.
   - Check for Replit-only lock-in: Replit Auth, Replit Object Storage, Replit KV/DB, `@replit/*` Vite plugins, `REPLIT_*` env vars, orange Replit `favicon.png`, and Replit references in in-app docs/guides.
   - Check for serverless incompatibilities:
     - Local disk writes (`fs.writeFile`, CSV/log backups) → Vercel FS is read-only.
     - Detached/fire-and-forget promises after `res.json()` → must use `waitUntil()` from `@vercel/functions`.
     - Large uploads (`multer` > 4.5 MB) → Vercel caps HTTP request/response bodies at **4.5 MB**; use client-side extraction/chunking or Vercel Blob client uploads.
     - Active `setInterval` timers → call `.unref()` so serverless/dev processes exit cleanly.
     - Long-lived `httpServer.listen(..., { reusePort: true })` → `reusePort: true` errors on macOS local dev.
3. Present the user with:
   - Confirmation + concrete list of code changes/gotchas found.
   - Database hosting options (recommend **Neon via Vercel Marketplace** free tier when dataset is small and Replit already ran on Neon).
   - Complete table of required/optional env vars and access needed (Vercel account/CLI/MCP, Replit secrets + Production `DATABASE_URL`, DNS host).

---

## Phase 2 — Collect Secrets & Audit Source Production DB

1. Obtain secrets and **Production** `DATABASE_URL` (from user paste or browser sign-in to Replit → `Tools → Secrets` and `Publishing → Production app secrets`). Distinguish **Production** vs **Development** DB!
2. Run a strictly read-only audit of all tables and row counts in the Replit Production DB so you have an exact baseline for 1:1 migration parity.
3. Note any custom domain configured in Replit (`Tools → Domains`), and **always verify the true authoritative DNS host** with:
   ```bash
   dig +short NS <root-domain>
   dig +short <app-hostname>
   ```
   Do not trust Replit's registrar label — registrar (e.g. GoDaddy) and DNS authority (e.g. Hostinger `ns1.dns-parking.com` / Cloudflare) often differ.

---

## Phase 3 — Refactor for Vercel + Local/Agent Dev (on `migrate-to-vercel` Branch)

1. **Split Express app from server listener:**
   - Extract Express middleware, session store, routes, and error handler into `server/app.ts` exporting synchronous `createExpressApp()`.
   - Keep `server/index.ts` for local `npm run dev` / standalone runs: import `server/env.ts` (`dotenv.config({ path: ".env.local" }); dotenv.config();`) **as the very first import** (remember ESM hoists imports!), wire Vite in dev or `serveStatic` in prod, and listen on `PORT || 5000` **without** `reusePort: true`.
   - Create `api/index.ts` exporting `export default createExpressApp();`.
2. **Fix ESM imports for Vercel Node 22/26 runtime:**
   - If `package.json` has `"type": "module"`, replace path aliases (`@shared/*`) in `api/` and runtime `server/` files with relative imports **with explicit `.js` extensions** (e.g. `../shared/schema.js`, `./db.js`). Without `.js`, Node ESM throws `ERR_MODULE_NOT_FOUND` at runtime on Vercel even when the build succeeds!
3. **Configure `vercel.json`:**
   - Set `buildCommand` (e.g. `npm run build:client`), `outputDirectory` (`dist/public`), `functions["api/index.ts"]` with appropriate `maxDuration` and `excludeFiles` (exclude `attached_assets`, exports, docs, `client`, `dist`, large SQL dumps so the serverless bundle stays small).
   - Add rewrites: `/api/(.*)` → `/api/index`, `/sitemap.xml` (and any server-rendered routes) → `/api/index`, and `/(.*)` → `/index.html`.
4. **Serverless hardening:**
   - `server/db.ts`: Configure `pg.Pool` with SSL for non-localhost URLs, bounded `max` on Vercel, and call `attachDatabasePool(pool)` from `@vercel/functions` when `process.env.VERCEL` is set.
   - `drizzle.config.ts`: Load `.env.local`/`.env` via `dotenv` and prefer `process.env.DATABASE_URL_UNPOOLED || process.env.DATABASE_URL`.
   - Wrap detached background tasks in `waitUntil(promise)` from `@vercel/functions` when `process.env.VERCEL` is set.
   - Guard disk writes with `if (process.env.VERCEL) return;` and `.unref()` cleanup intervals.
   - Ensure `package.json` sets `"engines": { "node": ">=22" }` (Node 20 is deprecated on Vercel).
5. **Remove Replit lock-in & branding:**
   - Remove `@replit/*` devDependencies and Vite plugins, `.replit`, `replit.md`, and Replit post-merge hooks.
   - Update `vite-plugin-meta-images.ts` (or equivalent) to drop `REPLIT_*` env vars.
   - Check `client/public/favicon.*` — replace the default orange Replit favicon with a branded SVG + PNG icon matching the app.
   - Update `.gitignore` (`.env`, `.env.local`, `.env.*.local`, `.vercel`), add `.env.example`, add `AGENTS.md`, and update any in-app Ops Guide referencing Replit.
6. **Verify locally:** Run `npm install`, `npm test`, and `npm run build` before committing and pushing `migrate-to-vercel`.

---

## Phase 4 — Provision Vercel Project, Neon Postgres & Migrate Data

1. Create the Vercel project linked to the GitHub repo (via Vercel MCP, Vercel CLI, or Vercel dashboard).
2. Add all non-DB environment variables across `production`, `preview`, and `development` (mark secrets as `sensitive`).
3. Provision **Neon Serverless Postgres** in Vercel Storage (`us-east-1` / `iad1` to colocate with Vercel Functions, Free tier unless user requests otherwise) and connect it to all environments (auto-injecting `DATABASE_URL` and `DATABASE_URL_UNPOOLED`).
4. Write gitignored `.env.local` locally for dev/migrations.
5. Push Drizzle schema against `DATABASE_URL_UNPOOLED`:
   ```bash
   npm run db:push -- --force
   ```
6. Run the reusable lossless migration script [scripts/migrate-postgres.mjs](./scripts/migrate-postgres.mjs) to copy all rows, preserve primary key IDs, reset all `SERIAL` sequences, verify 1:1 row-count parity, and test pooled `DATABASE_URL` connectivity.
7. Delete any temporary scratch credentials file once migration succeeds.

---

## Phase 5 — Preview Verification → Production Merge → DNS Cutover

1. Wait for the `migrate-to-vercel` Preview deployment to reach **Ready** on Vercel.
2. Verify end-to-end on the live Preview URL (using the logged-in browser if Deployment Protection is enabled):
   - Homepage + live DB stats/counts (`HTTP 200`, zero 4xx/5xx API errors).
   - Dynamic detail pages, search/filters, and AI/LLM endpoints (verify any `waitUntil()` telemetry rows actually land in Neon!).
   - Sitemap/XML endpoints.
   - Auth/Admin login + reload persistence (verifying Postgres session store) + logout.
3. Merge `migrate-to-vercel` → `main` (`git merge --no-ff`) and push `main` to trigger the Vercel **Production** deployment.
4. Register the custom domain in Vercel (`Settings → Domains`, assigned to Production) to obtain the exact `CNAME` (or `A`) record.
   - Note: Vercel's default Deployment Protection (`all_except_custom_domains`) keeps `*.vercel.app` behind Vercel Auth while making the custom domain 100% public automatically.
5. Instruct the user (or apply via browser) to update DNS at the **actual authoritative DNS provider** (from Phase 2 `dig NS`):
   - Delete any conflicting `A` record **and** any `replit-verify=...` `TXT` record on the same hostname (DNS forbids `CNAME` + `A`/`TXT` coexistence).
   - Add Vercel's exact `CNAME` record.
6. Verify live cutover:
   - `dig +short CNAME <app-hostname>` resolves to Vercel's target.
   - Vercel Domains shows **Valid Configuration** with HTTPS/TLS active.
   - Open `https://<app-hostname>/` and confirm `HTTP 200`, `server: Vercel` response headers on both `/` and `/api/*`, no Vercel login prompt, live DB data, and branded favicon (`200 OK`).
7. **Decommission Replit (after ~24 hours):**
   - Verify global DNS across multiple resolvers (`dig +short <app-hostname> @1.1.1.1` and `@8.8.8.8`) returns only Vercel and no old Replit IP.
   - In Replit, disconnect the custom domain under **Domains** and click **Publishing → Adjust settings → Unpublish** (do **not** delete the Repl or database — unpublishing stops deployment compute billing while keeping an offline backup).
   - Re-verify `https://<app-hostname>/` immediately afterward (`HTTP 200`, `server: Vercel`, live API data).
