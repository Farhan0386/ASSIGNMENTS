# PayTrack — Payroll & Attendance Management System

## 1. Abstract

PayTrack is a relational database application for managing employee attendance, leave, salary structures and monthly payroll in a mid-sized IT company. The solution combines a normalized PostgreSQL schema with PL/pgSQL functions, a payroll procedure, integrity triggers, SQL reporting queries, indexes, transaction handling and role-based access controls. A Flask web interface provides separate HR/Admin and Employee workflows over the same database.

## 2. Problem statement

A growing organization needs a consistent way to maintain employee master data, record daily attendance, process leave approvals, preserve salary history and generate monthly payslips. Storing these records in unrelated files or scripts can produce duplicate attendance entries, overlapping approved leave, inconsistent salary calculations and unauthorized access to payroll information. The project addresses these problems through a connected DBMS application with declarative constraints, procedural validation and role-restricted access.

## 3. Objectives

1. Design and implement a relational database normalized to at least 3NF.
2. Use primary keys, foreign keys, uniqueness rules and check constraints to protect data quality.
3. Implement salary/tax functions, a monthly payroll procedure and attendance/leave/salary triggers.
4. Populate at least 10 employees with three months of realistic sample attendance.
5. Produce monthly attendance, employee salary-slip and late-marks reports.
6. Demonstrate index-based query-plan analysis.
7. Separate HR/Admin privileges from employee self-service access.
8. Demonstrate transaction COMMIT and ROLLBACK behavior.
9. Integrate the database with a role-based web interface.

## 4. Scope and users

**HR/Admin:** Create and edit employee records and accounts, activate/deactivate employee access, record attendance, create/review leave, create salary revisions, generate monthly payroll and view reports/payslips.

**Employee:** Read-only access to their own profile, attendance, leave history and payslips. Employees cannot create or alter leave, attendance, salary or payroll records and cannot view another employee's records.

The database includes 12 core tables: `department`, `designation`, `employee`, `user_account`, `attendance`, `leave_type`, `leave_request`, `company_holiday`, `salary_structure`, `tax_bracket`, `payroll_run` and `payroll_entry`.

## 5. Architecture

The browser sends requests to Flask. Flask authenticates users, checks roles and uses parameterized SQL through Psycopg. PostgreSQL owns the schema, constraints, functions, procedures, triggers and reporting data. Row-level security uses server-set session context to limit employee queries to their own employee ID.

```text
Browser / HTML-CSS
        |
        v
Flask routes + signed session + role checks
        |
        v
Psycopg parameterized SQL / transaction boundary
        |
        v
PostgreSQL schema + PL/pgSQL + triggers + RLS + indexes
```

## 6. Data model and normalization

The ER diagram is in `ERD.svg` and its editable Mermaid source is `ERD.mmd`. The design separates organizational reference data, employees, authentication, attendance, leave types/requests, salary history, tax bands and payroll runs/results. The model uses single-column surrogate primary keys and meaningful unique candidate keys such as employee code, email, username and employee/date attendance.

The normalization report in `normalization.md` explains 1NF, 2NF and 3NF. In particular, department names, designation names and leave paid/unpaid classification are stored in reference tables instead of being repeated in transactional rows. Salary structures are effective-dated and are not overwritten. Payroll entries store historical salary-component snapshots so old payslips remain stable when an employee's salary changes.

## 7. Database implementation

### Functions

- `fn_calculate_annual_tax(income, year)` applies progressive sample tax bands and verifies that the bands start at zero, are contiguous and have an unbounded final band.
- `fn_calculate_monthly_salary(employee, year, month)` selects a salary structure covering the complete month, calculates working days and unpaid days, then returns gross salary and deductions.
- `fn_get_login_record(username)` provides the login lookup without granting the web application direct read access to password hashes.

### Procedure

`sp_generate_monthly_payroll(year, month, processed_by)` creates one payroll run, calculates every active employee's monthly result, writes payroll snapshots and marks the run processed. It rejects a repeated processed period and verifies that `processed_by` matches the authenticated HR/Admin session ID. The Flask route wraps the call in a database transaction; any exception rolls back the entire run rather than leaving partial payroll entries.

### Triggers

- Approved leave cannot overlap another approved leave for the same employee.
- Approved leave cannot be approved over existing attendance records.
- Attendance is rejected before the employee hire date, on weekends, company holidays and approved leave days.
- Leave requests cannot start before the employee hire date.
- Leave approval/rejection requires an active HR/Admin reviewer.
- Salary effective periods cannot overlap.
- Tax bands cannot overlap.

Table constraints additionally reject duplicate employee/date attendance, negative salary components and invalid time intervals.

## 8. Calculation rules and assumptions

The classroom model counts Monday–Friday as working days and excludes configured company holidays. Gross monthly salary is Basic + HRA + Special Allowance + Other Allowance. Unpaid days equal explicit ABSENT days plus half of HALF_DAY records plus approved unpaid leave weekdays. A scheduled weekday with no attendance row and no approved leave is treated as absent; pending or rejected leave does not excuse an unrecorded day. For a mid-month hire, salary components are prorated by the employee's scheduled weekdays divided by the month's total scheduled weekdays; pre-hire dates do not count as absences. Attendance deduction is prorated gross divided by the employee's scheduled working days multiplied by unpaid days. PF and monthly tax are calculated from full-month components and prorated by the same factor. Net salary is gross minus attendance deduction, PF and tax, floored at zero.

