# PayTrack — Payroll & Attendance Management System

A connected DBMS capstone implementation for a mid-sized IT firm. It demonstrates data modeling, 3NF normalization, PostgreSQL DDL, SQL functions/procedures/triggers, sample data, reports, index-based query optimization, transactions, role-based access control, and a Flask web interface.

## 1. Technology

- **Database:** PostgreSQL 14+
- **Database programming:** SQL and PL/pgSQL
- **Backend:** Python 3.10+ and Flask
- **Database driver:** Psycopg 3
- **Authentication:** Werkzeug password hashing and Flask signed sessions
- **Web security:** CSRF token validation on state-changing forms; HttpOnly and SameSite=Lax session cookies
- **Testing:** pytest + PostgreSQL integration tests

The database schema is the single source of truth. Flask calls the SQL objects created in the Phase 1–4 scripts; this is not a collection of disconnected phase-specific programs.

## 2. Features

### HR/Admin
- Create employees, edit basic profile details, and activate/deactivate employee access with linked login accounts.
- View the employee directory.
- Record attendance.
- Create, review and approve/reject leave requests.
- Create effective-dated salary revisions without overwriting salary history.
- Generate a monthly payroll run using one stored procedure and one database transaction; the procedure verifies the processor ID against the authenticated HR/Admin session.
- View employee payslips and run attendance / late-marks reports.

### Employee
- Read-only access to their own profile, attendance, leave history and payslips.
- No permission to create or edit leave, attendance, salary, payroll or another employee's records.

### Database rules
- Usernames are unique regardless of letter case.
- One attendance row per employee per date.
- Attendance is rejected before the employee hire date, on weekends, company holidays and approved leave days.
- Leave requests cannot start before the employee hire date.
- Approved leave periods cannot overlap for the same employee.
- A leave reviewer must be an active HR/Admin account.
- Salary effective periods cannot overlap.
- Negative salary components and invalid attendance times are rejected by constraints.
- Payroll entries retain salary-component snapshots, so later salary revisions do not change historical payslips.
- Row-level security scopes employee queries to the authenticated employee ID. The database login is backend-only; do not distribute it to users.
- All state-changing browser forms include a session-bound CSRF token.

## 3. Payroll assumptions

This is a teaching model, not a statutory payroll or tax product. The rules are deliberately simple and documented so the DBMS logic can be verified.

1. Working days are Monday–Friday, excluding rows in `company_holiday`.
2. Gross monthly salary = Basic + HRA + Special Allowance + Other Allowance.
3. Unpaid days = recorded ABSENT days + 0.5 per HALF_DAY + approved unpaid leave weekdays + scheduled weekdays with no attendance and no approved leave.
4. For a mid-month hire, monthly salary components are prorated by the employee's scheduled weekdays divided by the month's total scheduled weekdays. Pre-hire dates are excluded from attendance and leave calculations.
5. Attendance deduction = Prorated Gross Salary / Employee Working Days × Unpaid Days.
6. PF and monthly tax are calculated from the full-month salary components, then prorated by the same active-month factor.
7. Net salary = Gross − Attendance Deduction − PF − Tax; it is floored at zero.
8. A salary structure must cover the entire payroll month. Salary revisions should start on the first day of a month. Future hires are excluded from earlier payroll runs; mid-month hires are prorated.
9. The sample 2026 tax brackets are invented academic values. They do **not** represent Indian statutory income-tax slabs, rebates, exemptions or filing advice.
10. Late marks use a sample company start time of 09:30.

## 4. Database setup

Use a dedicated local database. The schema script drops and recreates only the `payroll` schema, so do not run it against a database containing unrelated work.

### Option A — pgAdmin

1. Install PostgreSQL and open pgAdmin.
2. Create a database named `payroll_db`.
3. Connect to `payroll_db` as a PostgreSQL superuser (usually `postgres`).
4. Open Query Tool and execute these files **in order**:
   - `database/01_schema.sql`
   - `database/02_functions.sql`
   - `database/03_procedures.sql`
   - `database/04_triggers.sql`
   - `database/05_seed_data.sql`
5. Confirm that the seed script reports 12 employees and attendance dates from August through October 2026.

### Option B — Windows PowerShell / psql

