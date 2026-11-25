from __future__ import annotations

import pytest
import psycopg


def test_seed_contains_at_least_ten_employees_and_three_months(owner_db):
    count = owner_db.execute("SELECT COUNT(*) AS n FROM employee").fetchone()["n"]
    months = owner_db.execute(
        "SELECT COUNT(DISTINCT DATE_TRUNC('month', attendance_date)) AS n "
        "FROM attendance WHERE attendance_date BETWEEN DATE '2026-08-01' AND DATE '2026-10-31'"
    ).fetchone()["n"]
    assert count >= 10
    assert months >= 3


def test_username_uniqueness_is_case_insensitive(owner_db):
    with owner_db.transaction():
        with pytest.raises(psycopg.errors.UniqueViolation):
            with owner_db.transaction():
                owner_db.execute(
                    "INSERT INTO user_account(username,password_hash,role,employee_id) "
                    "VALUES ('ADMIN','not-a-real-hash','HR_ADMIN',NULL)"
                )


def test_duplicate_attendance_is_rejected(owner_db):
    row = owner_db.execute(
        "SELECT a.employee_id, a.attendance_date, a.check_in, a.check_out, a.status "
        "FROM attendance a WHERE NOT EXISTS ("
        "  SELECT 1 FROM leave_request lr WHERE lr.employee_id=a.employee_id "
        "  AND lr.status='APPROVED' AND a.attendance_date BETWEEN lr.start_date AND lr.end_date"
        ") ORDER BY a.attendance_date, a.employee_id LIMIT 1"
    ).fetchone()
    with owner_db.transaction():
        with pytest.raises(psycopg.errors.UniqueViolation):
            with owner_db.transaction():
                owner_db.execute(
                    "INSERT INTO attendance(employee_id,attendance_date,check_in,check_out,status) "
                    "VALUES (%s,%s,%s,%s,%s)",
                    (row["employee_id"], row["attendance_date"], row["check_in"], row["check_out"], row["status"]),
                )


def test_attendance_on_approved_leave_is_rejected(owner_db):
    row = owner_db.execute(
        "SELECT lr.employee_id,lr.start_date FROM leave_request lr "
        "WHERE lr.status='APPROVED' ORDER BY lr.start_date LIMIT 1"
    ).fetchone()
    with owner_db.transaction():
        with pytest.raises(psycopg.errors.CheckViolation):
            with owner_db.transaction():
                owner_db.execute(
                    "INSERT INTO attendance(employee_id,attendance_date,check_in,check_out,status) "
                    "VALUES (%s,%s,TIME '09:00',TIME '18:00','PRESENT')",
                    (row["employee_id"], row["start_date"]),
                )


def test_overlapping_approved_leave_is_rejected(owner_db):
    original = owner_db.execute(
        "SELECT employee_id,leave_type_id,start_date,end_date FROM leave_request "
        "WHERE status='APPROVED' ORDER BY start_date LIMIT 1"
    ).fetchone()
    admin_id = owner_db.execute(
        "SELECT user_id FROM user_account WHERE username='admin'"
    ).fetchone()["user_id"]
    with owner_db.transaction():
        with pytest.raises(psycopg.errors.ExclusionViolation):
            with owner_db.transaction():
                owner_db.execute(
                    "INSERT INTO leave_request(employee_id,leave_type_id,start_date,end_date,status,reviewed_by,reviewed_at) "
                    "VALUES (%s,%s,%s,%s,'APPROVED',%s,NOW())",
                    (original["employee_id"], original["leave_type_id"], original["start_date"], original["end_date"], admin_id),
                )



def test_approved_leave_over_existing_attendance_is_rejected(owner_db):
    row = owner_db.execute(
        "SELECT a.employee_id,a.attendance_date "
        "FROM attendance a WHERE NOT EXISTS ("
        " SELECT 1 FROM leave_request lr WHERE lr.employee_id=a.employee_id "
        " AND lr.status='APPROVED' AND a.attendance_date BETWEEN lr.start_date AND lr.end_date"
        ") ORDER BY a.attendance_date,a.employee_id LIMIT 1"
    ).fetchone()
    leave_type_id = owner_db.execute(
        "SELECT leave_type_id FROM leave_type WHERE leave_type_name='Annual Leave'"
    ).fetchone()["leave_type_id"]
    admin_id = owner_db.execute(
        "SELECT user_id FROM user_account WHERE username='admin'"
    ).fetchone()["user_id"]
    with owner_db.transaction():
        with pytest.raises(psycopg.errors.CheckViolation):
            with owner_db.transaction():
                owner_db.execute(
                    "INSERT INTO leave_request(employee_id,leave_type_id,start_date,end_date,status,reviewed_by,reviewed_at) "
                    "VALUES (%s,%s,%s,%s,'APPROVED',%s,NOW())",
                    (row["employee_id"], leave_type_id, row["attendance_date"], row["attendance_date"], admin_id),
                )


