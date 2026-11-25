-- PHASE 2 — Deterministic sample dataset
-- At least 12 employees and three months of attendance (August–October 2026).
-- Demo credentials: admin / Admin@123; every employee / Employee@123.
-- Change these immediately outside a local classroom demonstration.
SET search_path TO payroll, public;

INSERT INTO department (department_name) VALUES
('Engineering'), ('Data Science'), ('Quality Assurance');

INSERT INTO designation (designation_name) VALUES
('Software Engineer'), ('Senior Software Engineer'), ('Data Analyst'),
('ML Engineer'), ('QA Engineer'), ('Team Lead');

INSERT INTO employee (
    employee_code, full_name, email, phone, hire_date,
    employment_status, department_id, designation_id
)
SELECT v.employee_code, v.full_name, v.email, v.phone, v.hire_date, 'ACTIVE',
       d.department_id, ds.designation_id
FROM (VALUES
    ('E1001','Aarav Sharma','aarav.sharma@example.test','9000000001',DATE '2022-03-14','Engineering','Senior Software Engineer'),
    ('E1002','Diya Verma','diya.verma@example.test','9000000002',DATE '2022-07-11','Engineering','Software Engineer'),
    ('E1003','Kabir Mehta','kabir.mehta@example.test','9000000003',DATE '2021-11-08','Data Science','ML Engineer'),
    ('E1004','Ananya Singh','ananya.singh@example.test','9000000004',DATE '2023-01-16','Data Science','Data Analyst'),
    ('E1005','Ishaan Gupta','ishaan.gupta@example.test','9000000005',DATE '2022-09-05','Quality Assurance','QA Engineer'),
    ('E1006','Meera Iyer','meera.iyer@example.test','9000000006',DATE '2020-05-18','Engineering','Team Lead'),
    ('E1007','Vivaan Patel','vivaan.patel@example.test','9000000007',DATE '2023-04-10','Engineering','Software Engineer'),
    ('E1008','Sara Khan','sara.khan@example.test','9000000008',DATE '2021-08-23','Data Science','Data Analyst'),
    ('E1009','Arjun Nair','arjun.nair@example.test','9000000009',DATE '2022-12-12','Quality Assurance','QA Engineer'),
    ('E1010','Aditi Rao','aditi.rao@example.test','9000000010',DATE '2020-02-03','Engineering','Senior Software Engineer'),
    ('E1011','Reyansh Das','reyansh.das@example.test','9000000011',DATE '2023-06-19','Data Science','ML Engineer'),
    ('E1012','Myra Joshi','myra.joshi@example.test','9000000012',DATE '2021-04-26','Quality Assurance','Team Lead')
) AS v(employee_code, full_name, email, phone, hire_date, department_name, designation_name)
JOIN department d ON d.department_name = v.department_name
JOIN designation ds ON ds.designation_name = v.designation_name;

-- PBKDF2-SHA256 hashes compatible with Werkzeug's check_password_hash().
INSERT INTO user_account (username, password_hash, role, employee_id)
VALUES (
    'admin',
    'pbkdf2:sha256:600000$fdf1603ea4f096c2637efd171974d66a$ab2c00b96eb980b23dcba4b20f9a8a7e3eb5c506afc35878320d6a27076c0aed',
    'HR_ADMIN', NULL
);

INSERT INTO user_account (username, password_hash, role, employee_id)
SELECT LOWER(e.employee_code),
       'pbkdf2:sha256:600000$92df4622b5b4d75c412cc692ff678424$9509956adc4f7f43e1b154ac6f2687f68d3b70cab284c725ef4d3514130559f5',
       'EMPLOYEE', e.employee_id
FROM employee e;

INSERT INTO leave_type (leave_type_name, is_paid) VALUES
('Annual Leave', TRUE), ('Sick Leave', TRUE), ('Leave Without Pay', FALSE);

