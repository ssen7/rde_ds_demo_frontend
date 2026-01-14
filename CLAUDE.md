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
```

## Architecture

- `app.py` - Main Streamlit UI with file upload, preview, and metadata display
- `utils/file_handler.py` - File storage (saves to `uploads/`) and reading (CSV/Excel via pandas)
- `utils/date_detector.py` - Heuristic date column detection (80% parse threshold) and date range extraction
- `utils/metadata.py` - JSON-based metadata storage (`uploads/.metadata.json`) using dataclasses; status transitions: pending → processing → completed/error
- `utils/async_processor.py` - Background thread processing that updates metadata when complete

## Data Flow

1. User uploads file → saved to `uploads/` → metadata created with "pending" status
2. Background thread starts → reads file → detects date column → extracts min/max dates
3. Metadata updated to "completed" with date info → UI auto-refreshes via `st.rerun()` while pending
