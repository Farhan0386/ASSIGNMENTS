-- PHASE 2 — Stored functions
SET ROLE payroll_owner;
SET search_path TO payroll, public;

-- Used by Flask for login without granting the application direct password_hash SELECT access.
CREATE OR REPLACE FUNCTION fn_get_login_record(p_username TEXT)
RETURNS TABLE (
    user_id BIGINT,
    username TEXT,
    password_hash TEXT,
    role TEXT,
    employee_id BIGINT,
    is_active BOOLEAN
)
LANGUAGE SQL
SECURITY DEFINER
SET search_path = payroll, pg_temp
AS $$
    SELECT ua.user_id, ua.username::TEXT, ua.password_hash, ua.role::TEXT,
           ua.employee_id, ua.is_active
    FROM user_account ua
    WHERE LOWER(ua.username) = LOWER(p_username)
    LIMIT 1;
$$;

-- Demonstration progressive annual tax. Tax bands are sample academic values, not statutory advice.
CREATE OR REPLACE FUNCTION fn_calculate_annual_tax(
    p_annual_taxable_income NUMERIC,
    p_tax_year INTEGER
) RETURNS NUMERIC
LANGUAGE plpgsql
STABLE
SECURITY DEFINER
SET search_path = payroll, pg_temp
AS $$
DECLARE
    v_tax NUMERIC(14,2);
    v_bracket_count INTEGER;
    v_invalid BOOLEAN;
BEGIN
    IF p_annual_taxable_income IS NULL OR p_annual_taxable_income < 0 THEN
        RAISE EXCEPTION 'Taxable income must be a non-negative value';
    END IF;

    SELECT COUNT(*) INTO v_bracket_count
    FROM tax_bracket WHERE tax_year = p_tax_year;
    IF v_bracket_count = 0 THEN
        RAISE EXCEPTION 'No tax brackets configured for tax year %', p_tax_year;
    END IF;

    WITH ordered AS (
        SELECT lower_limit, upper_limit,
               LAG(upper_limit) OVER (ORDER BY lower_limit) AS previous_upper,
               ROW_NUMBER() OVER (ORDER BY lower_limit) AS rn,
               COUNT(*) OVER () AS total_rows
        FROM tax_bracket
        WHERE tax_year = p_tax_year
    )
    SELECT BOOL_OR(
        (rn = 1 AND lower_limit <> 0)
        OR (rn > 1 AND previous_upper IS DISTINCT FROM lower_limit)
        OR (rn = total_rows AND upper_limit IS NOT NULL)
    ) INTO v_invalid
    FROM ordered;

    IF COALESCE(v_invalid, TRUE) THEN
        RAISE EXCEPTION 'Tax brackets for % must start at zero, be contiguous, and end with an open upper limit', p_tax_year;
    END IF;

    SELECT COALESCE(SUM(
        GREATEST(
            LEAST(p_annual_taxable_income, COALESCE(tb.upper_limit, p_annual_taxable_income))
            - tb.lower_limit,
            0
        ) * tb.rate_percent / 100.0
    ), 0)::NUMERIC(14,2)
    INTO v_tax
    FROM tax_bracket tb
    WHERE tb.tax_year = p_tax_year;

    RETURN ROUND(v_tax, 2);
END;
$$;