The configured PF rate and tax slabs are sample values. They are not represented as current Indian statutory rates. A production system would need current legal rules, exemptions, caps, audit trails and expert validation.

## 9. Reporting and optimization

The project includes these reports:

1. Monthly attendance summary by employee, including present, work-from-home, absent, half-day, paid/unpaid leave and attendance percentage.
2. Salary slip by employee and payroll period, with component snapshots and deductions.
3. Late-marks report with the sample start time set to 09:30.

Indexes cover attendance date, leave status/date filtering, effective-dated salary lookup, payroll-run payslip retrieval (`run_id` leading) and employee payslip history (`employee_id` leading). `09_performance_benchmark.sql` creates synthetic historical attendance, captures an execution plan for the full monthly attendance summary query (Report 1) before the date-leading index, creates the index, runs ANALYZE and captures the identical full report query again for a comparable month in the synthetic period. The actual EXPLAIN output must be saved with the submission; the report must describe the plan PostgreSQL actually chose.

## 10. Security and transaction design

The application distinguishes `HR_ADMIN` and `EMPLOYEE`. Flask enforces role access at routes, and PostgreSQL row-level security scopes employee records using server-set `app.user_role` and `app.employee_id` settings. The database login is intended to be held only by the backend, never distributed to end users. Database usernames are unique regardless of case, avoiding ambiguous case-insensitive login lookups. Passwords are hashed with Werkzeug, state-changing browser forms are protected by session-bound CSRF tokens, and session cookies use HttpOnly and SameSite=Lax settings. SQL values are passed as parameters rather than interpolated into SQL strings. Advisory transaction locks serialize attendance/leave and salary-period overlap checks for the same employee.

Salary revisions update the previous effective end date and insert a new structure in one transaction. Payroll generation writes the payroll run and all employee rows in one transaction; the stored procedure verifies that the supplied processor ID matches the authenticated session ID before processing. `08_transaction_demo.sql` demonstrates a salary update that is deliberately rolled back; the application salary-revision route demonstrates a committed revision.

## 11. Verification plan

The test suite checks sample-data volume and period coverage, duplicate attendance rejection, pre-hire attendance and leave rejection, weekend and holiday attendance rejection, attendance/approved-leave conflict, overlapping approved leave rejection, negative salary rejection, progressive tax calculation, payroll rollback when tax configuration is missing, role denial for payroll generation, a successful monthly payroll run and repeat-run rejection, authenticated processor-ID matching, case-insensitive username uniqueness, employee read-only row-level-security scope, denial of employee leave insertion and mid-month hire proration. Manual UI validation should also cover login, leave submission/review, salary revision, report filters, payroll generation and employee-versus-admin visibility.

Actual test output and before/after query-plan output should be attached after the package is run in a configured PostgreSQL environment. This report does not invent database execution results.

## 12. Real-world use cases and scaling considerations

In a mid-sized IT company, HR can use the system to onboard an employee, maintain department/designation information, record daily attendance, create and review leave requests, maintain effective-dated salary structures and process monthly payroll. Employees can use their accounts to review only their own attendance, leave history and payslips. The three reports support monthly attendance review, payroll reconciliation and follow-up on late arrivals. The sample database is deterministic and suitable for demonstrating these workflows; it is not production payroll software.

For a larger organization, the logical model can be extended without changing the core separation of employee, attendance, leave, salary and payroll data. Attendance can be partitioned by month or year once row volume warrants it; indexes should be validated against real query plans; historical reports can use read replicas or pre-aggregated reporting tables; and payroll processing can move to a background job queue with idempotent run tracking. Multiple offices would require configurable work calendars, time zones and holiday sets. A multi-company deployment would need tenant/company keys included in the data model and enforced in every relevant foreign key, query and security policy. Production use would also require audit trails, backup/recovery procedures, key management, HTTPS, stronger database-role separation and legally validated payroll/tax rules. These are scaling recommendations, not features claimed as implemented in this academic version.

## 13. Limitations and future work

The current version uses a Monday–Friday calendar, simplified salary/tax/PF calculations and month-boundary salary changes. Mid-month hires are prorated, but mid-month termination/separation proration is not implemented. It also does not yet implement shifts, overtime, multiple legal entities, attendance-device integration, email notifications, audit-log retention or production-grade deployment controls. Future work could add configurable work calendars, statutory payroll modules, audit trails, MFA, password reset, migrations, automated backups, rate limiting and stronger per-role database identities.

## 14. Conclusion

PayTrack integrates the major DBMS lab concepts into one application: a normalized relational model, SQL querying, procedural database logic, constraints and triggers, indexing and query plans, transactions, access control, testing and a user interface. The design prioritizes consistency and protection of historical payroll data while keeping the rules transparent enough to demonstrate and explain in a capstone evaluation.
