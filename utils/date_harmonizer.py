import polars as pl
import pandas as pd
from pathlib import Path
from io import BytesIO

DETECTION_SAMPLE_SIZE = 100

# Common date formats to try when parsing
DATE_FORMATS = [
    "%Y-%m-%d",      # ISO: 2024-01-15
    "%m/%d/%Y",      # US: 01/15/2024
    "%d/%m/%Y",      # EU: 15/01/2024
    "%Y/%m/%d",      # 2024/01/15
    "%m-%d-%Y",      # 01-15-2024
    "%d-%m-%Y",      # 15-01-2024
    "%Y%m%d",        # 20240115
    "%B %d, %Y",     # January 15, 2024
    "%b %d, %Y",     # Jan 15, 2024
    "%d %B %Y",      # 15 January 2024
    "%d %b %Y",      # 15 Jan 2024
]


def _try_parse_dates_polars(series: pl.Series) -> tuple[pl.Series | None, str | None]:
    """Try parsing a series with multiple date formats. Returns (parsed_series, format) or (None, None)."""
    for fmt in DATE_FORMATS:
        try:
            parsed = series.str.to_datetime(format=fmt, strict=False)
            valid_count = parsed.drop_nulls().len()
            # If most values parsed successfully, use this format
            if valid_count >= len(series) * 0.8:
                return parsed, fmt
        except Exception:
            continue
    return None, None


def _detect_date_columns_polars(df: pl.DataFrame, threshold: float = 0.8) -> list[tuple[str, str | None]]:
    """Detect date columns in a Polars DataFrame. Returns list of (column_name, format)."""
    date_columns = []

    for col in df.columns:
        col_dtype = df[col].dtype

        # Check if already datetime type
        if col_dtype in (pl.Datetime, pl.Date):
            date_columns.append((col, None))
            continue

        # Try to parse string/utf8 columns as dates
        if col_dtype == pl.Utf8:
            sample = df[col].drop_nulls().head(DETECTION_SAMPLE_SIZE)
            if len(sample) == 0:
                continue
            parsed, fmt = _try_parse_dates_polars(sample)
            if parsed is not None:
                valid_count = parsed.drop_nulls().len()
                if valid_count / len(sample) >= threshold:
                    date_columns.append((col, fmt))

    return date_columns


def _detect_date_columns_pandas(df: pd.DataFrame, threshold: float = 0.8) -> list[str]:
    """Detect date columns in a pandas DataFrame (for Excel files)."""
    date_columns = []

    for col in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            date_columns.append(col)
            continue

        if df[col].dtype == object:
            try:
                sample = df[col].dropna().head(DETECTION_SAMPLE_SIZE)
                if len(sample) == 0:
                    continue
                parsed = pd.to_datetime(sample, errors="coerce")
                if parsed.notna().sum() / len(sample) >= threshold:
                    date_columns.append(col)
            except Exception:
                continue

    return date_columns


def _harmonize_dates_polars(df: pl.DataFrame, date_columns: list[tuple[str, str | None]]) -> pl.DataFrame:
    """Harmonize date columns to ISO 8601 format using Polars."""
    result = df.clone()

    for col, fmt in date_columns:
        if col not in result.columns:
            continue

        col_dtype = result[col].dtype

        if col_dtype in (pl.Datetime, pl.Date):
            # Already datetime, just format
            harmonized = result[col].dt.strftime("%Y-%m-%d").fill_null("")
        else:
            # Parse string to datetime using detected format, then format to ISO
            harmonized = (
                result[col]
                .str.to_datetime(format=fmt, strict=False)
                .dt.strftime("%Y-%m-%d")
                .fill_null("")
            )

        result = result.with_columns(harmonized.alias(f"{col}_harmonized"))

    return result


def _harmonize_dates_pandas(df: pd.DataFrame, date_columns: list[str]) -> pd.DataFrame:
    """Harmonize date columns to ISO 8601 format using pandas (for Excel)."""
    result = df.copy()

    for col in date_columns:
        if col not in result.columns:
            continue

        parsed = pd.to_datetime(result[col], errors="coerce")
        harmonized = parsed.dt.strftime("%Y-%m-%d")
        harmonized = harmonized.fillna("")
        result[f"{col}_harmonized"] = harmonized

    return result


def get_harmonized_csv(file_path: Path) -> bytes:
    """
    Read a file, detect all date columns, harmonize them, and return as CSV bytes.

    Uses Polars for CSV files (efficient streaming) and pandas for Excel files.

    Args:
        file_path: Path to the CSV or Excel file

    Returns:
        CSV content as bytes, ready for download
    """
    suffix = file_path.suffix.lower()

    if suffix == ".csv":
        # Use Polars for CSV - more memory efficient
        df = pl.read_csv(file_path)
        date_columns = _detect_date_columns_polars(df)
        harmonized_df = _harmonize_dates_polars(df, date_columns)

        # Write to bytes
        buffer = BytesIO()
        harmonized_df.write_csv(buffer)
        return buffer.getvalue()

    elif suffix in (".xlsx", ".xls"):
        # Use pandas for Excel files
        df = pd.read_excel(file_path)
        date_columns = _detect_date_columns_pandas(df)
        harmonized_df = _harmonize_dates_pandas(df, date_columns)
        return harmonized_df.to_csv(index=False).encode("utf-8")

    else:
        raise ValueError(f"Unsupported file type: {suffix}")