-- Salary calculation for one employee and one complete calendar month.
-- Salary structures must cover the full month; revisions should start on day 1.
CREATE OR REPLACE FUNCTION fn_calculate_monthly_salary(
    p_employee_id BIGINT,
    p_pay_year INTEGER,
    p_pay_month INTEGER
)
RETURNS TABLE (
    salary_structure_id BIGINT,
    basic_salary NUMERIC,
    hra NUMERIC,
    special_allowance NUMERIC,
    other_allowance NUMERIC,
    gross_salary NUMERIC,
    working_days INTEGER,
    unpaid_days NUMERIC,
    attendance_deduction NUMERIC,
    pf_deduction NUMERIC,
    tax_deduction NUMERIC,
    net_salary NUMERIC
)
LANGUAGE plpgsql
STABLE
SECURITY DEFINER
SET search_path = payroll, pg_temp
AS $$
DECLARE
    v_month_start DATE;
    v_month_end DATE;
    v_hire_date DATE;
    v_period_start DATE;
    v_salary RECORD;
    v_working_days INTEGER;
    v_calendar_working_days INTEGER;
    v_proration_factor NUMERIC(9,6);
    v_attendance_unpaid NUMERIC(8,2);
    v_missing_days NUMERIC(8,2);
    v_unpaid_leave_days NUMERIC(8,2);
    v_unpaid_days NUMERIC(8,2);
    v_full_gross NUMERIC(12,2);
    v_gross NUMERIC(12,2);
    v_attendance_deduction NUMERIC(12,2);
    v_pf_deduction NUMERIC(12,2);
    v_tax_deduction NUMERIC(12,2);
    v_net NUMERIC(12,2);
