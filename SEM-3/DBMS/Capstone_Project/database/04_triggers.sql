-- PHASE 2 — Trigger-based validation
SET ROLE payroll_owner;
SET search_path TO payroll, public;

CREATE OR REPLACE FUNCTION trg_validate_leave_request()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = payroll, pg_temp
AS $$
DECLARE
    v_hire_date DATE;
BEGIN
    -- Serialize validations for one employee so concurrent leave/attendance writes
    -- cannot both pass a read-before-write overlap check.
    PERFORM pg_advisory_xact_lock(NEW.employee_id);

    SELECT e.hire_date INTO v_hire_date
    FROM employee e WHERE e.employee_id = NEW.employee_id;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Employee % does not exist', NEW.employee_id USING ERRCODE = '23503';
    END IF;
    IF NEW.start_date < v_hire_date THEN
        RAISE EXCEPTION 'Leave cannot start before employee hire date %', v_hire_date
            USING ERRCODE = '23514';
    END IF;

    IF NEW.status = 'PENDING' THEN
        NEW.reviewed_by := NULL;
        NEW.reviewed_at := NULL;
        RETURN NEW;
    END IF;

    IF NEW.reviewed_by IS NULL OR NOT EXISTS (
        SELECT 1 FROM user_account ua
        WHERE ua.user_id = NEW.reviewed_by
          AND ua.role = 'HR_ADMIN'
          AND ua.is_active = TRUE
    ) THEN
        RAISE EXCEPTION 'Only an active HR/Admin account can review leave requests';
    END IF;
    NEW.reviewed_at := COALESCE(NEW.reviewed_at, NOW());

    IF NEW.status = 'APPROVED' THEN
        IF EXISTS (
            SELECT 1 FROM leave_request lr
            WHERE lr.employee_id = NEW.employee_id
              AND lr.status = 'APPROVED'
              AND lr.leave_id <> COALESCE(NEW.leave_id, -1)
              AND NEW.start_date <= lr.end_date
              AND lr.start_date <= NEW.end_date
        ) THEN
            RAISE EXCEPTION 'Approved leave overlaps another approved leave for employee %', NEW.employee_id
                USING ERRCODE = '23P01';
        END IF;

        IF EXISTS (
            SELECT 1 FROM attendance a
            WHERE a.employee_id = NEW.employee_id
              AND a.attendance_date BETWEEN NEW.start_date AND NEW.end_date
        ) THEN
            RAISE EXCEPTION 'Approved leave conflicts with an existing attendance record for employee %', NEW.employee_id
                USING ERRCODE = '23514';
        END IF;
    END IF;
    RETURN NEW;
END;
$$;

CREATE OR REPLACE FUNCTION trg_validate_attendance()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = payroll, pg_temp
AS $$
DECLARE
    v_hire_date DATE;
BEGIN
    PERFORM pg_advisory_xact_lock(NEW.employee_id);

    SELECT e.hire_date INTO v_hire_date
    FROM employee e WHERE e.employee_id = NEW.employee_id;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Employee % does not exist', NEW.employee_id USING ERRCODE = '23503';
    END IF;
    IF NEW.attendance_date < v_hire_date THEN
        RAISE EXCEPTION 'Attendance cannot be recorded before employee hire date %', v_hire_date
            USING ERRCODE = '23514';
    END IF;

    IF EXTRACT(ISODOW FROM NEW.attendance_date) NOT BETWEEN 1 AND 5 THEN
        RAISE EXCEPTION 'Attendance cannot be recorded on a weekend';
    END IF;
    IF EXISTS (SELECT 1 FROM company_holiday h WHERE h.holiday_date = NEW.attendance_date) THEN
        RAISE EXCEPTION 'Attendance cannot be recorded on a company holiday';
    END IF;
    IF EXISTS (
        SELECT 1 FROM leave_request lr
        WHERE lr.employee_id = NEW.employee_id
          AND lr.status = 'APPROVED'
          AND NEW.attendance_date BETWEEN lr.start_date AND lr.end_date
    ) THEN
        RAISE EXCEPTION 'Attendance conflicts with approved leave for employee % on %',
            NEW.employee_id, NEW.attendance_date USING ERRCODE = '23514';
    END IF;
    RETURN NEW;
