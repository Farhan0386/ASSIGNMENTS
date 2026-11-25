# PayTrack Follow-up Audit — 25 November 2026

## Summary

The current release archive was extracted afresh and reviewed independently. The ZIP contains 48 files (plus directory entries) and passes archive integrity and the included static verifier. This confirms source/package consistency, not live PostgreSQL or Flask operation.

## Checks actually executed in this review

| Check | Result |
|---|---|
| `unzip -t` archive integrity | PASS |
| `python scripts/verify_package.py` | PASS |
| Python AST parsing via verifier | 6 Python files parsed |
| Jinja template parsing | 12 templates parsed |
| Template endpoint references | 15 references resolved against Flask view names |
| CSRF coverage scan | 11 POST forms each contain one CSRF token |
| Schema declaration scan | 12 `CREATE TABLE` declarations |
| Seed-data declaration scan | 12 employee rows; sample attendance range 1 Aug–31 Oct 2026 |
| ERD editable-source checks | Employee → Payroll Entry and payroll/salary links represented |
| Demo password derivation | Both published PBKDF2-SHA256 hashes match their documented demo passwords |

## Improvements made

1. Added `docs/demo_runbook.md`, defining demo-ready acceptance checks and a timed teacher walkthrough.
2. Updated `scripts/setup_db.ps1` to detect an existing `payroll_db` instead of failing at `createdb`. It warns that the schema script will drop/recreate the `payroll` schema.
3. Updated `scripts/run_windows.ps1` to invoke `.venv\Scripts\python.exe` explicitly, avoiding ambiguity about which Python interpreter `py` selects.
4. Updated README commands to use the active environment's `python` and documented the helper scripts and PowerShell execution-policy workaround.
5. Added the demo runbook to `scripts/verify_package.py` required-file checks.

## Runtime blockers in this authoring environment

The review container has Python 3.13 and Jinja2/pytest, but it has no PostgreSQL executables (`psql`, `postgres`, `pg_ctl`) and no Flask, Psycopg or Werkzeug packages. An attempted installation of Flask and Psycopg failed because package-index DNS/network access is unavailable. Therefore these were **not** executed here:

- PostgreSQL DDL/function/procedure/trigger execution;
- seed-data insertion in a live database;
- Flask server startup or login flows;
- PostgreSQL integration tests and RLS behavior;
- actual report outputs or before/after query plans;
- COMMIT/ROLLBACK output from a PostgreSQL session;
- screenshots from a live browser.

No runtime success, screenshots, or optimization gains are claimed. Run those checks on the target Windows laptop using `README.md`, `docs/demo_runbook.md` and `docs/submission_checklist.md`.

## Practical meaning of demo-ready

The application is demo-ready only after it starts locally and an observer can complete the core workflow: HR/Admin login → view/manage employees → attendance/leave → salary → generate one monthly payroll → open a payslip/report → Employee login → view own records → observe denied access to an HR-only or other-employee record. At least one database validation rejection should also be demonstrated.

A fully rubric-evidenced submission additionally needs the actual database tests, three report outputs, query plans, transaction traces, and genuine screenshots/output captures.
