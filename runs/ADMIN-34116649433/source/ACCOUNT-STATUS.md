# Account availability

This local teaching example retains the upstream enabled-authenticated-manager model.
Set ADMIN_DEMO_SECRET outside source and use an isolated SQLite database.
The account view edits and filters Enabled. Disabling rotates the alternative identity;
re-enabling does not restore old cookies. Migration is additive and idempotent.
Run `python -m unittest test_enabled -v`: thirteen real request/SQLite tests.
RLS validates only the current local Sandbox release contract, not production deployment.
