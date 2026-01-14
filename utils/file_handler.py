import os
from pathlib import Path
import pandas as pd
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
    """Read a CSV or Excel file efficiently into a DataFrame."""
    suffix = file_path.suffix.lower()
    if suffix == ".csv":
        return pd.read_csv(file_path, nrows=nrows)
    elif suffix in (".xlsx", ".xls"):
        return pd.read_excel(file_path, nrows=nrows)
    else:
        raise ValueError(f"Unsupported file type: {suffix}")


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
