"""Run dependency-light static checks for the PayTrack capstone package.

This does not connect to PostgreSQL or replace the database integration tests.
Run from the project root after installing requirements.txt.
"""
from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

from jinja2 import Environment

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = [
    "README.md",
    "docs/demo_runbook.md",
    "run.py",
    "requirements.txt",
    "database/01_schema.sql",
    "database/02_functions.sql",
    "database/03_procedures.sql",
    "database/04_triggers.sql",
    "database/05_seed_data.sql",
    "database/06_reports.sql",
    "database/07_indexes.sql",
    "database/08_transaction_demo.sql",
    "database/09_performance_benchmark.sql",
    "docs/ERD.png",
    "docs/ERD.svg",
    "docs/ERD.mmd",
    "docs/erd.dot",
    "docs/data_dictionary.md",
    "docs/normalization.md",
    "docs/project_report.md",
    "docs/test_plan.md",
    "docs/submission_checklist.md",
    "tests/test_database_rules.py",
    "tests/test_web_security.py",
]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def main() -> int:
    for relative in REQUIRED_FILES:
        require((ROOT / relative).is_file(), f"Missing required file: {relative}")

    python_files = sorted(ROOT.rglob("*.py"))
    for path in python_files:
        if ".venv" in path.parts or "__pycache__" in path.parts:
            continue
        ast.parse(path.read_text(encoding="utf-8"), filename=str(path))

    template_files = sorted((ROOT / "app" / "templates").glob("*.html"))
    require(template_files, "No Jinja templates found")
    template_text: dict[Path, str] = {}
    env = Environment(autoescape=True)
    for path in template_files:
        source = path.read_text(encoding="utf-8")
        env.parse(source)
        template_text[path] = source

    app_tree = ast.parse((ROOT / "app" / "__init__.py").read_text(encoding="utf-8"))
    view_names = {
        node.name
        for node in ast.walk(app_tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    template_endpoints: set[str] = set()
    post_form_count = 0
    for path, source in template_text.items():
        template_endpoints.update(
            re.findall(r"url_for\(['\"]([^'\"]+)", source)
        )
        for match in re.finditer(r"<form\b([^>]*)>(.*?)</form>", source, flags=re.I | re.S):
            attrs, body = match.group(1), match.group(2)
            if re.search(r"method\s*=\s*[\"']?post", attrs, flags=re.I):
                post_form_count += 1
                tokens = len(re.findall(r"name=[\"']csrf_token[\"']", body, flags=re.I))
                require(
                    tokens == 1,
                    f"{path.relative_to(ROOT)} POST form must contain exactly one CSRF token (found {tokens})",
                )

    unresolved = template_endpoints - view_names - {"static"}
    require(not unresolved, f"Unresolved template endpoints: {sorted(unresolved)}")

    schema = (ROOT / "database" / "01_schema.sql").read_text(encoding="utf-8")
    table_names = re.findall(r"CREATE\s+TABLE\s+(\w+)", schema, flags=re.I)
    require(len(table_names) == 12, f"Expected 12 tables, found {len(table_names)}")
    require(
        "user_account_username_lower_uq" in schema,
        "Case-insensitive username uniqueness index is missing",
    )

    seed = (ROOT / "database" / "05_seed_data.sql").read_text(encoding="utf-8")
    employee_insert = re.search(
        r"INSERT\s+INTO\s+employee\s*\(.*?\)\s*\nSELECT.*?FROM\s*\(VALUES(.*?)\)\s+AS\s+v\(",
        seed,
        flags=re.I | re.S,
    )
    require(employee_insert is not None, "Could not locate the sample employee VALUES block")
    employee_codes = re.findall(r"\('E\d{4}'", employee_insert.group(1))
    require(len(employee_codes) >= 10, f"Expected at least 10 sample employees, found {len(employee_codes)}")
    require("DATE '2026-08-01'" in seed and "DATE '2026-10-31'" in seed,
            "Three-month attendance seed range is not declared as expected")

    procedure = (ROOT / "database" / "03_procedures.sql").read_text(encoding="utf-8")
    require("app.user_id" in procedure and "authenticated HR/Admin session" in procedure,
            "Payroll processor is not bound to the authenticated session")

    dot = (ROOT / "docs" / "erd.dot").read_text(encoding="utf-8")
    mermaid = (ROOT / "docs" / "ERD.mmd").read_text(encoding="utf-8")
    require("employee -> payroll_entry" in dot, "ERD DOT is missing Employee → Payroll Entry")
    require("EMPLOYEE ||--o{ PAYROLL_ENTRY" in mermaid,
            "ERD Mermaid source is missing Employee → Payroll Entry")

    print("PayTrack static verification: PASS")
    print(f"Python source files parsed: {len(python_files)}")
    print(f"Jinja templates parsed: {len(template_files)}")
    print(f"Template URL references resolved: {len(template_endpoints)}")
    print(f"POST forms protected by one CSRF token: {post_form_count}")
    print(f"Database tables declared: {len(table_names)}")
    print(f"Sample employees declared: {len(employee_codes)}")
    print("ERD relationships and payroll-session identity: verified")
    print("Note: PostgreSQL execution and integration tests must be run separately.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # show one actionable failure to the student
        print(f"PayTrack static verification: FAIL — {exc}", file=sys.stderr)
        raise SystemExit(1)
