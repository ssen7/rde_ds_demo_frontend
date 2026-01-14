import asyncio
import concurrent.futures
from pathlib import Path
from .file_handler import read_file, get_date_range_lazy, get_column_names
from .date_detector import detect_date_column, get_date_range
from .metadata import MetadataManager

# Sample size for date column detection (no need to read entire file)
DETECTION_SAMPLE_SIZE = 1000


def _process_file_sync(file_path: Path, specified_date_column: str | None = None) -> dict:
    """Synchronous file processing logic.

    Uses efficient strategies for large files:
    - Only reads a sample for date column detection
    - Uses lazy evaluation (streaming) for date range on CSV files
    """
    metadata_manager = MetadataManager()
    filename = file_path.name
    is_csv = file_path.suffix.lower() == ".csv"

    try:
        metadata_manager.update(filename, status="processing")

        # Use specified date column or auto-detect
        user_specified = False
        if specified_date_column:
            # Verify column exists without loading full file
            columns = get_column_names(file_path)
            if specified_date_column in columns:
                date_column = specified_date_column
                user_specified = True
            else:
                # Fall back to detection if specified column doesn't exist
                df_sample = read_file(file_path, nrows=DETECTION_SAMPLE_SIZE)
                date_column = detect_date_column(df_sample)
        else:
            # Read only a sample for detection (not the full file)
            df_sample = read_file(file_path, nrows=DETECTION_SAMPLE_SIZE)
            date_column = detect_date_column(df_sample)

        if date_column is None:
            metadata_manager.update(
                filename,
                status="completed",
                date_column=None,
                earliest_date=None,
                latest_date=None,
                user_specified_date_column=False
            )
            return {"status": "completed", "date_column": None}

        # Get date range - use lazy evaluation for CSV (memory efficient)
        if is_csv:
            earliest_str, latest_str = get_date_range_lazy(file_path, date_column)
        else:
            # For Excel, read full file (no lazy support)
            df = read_file(file_path)
            earliest, latest = get_date_range(df, date_column)
            earliest_str = earliest.isoformat() if earliest else None
            latest_str = latest.isoformat() if latest else None

        metadata_manager.update(
            filename,
            status="completed",
            date_column=date_column,
            earliest_date=earliest_str,
            latest_date=latest_str,
            user_specified_date_column=user_specified
        )

        return {
            "status": "completed",
            "date_column": date_column,
            "earliest_date": earliest_str,
            "latest_date": latest_str
        }

    except Exception as e:
        metadata_manager.update(filename, status="error", error_message=str(e))
        return {"status": "error", "error": str(e)}


async def process_file_async(file_path: Path, specified_date_column: str | None = None) -> dict:
    """Process a file asynchronously to detect dates and update metadata."""
    loop = asyncio.get_event_loop()
    with concurrent.futures.ThreadPoolExecutor() as executor:
        result = await loop.run_in_executor(
            executor, _process_file_sync, file_path, specified_date_column
        )
    return result


def start_background_processing(file_path: Path, specified_date_column: str | None = None) -> None:
    """Start background processing of a file (for use in Streamlit)."""
    import threading

    def run():
        asyncio.run(process_file_async(file_path, specified_date_column))

    thread = threading.Thread(target=run, daemon=True)
    thread.start()


def reprocess_with_date_column(file_path: Path, date_column: str) -> None:
    """Reprocess a file with a user-specified date column."""
    start_background_processing(file_path, date_column)
