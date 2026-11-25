from __future__ import annotations

import os
import pytest
import psycopg
from psycopg.rows import dict_row


@pytest.fixture
def owner_db():
    dsn = os.getenv("TEST_DATABASE_URL")
    if not dsn:
        pytest.skip("Set TEST_DATABASE_URL to run database integration tests")
    conn = psycopg.connect(dsn, row_factory=dict_row)
    conn.execute("SET search_path TO payroll, public")
    try:
        yield conn
    finally:
        conn.rollback()
        conn.close()


@pytest.fixture
def app_db():
    dsn = os.getenv("TEST_APP_DATABASE_URL")
    if not dsn:
        pytest.skip("Set TEST_APP_DATABASE_URL to run RLS tests as payroll_app")
    conn = psycopg.connect(dsn, row_factory=dict_row)
    conn.execute("SET search_path TO payroll, public")
    try:
        yield conn
    finally:
        conn.rollback()
        conn.close()
