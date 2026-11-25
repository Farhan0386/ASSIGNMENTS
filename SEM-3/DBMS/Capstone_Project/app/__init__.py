"""Payroll & Attendance Management System Flask application."""
from __future__ import annotations

import os
import hmac
import secrets
from functools import wraps
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation

import psycopg
from dotenv import load_dotenv
from flask import Flask, abort, flash, g, redirect, render_template, request, session, url_for
from psycopg.rows import dict_row
from werkzeug.security import check_password_hash, generate_password_hash

load_dotenv()


def create_app(test_config: dict | None = None) -> Flask:
    app = Flask(__name__)
    app.config.update(
        SECRET_KEY=os.getenv("FLASK_SECRET_KEY", "dev-only-change-this-secret"),
        DATABASE_URL=os.getenv("DATABASE_URL", "postgresql://payroll_app:dev_only_change_me@localhost:5432/payroll_db"),
        DEBUG=os.getenv("FLASK_DEBUG", "0") == "1",
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=os.getenv("FLASK_COOKIE_SECURE", "0") == "1",
    )
    if test_config:
        app.config.update(test_config)

    def get_db() -> psycopg.Connection:
        if "db" not in g:
            g.db = psycopg.connect(app.config["DATABASE_URL"], row_factory=dict_row)
            g.db.execute("SET search_path TO payroll, public")
            set_db_context(g.db)
        return g.db

    def set_db_context(conn: psycopg.Connection) -> None:
        """Set per-connection RLS context from the signed Flask session.

        A fresh database connection is opened for each request and closed at
        teardown. Session-level settings therefore cannot leak between users.
        """
        conn.execute(
            "SELECT set_config('app.user_role', %s, false), "
            "set_config('app.user_id', %s, false), "
            "set_config('app.employee_id', %s, false)",
            (
                str(session.get("role") or ""),
                str(session.get("user_id") or ""),
                str(session.get("employee_id") or ""),
            ),
        )

    @app.teardown_appcontext
    def close_db(_error: BaseException | None = None) -> None:
        conn = g.pop("db", None)
        if conn is not None:
            try:
                if _error is None:
                    conn.commit()
                else:
                    conn.rollback()
            finally:
                conn.close()

    def active_account() -> bool:
        if not session.get("user_id"):
            return False
        account = get_db().execute(
            "SELECT is_active FROM user_account WHERE user_id=%s",
            (session["user_id"],),
        ).fetchone()
        if not account or not account["is_active"]:
            session.clear()
            flash("This account is inactive. Contact HR/Admin.", "error")
            return False
        return True

    def login_required(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if not active_account():
                return redirect(url_for("login", next=request.path))
            return view(*args, **kwargs)
        return wrapped

    def role_required(*roles: str):
        def decorator(view):
            @wraps(view)
            def wrapped(*args, **kwargs):
                if not active_account():
                    return redirect(url_for("login", next=request.path))
                if session.get("role") not in roles:
                    abort(403)
                return view(*args, **kwargs)
            return wrapped
        return decorator

    def parse_month(value: str | None) -> tuple[date, date, str]:
        text = value or "2026-10"  # latest month included in the deterministic demonstration dataset
        try:
            start = datetime.strptime(text, "%Y-%m").date().replace(day=1)
        except ValueError as exc:
            raise ValueError("Choose a valid month in YYYY-MM format") from exc
        if start.month == 12:
            end = date(start.year, 12, 31)
        else:
            end = date(start.year, start.month + 1, 1) - timedelta(days=1)
        return start, end, text

    def as_decimal(value: str, field_name: str, *, allow_zero: bool = True) -> Decimal:
        try:
            number = Decimal(value)
        except (InvalidOperation, TypeError):
            raise ValueError(f"{field_name} must be a valid number")
        if not number.is_finite() or number < 0 or (not allow_zero and number == 0):
            raise ValueError(f"{field_name} must be {'greater than zero' if not allow_zero else 'zero or greater'}")
        return number.quantize(Decimal("0.01"))

    def get_csrf_token() -> str:
        token = session.get("_csrf_token")
        if not token:
            token = secrets.token_urlsafe(32)
            session["_csrf_token"] = token
        return token

    @app.before_request
    def protect_state_changing_requests():
        if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
            submitted = request.form.get("csrf_token", "")
            expected = session.get("_csrf_token", "")
            if not submitted or not expected or not hmac.compare_digest(submitted, expected):
                abort(400, description="Invalid or missing CSRF token")

    @app.context_processor
    def inject_user():
        return {"current_user": session, "csrf_token": get_csrf_token}

    @app.get("/")
    def index():
        return redirect(url_for("dashboard" if session.get("user_id") else "login"))

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "")
            if not username or not password:
                flash("Enter both username and password.", "error")
                return render_template("login.html")
            try:
                record = get_db().execute(
                    "SELECT * FROM fn_get_login_record(%s)", (username,)
                ).fetchone()
            except psycopg.Error:
                app.logger.exception("Login lookup failed")
                flash("Database connection failed. Check the setup and try again.", "error")
                return render_template("login.html"), 503

            if not record or not record["is_active"] or not check_password_hash(record["password_hash"], password):
                flash("Invalid username or password.", "error")
                return render_template("login.html"), 401

            session.clear()
            session.update(
                user_id=record["user_id"],
                username=record["username"],
                role=record["role"],
                employee_id=record["employee_id"],
            )
            set_db_context(get_db())
            return redirect(url_for("dashboard"))
        return render_template("login.html")

    @app.post("/logout")
    @login_required
    def logout():
        session.clear()
        flash("You have been logged out.", "success")
        return redirect(url_for("login"))

    @app.get("/dashboard")
    @login_required
    def dashboard():
        conn = get_db()
        if session["role"] == "HR_ADMIN":
            stats = {
                "employees": conn.execute("SELECT COUNT(*) AS n FROM employee WHERE employment_status='ACTIVE'").fetchone()["n"],
                "today_attendance": conn.execute("SELECT COUNT(*) AS n FROM attendance WHERE attendance_date = CURRENT_DATE").fetchone()["n"],
                "pending_leave": conn.execute("SELECT COUNT(*) AS n FROM leave_request WHERE status='PENDING'").fetchone()["n"],
                "payroll_runs": conn.execute("SELECT COUNT(*) AS n FROM payroll_run WHERE status='PROCESSED'").fetchone()["n"],
            }
            recent_runs = conn.execute(
                "SELECT run_id, pay_year, pay_month, processed_at FROM payroll_run "
                "WHERE status='PROCESSED' ORDER BY pay_year DESC, pay_month DESC LIMIT 5"
            ).fetchall()
            pending = conn.execute(
                "SELECT lr.leave_id, e.employee_code, e.full_name, lr.start_date, lr.end_date, lt.leave_type_name "
                "FROM leave_request lr JOIN employee e USING(employee_id) JOIN leave_type lt USING(leave_type_id) "
                "WHERE lr.status='PENDING' ORDER BY lr.created_at LIMIT 5"
            ).fetchall()
            return render_template("dashboard.html", stats=stats, recent_runs=recent_runs, pending=pending)

        employee = conn.execute(
            "SELECT e.*, d.department_name, ds.designation_name FROM employee e "
            "JOIN department d USING(department_id) JOIN designation ds USING(designation_id) "
            "WHERE e.employee_id=%s", (session["employee_id"],)
        ).fetchone()
        attendance = conn.execute(
            "SELECT attendance_date, check_in, check_out, status FROM attendance "
            "WHERE employee_id=%s ORDER BY attendance_date DESC LIMIT 7", (session["employee_id"],)
        ).fetchall()
        payslips = conn.execute(
            "SELECT pe.run_id, pr.pay_year, pr.pay_month, pe.gross_salary, pe.net_salary "
            "FROM payroll_entry pe JOIN payroll_run pr USING(run_id) "
            "WHERE pe.employee_id=%s ORDER BY pr.pay_year DESC, pr.pay_month DESC LIMIT 4",
            (session["employee_id"],),
        ).fetchall()
        leaves = conn.execute(
            "SELECT lr.leave_id, lt.leave_type_name, lr.start_date, lr.end_date, lr.status "
            "FROM leave_request lr JOIN leave_type lt USING(leave_type_id) "
            "WHERE lr.employee_id=%s ORDER BY lr.created_at DESC LIMIT 5",
            (session["employee_id"],),
        ).fetchall()
        return render_template("dashboard.html", employee=employee, attendance=attendance, payslips=payslips, leaves=leaves)

    @app.route("/employees", methods=["GET", "POST"])
    @role_required("HR_ADMIN")
    def employees():
        conn = get_db()
        if request.method == "POST":
            try:
                employee_code = request.form.get("employee_code", "").strip().upper()
                full_name = request.form.get("full_name", "").strip()
                email = request.form.get("email", "").strip().lower()
                phone = request.form.get("phone", "").strip() or None
                username = request.form.get("username", "").strip().lower()
                password = request.form.get("password", "")
                hire_date = date.fromisoformat(request.form.get("hire_date", ""))
                department_id = int(request.form.get("department_id", "0"))
                designation_id = int(request.form.get("designation_id", "0"))
                if not all([employee_code, full_name, email, username]) or len(password) < 8:
                    raise ValueError("Complete all required fields and use a password of at least 8 characters")
                password_hash = generate_password_hash(password)
                with conn.transaction():
                    row = conn.execute(
                        "INSERT INTO employee(employee_code,full_name,email,phone,hire_date,department_id,designation_id) "
                        "VALUES (%s,%s,%s,%s,%s,%s,%s) RETURNING employee_id",
                        (employee_code, full_name, email, phone, hire_date, department_id, designation_id),
                    ).fetchone()
                    conn.execute(
                        "INSERT INTO user_account(username,password_hash,role,employee_id) VALUES (%s,%s,'EMPLOYEE',%s)",
                        (username, password_hash, row["employee_id"]),
                    )
                flash(f"Employee {employee_code} and login account created.", "success")
                return redirect(url_for("employees"))
            except (ValueError, psycopg.Error) as exc:
                flash(f"Employee was not created: {exc}", "error")

        rows = conn.execute(
            "SELECT e.employee_id,e.employee_code,e.full_name,e.email,e.phone,e.hire_date,e.employment_status, "
            "d.department_name,ds.designation_name FROM employee e "
            "JOIN department d USING(department_id) JOIN designation ds USING(designation_id) "
            "ORDER BY e.employee_code"
        ).fetchall()
        departments = conn.execute("SELECT department_id,department_name FROM department ORDER BY department_name").fetchall()
        designations = conn.execute("SELECT designation_id,designation_name FROM designation ORDER BY designation_name").fetchall()
        return render_template("employees.html", employees=rows, departments=departments, designations=designations)

    @app.post("/employees/<int:employee_id>/edit")
    @role_required("HR_ADMIN")
    def edit_employee(employee_id: int):
        conn = get_db()
        try:
            full_name = request.form.get("full_name", "").strip()
            email = request.form.get("email", "").strip().lower()
            phone = request.form.get("phone", "").strip() or None
            department_id = int(request.form.get("department_id", "0"))
            designation_id = int(request.form.get("designation_id", "0"))
            if not full_name or not email or "@" not in email:
                raise ValueError("Enter a valid full name and email address")
            with conn.transaction():
                updated = conn.execute(
                    "UPDATE employee SET full_name=%s,email=%s,phone=%s,department_id=%s,designation_id=%s "
                    "WHERE employee_id=%s RETURNING employee_id",
                    (full_name, email, phone, department_id, designation_id, employee_id),
                ).fetchone()
                if not updated:
                    raise ValueError("Employee not found")
            flash("Employee profile updated.", "success")
        except (ValueError, psycopg.Error) as exc:
            flash(f"Employee profile was not updated: {exc}", "error")
        return redirect(url_for("employees"))

    @app.post("/employees/<int:employee_id>/status")
    @role_required("HR_ADMIN")
    def employee_status(employee_id: int):
        new_status = request.form.get("employment_status", "")
        if new_status not in {"ACTIVE", "INACTIVE"}:
            abort(400)
        conn = get_db()
        try:
            with conn.transaction():
                updated = conn.execute(
                    "UPDATE employee SET employment_status=%s WHERE employee_id=%s RETURNING employee_id",
                    (new_status, employee_id),
                ).fetchone()
                if not updated:
                    raise ValueError("Employee not found")
                conn.execute(
                    "UPDATE user_account SET is_active=%s WHERE employee_id=%s",
                    (new_status == "ACTIVE", employee_id),
                )
            flash(f"Employee status changed to {new_status}.", "success")
        except (ValueError, psycopg.Error) as exc:
            flash(f"Employee status update failed: {exc}", "error")
        return redirect(url_for("employees"))

    @app.route("/attendance", methods=["GET", "POST"])
    @role_required("HR_ADMIN")
    def attendance():
        conn = get_db()
        if request.method == "POST":
            try:
                employee_id = int(request.form.get("employee_id", "0"))
                attendance_date = date.fromisoformat(request.form.get("attendance_date", ""))
                status = request.form.get("status", "PRESENT")
                check_in = request.form.get("check_in") or None
                check_out = request.form.get("check_out") or None
                remarks = request.form.get("remarks", "").strip() or None
                if status == "ABSENT":
                    check_in = check_out = None
                elif not check_in:
                    raise ValueError("Check-in time is required unless the employee is absent")
                with conn.transaction():
                    conn.execute(
                        "INSERT INTO attendance(employee_id,attendance_date,check_in,check_out,status,remarks) "
                        "VALUES (%s,%s,%s,%s,%s,%s)",
                        (employee_id, attendance_date, check_in, check_out, status, remarks),
                    )
                flash("Attendance record saved.", "success")
                return redirect(url_for("attendance"))
            except (ValueError, psycopg.Error) as exc:
                flash(f"Attendance was not saved: {exc}", "error")
        rows = conn.execute(
            "SELECT a.attendance_date,e.employee_code,e.full_name,a.check_in,a.check_out,a.status "
            "FROM attendance a JOIN employee e USING(employee_id) "
            "ORDER BY a.attendance_date DESC,e.employee_code LIMIT 80"
        ).fetchall()
        employee_rows = conn.execute("SELECT employee_id,employee_code,full_name FROM employee WHERE employment_status='ACTIVE' ORDER BY employee_code").fetchall()
        return render_template("attendance.html", rows=rows, employees=employee_rows)

    @app.route("/leave", methods=["GET", "POST"])
    @login_required
    def leave():
        conn = get_db()
        if request.method == "POST":
            if session["role"] != "HR_ADMIN":
                abort(403)
            try:
                employee_id = int(request.form.get("employee_id", "0"))
                leave_type_id = int(request.form.get("leave_type_id", "0"))
                start_date = date.fromisoformat(request.form.get("start_date", ""))
                end_date = date.fromisoformat(request.form.get("end_date", ""))
                reason = request.form.get("reason", "").strip() or None
                if end_date < start_date:
                    raise ValueError("End date cannot be before start date")
                with conn.transaction():
                    conn.execute(
                        "INSERT INTO leave_request(employee_id,leave_type_id,start_date,end_date,reason,status) "
                        "VALUES (%s,%s,%s,%s,%s,'PENDING')",
                        (employee_id, leave_type_id, start_date, end_date, reason),
                    )
                flash("Leave request created for HR review.", "success")
                return redirect(url_for("leave"))
            except (ValueError, psycopg.Error) as exc:
                flash(f"Leave request was not created: {exc}", "error")

        rows = conn.execute(
            "SELECT lr.leave_id,e.employee_code,e.full_name,lt.leave_type_name,lt.is_paid, "
            "lr.start_date,lr.end_date,lr.reason,lr.status,lr.reviewed_at "
            "FROM leave_request lr JOIN employee e USING(employee_id) "
            "JOIN leave_type lt USING(leave_type_id) "
            "ORDER BY lr.created_at DESC LIMIT 100"
        ).fetchall()
        types = conn.execute("SELECT leave_type_id,leave_type_name,is_paid FROM leave_type ORDER BY leave_type_name").fetchall()
        employees = []
        if session["role"] == "HR_ADMIN":
            employees = conn.execute(
                "SELECT employee_id,employee_code,full_name FROM employee "
                "WHERE employment_status='ACTIVE' ORDER BY employee_code"
            ).fetchall()
        return render_template("leave.html", rows=rows, types=types, employees=employees)

    @app.post("/leave/<int:leave_id>/review")
    @role_required("HR_ADMIN")
    def review_leave(leave_id: int):
        status = request.form.get("status", "")
        if status not in {"APPROVED", "REJECTED"}:
            abort(400)
        conn = get_db()
        try:
            with conn.transaction():
                updated = conn.execute(
                    "UPDATE leave_request SET status=%s, reviewed_by=%s, reviewed_at=NOW() "
                    "WHERE leave_id=%s AND status='PENDING' RETURNING leave_id",
                    (status, session["user_id"], leave_id),
                ).fetchone()
                if not updated:
                    raise ValueError("Request not found or already reviewed")
            flash(f"Leave request {status.lower()}.", "success")
        except (ValueError, psycopg.Error) as exc:
            flash(f"Leave review failed: {exc}", "error")
        return redirect(url_for("leave"))

    @app.route("/salary", methods=["GET", "POST"])
    @role_required("HR_ADMIN")
    def salary():
        conn = get_db()
        if request.method == "POST":
            try:
                employee_id = int(request.form.get("employee_id", "0"))
                effective_from = date.fromisoformat(request.form.get("effective_from", ""))
                if effective_from.day != 1:
                    raise ValueError("Salary changes must take effect on the first day of a month")
                basic = as_decimal(request.form.get("basic_salary", ""), "Basic salary", allow_zero=False)
                hra = as_decimal(request.form.get("hra", "0"), "HRA")
                special = as_decimal(request.form.get("special_allowance", "0"), "Special allowance")
                other = as_decimal(request.form.get("other_allowance", "0"), "Other allowance")
                pf = as_decimal(request.form.get("pf_rate_percent", "12"), "PF rate")
                if pf > 100:
                    raise ValueError("PF rate cannot exceed 100 percent")
                with conn.transaction():
                    old = conn.execute(
                        "SELECT salary_structure_id,effective_from FROM salary_structure "
                        "WHERE employee_id=%s AND effective_to IS NULL FOR UPDATE",
                        (employee_id,),
                    ).fetchone()
                    if old:
                        if effective_from <= old["effective_from"]:
                            raise ValueError("New salary revision must be later than the current structure start date")
                        conn.execute(
                            "UPDATE salary_structure SET effective_to=%s WHERE salary_structure_id=%s",
                            (date.fromordinal(effective_from.toordinal() - 1), old["salary_structure_id"]),
                        )
                    conn.execute(
                        "INSERT INTO salary_structure(employee_id,effective_from,basic_salary,hra,special_allowance,other_allowance,pf_rate_percent) "
                        "VALUES (%s,%s,%s,%s,%s,%s,%s)",
                        (employee_id, effective_from, basic, hra, special, other, pf),
                    )
                flash("Salary structure saved. Previous salary history was preserved.", "success")
                return redirect(url_for("salary"))
            except (ValueError, psycopg.Error) as exc:
                flash(f"Salary revision failed: {exc}", "error")
        rows = conn.execute(
            "SELECT ss.salary_structure_id,e.employee_code,e.full_name,ss.effective_from,ss.effective_to, "
            "ss.basic_salary,ss.hra,ss.special_allowance,ss.other_allowance,ss.pf_rate_percent "
            "FROM salary_structure ss JOIN employee e USING(employee_id) "
            "ORDER BY e.employee_code,ss.effective_from DESC"
        ).fetchall()
        employee_rows = conn.execute("SELECT employee_id,employee_code,full_name FROM employee ORDER BY employee_code").fetchall()
        return render_template("salary.html", rows=rows, employees=employee_rows)

    @app.route("/payroll", methods=["GET", "POST"])
    @role_required("HR_ADMIN")
    def payroll():
        conn = get_db()
        if request.method == "POST":
            try:
                raw_period = request.form.get("pay_period", "").strip()
                if not raw_period:
                    raise ValueError("Select a payroll month before generating payroll")
                start, _end, _text = parse_month(raw_period)
                with conn.transaction():
                    conn.execute(
                        "CALL sp_generate_monthly_payroll(%s,%s,%s)",
                        (start.year, start.month, session["user_id"]),
                    )
                flash(f"Payroll generated for {start:%B %Y}.", "success")
                return redirect(url_for("payroll"))
            except (ValueError, psycopg.Error) as exc:
                flash(f"Payroll generation failed: {exc}", "error")
        runs = conn.execute(
            "SELECT pr.run_id,pr.pay_year,pr.pay_month,pr.status,pr.processed_at, "
            "COUNT(pe.entry_id) AS employee_count,COALESCE(SUM(pe.net_salary),0) AS net_payroll "
            "FROM payroll_run pr LEFT JOIN payroll_entry pe USING(run_id) "
            "GROUP BY pr.run_id ORDER BY pr.pay_year DESC,pr.pay_month DESC"
        ).fetchall()
        return render_template("payroll.html", runs=runs)

    @app.get("/reports/attendance")
    @role_required("HR_ADMIN")
    def attendance_report():
        conn = get_db()
        try:
            start, end, period = parse_month(request.args.get("period"))
        except ValueError as exc:
            flash(str(exc), "error")
            start, end, period = parse_month(None)
        rows = conn.execute(
            "WITH calendar AS ("
            " SELECT g.day_value::date AS work_date FROM GENERATE_SERIES(%s::date,%s::date,INTERVAL '1 day') g(day_value)"
            " WHERE EXTRACT(ISODOW FROM g.day_value) BETWEEN 1 AND 5"
            " AND NOT EXISTS (SELECT 1 FROM company_holiday h WHERE h.holiday_date=g.day_value::date)"
            "), working AS (SELECT e.employee_id,COUNT(c.work_date)::int working_days "
            " FROM employee e LEFT JOIN calendar c ON c.work_date>=e.hire_date GROUP BY e.employee_id), att AS ("
            " SELECT a.employee_id,COUNT(*) FILTER(WHERE a.status='PRESENT')::int present_days,"
            " COUNT(*) FILTER(WHERE a.status='WORK_FROM_HOME')::int wfh_days,"
            " COUNT(*) FILTER(WHERE a.status='ABSENT')::int recorded_absent_days,"
            " COUNT(*) FILTER(WHERE a.status='HALF_DAY')::int half_days"
            " FROM attendance a JOIN employee e USING(employee_id) "
            " WHERE a.attendance_date BETWEEN %s AND %s AND a.attendance_date>=e.hire_date GROUP BY a.employee_id"
            "), lv AS ("
            " SELECT lr.employee_id,COUNT(*) FILTER(WHERE lt.is_paid)::int paid_leave_days,"
            " COUNT(*) FILTER(WHERE NOT lt.is_paid)::int unpaid_leave_days"
            " FROM leave_request lr JOIN employee e USING(employee_id) JOIN leave_type lt USING(leave_type_id)"
            " CROSS JOIN LATERAL GENERATE_SERIES(GREATEST(lr.start_date,%s::date,e.hire_date),LEAST(lr.end_date,%s::date),INTERVAL '1 day') d(day_value)"
            " WHERE lr.status='APPROVED' AND EXTRACT(ISODOW FROM d.day_value) BETWEEN 1 AND 5"
            " AND NOT EXISTS(SELECT 1 FROM company_holiday h WHERE h.holiday_date=d.day_value::date)"
            " GROUP BY lr.employee_id"
            "), missing AS ("
            " SELECT e.employee_id,COUNT(c.work_date)::int missing_days FROM employee e CROSS JOIN calendar c"
            " WHERE c.work_date>=e.hire_date "
            " AND NOT EXISTS(SELECT 1 FROM attendance a WHERE a.employee_id=e.employee_id AND a.attendance_date=c.work_date)"
            " AND NOT EXISTS(SELECT 1 FROM leave_request lr WHERE lr.employee_id=e.employee_id AND lr.status='APPROVED'"
            " AND c.work_date BETWEEN lr.start_date AND lr.end_date) GROUP BY e.employee_id"
            ") SELECT e.employee_code,e.full_name,w.working_days,"
            "COALESCE(a.present_days,0) present_days,COALESCE(a.wfh_days,0) wfh_days,"
            "COALESCE(a.recorded_absent_days,0)+COALESCE(m.missing_days,0) absent_days,"
            "COALESCE(a.half_days,0) half_days,COALESCE(l.paid_leave_days,0) paid_leave_days,"
            "COALESCE(l.unpaid_leave_days,0) unpaid_leave_days,"
            "ROUND(100.0*(COALESCE(a.present_days,0)+COALESCE(a.wfh_days,0)+0.5*COALESCE(a.half_days,0)+COALESCE(l.paid_leave_days,0)) / NULLIF(w.working_days,0),2) attendance_percentage "
            "FROM employee e JOIN working w USING(employee_id) LEFT JOIN att a USING(employee_id) "
            "LEFT JOIN lv l USING(employee_id) LEFT JOIN missing m USING(employee_id) "
            "WHERE e.employment_status='ACTIVE' ORDER BY e.employee_code",
            (start, end, start, end, start, end),
        ).fetchall()
        return render_template("attendance_report.html", rows=rows, period=period)

    @app.get("/reports/late-marks")
    @role_required("HR_ADMIN")
    def late_marks_report():
        conn = get_db()
        try:
            start, end, period = parse_month(request.args.get("period"))
        except ValueError as exc:
            flash(str(exc), "error")
            start, end, period = parse_month(None)
        rows = conn.execute(
            "SELECT e.employee_code,e.full_name,a.attendance_date,a.check_in,"
            "ROUND(EXTRACT(EPOCH FROM (a.check_in-TIME '09:30'))/60.0)::INTEGER AS minutes_late "
            "FROM attendance a JOIN employee e USING(employee_id) "
            "WHERE a.attendance_date BETWEEN %s AND %s AND a.check_in>TIME '09:30' "
            "ORDER BY a.attendance_date,e.employee_code",
            (start, end),
        ).fetchall()
        return render_template("late_report.html", rows=rows, period=period)

    @app.get("/payslip/<int:run_id>")
    @login_required
    def payslip(run_id: int):
        conn = get_db()
        if session["role"] == "HR_ADMIN":
            rows = conn.execute(
                "SELECT e.employee_code,e.full_name,pr.pay_year,pr.pay_month,pe.* "
                "FROM payroll_entry pe JOIN payroll_run pr USING(run_id) JOIN employee e USING(employee_id) "
                "WHERE pe.run_id=%s ORDER BY e.employee_code", (run_id,)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT e.employee_code,e.full_name,pr.pay_year,pr.pay_month,pe.* "
                "FROM payroll_entry pe JOIN payroll_run pr USING(run_id) JOIN employee e USING(employee_id) "
                "WHERE pe.run_id=%s AND pe.employee_id=%s",
                (run_id, session["employee_id"]),
            ).fetchall()
        if not rows:
            abort(404)
        return render_template("payslip.html", rows=rows, run=rows[0])

    @app.errorhandler(403)
    def forbidden(_error):
        return render_template("error.html", code=403, message="You do not have permission to access this page."), 403

    @app.errorhandler(404)
    def not_found(_error):
        return render_template("error.html", code=404, message="The requested record or page was not found."), 404

    @app.errorhandler(psycopg.Error)
    def database_error(error):
        app.logger.exception("Unhandled database error", exc_info=error)
        return render_template(
            "error.html", code=500,
            message="A database operation failed. Verify the database setup and consult the server log."
        ), 500

    return app


app = create_app()