def test_non_admin_cannot_review_leave(owner_db):
    leave = owner_db.execute(
        "SELECT leave_id FROM leave_request WHERE status='PENDING' ORDER BY leave_id LIMIT 1"
    ).fetchone()
    employee_user_id = owner_db.execute(
        "SELECT user_id FROM user_account WHERE username='e1001'"
    ).fetchone()["user_id"]
    with owner_db.transaction():
        with pytest.raises(psycopg.Error):
            with owner_db.transaction():
                owner_db.execute(
                    "UPDATE leave_request SET status='APPROVED',reviewed_by=%s,reviewed_at=NOW() WHERE leave_id=%s",
                    (employee_user_id, leave["leave_id"]),
                )


def test_overlapping_salary_period_is_rejected(owner_db):
    employee_id = owner_db.execute(
        "SELECT employee_id FROM employee WHERE employee_code='E1001'"
    ).fetchone()["employee_id"]
    with owner_db.transaction():
        with pytest.raises(psycopg.errors.ExclusionViolation):
            with owner_db.transaction():
                owner_db.execute(
                    "INSERT INTO salary_structure(employee_id,effective_from,effective_to,basic_salary) "
                    "VALUES (%s,DATE '2026-06-01',DATE '2026-10-31',50000)",
                    (employee_id,),
                )

def test_negative_salary_is_rejected(owner_db):
    employee_id = owner_db.execute("SELECT employee_id FROM employee ORDER BY employee_id LIMIT 1").fetchone()["employee_id"]
    with owner_db.transaction():
        owner_db.execute(
            "UPDATE salary_structure SET effective_to=DATE '2029-12-31' "
            "WHERE employee_id=%s AND effective_to IS NULL", (employee_id,)
        )
        with pytest.raises(psycopg.errors.CheckViolation):
            with owner_db.transaction():
                owner_db.execute(
                    "INSERT INTO salary_structure(employee_id,effective_from,effective_to,basic_salary) "
                    "VALUES (%s,DATE '2030-01-01',DATE '2030-12-31',-1)", (employee_id,)
                )


def test_tax_function_calculates_progressive_bands(owner_db):
    tax = owner_db.execute(
        "SELECT fn_calculate_annual_tax(600000, 2026) AS tax"
    ).fetchone()["tax"]
    assert float(tax) == pytest.approx(15000.00)


def test_payroll_call_rolls_back_if_tax_configuration_is_missing(owner_db):
    admin_id = owner_db.execute("SELECT user_id FROM user_account WHERE username='admin'").fetchone()["user_id"]
    with owner_db.transaction():
        owner_db.execute("SELECT set_config('app.user_role','HR_ADMIN',true)")
        owner_db.execute("SELECT set_config('app.user_id',%s,true)", (str(admin_id),))
        with pytest.raises(psycopg.Error):
            with owner_db.transaction():
                owner_db.execute("CALL sp_generate_monthly_payroll(2027,1,%s)", (admin_id,))
        rows = owner_db.execute(
            "SELECT COUNT(*) AS n FROM payroll_run WHERE pay_year=2027 AND pay_month=1"
        ).fetchone()["n"]
        assert rows == 0