Open PowerShell in the project root. Make sure PostgreSQL's `bin` folder is on PATH. If `payroll_db` already exists, do not run `createdb` again; execute only the SQL file commands below, or use `scripts/setup_db.ps1`, which checks for the database first.

```powershell
createdb -U postgres payroll_db
psql -U postgres -d payroll_db -v ON_ERROR_STOP=1 -f database/01_schema.sql
psql -U postgres -d payroll_db -v ON_ERROR_STOP=1 -f database/02_functions.sql
psql -U postgres -d payroll_db -v ON_ERROR_STOP=1 -f database/03_procedures.sql
psql -U postgres -d payroll_db -v ON_ERROR_STOP=1 -f database/04_triggers.sql
psql -U postgres -d payroll_db -v ON_ERROR_STOP=1 -f database/05_seed_data.sql
```

The schema script creates `payroll_owner` and `payroll_app` if they do not exist. A newly created `payroll_app` receives the local demo password `dev_only_change_me`; an existing password is preserved on later schema rebuilds. Change the password with `ALTER ROLE payroll_app WITH PASSWORD 'your-new-password';` and update `.env` before any non-demo use.

### Phase 3 — Query plan evidence

Run `database/09_performance_benchmark.sql` once after seeding and **before** `database/07_indexes.sql`. It inserts synthetic historical attendance records, captures an `EXPLAIN (ANALYZE, BUFFERS)` plan for the full monthly attendance summary query (Report 1), creates the date-leading index, and captures the identical full report query again. Save both outputs in `docs/query_plan_before.txt` and `docs/query_plan_after.txt` (or screenshots). The planner may choose a sequential scan for a small table; use the benchmark rows and report what PostgreSQL actually chooses. Never invent an optimization result.

Then execute `database/07_indexes.sql` for the remaining reporting indexes. `database/06_reports.sql` contains the three required report queries; run it after the appropriate payroll run has been generated. `database/08_transaction_demo.sql` demonstrates ROLLBACK without keeping the temporary salary change.

## 5. Static package verification

After installing the Python requirements, run the repository's static checks from the project root:

```powershell
py scripts/verify_package.py
```

This checks Python syntax, Jinja templates, template route references, CSRF tokens on POST forms, schema/table counts, seed-data coverage declarations and ERD relationship source files. It does not replace PostgreSQL integration tests.

## 6. Python application setup

Use Python 3.10 or later. In PowerShell, from the project root:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Edit `.env` and set a strong random Flask secret and the database password:

```dotenv
FLASK_SECRET_KEY=replace-with-a-long-random-secret
DATABASE_URL=postgresql://payroll_app:dev_only_change_me@localhost:5432/payroll_db
FLASK_DEBUG=1
FLASK_COOKIE_SECURE=0  # Use 1 when serving over HTTPS
```

If the PostgreSQL password contains reserved URL characters, URL-encode it.

Start the app:

```powershell
python run.py
```

Open <http://127.0.0.1:5000>.

## 7. Windows helper scripts

From PowerShell opened in the project root. If script execution is blocked for this terminal, first run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`.

```powershell
# First-time Python environment setup
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt

# Create/rebuild the payroll schema and load sample data (requires PostgreSQL tools on PATH)
.\scripts\setup_db.ps1

