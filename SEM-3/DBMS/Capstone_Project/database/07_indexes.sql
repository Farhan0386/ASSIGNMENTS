-- PHASE 3 — Reporting indexes. Run once after recording the unindexed plan.
CREATE INDEX IF NOT EXISTS idx_attendance_date_employee
    ON payroll.attendance (attendance_date, employee_id);
CREATE INDEX IF NOT EXISTS idx_leave_employee_status_dates
    ON payroll.leave_request (employee_id, status, start_date, end_date);
CREATE INDEX IF NOT EXISTS idx_salary_employee_effective
    ON payroll.salary_structure (employee_id, effective_from DESC, effective_to);
-- run_id leads because the payslip report selects a payroll run first, then
-- fetches that run's employee entries. The employee-leading index supports
-- the employee dashboard's own payslip history.
CREATE INDEX IF NOT EXISTS idx_payroll_entry_run_employee
    ON payroll.payroll_entry (run_id, employee_id);
CREATE INDEX IF NOT EXISTS idx_payroll_entry_employee_run
    ON payroll.payroll_entry (employee_id, run_id);

ANALYZE payroll.attendance;
ANALYZE payroll.leave_request;
ANALYZE payroll.salary_structure;
ANALYZE payroll.payroll_entry;
