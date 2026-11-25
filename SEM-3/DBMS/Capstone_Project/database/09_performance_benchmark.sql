-- PHASE 3 — Full Report 1 query-plan benchmark
-- Run once after 05_seed_data.sql and before 07_indexes.sql.
-- Adds synthetic historical attendance so the monthly attendance summary
-- can be compared on a meaningful volume of rows. The August–October 2026
-- classroom sample remains intact.

INSERT INTO payroll.attendance (
    employee_id, attendance_date, check_in, check_out, status, remarks
)
SELECT e.employee_id,
       g.day_value::DATE,
       CASE WHEN (e.employee_id + EXTRACT(DOY FROM g.day_value)::INTEGER) % 17 = 0
            THEN TIME '09:47' ELSE TIME '09:15' END,
       TIME '18:00',
       CASE WHEN (e.employee_id * 11 + EXTRACT(DOY FROM g.day_value)::INTEGER) % 29 = 0
            THEN 'WORK_FROM_HOME' ELSE 'PRESENT' END,
       'Synthetic historical benchmark row'
FROM payroll.employee e
CROSS JOIN GENERATE_SERIES(DATE '2021-01-01', DATE '2026-07-31', INTERVAL '1 day') AS g(day_value)
WHERE g.day_value::DATE >= e.hire_date
  AND EXTRACT(ISODOW FROM g.day_value) BETWEEN 1 AND 5
  AND NOT EXISTS (
      SELECT 1 FROM payroll.attendance a
      WHERE a.employee_id = e.employee_id
        AND a.attendance_date = g.day_value::DATE
  );

ANALYZE payroll.attendance;

