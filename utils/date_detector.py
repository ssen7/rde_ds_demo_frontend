import pandas as pd
from datetime import datetime


def detect_date_column(df: pd.DataFrame) -> str | None:
    """
    Detect the most likely date column in a DataFrame.
    Returns the column name or None if no date column found.
    """
    for col in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            return col

    # Try to parse string columns as dates
    for col in df.columns:
        if df[col].dtype == object:
            try:
                sample = df[col].dropna().head(100)
                if len(sample) == 0:
                    continue
                parsed = pd.to_datetime(sample, errors="coerce")
                # If more than 80% parse successfully, it's likely a date column
                if parsed.notna().sum() / len(sample) > 0.8:
                    return col
            except Exception:
                continue

    return None


def get_date_range(df: pd.DataFrame, date_column: str) -> tuple[datetime | None, datetime | None]:
    """
    Get the earliest and latest dates from a date column.
    Returns (earliest_date, latest_date) or (None, None) if parsing fails.
    """
    try:
        dates = pd.to_datetime(df[date_column], errors="coerce")
        valid_dates = dates.dropna()
        if len(valid_dates) == 0:
            return None, None
        return valid_dates.min().to_pydatetime(), valid_dates.max().to_pydatetime()
    except Exception:
        return None, None