END;
$$;

CREATE OR REPLACE FUNCTION trg_validate_salary_period()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = payroll, pg_temp
AS $$
BEGIN
    PERFORM pg_advisory_xact_lock(NEW.employee_id);

    IF EXISTS (
        SELECT 1 FROM salary_structure ss
        WHERE ss.employee_id = NEW.employee_id
          AND ss.salary_structure_id <> COALESCE(NEW.salary_structure_id, -1)
          AND NEW.effective_from <= COALESCE(ss.effective_to, 'infinity'::DATE)
          AND ss.effective_from <= COALESCE(NEW.effective_to, 'infinity'::DATE)
    ) THEN
        RAISE EXCEPTION 'Salary effective periods cannot overlap for employee %', NEW.employee_id
            USING ERRCODE = '23P01';
    END IF;
    RETURN NEW;
END;
$$;

CREATE OR REPLACE FUNCTION trg_validate_tax_bracket()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = payroll, pg_temp
AS $$
BEGIN
    PERFORM pg_advisory_xact_lock(NEW.tax_year::BIGINT + 1000000000000::BIGINT);

    IF EXISTS (
        SELECT 1 FROM tax_bracket tb
        WHERE tb.tax_year = NEW.tax_year
          AND tb.tax_bracket_id <> COALESCE(NEW.tax_bracket_id, -1)
          AND (tb.upper_limit IS NULL OR NEW.lower_limit < tb.upper_limit)
          AND (NEW.upper_limit IS NULL OR tb.lower_limit < NEW.upper_limit)
    ) THEN
        RAISE EXCEPTION 'Tax brackets overlap for tax year %', NEW.tax_year
            USING ERRCODE = '23P01';
    END IF;
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS validate_leave_request_trg ON leave_request;
CREATE TRIGGER validate_leave_request_trg
BEFORE INSERT OR UPDATE OF employee_id, start_date, end_date, status, reviewed_by
ON leave_request FOR EACH ROW EXECUTE FUNCTION trg_validate_leave_request();

DROP TRIGGER IF EXISTS validate_attendance_trg ON attendance;
CREATE TRIGGER validate_attendance_trg
BEFORE INSERT OR UPDATE OF employee_id, attendance_date
ON attendance FOR EACH ROW EXECUTE FUNCTION trg_validate_attendance();

DROP TRIGGER IF EXISTS validate_salary_period_trg ON salary_structure;
CREATE TRIGGER validate_salary_period_trg
BEFORE INSERT OR UPDATE OF employee_id, effective_from, effective_to
ON salary_structure FOR EACH ROW EXECUTE FUNCTION trg_validate_salary_period();

DROP TRIGGER IF EXISTS validate_tax_bracket_trg ON tax_bracket;
CREATE TRIGGER validate_tax_bracket_trg
BEFORE INSERT OR UPDATE OF tax_year, lower_limit, upper_limit
ON tax_bracket FOR EACH ROW EXECUTE FUNCTION trg_validate_tax_bracket();

REVOKE ALL ON FUNCTION trg_validate_leave_request() FROM PUBLIC;
REVOKE ALL ON FUNCTION trg_validate_attendance() FROM PUBLIC;
REVOKE ALL ON FUNCTION trg_validate_salary_period() FROM PUBLIC;
REVOKE ALL ON FUNCTION trg_validate_tax_bracket() FROM PUBLIC;
GRANT EXECUTE ON FUNCTION trg_validate_leave_request() TO payroll_app;
GRANT EXECUTE ON FUNCTION trg_validate_attendance() TO payroll_app;
GRANT EXECUTE ON FUNCTION trg_validate_salary_period() TO payroll_app;
GRANT EXECUTE ON FUNCTION trg_validate_tax_bracket() TO payroll_app;

RESET ROLE;
