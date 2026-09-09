# Batch account status

Open `/admin/users/bulk/` after signing in. The JSON list at `/admin/users/data/` shares `enabled=all|true|false`, literal username substring `q`, and `page` / `per_page` (1..100) with the HTML page. IDs sort ascending; total is calculated after filtering.

POST `/admin/users/status/` accepts JSON `{"ids":[2,3],"enabled":false}` and a valid `X-CSRFToken` header, or the page form. IDs are deduplicated; 1..100 positive integer entries are required. Unknown IDs return404 and invalid input400 before any writes. Including the signed-in actor returns409 for the whole batch. Success reports requested unique targets and actual changes. Repeating the same state returns changed0 and retains the same revocation marker.

Disabling rotates the existing Flask-Login alternative ID. Re-enabling never revives old cookies. The local example continues to give all enabled signed-in accounts management access; it has no production role model. No audit/idempotency-key API is included in R1.

Run original `python -B -m unittest test_enabled -v` and new `python -B -m unittest test_bulk_status -v` in the isolated Q0 environment. Tests create isolated SQLite files and synthetic accounts; no real credentials are needed.

Username matching uses Unicode casefold on each SQLite connection, including after restart. Form IDs use the same signed64-bit positive range as JSON.