-- BEFORE: Full monthly attendance summary query (Report 1), using May 2024
-- as a benchmark period within the synthetic historical data. Save this plan.
EXPLAIN (ANALYZE, BUFFERS)
WITH params AS (
    SELECT DATE '2024-05-01' AS month_start,
           DATE '2024-05-31' AS month_end
), calendar AS (
    SELECT g.day_value::DATE AS work_date
    FROM params p
    CROSS JOIN GENERATE_SERIES(p.month_start, p.month_end, INTERVAL '1 day') AS g(day_value)
    WHERE EXTRACT(ISODOW FROM g.day_value) BETWEEN 1 AND 5
      AND NOT EXISTS (
          SELECT 1 FROM payroll.company_holiday h
          WHERE h.holiday_date = g.day_value::DATE
      )
), working AS (
    SELECT e.employee_id, COUNT(c.work_date)::INTEGER AS working_days
    FROM payroll.employee e
    LEFT JOIN calendar c ON c.work_date >= e.hire_date
    GROUP BY e.employee_id
), attendance_totals AS (
    SELECT a.employee_id,
           COUNT(*) FILTER (WHERE a.status = 'PRESENT')::INTEGER AS present_days,
           COUNT(*) FILTER (WHERE a.status = 'WORK_FROM_HOME')::INTEGER AS wfh_days,
           COUNT(*) FILTER (WHERE a.status = 'ABSENT')::INTEGER AS recorded_absent_days,
           COUNT(*) FILTER (WHERE a.status = 'HALF_DAY')::INTEGER AS half_days
    FROM payroll.attendance a
    JOIN payroll.employee e ON e.employee_id = a.employee_id
    CROSS JOIN params p
    WHERE a.attendance_date BETWEEN p.month_start AND p.month_end
      AND a.attendance_date >= e.hire_date
    GROUP BY a.employee_id
), leave_totals AS (
    SELECT lr.employee_id,
           COUNT(*) FILTER (WHERE lt.is_paid)::INTEGER AS paid_leave_days,
           COUNT(*) FILTER (WHERE NOT lt.is_paid)::INTEGER AS unpaid_leave_days
    FROM payroll.leave_request lr
    JOIN payroll.employee e ON e.employee_id = lr.employee_id
    JOIN payroll.leave_type lt ON lt.leave_type_id = lr.leave_type_id
    CROSS JOIN params p
    CROSS JOIN LATERAL GENERATE_SERIES(
        GREATEST(lr.start_date, p.month_start, e.hire_date),
        LEAST(lr.end_date, p.month_end),
        INTERVAL '1 day'
    ) AS d(day_value)
    WHERE lr.status = 'APPROVED'
      AND EXTRACT(ISODOW FROM d.day_value) BETWEEN 1 AND 5
      AND NOT EXISTS (
          SELECT 1 FROM payroll.company_holiday h
          WHERE h.holiday_date = d.day_value::DATE
      )
    GROUP BY lr.employee_id
), missing_totals AS (
    SELECT e.employee_id, COUNT(c.work_date)::INTEGER AS missing_days
    FROM payroll.employee e
    CROSS JOIN calendar c
    WHERE c.work_date >= e.hire_date
      AND NOT EXISTS (
          SELECT 1 FROM payroll.attendance a
          WHERE a.employee_id = e.employee_id
            AND a.attendance_date = c.work_date
      )
      AND NOT EXISTS (
          SELECT 1 FROM payroll.leave_request lr
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
FROM payroll.employee e
JOIN working w ON w.employee_id = e.employee_id
LEFT JOIN attendance_totals a ON a.employee_id = e.employee_id
LEFT JOIN leave_totals l ON l.employee_id = e.employee_id
LEFT JOIN missing_totals m ON m.employee_id = e.employee_id
WHERE e.employment_status = 'ACTIVE'
ORDER BY e.employee_code;

-- Create the date-leading index evaluated for the Report 1 date filter.
CREATE INDEX IF NOT EXISTS idx_attendance_date_employee
    ON payroll.attendance (attendance_date, employee_id);
ANALYZE payroll.attendance;

-- AFTER: Run the exact same full monthly attendance summary query and save it.
EXPLAIN (ANALYZE, BUFFERS)
WITH params AS (
    SELECT DATE '2024-05-01' AS month_start,
           DATE '2024-05-31' AS month_end
), calendar AS (
    SELECT g.day_value::DATE AS work_date
    FROM params p
    CROSS JOIN GENERATE_SERIES(p.month_start, p.month_end, INTERVAL '1 day') AS g(day_value)
    WHERE EXTRACT(ISODOW FROM g.day_value) BETWEEN 1 AND 5
      AND NOT EXISTS (
          SELECT 1 FROM payroll.company_holiday h
          WHERE h.holiday_date = g.day_value::DATE
      )
), working AS (
    SELECT e.employee_id, COUNT(c.work_date)::INTEGER AS working_days
    FROM payroll.employee e
    LEFT JOIN calendar c ON c.work_date >= e.hire_date
    GROUP BY e.employee_id
), attendance_totals AS (
    SELECT a.employee_id,
           COUNT(*) FILTER (WHERE a.status = 'PRESENT')::INTEGER AS present_days,
           COUNT(*) FILTER (WHERE a.status = 'WORK_FROM_HOME')::INTEGER AS wfh_days,
           COUNT(*) FILTER (WHERE a.status = 'ABSENT')::INTEGER AS recorded_absent_days,
           COUNT(*) FILTER (WHERE a.status = 'HALF_DAY')::INTEGER AS half_days
    FROM payroll.attendance a
    JOIN payroll.employee e ON e.employee_id = a.employee_id
    CROSS JOIN params p
    WHERE a.attendance_date BETWEEN p.month_start AND p.month_end
      AND a.attendance_date >= e.hire_date
    GROUP BY a.employee_id
), leave_totals AS (
    SELECT lr.employee_id,
           COUNT(*) FILTER (WHERE lt.is_paid)::INTEGER AS paid_leave_days,
           COUNT(*) FILTER (WHERE NOT lt.is_paid)::INTEGER AS unpaid_leave_days
    FROM payroll.leave_request lr
    JOIN payroll.employee e ON e.employee_id = lr.employee_id
    JOIN payroll.leave_type lt ON lt.leave_type_id = lr.leave_type_id
    CROSS JOIN params p
    CROSS JOIN LATERAL GENERATE_SERIES(
        GREATEST(lr.start_date, p.month_start, e.hire_date),
        LEAST(lr.end_date, p.month_end),
        INTERVAL '1 day'
    ) AS d(day_value)
    WHERE lr.status = 'APPROVED'
      AND EXTRACT(ISODOW FROM d.day_value) BETWEEN 1 AND 5
      AND NOT EXISTS (
          SELECT 1 FROM payroll.company_holiday h
          WHERE h.holiday_date = d.day_value::DATE
      )
    GROUP BY lr.employee_id
), missing_totals AS (
    SELECT e.employee_id, COUNT(c.work_date)::INTEGER AS missing_days
    FROM payroll.employee e
    CROSS JOIN calendar c
    WHERE c.work_date >= e.hire_date
      AND NOT EXISTS (
          SELECT 1 FROM payroll.attendance a
          WHERE a.employee_id = e.employee_id
            AND a.attendance_date = c.work_date
      )
      AND NOT EXISTS (
          SELECT 1 FROM payroll.leave_request lr
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
FROM payroll.employee e
JOIN working w ON w.employee_id = e.employee_id
LEFT JOIN attendance_totals a ON a.employee_id = e.employee_id
LEFT JOIN leave_totals l ON l.employee_id = e.employee_id
LEFT JOIN missing_totals m ON m.employee_id = e.employee_id
WHERE e.employment_status = 'ACTIVE'
ORDER BY e.employee_code;

-- Compare actual scan type, rows, buffers and execution time; do not manufacture a speedup.
