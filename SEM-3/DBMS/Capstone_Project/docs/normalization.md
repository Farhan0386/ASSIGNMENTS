# Phase 1 — Normalization to Third Normal Form

## Functional design

The database separates employee identity, organizational structure, attendance events, leave classification, salary history, tax configuration, payroll runs and payroll results. Each entity has a stable primary key. Descriptive names that can change independently are stored once and referenced by foreign keys.

## First Normal Form (1NF)

Every table has a primary key and each attribute stores one value per row. There are no comma-separated lists or repeating groups. For example, a workday has one attendance row for an employee/date pair; the database enforces `UNIQUE(employee_id, attendance_date)`. Allowances are separate numeric columns because they are distinct salary components, not a repeating list in a single field.

## Second Normal Form (2NF)

All non-key attributes depend on the whole candidate key. The tables use surrogate single-column primary keys. The attendance uniqueness rule is the composite candidate key `(employee_id, attendance_date)` and its non-key attributes (`check_in`, `check_out`, `status`, `remarks`) describe that employee's attendance on that date. Employee names, departments and designation descriptions are not copied into attendance rows. Usernames are also constrained case-insensitively so the login lookup cannot resolve multiple records.

## Third Normal Form (3NF)

There are no intended transitive dependencies among non-key attributes:

- Department name depends on `department_id` in `department`, not on an employee row.
- Designation name depends on `designation_id` in `designation`.
- Leave paid/unpaid classification depends on `leave_type_id` in `leave_type`, not on every leave request.
- Salary components depend on `salary_structure_id` and its employee/effective period. Old structures are retained rather than overwritten.
- Tax rate depends on the tax year and tax-band lower limit in `tax_bracket`.
- Payroll totals and salary snapshots belong to `payroll_entry`, associated with one payroll run and employee.

## Relationship and integrity notes

- `department` 1:M `employee`; `designation` 1:M `employee`.
- `employee` 1:0..1 `user_account` for employee accounts. HR/Admin accounts have no employee link.
- `employee` 1:M `attendance`, `leave_request` and `salary_structure`.
- `leave_type` 1:M `leave_request`; `user_account` 1:M reviewed leave requests.
- `payroll_run` 1:M `payroll_entry`; `employee` 1:M `payroll_entry`; `salary_structure` 1:M payroll snapshots across runs.
- `company_holiday` is a date calendar referenced by procedural/report queries.
- `tax_bracket` is keyed by year and band. Progressive-tax calculations validate the bands are contiguous and have an open-ended final band.

## Business rule for missing attendance

A scheduled weekday without an attendance row is treated as absent unless an approved leave request covers that date. This avoids silently treating incomplete attendance data as a fully paid day.

## Why payroll snapshots are intentional

A payroll entry stores the component amounts used at the time the payroll is calculated. These are historical facts, not duplicated current master data. Keeping them in the payroll transaction is necessary so a later salary revision cannot retroactively change an issued payslip.
