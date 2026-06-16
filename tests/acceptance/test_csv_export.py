"""Feature-acceptance test for issue #5 (CSV export).

FAILS until the feature is implemented: taskflow.reporting.export_csv
does not exist yet, so this raises ImportError at call time.
Implementing #5 (a reporting/export.py with export_csv, exported from
reporting/__init__.py) makes it pass.
"""

from taskflow.models import Task


def test_export_csv_header_and_rows():
    from taskflow.reporting import export_csv  # noqa: PLC0415 — deferred so collection doesn't error

    rows = export_csv([Task(id=1, text="alpha", tags=["x"])])
    lines = rows.strip().splitlines()
    assert lines[0].startswith("id,")
    assert "alpha" in lines[1]