# After creating/editing .env, launch Flask using the venv interpreter explicitly
.\scripts\run_windows.ps1
```

The database helper detects an existing `payroll_db` and does not try to create it twice. It then runs the schema script, which drops and recreates the `payroll` schema inside that dedicated database. Do not use it if that schema contains data you need to keep. The app helper uses `.venv\Scripts\python.exe` directly so it cannot accidentally launch with a different global Python interpreter.

## 8. Demo accounts

| Role | Username | Password |
|---|---|---|
| HR/Admin | `admin` | `Admin@123` |
| Employee | `e1001` | `Employee@123` |

All seeded employee accounts use the same demonstration password. These accounts are only for a local academic demo. Change or remove them before any deployment.

## 9. Suggested demonstration sequence

1. Sign in as `admin` and show the HR dashboard and 12 employees.
2. Open Attendance and show a normal record; then try a duplicate date or approved-leave date to show a database rejection.
3. Open Leave and approve/reject a pending request.
4. Open Salary and show the salary history for E1001, including the September 2026 revision.
5. Generate payroll for August, September and October 2026 (each month only once).
6. Open the October payroll run and show payslip components and net salary.
7. Run the monthly attendance report and late-marks report for October 2026.
8. Sign out and sign in as `e1001`; show the employee dashboard, own leave history and payslip.
9. Attempt to open a different employee's data by changing an ID in a request or URL; the app should not expose it. The payslip route is scoped by the signed-in employee ID and database row-level security.
10. Show the transaction ROLLBACK example and retain the SQL output.

**Important:** Payroll generation is one-time per year/month. The stored procedure also requires the processor ID to match the authenticated HR/Admin session context. If you already processed a month, the procedure intentionally rejects a second run. For a fresh demonstration, restore the database from the scripts or create a clean `payroll_db` database.

## 10. Testing

The integration tests use two database connections:

- `TEST_DATABASE_URL`: a database owner/superuser URL for testing constraints and stored procedure rollback.
- `TEST_APP_DATABASE_URL`: the `payroll_app` URL for row-level-security tests.

Set them in PowerShell (use your actual local credentials):

```powershell
$env:TEST_DATABASE_URL="postgresql://postgres:YOUR_PASSWORD@localhost:5432/payroll_db"
$env:TEST_APP_DATABASE_URL="postgresql://payroll_app:dev_only_change_me@localhost:5432/payroll_db"
py -m pytest -q
```

Tests requiring a database URL are skipped when it is not configured. PostgreSQL integration cases cover seed data, duplicate/pre-hire attendance/leave, weekend/holiday attendance, attendance/leave conflicts, overlapping approved leave, active-HR reviewer validation, overlapping salary periods, negative salary, progressive tax calculation, successful and repeated payroll calls, rollback on missing tax configuration, role denial, employee read-only row-level security, successful/repeated payroll processing and mid-month hire proration. Web-security tests cover CSRF token rendering/rejection and session-cookie flags; they require the Python dependencies (including Flask and Psycopg) but do not need a running PostgreSQL server. The payroll route also rejects a missing period server-side rather than silently defaulting a missing form value to October 2026.

## 11. Project structure

```text
payroll-attendance-system/
├── app/
│   ├── __init__.py
│   ├── static/style.css
│   └── templates/
├── database/
│   ├── 01_schema.sql
│   ├── 02_functions.sql
│   ├── 03_procedures.sql
│   ├── 04_triggers.sql
│   ├── 05_seed_data.sql
│   ├── 06_reports.sql
│   ├── 07_indexes.sql
│   ├── 08_transaction_demo.sql
│   └── 09_performance_benchmark.sql
├── docs/
│   ├── ERD.svg
│   ├── ERD.mmd
│   ├── data_dictionary.md
│   ├── normalization.md
│   ├── project_report.md
│   └── test_plan.md
├── tests/
├── .env.example
├── requirements.txt
├── run.py
└── README.md
```

## 12. Known limitations and future improvements

- This implementation is designed for a local academic demonstration, not production deployment.
- Payroll tax and PF rules are simplified; production payroll requires current statutory rules, approvals, audit controls and legal review.
- The model assumes a Monday–Friday workweek and does not yet include shifts, overtime, comp-off, multiple locations or configurable work calendars.
- Salary revisions are month-boundary effective. Mid-month hires are prorated, but mid-month termination/separation proration is not implemented because the schema does not currently store an effective end-of-employment date.
- The benchmark data is synthetic and must be labelled as such in the report.
- Production hardening would require secure secret management, HTTPS, password reset/rotation, audit logging, backups, migrations, rate limiting and stronger database-role separation.

## 13. Capstone mapping

| Phase | Marks | Main files / evidence |
|---|---:|---|
| 1. Data modeling & schema | 20 | `docs/ERD.svg`, `docs/normalization.md`, `docs/data_dictionary.md`, `database/01_schema.sql` |
| 2. Procedural implementation | 20 | `database/02_functions.sql`, `03_procedures.sql`, `04_triggers.sql`, `05_seed_data.sql` |
| 3. Query & report development | 20 | `database/06_reports.sql`, `07_indexes.sql`, `09_performance_benchmark.sql`, captured query plans |
| 4. Security, access control & testing | 20 | RLS policies in schema, role checks in Flask, `08_transaction_demo.sql`, `tests/` |
| 5. Integration, UI & presentation | 20 | `app/`, `run.py`, README, screenshots, project report and live demo |
