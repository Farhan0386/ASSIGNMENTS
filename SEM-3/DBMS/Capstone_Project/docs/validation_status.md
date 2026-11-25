# Implementation and recheck status

## Rubric coverage

- **Phase 1 (20):** 12-table PostgreSQL schema; PK/FK, unique and check constraints; ER diagram; data dictionary; 1NF/2NF/3NF explanation; DDL.
- **Phase 2 (20):** progressive annual-tax and monthly-salary functions; monthly payroll procedure; triggers for leave overlap, attendance/leave conflict, weekends, holidays, pre-hire dates, salary-period overlap and tax-band overlap; deterministic sample data for 12 employees across August–October 2026.
- **Phase 3 (20):** monthly attendance, payslip and late-marks reports; HR navigation for all reports; reporting indexes for date, leave, salary and payroll queries; before/after benchmark script for the full Report 1 monthly attendance query.
- **Phase 4 (20):** HR/Admin full access and strictly read-only Employee access to own records; PostgreSQL RLS; CSRF protection; password hashing; HttpOnly/SameSite cookies; payroll and salary-revision transactions; SQL integration tests and test plan.
- **Phase 5 (20):** one Flask application over the same PostgreSQL backend; HR/Admin can create/edit employees, activate/deactivate access, record attendance, create/review leave, revise salary, generate payroll and view reports; Employees can view only their own records; README, report and presentation outline.

## Checks performed in this authoring environment

- The original ZIP was inspected and the rechecked archive is rebuilt from the audited project directory.
- A repeatable `scripts/verify_package.py` static audit was added and executed successfully.
- The SQL schema now enforces case-insensitive username uniqueness to match the login lookup.
- Payroll generation now verifies that `p_processed_by` matches the authenticated `app.user_id` session value; integration tests cover mismatched identity.
- A database test now covers case-insensitive username uniqueness.
- Payroll procedure and salary function reject NULL year/month inputs explicitly.
- The rendered ERD PNG/SVG were regenerated from `docs/erd.dot`; all three editable/rendered diagram sources include Employee → Payroll Entry, Payroll Run → Payroll Entry and Salary Structure → Payroll Entry.
- Python source files pass AST parsing and `python -m compileall` (6 source files).
- Static audit reports: 12 Jinja templates parsed; 15 template URL references resolved; 11 POST forms each contain exactly one CSRF token; 12 DDL tables and 12 seed employee records verified.
- All 12 Jinja templates parse successfully.
- All 11 POST forms each contain exactly one hidden CSRF token.
- The DDL contains 12 `CREATE TABLE` statements and 18 row-level-security policies.
- Four validation triggers are declared.
- Seed SQL defines 12 employee records and generates attendance from 1 August to 31 October 2026, excluding weekends, configured holidays and leave intervals.
- Template `url_for` references were checked against Flask view-function names.
- Demo password hashes were previously independently recomputed and matched the documented passwords (`Admin@123` and `Employee@123`).
- RLS test expectations were corrected: PostgreSQL's `UPDATE` policy filters unauthorized rows (zero affected rows) rather than necessarily raising an exception.
- HR/Admin profile editing was added; Employee edit attempts remain blocked by route authorization and database RLS.
- The late-marks report is linked in HR navigation; HR/Admin sessions set an empty employee-ID database context rather than the literal string `None`.
- The payroll-app password is no longer reset on every schema rebuild.
- Payroll report indexes now include both `run_id`-leading payslip retrieval and `employee_id`-leading employee history.
- The HR employee edit query preserves the existing phone field when saving other profile edits.
- The transaction demo now shows explicit COMMIT and ROLLBACK on a temporary table plus a real salary-row rollback.

## Checks not executable here

This environment does not contain a PostgreSQL server/client (`postgres`/`psql`), Flask or Psycopg. As a result, SQL scripts and the PostgreSQL integration/web test suite have **not** been executed against a live database here. The standalone static audit itself was executed successfully; it is not a substitute for runtime execution. Actual report result sets, COMMIT/ROLLBACK console output, before/after `EXPLAIN (ANALYZE, BUFFERS)` plans, and running-application screenshots remain to be generated on the target machine. No test results, screenshots or performance improvements have been fabricated.

## Required final verification on the target machine

1. Install PostgreSQL and Python dependencies from `requirements.txt`.
2. Follow the database setup order in `README.md`; confirm the seed output shows 12 employees and three months of attendance.
3. Run `database/09_performance_benchmark.sql` before `database/07_indexes.sql`; save both actual plans and describe the observed result.
4. Run `database/06_reports.sql` after generating a payroll run for the report period.
5. Configure `TEST_DATABASE_URL` and `TEST_APP_DATABASE_URL`; run `py -m pytest -q` and retain the real output.
6. Test both roles in the browser, including HR/Admin employee editing and leave review, Employee own-record viewing, and unauthorized-access denial.
7. Save genuine application/database screenshots and query/test traces under `docs/screenshots/` before submission.
