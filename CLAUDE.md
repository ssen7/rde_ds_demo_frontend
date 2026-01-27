# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Streamlit web application for uploading CSV/Excel files with automatic date column detection. Files are stored locally in `uploads/`, and async processing determines date ranges which are stored as metadata.

## Development Setup

```bash
pip install -r requirements.txt
```

## Build Commands

```bash
# Run the application
streamlit run app.py

# Run on a specific port
streamlit run app.py --server.port 8501

# Generate test data (1M rows by default)
python scripts/generate_demo_csv.py -o demo_data.csv -n 1000000
```

## Architecture

- `app.py` - Main Streamlit UI with file upload, preview, and metadata display
- `utils/file_handler.py` - File storage (saves to `uploads/`) and reading; uses Polars for CSV (fast lazy evaluation) and pandas for Excel
- `utils/date_detector.py` - Heuristic date column detection (80% parse threshold) and date range extraction
- `utils/date_harmonizer.py` - Date format harmonization to ISO 8601; uses Polars for CSV (11 format patterns), pandas for Excel
- `utils/metadata.py` - JSON-based metadata storage (`uploads/.metadata.json`) using dataclasses; status transitions: pending → processing → completed/error
- `utils/async_processor.py` - Background thread processing that updates metadata when complete

## Data Flow

1. User uploads file → saved to `uploads/` → metadata created with "pending" status
2. Background thread starts → reads file → detects date column → extracts min/max dates
3. Metadata updated to "completed" with date info → UI auto-refreshes via `st.rerun()` while pending

## Key Implementation Details

- **Large file handling**: CSV files use Polars lazy evaluation (`scan_csv`) to compute date ranges without loading entire files into memory
- **Date detection sampling**: Only reads first 1000 rows (`DETECTION_SAMPLE_SIZE`) for auto-detecting date columns
- **Date harmonization**: On-demand (button-triggered) using Polars for CSV files (processes 100k rows in ~30ms), pandas for Excel; detects 11 common date formats and converts to ISO 8601 (YYYY-MM-DD); results cached in session state
- **Session state**: Uses `st.session_state.last_uploaded` to track uploads and prevent duplicate processing; `st.session_state.just_deleted` prevents auto-refresh race conditions after deletion; `st.session_state.harmonized_data_{filename}` caches harmonized CSV data