INSERT INTO company_holiday (holiday_date, holiday_name) VALUES
(DATE '2026-08-15', 'Company Holiday'),
(DATE '2026-09-25', 'Company Foundation Day'),
(DATE '2026-10-02', 'Company Holiday');

-- Sample academic tax bands for 2026; NOT a statutory tax table.
INSERT INTO tax_bracket (tax_year, lower_limit, upper_limit, rate_percent) VALUES
(2026, 0,       300000,  0),
(2026, 300000,  600000,  5),
(2026, 600000,  1000000, 10),
(2026, 1000000, 1500000, 15),
(2026, 1500000, NULL,    20);

-- Baseline monthly salary structures effective from 1 January 2026.
INSERT INTO salary_structure (
    employee_id, effective_from, effective_to,
    basic_salary, hra, special_allowance, other_allowance, pf_rate_percent
)
SELECT e.employee_id, DATE '2026-01-01', NULL,
       CASE e.employee_code
           WHEN 'E1001' THEN 60000 WHEN 'E1002' THEN 38000
           WHEN 'E1003' THEN 52000 WHEN 'E1004' THEN 42000
           WHEN 'E1005' THEN 35000 WHEN 'E1006' THEN 75000
           WHEN 'E1007' THEN 40000 WHEN 'E1008' THEN 45000
           WHEN 'E1009' THEN 36000 WHEN 'E1010' THEN 68000
           WHEN 'E1011' THEN 50000 ELSE 62000
       END,
       CASE e.employee_code
           WHEN 'E1001' THEN 24000 WHEN 'E1002' THEN 15200
           WHEN 'E1003' THEN 20800 WHEN 'E1004' THEN 16800
           WHEN 'E1005' THEN 14000 WHEN 'E1006' THEN 30000
           WHEN 'E1007' THEN 16000 WHEN 'E1008' THEN 18000
           WHEN 'E1009' THEN 14400 WHEN 'E1010' THEN 27200
           WHEN 'E1011' THEN 20000 ELSE 24800
       END,
       CASE e.employee_code
           WHEN 'E1001' THEN 18000 WHEN 'E1002' THEN 11400
           WHEN 'E1003' THEN 15600 WHEN 'E1004' THEN 12600
           WHEN 'E1005' THEN 10500 WHEN 'E1006' THEN 22500
           WHEN 'E1007' THEN 12000 WHEN 'E1008' THEN 13500
           WHEN 'E1009' THEN 10800 WHEN 'E1010' THEN 20400
           WHEN 'E1011' THEN 15000 ELSE 18600
       END,
       3000, 12.00
FROM employee e;

-- Employee E1001 receives a revised salary effective 1 September 2026.
UPDATE salary_structure ss
SET effective_to = DATE '2026-08-31'
FROM employee e
WHERE ss.employee_id = e.employee_id
  AND e.employee_code = 'E1001'
  AND ss.effective_to IS NULL;

INSERT INTO salary_structure (
    employee_id, effective_from, effective_to,
    basic_salary, hra, special_allowance, other_allowance, pf_rate_percent
)
SELECT e.employee_id, DATE '2026-09-01', NULL,
       65000, 26000, 19500, 3500, 12.00
FROM employee e WHERE e.employee_code = 'E1001';

-- Leave records are inserted before attendance so approved leave days are not assigned attendance.
INSERT INTO leave_request (
    employee_id, leave_type_id, start_date, end_date, reason,
    status, reviewed_by, reviewed_at
)
SELECT e.employee_id, lt.leave_type_id, v.start_date, v.end_date, v.reason,
       v.status,
       CASE WHEN v.status IN ('APPROVED','REJECTED') THEN ua.user_id ELSE NULL END,
       CASE WHEN v.status IN ('APPROVED','REJECTED') THEN NOW() ELSE NULL END
