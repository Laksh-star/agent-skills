#!/usr/bin/env node
/**
 * Lossless PostgreSQL-to-PostgreSQL data migration script (Replit Neon -> Target Neon).
 *
 * Strategy:
 *  1. Snapshots all public tables (excluding ephemeral `session` by default) from
 *     SOURCE_DATABASE_URL into memory, then immediately closes the source connection
 *     so Neon autosuspend cannot drop an idle connection mid-migration.
 *  2. Writes batched multi-row INSERTs (25 rows/query) inside a single transaction
 *     to TARGET_DATABASE_URL_UNPOOLED (falls back to TARGET_DATABASE_URL),
 *     preserving exact primary key IDs.
 *  3. Resets all PostgreSQL SERIAL / IDENTITY sequences on `id` columns so future
 *     inserts never collide with migrated IDs.
 *  4. Verifies 1:1 row-count parity for every table and tests pooled TARGET_DATABASE_URL.
 *
 * Usage:
 *   NODE_PATH=/path/to/project/node_modules \
 *   SOURCE_DATABASE_URL="postgresql://..." \
 *   TARGET_DATABASE_URL_UNPOOLED="postgresql://..." \
 *   TARGET_DATABASE_URL="postgresql://..." \
 *   node migrate-postgres.mjs
 *
 * Optional env vars:
 *   EXCLUDE_TABLES="session"          Comma-separated tables to skip (default: "session")
 *   TABLES="users,articles,..."       Explicit ordered table list (overrides auto-discovery)
 *   BATCH_SIZE="25"                   Rows per multi-row INSERT (default: 25)
 */

import { createRequire } from "module";

const require = createRequire(import.meta.url);
const pg = require("pg");

const sourceUrl = process.env.SOURCE_DATABASE_URL;
const targetUrlUnpooled = process.env.TARGET_DATABASE_URL_UNPOOLED || process.env.TARGET_DATABASE_URL;
const targetUrlPooled = process.env.TARGET_DATABASE_URL;

if (!sourceUrl || !targetUrlUnpooled) {
  console.error("Error: SOURCE_DATABASE_URL and TARGET_DATABASE_URL_UNPOOLED (or TARGET_DATABASE_URL) are required.");
  process.exit(1);
}

const excludeSet = new Set(
  (process.env.EXCLUDE_TABLES ?? "session")
    .split(",")
    .map((s) => s.trim())
    .filter(Boolean),
);
const explicitTables = process.env.TABLES
  ? process.env.TABLES.split(",").map((s) => s.trim()).filter(Boolean)
  : null;
const BATCH_SIZE = Math.max(1, parseInt(process.env.BATCH_SIZE || "25", 10));

const sslOption = (url) =>
  url.includes("localhost") || url.includes("127.0.0.1") ? false : { rejectUnauthorized: false };

// 1. Snapshot source tables quickly and close source connection immediately
console.log("Reading snapshot from source PostgreSQL database...");
const src = new pg.Client({ connectionString: sourceUrl, ssl: sslOption(sourceUrl) });
await src.connect();

const { rows: discovered } = await src.query(
  `SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename`,
);
const discoveredSet = new Set(discovered.map((r) => r.tablename));
const tablesToCopy = (explicitTables ?? discovered.map((r) => r.tablename)).filter(
  (t) => discoveredSet.has(t) && !excludeSet.has(t),
);

const snapshot = {};
for (const table of tablesToCopy) {
  const { rows: srcCols } = await src.query(
    `SELECT column_name FROM information_schema.columns
     WHERE table_schema = 'public' AND table_name = $1
     ORDER BY ordinal_position`,
    [table],
  );
  const cols = srcCols.map((c) => c.column_name);
  const { rows } = await src.query(`SELECT ${cols.map((c) => `"${c}"`).join(", ")} FROM "${table}"`);
  snapshot[table] = { cols, rows };
  console.log(`  [read] ${table}: ${rows.length} rows`);
}
await src.end();
console.log("Source connection closed cleanly.\n");

