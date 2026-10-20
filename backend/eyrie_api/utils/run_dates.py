"""Sequencing run dates from run IDs."""

import re
from datetime import datetime
from typing import Optional

RUN_DATE_PATTERNS = [
    (r'(?<!\d)(\d{4})[_-]?(\d{2})[_-]?(\d{2})(?!\d)', 0),
    (r'(?<!\d)(\d{2})(\d{2})(\d{2})(?!\d)', 2000),
]


def run_date_from_id(sequencing_run_id: Optional[str]) -> Optional[datetime]:
    """First YYYYMMDD, YYYY_MM_DD or YYMMDD date in a run ID, e.g. 20250930_1234_MN12345_FAQ12345."""
    for pattern, century in RUN_DATE_PATTERNS:
        for year, month, day in re.findall(pattern, sequencing_run_id or ''):
            try:
                return datetime(century + int(year), int(month), int(day))
            except ValueError:
                continue
    return None
