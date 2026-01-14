import asyncio
import concurrent.futures
from pathlib import Path
from .file_handler import read_file
from .date_detector import detect_date_column, get_date_range
from .metadata import MetadataManager


def _process_file_sync(file_path: Path) -> dict:
    """Synchronous file processing logic."""
    metadata_manager = MetadataManager()
    filename = file_path.name

    try:
        metadata_manager.update(filename, status="processing")

        # Read the file
        df = read_file(file_path)

        # Detect date column
        date_column = detect_date_column(df)

        if date_column is None:
            metadata_manager.update(
                filename,
                status="completed",
                date_column=None,
                earliest_date=None,
                latest_date=None
            )
            return {"status": "completed", "date_column": None}

        # Get date range
        earliest, latest = get_date_range(df, date_column)

        metadata_manager.update(
            filename,
            status="completed",
            date_column=date_column,
            earliest_date=earliest.isoformat() if earliest else None,
            latest_date=latest.isoformat() if latest else None
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


async def process_file_async(file_path: Path) -> dict:
    """Process a file asynchronously to detect dates and update metadata."""
    loop = asyncio.get_event_loop()
    with concurrent.futures.ThreadPoolExecutor() as executor:
        result = await loop.run_in_executor(executor, _process_file_sync, file_path)
    return result


def start_background_processing(file_path: Path) -> None:
    """Start background processing of a file (for use in Streamlit)."""
    import threading

    def run():
        asyncio.run(process_file_async(file_path))

    thread = threading.Thread(target=run, daemon=True)
    thread.start()
