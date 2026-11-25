-- PHASE 4 — Safe transaction demonstration. Run in one SQL session as a DB owner/admin.
-- A temporary table allows an explicit COMMIT demonstration without changing project data.
CREATE TEMP TABLE IF NOT EXISTS transaction_demo (demo_id INTEGER PRIMARY KEY, amount NUMERIC(10,2) NOT NULL)
ON COMMIT PRESERVE ROWS;
TRUNCATE TABLE transaction_demo;
INSERT INTO transaction_demo VALUES (1, 100.00);

BEGIN;
UPDATE transaction_demo SET amount = 150.00 WHERE demo_id = 1;
SELECT 'before COMMIT' AS step, amount FROM transaction_demo WHERE demo_id = 1;
COMMIT;
SELECT 'after COMMIT' AS step, amount FROM transaction_demo WHERE demo_id = 1;

BEGIN;
UPDATE transaction_demo SET amount = 999999.00 WHERE demo_id = 1;
SELECT 'before ROLLBACK' AS step, amount FROM transaction_demo WHERE demo_id = 1;
ROLLBACK;
SELECT 'after ROLLBACK' AS step, amount FROM transaction_demo WHERE demo_id = 1;

-- Also demonstrate rollback on a real salary row without keeping the change.
BEGIN;
UPDATE payroll.salary_structure
SET basic_salary = basic_salary + 999999
WHERE salary_structure_id = (
    SELECT salary_structure_id FROM payroll.salary_structure ORDER BY salary_structure_id LIMIT 1
);
SELECT salary_structure_id, basic_salary
FROM payroll.salary_structure
ORDER BY salary_structure_id
LIMIT 1;
ROLLBACK;

-- Verify the original salary value is still present after ROLLBACK.
SELECT salary_structure_id, basic_salary
FROM payroll.salary_structure
ORDER BY salary_structure_id
LIMIT 1;

-- The Flask salary-revision route demonstrates a committed production operation:
-- closing the prior salary period and inserting its successor in one transaction.