BEGIN
    IF p_pay_year IS NULL OR p_pay_year NOT BETWEEN 2000 AND 2100 THEN
        RAISE EXCEPTION 'Invalid payroll year: %', p_pay_year;
    END IF;
    IF p_pay_month IS NULL OR p_pay_month NOT BETWEEN 1 AND 12 THEN
        RAISE EXCEPTION 'Invalid payroll month: %', p_pay_month;
    END IF;

    v_month_start := MAKE_DATE(p_pay_year, p_pay_month, 1);
    v_month_end := (v_month_start + INTERVAL '1 month - 1 day')::DATE;

    SELECT e.hire_date INTO v_hire_date
    FROM employee e
    WHERE e.employee_id = p_employee_id;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Employee % does not exist', p_employee_id;
    END IF;
    IF v_hire_date > v_month_end THEN
        RAISE EXCEPTION 'Employee % was hired after the payroll period', p_employee_id;
    END IF;
    v_period_start := GREATEST(v_month_start, v_hire_date);

    SELECT ss.* INTO v_salary
    FROM salary_structure ss
    WHERE ss.employee_id = p_employee_id
      AND ss.effective_from <= v_month_start
      AND (ss.effective_to IS NULL OR ss.effective_to >= v_month_end)
    ORDER BY ss.effective_from DESC
    LIMIT 1;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'No salary structure covers the complete payroll period for employee %', p_employee_id;
    END IF;

    SELECT COUNT(*)::INTEGER INTO v_calendar_working_days
    FROM GENERATE_SERIES(v_month_start, v_month_end, INTERVAL '1 day') AS g(day_value)
    WHERE EXTRACT(ISODOW FROM g.day_value) BETWEEN 1 AND 5
      AND NOT EXISTS (
          SELECT 1 FROM company_holiday h WHERE h.holiday_date = g.day_value::DATE
      );

    SELECT COUNT(*)::INTEGER INTO v_working_days
    FROM GENERATE_SERIES(v_period_start, v_month_end, INTERVAL '1 day') AS g(day_value)
    WHERE EXTRACT(ISODOW FROM g.day_value) BETWEEN 1 AND 5
      AND NOT EXISTS (
          SELECT 1 FROM company_holiday h WHERE h.holiday_date = g.day_value::DATE
      );

    v_proration_factor := CASE
        WHEN v_calendar_working_days = 0 THEN 0
        ELSE v_working_days::NUMERIC / v_calendar_working_days
    END;

    SELECT COALESCE(SUM(
        CASE a.status WHEN 'ABSENT' THEN 1.0 WHEN 'HALF_DAY' THEN 0.5 ELSE 0.0 END
    ), 0)::NUMERIC(8,2)
    INTO v_attendance_unpaid
    FROM attendance a
    WHERE a.employee_id = p_employee_id
      AND a.attendance_date BETWEEN v_period_start AND v_month_end
      AND EXTRACT(ISODOW FROM a.attendance_date) BETWEEN 1 AND 5
      AND NOT EXISTS (
          SELECT 1 FROM company_holiday h WHERE h.holiday_date = a.attendance_date
      );

    -- Any scheduled weekday without attendance and without an approved leave record is treated as absent.
    -- This covers rejected/pending leave and missing check-in submissions.
    SELECT COUNT(*)::NUMERIC(8,2) INTO v_missing_days
    FROM GENERATE_SERIES(v_period_start, v_month_end, INTERVAL '1 day') AS d(day_value)
    WHERE EXTRACT(ISODOW FROM d.day_value) BETWEEN 1 AND 5
      AND NOT EXISTS (
          SELECT 1 FROM company_holiday h WHERE h.holiday_date = d.day_value::DATE
      )
      AND NOT EXISTS (
          SELECT 1 FROM attendance a
          WHERE a.employee_id = p_employee_id AND a.attendance_date = d.day_value::DATE
      )
      AND NOT EXISTS (
          SELECT 1 FROM leave_request lr
          WHERE lr.employee_id = p_employee_id
            AND lr.status = 'APPROVED'
            AND d.day_value::DATE BETWEEN lr.start_date AND lr.end_date
      );

    SELECT COUNT(*)::NUMERIC(8,2) INTO v_unpaid_leave_days
    FROM leave_request lr
    JOIN leave_type lt ON lt.leave_type_id = lr.leave_type_id
    CROSS JOIN LATERAL GENERATE_SERIES(
        GREATEST(lr.start_date, v_period_start),
        LEAST(lr.end_date, v_month_end),
        INTERVAL '1 day'
    ) AS d(day_value)
    WHERE lr.employee_id = p_employee_id
      AND lr.status = 'APPROVED'
      AND lt.is_paid = FALSE
      AND EXTRACT(ISODOW FROM d.day_value) BETWEEN 1 AND 5
      AND NOT EXISTS (
          SELECT 1 FROM company_holiday h WHERE h.holiday_date = d.day_value::DATE
      );

    v_unpaid_days := v_attendance_unpaid + v_missing_days + v_unpaid_leave_days;
    IF v_unpaid_days > v_working_days THEN
        RAISE EXCEPTION 'Unpaid days (%) exceed working days (%) for employee %',
            v_unpaid_days, v_working_days, p_employee_id;
    END IF;

    v_full_gross := v_salary.basic_salary + v_salary.hra
                    + v_salary.special_allowance + v_salary.other_allowance;
    v_gross := ROUND(v_full_gross * v_proration_factor, 2);
    v_attendance_deduction := CASE
        WHEN v_working_days = 0 THEN 0
        ELSE ROUND((v_gross / v_working_days) * v_unpaid_days, 2)
    END;
    v_pf_deduction := ROUND(
        v_salary.basic_salary * v_proration_factor * v_salary.pf_rate_percent / 100.0, 2
    );
    v_tax_deduction := ROUND(
        fn_calculate_annual_tax(v_full_gross * 12, p_pay_year) / 12.0 * v_proration_factor, 2
    );
    v_net := GREATEST(0, v_gross - v_attendance_deduction - v_pf_deduction - v_tax_deduction);

    RETURN QUERY SELECT
        v_salary.salary_structure_id,
        ROUND(v_salary.basic_salary * v_proration_factor, 2),
        ROUND(v_salary.hra * v_proration_factor, 2),
        ROUND(v_salary.special_allowance * v_proration_factor, 2),
        ROUND(v_salary.other_allowance * v_proration_factor, 2),
        ROUND(v_gross, 2),
        v_working_days,
        v_unpaid_days,
        ROUND(v_attendance_deduction, 2),
        ROUND(v_pf_deduction, 2),
        ROUND(v_tax_deduction, 2),
        ROUND(v_net, 2);
END;
$$;

REVOKE ALL ON FUNCTION fn_get_login_record(TEXT) FROM PUBLIC;
REVOKE ALL ON FUNCTION fn_calculate_annual_tax(NUMERIC, INTEGER) FROM PUBLIC;
REVOKE ALL ON FUNCTION fn_calculate_monthly_salary(BIGINT, INTEGER, INTEGER) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION fn_get_login_record(TEXT) TO payroll_app;

RESET ROLE;
