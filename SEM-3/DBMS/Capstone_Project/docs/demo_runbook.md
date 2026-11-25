# PayTrack — Teacher Demonstration Runbook

This runbook distinguishes a **demo-ready** application from a **fully rubric-evidenced** submission.

## 1. What “demo-ready” means

Call the application demo-ready only when all of these have been observed on the target laptop:

1. PostgreSQL service is running and the five setup SQL files execute successfully in order.
2. Flask starts without import or connection errors and opens at `http://127.0.0.1:5000`.
3. HR/Admin login succeeds with the local demo account.
4. The HR dashboard shows the seeded employee and record counts.
5. HR/Admin can open the employee directory, attendance, leave, salary, payroll and reports pages.
6. At least one monthly payroll run can be generated and its payslip opens.
7. Employee login succeeds and shows only that employee's records.
8. An employee cannot open an HR-only route or another employee's payslip.
9. At least one database validation rule is demonstrated (for example duplicate attendance or attendance on approved leave is rejected).

A page merely loading is not enough. The key workflows above must work against the same PostgreSQL database.

## 2. What “fully rubric-evidenced” additionally means

For a defensible final submission, also collect real evidence for:

- Phase 1: ERD, 3NF explanation, data dictionary, and successful schema execution output.
- Phase 2: actual function/procedure calls and trigger rejections.
- Phase 3: output of all three reports and before/after `EXPLAIN (ANALYZE, BUFFERS)` for the same report query.
- Phase 4: employee RLS denial, HR/Admin access, COMMIT and ROLLBACK traces, and actual automated test output.
- Phase 5: genuine screenshots of both dashboards and the end-to-end application workflow.

Do not claim a test passed, an index improved performance, or security was demonstrated unless the result has been observed and saved.

## 3. Recommended 7-minute live walkthrough

### Minute 0–1: Introduce the problem

“PayTrack is a PostgreSQL-backed payroll and attendance application for a mid-sized IT company. It combines data modeling, SQL programming, reporting, optimization, transactions and role-based access control in one connected system.”

### Minute 1–2: Show the database structure

Open `docs/ERD.png`. Explain Employee as the central entity and point out Attendance, Leave Request, Salary Structure, Payroll Run and Payroll Entry. Mention that salary history is separated from employee master data and payroll entries retain salary snapshots.

### Minute 2–3: Show HR/Admin workflows

Log in as `admin`. Show the dashboard and employee directory. Open attendance and leave. Demonstrate a valid record or a database rejection such as a duplicate employee/date attendance row.

### Minute 3–4: Show payroll

Open Salary and show the effective-dated salary history. Generate one unprocessed month only. Open its payroll run and a payslip. Explain gross salary, unpaid-day deduction, PF, sample tax and net salary. State that the tax brackets are academic demonstration values, not statutory tax rules.

### Minute 4–5: Show reports and DBMS logic

Open Monthly Attendance and Late Marks. Show the SQL files for the reports and the stored payroll procedure. If the benchmark has been run, show the actual before/after query plans and explain what PostgreSQL chose.

### Minute 5–6: Show employee access restrictions

Log out and sign in as `e1001`. Show own profile, attendance, leave and payslip. Demonstrate a denied HR-only page or a 404 for a different employee's payslip.

### Minute 6–7: Show transaction safety and conclude

Show the saved COMMIT/ROLLBACK output from `database/08_transaction_demo.sql`. Conclude that the same backend supports both roles and that the database enforces integrity rules beyond the web form.

## 4. One-hour priority if time is short

1. Get PostgreSQL schema + seed data installed.
2. Get Flask login and both role dashboards working.
3. Generate a single payroll month and open a payslip.
4. Show the three reports.
5. Demonstrate one trigger rejection and employee access denial.
6. Capture screenshots and save terminal output.

For a fresh demonstration database, generate only one payroll run per month. The procedure intentionally rejects rerunning an already processed month. If Aug–Oct payrolls are already processed, either show an existing payslip or rebuild the dedicated demo database from the included SQL scripts.

## 5. Known evidence limitations before local execution

The ZIP's static verification script can validate source structure, template parsing, route references and CSRF-form coverage. It cannot prove PostgreSQL syntax/runtime behavior, actual Flask database connectivity, live RLS behavior, real query-plan improvements or end-to-end browser behavior. Those require the local PostgreSQL/Python environment.
