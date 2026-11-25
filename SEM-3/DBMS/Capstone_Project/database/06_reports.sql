-- PHASE 3 — Required reporting queries
-- Replace the sample month with the period being demonstrated.
SET search_path TO payroll, public;

-- REPORT 1: Monthly attendance summary. Missing unapproved weekdays count as absent.
WITH params AS (
    SELECT DATE '2026-10-01' AS month_start,
           (DATE '2026-10-01' + INTERVAL '1 month - 1 day')::DATE AS month_end
), calendar AS (
    SELECT g.day_value::DATE AS work_date
    FROM params p
    CROSS JOIN GENERATE_SERIES(p.month_start, p.month_end, INTERVAL '1 day') AS g(day_value)
    WHERE EXTRACT(ISODOW FROM g.day_value) BETWEEN 1 AND 5
      AND NOT EXISTS (SELECT 1 FROM company_holiday h WHERE h.holiday_date = g.day_value::DATE)
), working AS (
    SELECT e.employee_id, COUNT(c.work_date)::INTEGER AS working_days
    FROM employee e
    LEFT JOIN calendar c ON c.work_date >= e.hire_date
    GROUP BY e.employee_id
), attendance_totals AS (
    SELECT a.employee_id,
           COUNT(*) FILTER (WHERE a.status = 'PRESENT')::INTEGER AS present_days,
           COUNT(*) FILTER (WHERE a.status = 'WORK_FROM_HOME')::INTEGER AS wfh_days,
           COUNT(*) FILTER (WHERE a.status = 'ABSENT')::INTEGER AS recorded_absent_days,
           COUNT(*) FILTER (WHERE a.status = 'HALF_DAY')::INTEGER AS half_days
    FROM attendance a
    JOIN employee e ON e.employee_id = a.employee_id
    CROSS JOIN params p
    WHERE a.attendance_date BETWEEN p.month_start AND p.month_end
      AND a.attendance_date >= e.hire_date
    GROUP BY a.employee_id
), leave_totals AS (
    SELECT lr.employee_id,
           COUNT(*) FILTER (WHERE lt.is_paid)::INTEGER AS paid_leave_days,
           COUNT(*) FILTER (WHERE NOT lt.is_paid)::INTEGER AS unpaid_leave_days
    FROM leave_request lr
    JOIN employee e ON e.employee_id = lr.employee_id
    JOIN leave_type lt ON lt.leave_type_id = lr.leave_type_id
    CROSS JOIN params p
    CROSS JOIN LATERAL GENERATE_SERIES(
        GREATEST(lr.start_date, p.month_start, e.hire_date),
        LEAST(lr.end_date, p.month_end),
        INTERVAL '1 day'
    ) AS d(day_value)
    WHERE lr.status = 'APPROVED'
      AND EXTRACT(ISODOW FROM d.day_value) BETWEEN 1 AND 5
      AND NOT EXISTS (SELECT 1 FROM company_holiday h WHERE h.holiday_date = d.day_value::DATE)
    GROUP BY lr.employee_id
), missing_totals AS (
    SELECT e.employee_id, COUNT(c.work_date)::INTEGER AS missing_days
    FROM employee e CROSS JOIN calendar c
    WHERE c.work_date >= e.hire_date
      AND NOT EXISTS (
        SELECT 1 FROM attendance a
        WHERE a.employee_id = e.employee_id AND a.attendance_date = c.work_date
    )
      AND NOT EXISTS (
        SELECT 1 FROM leave_request lr
        WHERE lr.employee_id = e.employee_id
          AND lr.status = 'APPROVED'
          AND c.work_date BETWEEN lr.start_date AND lr.end_date
      )
    GROUP BY e.employee_id
)
SELECT e.employee_code, e.full_name,
       w.working_days,
       COALESCE(a.present_days, 0) AS present_days,
       COALESCE(a.wfh_days, 0) AS work_from_home_days,
       COALESCE(a.recorded_absent_days, 0) + COALESCE(m.missing_days, 0) AS absent_days,
       COALESCE(a.half_days, 0) AS half_days,
       COALESCE(l.paid_leave_days, 0) AS paid_leave_days,
       COALESCE(l.unpaid_leave_days, 0) AS unpaid_leave_days,
       ROUND(100.0 * (
           COALESCE(a.present_days, 0) + COALESCE(a.wfh_days, 0)
           + 0.5 * COALESCE(a.half_days, 0) + COALESCE(l.paid_leave_days, 0)
       ) / NULLIF(w.working_days, 0), 2) AS attendance_percentage
FROM employee e
JOIN working w ON w.employee_id = e.employee_id
LEFT JOIN attendance_totals a ON a.employee_id = e.employee_id
LEFT JOIN leave_totals l ON l.employee_id = e.employee_id
LEFT JOIN missing_totals m ON m.employee_id = e.employee_id
WHERE e.employment_status = 'ACTIVE'
ORDER BY e.employee_code;

-- REPORT 2: Payslip rows for one generated payroll run.
SELECT e.employee_code, e.full_name, pr.pay_year, pr.pay_month,
       pe.basic_salary, pe.hra, pe.special_allowance, pe.other_allowance,
       pe.gross_salary, pe.working_days, pe.unpaid_days,
       pe.attendance_deduction, pe.pf_deduction, pe.tax_deduction, pe.net_salary
FROM payroll_entry pe
JOIN payroll_run pr ON pr.run_id = pe.run_id
JOIN employee e ON e.employee_id = pe.employee_id
WHERE pr.pay_year = 2026 AND pr.pay_month = 10
ORDER BY e.employee_code;

-- REPORT 3: Late marks report. Company start time for this academic model is 09:30.
SELECT e.employee_code, e.full_name, a.attendance_date, a.check_in,
       ROUND(EXTRACT(EPOCH FROM (a.check_in - TIME '09:30')) / 60.0)::INTEGER AS minutes_late
FROM attendance a
JOIN employee e ON e.employee_id = a.employee_id
WHERE a.attendance_date >= DATE '2026-10-01'
  AND a.attendance_date < DATE '2026-11-01'
  AND a.check_in > TIME '09:30'
ORDER BY a.attendance_date, e.employee_code;
