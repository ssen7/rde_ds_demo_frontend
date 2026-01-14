from pathlib import Path
import pandas as pd
import polars as pl
from streamlit.runtime.uploaded_file_manager import UploadedFile

UPLOADS_DIR = Path(__file__).parent.parent / "uploads"


def save_uploaded_file(uploaded_file: UploadedFile) -> Path:
    """Save an uploaded file to the uploads directory and return the path."""
    UPLOADS_DIR.mkdir(exist_ok=True)
    file_path = UPLOADS_DIR / uploaded_file.name
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return file_path


def read_file(file_path: Path, nrows: int | None = None) -> pd.DataFrame:
    """Read a CSV or Excel file into a pandas DataFrame.

    Uses Polars for CSV (faster) and converts to pandas for Streamlit compatibility.
    Uses Pandas directly for Excel files.
    """
    suffix = file_path.suffix.lower()
    if suffix == ".csv":
        if nrows is not None:
            df = pl.read_csv(file_path, n_rows=nrows)
        else:
            df = pl.read_csv(file_path)
        return df.to_pandas()
    elif suffix in (".xlsx", ".xls"):
        return pd.read_excel(file_path, nrows=nrows)
    else:
        raise ValueError(f"Unsupported file type: {suffix}")


def scan_csv_lazy(file_path: Path) -> pl.LazyFrame:
    """Return a lazy frame for CSV files - no data loaded until collected."""
    return pl.scan_csv(file_path)


def get_column_names(file_path: Path) -> list[str]:
    """Get column names without loading the entire file."""
    suffix = file_path.suffix.lower()
    if suffix == ".csv":
        # Polars scan_csv reads only schema, very fast
        return pl.scan_csv(file_path).collect_schema().names()
    elif suffix in (".xlsx", ".xls"):
        # Read just first row for Excel
        return list(pd.read_excel(file_path, nrows=0).columns)
    else:
        raise ValueError(f"Unsupported file type: {suffix}")


def get_date_range_lazy(file_path: Path, date_column: str) -> tuple[str | None, str | None]:
    """Get min/max dates from a CSV file using lazy evaluation.

    This never loads the full file into memory - Polars streams through
    the file computing only the min/max of the specified column.

    Returns (earliest_date, latest_date) as ISO format strings, or (None, None) on error.
    """
    suffix = file_path.suffix.lower()
    if suffix != ".csv":
        return None, None  # Fall back to regular processing for Excel

    try:
        result = (
            pl.scan_csv(file_path)
            .select(
                pl.col(date_column).str.to_datetime(strict=False).alias("date")
            )
            .select(
                pl.col("date").min().alias("min_date"),
                pl.col("date").max().alias("max_date")
            )
            .collect()
        )

        min_date = result["min_date"][0]
        max_date = result["max_date"][0]

        if min_date is None or max_date is None:
            return None, None

        return min_date.isoformat(), max_date.isoformat()
    except Exception:
        return None, None


def get_uploaded_files() -> list[Path]:
    """Return a list of all uploaded files."""
    if not UPLOADS_DIR.exists():
        return []
    return [f for f in UPLOADS_DIR.iterdir() if f.is_file() and not f.name.startswith(".")]


def delete_file(filename: str) -> bool:
    """Delete a file from the uploads directory. Returns True if successful."""
    file_path = UPLOADS_DIR / filename
    if file_path.exists() and file_path.is_file():
        file_path.unlink()
        return True
    return False
