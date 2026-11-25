-- PHASE 2 — Monthly payroll procedure. The caller wraps CALL in one DB transaction.
SET ROLE payroll_owner;
SET search_path TO payroll, public;

CREATE OR REPLACE PROCEDURE sp_generate_monthly_payroll(
    p_pay_year INTEGER,
    p_pay_month INTEGER,
    p_processed_by BIGINT
)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = payroll, pg_temp
AS $$
DECLARE
    v_run_id BIGINT;
    v_run_status TEXT;
    v_employee RECORD;
    v_calc RECORD;
    v_employee_count INTEGER := 0;
BEGIN
    IF current_setting('app.user_role', true) IS DISTINCT FROM 'HR_ADMIN' THEN
        RAISE EXCEPTION 'Only HR/Admin may generate payroll';
    END IF;
    IF NULLIF(current_setting('app.user_id', true), '')::BIGINT IS DISTINCT FROM p_processed_by THEN
        RAISE EXCEPTION 'Payroll processor must match the authenticated HR/Admin session';
    END IF;
    IF p_pay_year IS NULL OR p_pay_month IS NULL
       OR p_pay_year NOT BETWEEN 2000 AND 2100
       OR p_pay_month NOT BETWEEN 1 AND 12 THEN
        RAISE EXCEPTION 'Invalid payroll period';
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM user_account
        WHERE user_id = p_processed_by AND role = 'HR_ADMIN' AND is_active = TRUE
    ) THEN
        RAISE EXCEPTION 'Invalid or inactive HR/Admin account';
    END IF;

    INSERT INTO payroll_run(pay_year, pay_month, status, processed_by)
    VALUES (p_pay_year, p_pay_month, 'PROCESSING', p_processed_by)
    ON CONFLICT (pay_year, pay_month) DO NOTHING;

    SELECT pr.run_id, pr.status INTO v_run_id, v_run_status
    FROM payroll_run pr
    WHERE pr.pay_year = p_pay_year AND pr.pay_month = p_pay_month
    FOR UPDATE;

    IF v_run_status = 'PROCESSED' THEN
        RAISE EXCEPTION 'Payroll for %-% has already been processed', p_pay_year, p_pay_month;
    END IF;

    DELETE FROM payroll_entry WHERE run_id = v_run_id;
    UPDATE payroll_run
    SET status = 'PROCESSING', processed_by = p_processed_by, processed_at = NULL
    WHERE run_id = v_run_id;

    FOR v_employee IN
        SELECT e.employee_id
        FROM employee e
        WHERE e.employment_status = 'ACTIVE'
          AND e.hire_date <= (MAKE_DATE(p_pay_year, p_pay_month, 1) + INTERVAL '1 month - 1 day')::DATE
        ORDER BY e.employee_id
    LOOP
        v_employee_count := v_employee_count + 1;
        SELECT * INTO STRICT v_calc
        FROM fn_calculate_monthly_salary(v_employee.employee_id, p_pay_year, p_pay_month);

        INSERT INTO payroll_entry(
            run_id, employee_id, salary_structure_id,
            basic_salary, hra, special_allowance, other_allowance,
            gross_salary, working_days, unpaid_days,
            attendance_deduction, pf_deduction, tax_deduction, net_salary
        ) VALUES (
            v_run_id, v_employee.employee_id, v_calc.salary_structure_id,
            v_calc.basic_salary, v_calc.hra, v_calc.special_allowance, v_calc.other_allowance,
            v_calc.gross_salary, v_calc.working_days, v_calc.unpaid_days,
            v_calc.attendance_deduction, v_calc.pf_deduction, v_calc.tax_deduction, v_calc.net_salary
        );
    END LOOP;

    IF v_employee_count = 0 THEN
        RAISE EXCEPTION 'No active employees found; payroll was not generated';
    END IF;

    UPDATE payroll_run
    SET status = 'PROCESSED', processed_by = p_processed_by, processed_at = NOW()
    WHERE run_id = v_run_id;
END;
$$;

REVOKE ALL ON PROCEDURE sp_generate_monthly_payroll(INTEGER, INTEGER, BIGINT) FROM PUBLIC;
GRANT EXECUTE ON PROCEDURE sp_generate_monthly_payroll(INTEGER, INTEGER, BIGINT) TO payroll_app;

RESET ROLE;
