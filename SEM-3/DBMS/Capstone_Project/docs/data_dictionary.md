# Phase 1 — Data Dictionary

| Table | Key fields | Purpose / constraints |
|---|---|---|
| `department` | `department_id` PK, `department_name` UNIQUE | Organizational unit master. |
| `designation` | `designation_id` PK, `designation_name` UNIQUE | Job title master. |
| `employee` | `employee_id` PK, `employee_code` UNIQUE, `email` UNIQUE, `department_id` FK, `designation_id` FK | Employee master; status is ACTIVE/INACTIVE. |
| `user_account` | `user_id` PK, `username` UNIQUE (case-insensitive index), `employee_id` UNIQUE FK | Login identity and HR_ADMIN/EMPLOYEE role. Employee role requires an employee link; HR/Admin role requires none. Passwords are stored as salted password hashes. |
| `attendance` | `attendance_id` PK, `(employee_id, attendance_date)` UNIQUE, `employee_id` FK | Daily attendance status and times. Valid statuses: PRESENT, ABSENT, HALF_DAY, WORK_FROM_HOME. |
| `leave_type` | `leave_type_id` PK, `leave_type_name` UNIQUE | Paid/unpaid leave category. |
| `leave_request` | `leave_id` PK, `employee_id` FK, `leave_type_id` FK, `reviewed_by` FK | Leave interval, reason, status and reviewer. Trigger rejects overlapping approved leave. |
| `company_holiday` | `holiday_date` PK | Calendar dates excluded from working-day calculations. |
| `salary_structure` | `salary_structure_id` PK, `employee_id` FK, effective dates | Salary components and PF percentage for an effective period. Trigger prevents overlapping periods. |
| `tax_bracket` | `tax_bracket_id` PK, UNIQUE `(tax_year, lower_limit)` | Progressive tax bands with lower-inclusive/upper-exclusive limits. Trigger rejects overlapping bands. |
| `payroll_run` | `run_id` PK, UNIQUE `(pay_year, pay_month)`, `processed_by` FK | One processing run per calendar month. |
| `payroll_entry` | `entry_id` PK, UNIQUE `(run_id, employee_id)`, FKs to run/employee/salary structure | Per-employee salary, deductions and historical salary-component snapshots. |

## Important numeric fields

- All money is stored as `NUMERIC(...,2)` to avoid binary floating-point rounding.
- `pf_rate_percent` and `rate_percent` are percentages in the range 0–100.
- `unpaid_days` can contain half-day increments, so it uses `NUMERIC(6,2)`.
- All date intervals are inclusive. Payroll selects a salary structure that covers the complete month.

## Reporting index rationale

- `attendance(attendance_date, employee_id)` supports month-range attendance summaries and late-mark filtering.
- `leave_request(employee_id, status, start_date, end_date)` supports employee leave history and approved-leave date checks.
- `salary_structure(employee_id, effective_from DESC, effective_to)` supports effective-dated salary selection.
- `payroll_entry(run_id, employee_id)` supports generating/viewing every payslip in one payroll run.
- `payroll_entry(employee_id, run_id)` supports an employee's own payslip history.