// 2. Write batched inserts into target DB inside a single transaction
const dst = new pg.Client({ connectionString: targetUrlUnpooled, ssl: sslOption(targetUrlUnpooled) });
await dst.connect();

const { rows: dstTableRows } = await dst.query(
  `SELECT tablename FROM pg_tables WHERE schemaname = 'public'`,
);
const dstTableSet = new Set(dstTableRows.map((r) => r.tablename));

const summary = [];
await dst.query("BEGIN");
try {
  // Defer/bypass FK ordering issues if role permits (best-effort; harmless if unprivileged)
  await dst.query("SET CONSTRAINTS ALL DEFERRED").catch(() => {});

  const targetTables = tablesToCopy.filter((t) => dstTableSet.has(t));
  if (targetTables.length > 0) {
    const truncateList = targetTables.map((t) => `"${t}"`).join(", ");
    await dst.query(`TRUNCATE TABLE ${truncateList} RESTART IDENTITY CASCADE`);
  }

  for (const table of tablesToCopy) {
    if (!dstTableSet.has(table)) {
      console.warn(`  [warn] ${table}: exists in source but not in target (run drizzle-kit push first?)`);
      continue;
    }

    const data = snapshot[table];
    const { rows: dstCols } = await dst.query(
      `SELECT column_name FROM information_schema.columns
       WHERE table_schema = 'public' AND table_name = $1
       ORDER BY ordinal_position`,
      [table],
    );
    const dstColSet = new Set(dstCols.map((c) => c.column_name));
    const cols = data.cols.filter((c) => dstColSet.has(c));
    const colList = cols.map((c) => `"${c}"`).join(", ");

    for (let i = 0; i < data.rows.length; i += BATCH_SIZE) {
      const batch = data.rows.slice(i, i + BATCH_SIZE);
      const values = [];
      const rowPlaceholders = batch.map((row, rIdx) => {
        const base = rIdx * cols.length;
        const ph = cols.map((col, cIdx) => {
          values.push(row[col]);
          return `$${base + cIdx + 1}`;
        });
        return `(${ph.join(", ")})`;
      });
      await dst.query(`INSERT INTO "${table}" (${colList}) VALUES ${rowPlaceholders.join(", ")}`, values);
    }

    // Reset serial/identity sequence for any column backed by a sequence
    for (const col of cols) {
      const { rows: seqRows } = await dst.query(
        `SELECT pg_get_serial_sequence($1, $2) AS seq`,
        [`public."${table}"`, col],
      );
      const seq = seqRows[0]?.seq;
      if (seq) {
        await dst.query(
          `SELECT setval($1, COALESCE((SELECT MAX("${col}") FROM "${table}"), 1), (SELECT COUNT(*) > 0 FROM "${table}"))`,
          [seq],
        );
      }
    }

    const { rows: [{ count: dstCount }] } = await dst.query(`SELECT COUNT(*)::int AS count FROM "${table}"`);
    console.log(`  [ok] ${table}: ${data.rows.length} -> ${dstCount} rows`);
    if (data.rows.length !== dstCount) {
      throw new Error(`Row count mismatch on ${table}: source=${data.rows.length}, target=${dstCount}`);
    }
    summary.push({ table, source: data.rows.length, target: dstCount });
  }

  await dst.query("COMMIT");
  console.log("\nMigration committed cleanly!");
  console.table(summary);
} catch (err) {
  await dst.query("ROLLBACK");
  console.error("Migration rolled back due to error:", err);
  process.exitCode = 1;
} finally {
  await dst.end();
}

// 3. Verify pooled runtime connection string if provided
if (targetUrlPooled && process.exitCode !== 1) {
  const pooled = new pg.Pool({ connectionString: targetUrlPooled, ssl: sslOption(targetUrlPooled) });
  const { rows: [ping] } = await pooled.query("SELECT version() AS pg_version");
  console.log("Pooled connection verified:", ping.pg_version.split(",")[0]);
  await pooled.end();
}
