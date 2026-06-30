from __future__ import annotations

import re
from datetime import datetime


def sanitize_token(value: str) -> str:
    token = re.sub(r"[^A-Za-z0-9_.-]+", "-", str(value).strip())
    token = re.sub(r"-{2,}", "-", token).strip("-")
    return token or "unknown"


def build_output_filename(
    dataset: str,
    analysis_type: str,
    pattern: str,
    timestamp_format: str,
) -> str:
    timestamp = datetime.now().strftime(timestamp_format)
    return pattern.format(
        dataset=sanitize_token(dataset),
        analysisType=sanitize_token(analysis_type),
        timestamp=timestamp,
    )
