# Local account availability

The original teaching example lets each enabled authenticated user manage accounts. This increment does not introduce roles.
The user form edits Enabled and the user list filters it. Disabling rotates the alternative session identifier once; re-enabling does not restore an old cookie.
SQLite initialization adds a missing enabled column without deleting rows; repeat initialization preserves existing data.

Use Python 3.11 with requirements.lock in an isolated virtual environment. Run `python -B -m unittest test_enabled -v` for the original 13 actual HTTP/SQLite tests.
For local interactive use provide ADMIN_DEMO_SECRET outside the source and optionally ADMIN_DEMO_DATABASE_URI pointing to a disposable SQLite path, then run `python main.py`. No built-in accounts or destructive seeding are provided. The server binds only 127.0.0.1 and runs without debug.
This deliverable is a local example package, not production deployment.
