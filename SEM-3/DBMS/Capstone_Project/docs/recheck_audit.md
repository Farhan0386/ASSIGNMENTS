# Independent Package Recheck

**Recheck date:** 18 November 2026  
**Artifact reviewed:** `Payroll_Attendance_Capstone.zip` and its extracted project tree  
**Scope:** Rubric coverage, source/package integrity, static Python/Jinja checks, SQL/schema consistency, sample data declarations, forms/route references, documentation and release contents.

## Result

The package covers all five rubric phases at the source/design level. Static verification passes. The project is not yet entitled to a claim of fully runtime-verified completion because this authoring environment does not contain PostgreSQL, `psql`, Flask or Psycopg. Live SQL execution, real test output, real query plans and running-browser screenshots must be collected on the target machine.

## Rubric cross-check

| Phase | Required work | Present in package | Runtime evidence still required |
|---|---|---|---|
| 1 — Data modeling (20) | Entities, relationships/cardinalities, normalization to 3NF, final relational schema, PK/FK constraints, DDL | ERD in PNG/SVG/Mermaid/DOT, normalization explanation, data dictionary, 12-table DDL | Execute schema on a clean PostgreSQL database and preserve output |
| 2 — Procedural implementation (20) | Salary/tax functions, payroll procedure, validation triggers, at least 10 employees and 3 months of data | PL/pgSQL functions/procedure, triggers, 12 employee seed rows, Aug–Oct 2026 attendance generator | Execute scripts; demonstrate valid and rejected writes; generate payroll |
| 3 — Query/report (20) | Attendance summary, payslip, late marks, indexes, before/after execution plan | Three SQL reports, Flask report pages, indexes, full-query benchmark script | Save actual report results and `EXPLAIN (ANALYZE, BUFFERS)` before/after output |
| 4 — Security/testing (20) | HR/Admin vs read-only employee scope, transaction COMMIT/ROLLBACK, valid/invalid/boundary testing | Flask role checks, PostgreSQL RLS, CSRF, password hashes, transactional procedure/revision route, SQL demo, integration tests and test plan | Run database/web tests and capture real role-denial and transaction traces |
| 5 — Integration/demo (20) | One connected application, role-specific UI, source, README, screenshots/traces and short report | One Flask application over the same PostgreSQL schema; HR/Admin and Employee views; README, report and slide outline | Run it locally, capture real app screenshots/output traces, and present the live workflow |

## Static checks executed

The following checks completed successfully in this environment:

- Python AST parsing and `compileall`: 6 Python source files.
- Jinja parsing: 12 HTML templates.
- Template route references: 15 references, no unresolved endpoints.
- CSRF form scan: 11 POST forms, each containing exactly one CSRF token.
- Schema declarations: 12 `CREATE TABLE` statements and 18 row-level-security policies.
- Seed declarations: 12 employee records and attendance generation from 1 August through 31 October 2026.
- ERD source consistency: Employee → Payroll Entry, Payroll Run → Payroll Entry and Salary Structure → Payroll Entry are represented in editable sources; PNG and SVG regenerated from the DOT source.
- Demo password hashes: both documented password/hash pairs independently recomputed and matched.
- `scripts/verify_package.py`: PASS.

## Final corrections included in this recheck

1. Added a case-insensitive unique index for account usernames, matching the login lookup behavior.
2. Bound payroll `processed_by` to the authenticated session's `app.user_id` and added a test for mismatched processor identity.
3. Added explicit NULL validation for payroll year/month parameters.
4. Added a repeatable static verification script and updated README instructions.
5. Updated the test plan, data dictionary, normalization note, project report and validation status.
6. Regenerated ERD PNG/SVG from the editable Graphviz source.
7. Removed generated Python `__pycache__` folders from the release tree.

## Outstanding before submission

These items cannot be generated honestly without running the application and PostgreSQL locally:

- successful clean-database execution of SQL files 01–05;
- execution of the Phase 2 functions, payroll procedure and trigger rejection cases;
- actual output of all three reports;
- actual before/after query plans and performance interpretation;
- actual COMMIT/ROLLBACK traces;
- successful `pytest` output with both database URLs configured;
- screenshots from the running HR/Admin and Employee interfaces;
- a demonstrated unauthorized access denial.

Use `docs/submission_checklist.md` and `README.md` to capture these. Do not mark runtime-only evidence complete until it has been observed on the target machine.