def test_employee_row_level_security_returns_only_own_row(app_db):
    # The SECURITY DEFINER login lookup safely returns the account's linked employee ID.
    login = app_db.execute(
        "SELECT user_id,employee_id FROM fn_get_login_record('e1001')"
    ).fetchone()
    employee_id = login["employee_id"]
    app_db.execute("SELECT set_config('app.user_role','EMPLOYEE',true)")
    app_db.execute("SELECT set_config('app.user_id',%s,true)", (str(login["user_id"]),))
    app_db.execute("SELECT set_config('app.employee_id',%s,true)", (str(employee_id),))
    rows = app_db.execute("SELECT employee_id FROM employee ORDER BY employee_id").fetchall()
    assert len(rows) == 1
    assert rows[0]["employee_id"] == employee_id
    attendance_rows = app_db.execute(
        "SELECT DISTINCT employee_id FROM attendance"
    ).fetchall()
    assert all(row["employee_id"] == employee_id for row in attendance_rows)

    salary_rows = app_db.execute(
        "SELECT DISTINCT employee_id FROM salary_structure"
    ).fetchall()
    assert all(row["employee_id"] == employee_id for row in salary_rows)

    leave_rows = app_db.execute(
        "SELECT DISTINCT employee_id FROM leave_request"
    ).fetchall()
    assert all(row["employee_id"] == employee_id for row in leave_rows)

    account_rows = app_db.execute(
        "SELECT user_id FROM user_account ORDER BY user_id"
    ).fetchall()
    assert len(account_rows) == 1
    assert account_rows[0]["user_id"] == login["user_id"]

    leave_type_id = app_db.execute(
        "SELECT leave_type_id FROM leave_type WHERE leave_type_name='Annual Leave'"
    ).fetchone()["leave_type_id"]
    # Employee access is read-only, including their own leave history.
    with app_db.transaction():
        with pytest.raises(psycopg.Error):
            with app_db.transaction():
                app_db.execute(
                    "INSERT INTO leave_request(employee_id,leave_type_id,start_date,end_date,status) "
                    "VALUES (%s,%s,DATE '2026-11-23',DATE '2026-11-23','PENDING')",
                    (employee_id, leave_type_id),
                )
    # RLS USING policies silently filter UPDATE/DELETE rows rather than raising.
    with app_db.transaction():
        updated = app_db.execute(
            "UPDATE employee SET full_name='Unauthorized change' WHERE employee_id=%s "
            "RETURNING employee_id",
            (employee_id,),
        ).fetchone()
        assert updated is None
    with app_db.transaction():
        changed_salary = app_db.execute(
            "UPDATE salary_structure SET basic_salary=basic_salary+1 "
            "WHERE employee_id=%s RETURNING salary_structure_id",
            (employee_id,),
        ).fetchone()
        assert changed_salary is None
    with app_db.transaction():
        changed_leave = app_db.execute(
            "UPDATE leave_request SET reason='Unauthorized change' "
            "WHERE employee_id=%s RETURNING leave_id",
            (employee_id,),
        ).fetchone()
        assert changed_leave is None
    with app_db.transaction():
        with pytest.raises(psycopg.Error):
            with app_db.transaction():
                app_db.execute(
                    "INSERT INTO attendance(employee_id,attendance_date,check_in,check_out,status) "
                    "VALUES (%s,DATE '2026-11-02',TIME '09:00',TIME '18:00','PRESENT')",
                    (employee_id,),
                )

    admin_id = app_db.execute(
        "SELECT user_id FROM fn_get_login_record('admin')"
    ).fetchone()["user_id"]
    with app_db.transaction():
        with pytest.raises(psycopg.Error):
            with app_db.transaction():
                app_db.execute(
                    "CALL sp_generate_monthly_payroll(2026,8,%s)", (admin_id,)
                )


def test_mid_month_hire_is_prorated_and_pre_hire_days_are_excluded(owner_db):
    employee_id = owner_db.execute(
        "SELECT employee_id FROM employee WHERE employee_code='E1001'"
    ).fetchone()["employee_id"]
    owner_db.execute(
        "UPDATE employee SET hire_date=DATE '2026-10-15' WHERE employee_id=%s",
        (employee_id,),
    )
    result = owner_db.execute(
        "SELECT * FROM fn_calculate_monthly_salary(%s,2026,10)",
        (employee_id,),
    ).fetchone()
    # 15–31 October 2026 contains 12 Monday–Friday dates (no configured holiday).
    assert result["working_days"] == 12
    assert float(result["basic_salary"]) == pytest.approx(37142.89, abs=0.05)
    assert result["unpaid_days"] <= result["working_days"]


