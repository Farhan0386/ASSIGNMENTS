# Phase 4 — Test Plan

| ID | Area | Test input/action | Expected result |
|---|---|---|---|
| T01 | Seed data | Count employees and attendance date range | At least 10 employees; attendance covers at least 3 months |
| T02 | Attendance | Insert a second record for the same employee/date | Unique constraint rejects the row |
| T03 | Attendance | Insert attendance on Saturday/Sunday | Trigger rejects the row |
| T04 | Attendance | Insert attendance on a configured company holiday | Trigger rejects the row |
| T04a | Attendance/leave | Insert attendance or leave before the employee hire date | Trigger rejects the row |
| T05 | Leave | Approve a leave interval overlapping an existing approved interval | Trigger rejects approval |
| T06 | Leave | Approve leave where attendance records already exist | Trigger rejects approval |
| T07 | Attendance/leave | Insert attendance during approved leave | Trigger rejects attendance |
| T08 | Leave reviewer | Approve/reject as a non-HR account | Trigger rejects reviewer |
| T09 | Salary | Insert a negative basic salary | CHECK constraint rejects row |
| T10 | Salary | Insert overlapping effective salary period | Trigger rejects row |
| T11 | Salary history | Change salary effective from a later month | Prior structure is closed; new structure starts; old payslips unchanged |
| T12 | Tax | Calculate tax at ₹600,000 annual income with sample bands | ₹15,000 annual tax |
| T13 | Payroll | Generate an unprocessed month with valid data | One processed run and one entry per active employee |
| T14 | Payroll | Generate the same processed month again | Procedure rejects duplicate processing |
| T15 | Transaction | Force a payroll failure due to missing tax-year brackets | Payroll run and entries roll back together |
| T16 | RBAC | Employee queries employee master records | Only own employee row is visible under RLS |
| T17 | RBAC | Employee opens a different employee's payslip | No rows / 404; no disclosure |
| T18 | RBAC | Employee attempts to insert a leave request | Denied; Employee role is read-only |
| T19 | RBAC | Employee attempts HR-only attendance/salary/payroll routes | HTTP 403 |
| T20 | Reports | Run three report queries for October 2026 | Attendance summary, salary slips and late marks return consistent data |
| T21 | Optimization | Compare same attendance query before/after date index | Save actual EXPLAIN ANALYZE plans and explain observed difference |
| T22 | Login | Wrong password or inactive account | Login denied |
| T23 | Payroll boundary | Hire an employee mid-month and calculate payroll | Pre-hire dates are excluded and salary components are prorated |
| T24 | RBAC | HR/Admin updates an employee profile | Profile fields update in one transaction; employee code and hire date remain unchanged |
| T25 | RBAC | Employee attempts to update their own employee row | RLS filters the update; zero rows are changed |
| T26 | Web security | Submit a state-changing form without a valid CSRF token | Request is rejected with HTTP 400 |
| T27 | RBAC | HR/Admin creates a pending leave request | Accepted; request appears in the review queue |
| T28 | Payroll | Submit payroll form without a selected month | Request rejected; no default period is processed |
| T29 | Payroll security | Pass a different HR/Admin user ID than the authenticated session | Procedure rejects the mismatched processor identity; no payroll run is created |
| T30 | Login | Insert a username differing only by letter case from an existing username | Case-insensitive unique index rejects the duplicate |

## Evidence to capture

- ER diagram and Phase 1 schema creation output.
- Function and procedure definitions plus successful sample calls.
- Screenshots of trigger/constraint rejections.
- Seed-data query showing 12 employees and attendance coverage.
- Three report outputs.
- Before/after `EXPLAIN (ANALYZE, BUFFERS)` text output.
- COMMIT and ROLLBACK output.
- HR/Admin dashboard and employee dashboard screenshots.
- Employee unauthorized-access attempt and denied result.
- Web CSRF token rendering and rejection of a state-changing request without a valid token.
- Session cookie flags (HttpOnly and SameSite=Lax).

Do not mark a test as Passed until it has actually been executed in the target PostgreSQL environment.
