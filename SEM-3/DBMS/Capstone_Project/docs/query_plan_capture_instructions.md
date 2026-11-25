# Phase 3 — Query Plan Evidence Instructions

1. Complete schema creation and sample seeding.
2. Run `database/09_performance_benchmark.sql` once before `database/07_indexes.sql`.
3. The benchmark adds synthetic historical attendance and captures the **full Report 1 monthly attendance summary query** for May 2024 before and after creating `attendance(attendance_date, employee_id)`. The August–October 2026 classroom sample remains intact.
4. Copy the first `EXPLAIN (ANALYZE, BUFFERS)` output into `docs/query_plan_before.txt`.
5. Copy the second identical full-report query plan into `docs/query_plan_after.txt`.
6. Compare scan method (`Seq Scan`, `Index Scan`, `Bitmap Heap Scan`, etc.), actual rows, rows removed by filter, shared buffer hits/reads, and planning/execution time.
7. State whether the date-leading index was selected and whether the measured plan improved. Execution time can fluctuate; do not infer a reliable speedup from one run alone.
8. Include the PostgreSQL version, attendance row count, query text and benchmark month in the submission.

If the planner chooses a sequential scan after indexing, explain why that may happen (table size, selectivity, cache state or statistics). Do not force or fabricate an index scan or performance result.
