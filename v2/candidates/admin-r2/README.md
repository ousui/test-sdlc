# Auth with Flask-Login Example

This example shows how to integrate Flask-Login authentication with Flask-Admin using the SQLAlchemy backend.

## How to run this example

Clone the repository and navigate to this example:

```shell
git clone https://github.com/pallets-eco/flask-admin.git
cd flask-admin/examples/auth-flask-login
```

> This example uses [`uv`](https://docs.astral.sh/uv/) to manage its dependencies and developer environment.

Run the example using `uv`, which will manage the environment and dependencies automatically:

```shell
uv run main.py
```

## Local R2 bulk status audit

The batch page `/admin/users/bulk/` includes a per-render operation key. JSON POST
`/admin/users/status/` accepts optional `operation_key` (1–128 ASCII letters,
digits, dot, underscore, colon or hyphen). Same key and canonical actor/IDs/state
returns the original receipt and `X-Operation-ID`, even after later state changes.
A different payload or actor gets 409. Missing keys preserve legacy response
semantics and create independent operations. Keep a key when retrying after 503.

Only enabled signed-in managers can read `/admin/users/audit/` or its `data/`
JSON endpoint. Filter by exact `actor_id` / `target_id`, with `page` and `per_page`
(1–100). Audit contains UTC timestamps and account snapshots, never credentials.
SQLite state, session revocation and audit commit together. Tables are additive;
restart and repeated setup preserve receipts. This retains the example's existing
simplified management access; it does not add production RBAC.

Run the isolated Python environment with `python -B -m unittest -v`.

Idempotency belongs to a stable per-account audit identity. Additive migration
assigns it once to existing accounts; it is internal, not an authentication token,
and is excluded from management forms. Deleting/recreating an account cannot
inherit old keys, even if SQLite reuses the integer ID. Renaming an account or
revoking and renewing its login does not change its ownership of prior keys.