def test_attendance_and_leave_before_hire_date_are_rejected(owner_db):
    employee_id = owner_db.execute(
        "SELECT employee_id FROM employee WHERE employee_code='E1001'"
    ).fetchone()["employee_id"]
    owner_db.execute(
        "UPDATE employee SET hire_date=DATE '2026-11-10' WHERE employee_id=%s",
        (employee_id,),
    )
    with owner_db.transaction():
        with pytest.raises(psycopg.errors.CheckViolation):
            with owner_db.transaction():
                owner_db.execute(
                    "INSERT INTO attendance(employee_id,attendance_date,check_in,check_out,status) "
                    "VALUES (%s,DATE '2026-11-09',TIME '09:00',TIME '18:00','PRESENT')",
                    (employee_id,),
                )
    leave_type_id = owner_db.execute(
        "SELECT leave_type_id FROM leave_type WHERE leave_type_name='Annual Leave'"
    ).fetchone()["leave_type_id"]
    with owner_db.transaction():
        with pytest.raises(psycopg.errors.CheckViolation):
            with owner_db.transaction():
                owner_db.execute(
                    "INSERT INTO leave_request(employee_id,leave_type_id,start_date,end_date,status) "
                    "VALUES (%s,%s,DATE '2026-11-09',DATE '2026-11-09','PENDING')",
                    (employee_id, leave_type_id),
                )


def test_weekend_attendance_is_rejected(owner_db):
    employee_id = owner_db.execute(
        "SELECT employee_id FROM employee WHERE employee_code='E1001'"
    ).fetchone()["employee_id"]
    with owner_db.transaction():
        with pytest.raises(psycopg.Error):
            with owner_db.transaction():
                owner_db.execute(
                    "INSERT INTO attendance(employee_id,attendance_date,check_in,check_out,status) "
                    "VALUES (%s,DATE '2026-08-01',TIME '09:00',TIME '18:00','PRESENT')",
                    (employee_id,),
                )


def test_company_holiday_attendance_is_rejected(owner_db):
    employee_id = owner_db.execute(
        "SELECT employee_id FROM employee WHERE employee_code='E1001'"
    ).fetchone()["employee_id"]
    with owner_db.transaction():
        with pytest.raises(psycopg.Error):
            with owner_db.transaction():
                owner_db.execute(
                    "INSERT INTO attendance(employee_id,attendance_date,check_in,check_out,status) "
                    "VALUES (%s,DATE '2026-09-25',TIME '09:00',TIME '18:00','PRESENT')",
                    (employee_id,),
                )


def test_employee_role_cannot_generate_payroll(owner_db):
    admin_id = owner_db.execute(
        "SELECT user_id FROM user_account WHERE username='admin'"
    ).fetchone()["user_id"]
    with owner_db.transaction():
        owner_db.execute("SELECT set_config('app.user_role','EMPLOYEE',true)")
        with pytest.raises(psycopg.Error):
            with owner_db.transaction():
                owner_db.execute("CALL sp_generate_monthly_payroll(2026,8,%s)", (admin_id,))
        count = owner_db.execute(
            "SELECT COUNT(*) AS n FROM payroll_run WHERE pay_year=2026 AND pay_month=8"
        ).fetchone()["n"]
        assert count == 0


def test_payroll_processor_must_match_authenticated_session(owner_db):
    admin_id = owner_db.execute(
        "SELECT user_id FROM user_account WHERE username='admin'"
    ).fetchone()["user_id"]
    employee_id = owner_db.execute(
        "SELECT user_id FROM user_account WHERE username='e1001'"
    ).fetchone()["user_id"]
    with owner_db.transaction():
        owner_db.execute("SELECT set_config('app.user_role','HR_ADMIN',true)")
        owner_db.execute("SELECT set_config('app.user_id',%s,true)", (str(employee_id),))
        with pytest.raises(psycopg.Error):
            with owner_db.transaction():
                owner_db.execute("CALL sp_generate_monthly_payroll(2026,8,%s)", (admin_id,))
        assert owner_db.execute(
            "SELECT COUNT(*) AS n FROM payroll_run WHERE pay_year=2026 AND pay_month=8"
        ).fetchone()["n"] == 0


