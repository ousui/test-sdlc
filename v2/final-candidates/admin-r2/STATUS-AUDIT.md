# Status audit and optional operation keys

Authenticated enabled management users can use `/admin/users/status/` with the existing `ids` and boolean `enabled`. Optional `operation_key` accepts 1–128 ASCII letters, digits, dots, underscores, colons or hyphens. Every successful request returns the unchanged R1 JSON and an `X-Operation-ID` header. An unkeyed call always creates a distinct operation, including a no-op.

Same-key retries by the same stable account and normalized request return the original receipt. Later operations, deleted targets and reused target IDs do not cause the old action to execute again. Changed payloads or another account receive opaque `409 operation_conflict`. Form pages generate fresh keys and preserve CSRF and paging filters.

SQLite `BEGIN IMMEDIATE` serializes writers. After acquiring the lock the request rechecks the live login marker. Status, revocation marker, receipt and target snapshots commit together. Storage failure rolls back everything with `503 storage_failure`; retrying the key can then succeed.

Audit HTML and JSON are at `/admin/users/audit/` and `/admin/users/audit/data/`. Exact `actor_id` and `target_id` filters combine with stable ascending operation order and matching totals. Snapshot names survive deletion and HTML escapes them. Audit rows never contain authentication markers, password hashes, cookies or token values.

Migration adds stable random user `audit_identity` values without rotating existing login identifiers. This identity is internal and survives renaming and login revocation. Historical receipts without trustworthy stable ownership remain queryable but replay fails closed; migration never associates them with a possibly reused numeric account ID. Use a new key for a new request.

Run the preserved original and FINAL modules with the existing Python 3.11 environment: `python -B -m unittest -v test_enabled test_final_r0 test_bulk_status test_final_r1 test_status_audit test_sqlite_probe test_final_r2`. This is local Flask HTTP/SQLite validation with synthetic fixture data.
