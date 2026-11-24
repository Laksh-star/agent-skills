# Replit → Vercel Migration Gotchas & Fixes

Real issues encountered migrating Replit full-stack apps (React + Vite + Express + Drizzle + Neon) to Vercel, and their proven fixes.

---

## 1. Node 26 ESM `ERR_MODULE_NOT_FOUND` on Vercel Runtime
- **Symptom:** Vercel build succeeds (`Ready`), static site loads, but every `/api/*` request returns `HTTP 500 FUNCTION_INVOCATION_FAILED` with:
  `Error [ERR_MODULE_NOT_FOUND]: Cannot find module '/var/task/server/app' imported from /var/task/api/index.js`
- **Cause:** `package.json` has `"type": "module"`, and `@vercel/node` compiles TypeScript files without rewriting extensionless relative imports (`../server/app`) or tsconfig path aliases (`@shared/schema`).
- **Fix:**
  1. Replace `@shared/*` imports in `api/` and runtime `server/` files with relative paths (`../shared/schema.js`, `../../shared/schema.js`).
  2. Append explicit `.js` extensions to **all** relative imports in `api/` and runtime `server/` files (`./db.js`, `./routes/articles.js`, etc.). TypeScript (`moduleResolution: "bundler"`), `tsx`, `esbuild`, and Node 22/26 ESM all resolve `.js` → `.ts` cleanly.

## 2. ESM Import Hoisting Breaks `dotenv.config()`
- **Symptom:** Running `npm run dev` locally throws `DATABASE_URL must be set` even though `.env.local` exists and `dotenv.config()` is at the top of `server/index.ts`.
- **Cause:** In ESM (`"type": "module"`), static `import` declarations are hoisted and evaluated *before* any top-level statements in the same file.
- **Fix:** Create a tiny `server/env.ts` containing `dotenv.config({ path: ".env.local" }); dotenv.config();` and import `import "./env.js";` as the **very first line** of `server/index.ts`.

## 3. `reusePort: true` Crashes Local macOS Dev
- **Symptom:** `ENOTSUP: operation not supported on socket` when starting `npm run dev` on macOS.
- **Cause:** Replit templates include `httpServer.listen({ port, host: "0.0.0.0", reusePort: true })`.
- **Fix:** Remove `reusePort: true` from `server/index.ts`.

## 4. Neon Idle Autosuspend (`57P01`) During Row-by-Row Migration
- **Symptom:** Migration script aborts midway with `error: terminating connection due to administrator command` (`code: '57P01'`).
- **Cause:** Holding the source Neon connection open for >2 minutes while running hundreds of single-row remote `INSERT`s into the target database causes Neon's autosuspend to kill the idle source connection.
- **Fix:** Read all source tables into memory first and immediately `await src.end()` (~2s), then write **batched multi-row `INSERT`s** (25 rows per statement) into the target database via `DATABASE_URL_UNPOOLED`. See [scripts/migrate-postgres.mjs](../scripts/migrate-postgres.mjs).

## 5. Detached Promises Killed on Serverless (`waitUntil`)
- **Symptom:** Fire-and-forget async work after `res.json()` (telemetry, LLM shadow judges, webhook retries) silently disappears on Vercel.
- **Fix:** Wrap the promise with `waitUntil(promise)` from `@vercel/functions` when `process.env.VERCEL` is truthy. Pass a **Promise**, not a callback.

## 6. Connection Pooling & Fluid Compute (`attachDatabasePool`)
- **Fix:** In `server/db.ts`, keep `pg.Pool` at module scope, set `ssl: { rejectUnauthorized: false }` for non-localhost URLs, bound `max` (e.g. `10` on Vercel), and call `attachDatabasePool(pool)` from `@vercel/functions` so idle connections close cleanly when instances suspend.
- Prefer `DATABASE_URL_UNPOOLED || DATABASE_URL` in `drizzle.config.ts` for schema pushes (`drizzle-kit push`).

## 7. Read-Only Filesystem & 4.5 MB Upload Limit
- **Read-only FS:** Any `fs.writeFile` backup (like `data/subscribers.csv`) throws `EROFS` on Vercel. Guard with `if (process.env.VERCEL) return;`.
- **4.5 MB payload cap:** Vercel Serverless Functions return `413 FUNCTION_PAYLOAD_TOO_LARGE` for bodies > 4.5 MB. For admin ZIP imports (e.g. Medium exports), extract files client-side with `jszip` and POST chunked JSON batches (~1.5 MB each) to a batch endpoint — or use Vercel Blob client uploads for binary media.

## 8. Leftover Replit Branding & Bloated Bundles
- **Favicon:** Replit templates ship an orange Replit logo at `client/public/favicon.png`. Replace with a branded `favicon.svg` + `favicon.png` matching the app's UI.
- **Function bundle bloat:** Replit projects accumulate `attached_assets/`, export zips, and SQL dumps. Add `excludeFiles` in `vercel.json` under `functions["api/index.ts"]` to exclude non-runtime directories.
- **Node version:** Node.js 20 was deprecated on Vercel on Oct 1, 2026 — set `"engines": { "node": ">=22" }` in `package.json`.

## 9. DNS Registrar vs Authoritative DNS Host & `replit-verify=` TXT Conflict
- **Trap 1:** Replit's Domains pane may display the domain registrar (e.g. GoDaddy), while actual DNS records live at another provider (e.g. Hostinger `ns1.dns-parking.com` or Cloudflare). Always run `dig +short NS <root-domain>` first.
- **Trap 2:** Replit domains typically have both an `A` record pointing to Replit **and** a `TXT` record (`replit-verify=<uuid>`) on the subdomain. Per RFC DNS rules, a `CNAME` cannot coexist with either `A` or `TXT` at the same hostname — delete **both** before adding Vercel's `CNAME`.
- **Deployment Protection:** New Vercel projects default to `Standard Protection` (`all_except_custom_domains`), meaning `*.vercel.app` asks logged-out visitors to sign in to Vercel, while custom domains are 100% public automatically once attached.