def test_successful_payroll_generates_one_entry_per_active_employee(owner_db):
    admin_id = owner_db.execute(
        "SELECT user_id FROM user_account WHERE username='admin'"
    ).fetchone()["user_id"]
    with owner_db.transaction():
        owner_db.execute("SELECT set_config('app.user_role','HR_ADMIN',true)")
        owner_db.execute("SELECT set_config('app.user_id',%s,true)", (str(admin_id),))
        owner_db.execute("CALL sp_generate_monthly_payroll(2026,8,%s)", (admin_id,))
        run = owner_db.execute(
            "SELECT run_id,status FROM payroll_run WHERE pay_year=2026 AND pay_month=8"
        ).fetchone()
        assert run["status"] == "PROCESSED"
        counts = owner_db.execute(
            "SELECT COUNT(*) AS entries, COUNT(DISTINCT employee_id) AS employees "
            "FROM payroll_entry WHERE run_id=%s", (run["run_id"],)
        ).fetchone()
        expected = owner_db.execute(
            "SELECT COUNT(*) AS n FROM employee WHERE employment_status='ACTIVE' "
            "AND hire_date <= DATE '2026-08-31'"
        ).fetchone()["n"]
        assert counts["entries"] == expected
        assert counts["employees"] == expected

        # The processed period is immutable: a second attempt must fail.
        with pytest.raises(psycopg.Error):
            with owner_db.transaction():
                owner_db.execute("CALL sp_generate_monthly_payroll(2026,8,%s)", (admin_id,))
        assert owner_db.execute(
            "SELECT status FROM payroll_run WHERE run_id=%s", (run["run_id"],)
        ).fetchone()["status"] == "PROCESSED"


def test_hr_admin_row_level_security_context_can_see_all_employees(app_db):
    admin_id = app_db.execute(
        "SELECT user_id FROM fn_get_login_record('admin')"
    ).fetchone()["user_id"]
    app_db.execute("SELECT set_config('app.user_role','HR_ADMIN',true)")
    app_db.execute("SELECT set_config('app.user_id',%s,true)", (str(admin_id),))
    # HR/Admin accounts have no employee_id; the application sends an empty GUC, not the string 'None'.
    app_db.execute("SELECT set_config('app.employee_id','',true)")
    count = app_db.execute("SELECT COUNT(*) AS n FROM employee").fetchone()["n"]
    assert count == 12


def test_hr_admin_can_update_employee_profile(app_db):
    admin_id = app_db.execute(
        "SELECT user_id FROM fn_get_login_record('admin')"
    ).fetchone()["user_id"]
    app_db.execute("SELECT set_config('app.user_role','HR_ADMIN',true)")
    app_db.execute("SELECT set_config('app.user_id',%s,true)", (str(admin_id),))
    app_db.execute("SELECT set_config('app.employee_id','',true)")
    row = app_db.execute(
        "SELECT employee_id,full_name FROM employee WHERE employee_code='E1001'"
    ).fetchone()
    changed = app_db.execute(
        "UPDATE employee SET full_name=%s WHERE employee_id=%s RETURNING full_name",
        (row["full_name"] + ' (test edit)', row["employee_id"]),
    ).fetchone()
    assert changed["full_name"].endswith('(test edit)')


def test_hr_admin_can_create_pending_leave_request(app_db):
    admin_id = app_db.execute(
        "SELECT user_id FROM fn_get_login_record('admin')"
    ).fetchone()["user_id"]
    # Establish the HR/Admin RLS context before reading employee rows.
    app_db.execute("SELECT set_config('app.user_role','HR_ADMIN',true)")
    app_db.execute("SELECT set_config('app.user_id',%s,true)", (str(admin_id),))
    app_db.execute("SELECT set_config('app.employee_id','',true)")
    employee_id = app_db.execute(
        "SELECT employee_id FROM employee WHERE employee_code='E1001'"
    ).fetchone()["employee_id"]
    leave_type_id = app_db.execute(
        "SELECT leave_type_id FROM leave_type WHERE leave_type_name='Annual Leave'"
    ).fetchone()["leave_type_id"]
    with app_db.transaction():
        row = app_db.execute(
            "INSERT INTO leave_request(employee_id,leave_type_id,start_date,end_date,reason,status) "
            "VALUES (%s,%s,DATE '2026-11-23',DATE '2026-11-23','RBAC test','PENDING') "
            "RETURNING status,reviewed_by,reviewed_at",
            (employee_id, leave_type_id),
        ).fetchone()
        assert row["status"] == "PENDING"
        assert row["reviewed_by"] is None
        assert row["reviewed_at"] is None