FROM (VALUES
    ('E1001','Annual Leave',DATE '2026-10-05',DATE '2026-10-06','Family event','APPROVED'),
    ('E1002','Leave Without Pay',DATE '2026-09-14',DATE '2026-09-15','Personal work','APPROVED'),
    ('E1003','Sick Leave',DATE '2026-08-20',DATE '2026-08-20','Medical rest','APPROVED'),
    ('E1004','Leave Without Pay',DATE '2026-10-12',DATE '2026-10-12','Personal work','APPROVED'),
    ('E1005','Annual Leave',DATE '2026-10-22',DATE '2026-10-23','Planned trip','PENDING'),
    ('E1006','Sick Leave',DATE '2026-09-21',DATE '2026-09-21','Not approved','REJECTED'),
    ('E1007','Annual Leave',DATE '2026-08-03',DATE '2026-08-03','Personal day','APPROVED'),
    ('E1008','Leave Without Pay',DATE '2026-10-19',DATE '2026-10-20','Unpaid personal leave','APPROVED')
) AS v(employee_code, leave_type_name, start_date, end_date, reason, status)
JOIN employee e ON e.employee_code = v.employee_code
JOIN leave_type lt ON lt.leave_type_name = v.leave_type_name
LEFT JOIN user_account ua ON ua.username = 'admin';

-- Deterministic daily attendance for working days in the required 3-month sample period.
-- Approved leave days and company holidays are intentionally excluded.
INSERT INTO attendance (employee_id, attendance_date, check_in, check_out, status, remarks)
SELECT e.employee_id,
       g.day_value::DATE,
       CASE
           WHEN s.status_value = 'ABSENT' THEN NULL
           WHEN s.status_value = 'HALF_DAY' THEN TIME '09:25'
           WHEN s.status_value = 'WORK_FROM_HOME' THEN TIME '09:10'
           WHEN ((e.employee_id + EXTRACT(DOY FROM g.day_value)::INTEGER) % 7) = 0 THEN TIME '09:48'
           ELSE TIME '09:15'
       END,
       CASE
           WHEN s.status_value = 'ABSENT' THEN NULL
           WHEN s.status_value = 'HALF_DAY' THEN TIME '13:30'
           ELSE TIME '18:00'
       END,
       s.status_value,
       CASE WHEN s.status_value = 'WORK_FROM_HOME' THEN 'Remote work'
            WHEN s.status_value = 'ABSENT' THEN 'Recorded absence'
            ELSE 'Sample attendance' END
FROM employee e
CROSS JOIN GENERATE_SERIES(DATE '2026-08-01', DATE '2026-10-31', INTERVAL '1 day') AS g(day_value)
CROSS JOIN LATERAL (
    SELECT CASE
        WHEN (e.employee_id * 13 + EXTRACT(DOY FROM g.day_value)::INTEGER) % 31 = 0 THEN 'ABSENT'
        WHEN (e.employee_id * 7 + EXTRACT(DOY FROM g.day_value)::INTEGER) % 23 = 0 THEN 'HALF_DAY'
        WHEN (e.employee_id * 5 + EXTRACT(DOY FROM g.day_value)::INTEGER) % 13 = 0 THEN 'WORK_FROM_HOME'
        ELSE 'PRESENT'
    END AS status_value
) AS s
WHERE EXTRACT(ISODOW FROM g.day_value) BETWEEN 1 AND 5
  AND NOT EXISTS (SELECT 1 FROM company_holiday h WHERE h.holiday_date = g.day_value::DATE)
  AND NOT EXISTS (
      SELECT 1 FROM leave_request lr
      WHERE lr.employee_id = e.employee_id
        AND lr.status IN ('APPROVED','PENDING')
        AND g.day_value::DATE BETWEEN lr.start_date AND lr.end_date
  );

-- Quick seed validation outputs.
SELECT COUNT(*) AS employee_count FROM employee;
SELECT MIN(attendance_date) AS first_attendance,
       MAX(attendance_date) AS last_attendance,
       COUNT(*) AS attendance_rows
FROM attendance;
SELECT status, COUNT(*) FROM attendance GROUP BY status ORDER BY status;
