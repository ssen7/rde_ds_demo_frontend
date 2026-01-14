import asyncio
import concurrent.futures
from pathlib import Path
from .file_handler import read_file
from .date_detector import detect_date_column, get_date_range
from .metadata import MetadataManager


def _process_file_sync(file_path: Path, specified_date_column: str | None = None) -> dict:
    """Synchronous file processing logic."""
    metadata_manager = MetadataManager()
    filename = file_path.name

    try:
        metadata_manager.update(filename, status="processing")

        # Read the file
        df = read_file(file_path)

        # Use specified date column or auto-detect
        user_specified = False
        if specified_date_column and specified_date_column in df.columns:
            date_column = specified_date_column
            user_specified = True
        else:
            date_column = detect_date_column(df)

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

        # Get date range
        earliest, latest = get_date_range(df, date_column)

        metadata_manager.update(
            filename,
            status="completed",
            date_column=date_column,
            earliest_date=earliest.isoformat() if earliest else None,
            latest_date=latest.isoformat() if latest else None,
            user_specified_date_column=user_specified
        )

        return {
            "status": "completed",
            "date_column": date_column,
            "earliest_date": earliest,
            "latest_date": latest
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
