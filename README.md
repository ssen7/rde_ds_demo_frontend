# File Upload & Date Analysis Demo

A Streamlit web application for uploading CSV and Excel files with automatic date column detection and analysis.

**This application was built with [Claude Code](https://claude.ai/code) for demonstration purposes.**

## Features

- Upload CSV and Excel files (.csv, .xlsx, .xls)
- Automatic date column detection using heuristic parsing
- Manual date column specification (before or after upload)
- Date range extraction (earliest and latest dates)
- **Date harmonization** - Convert all date columns to ISO 8601 format (YYYY-MM-DD)
- File preview with data table display
- Async background processing for responsive UI
- Persistent metadata storage

### Supported Date Formats

The date harmonizer automatically detects and converts these formats:
- ISO: `2024-01-15`, `2024/01/15`
- US: `01/15/2024`, `01-15-2024`
- EU: `15/01/2024`, `15-01-2024`
- Compact: `20240115`
- Text: `January 15, 2024`, `Jan 15, 2024`, `15 January 2024`

## Usage

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the application:
   ```bash
   streamlit run app.py
   ```

3. Open http://localhost:8501 in your browser

## How It Works

1. **Upload a file** - Drag and drop or browse for a CSV/Excel file
2. **Optionally specify a date column** - Enter the column name before uploading, or select from a dropdown after
3. **View results** - The app automatically detects date columns and displays the date range
4. **Change date column** - Use the dropdown selector to pick a different date column if needed
5. **Harmonize dates** - Click "Harmonize Dates" to convert all date columns to ISO 8601 format, then download the result

## Architecture

- `app.py` - Main Streamlit UI
- `utils/file_handler.py` - File storage and reading
- `utils/date_detector.py` - Date column detection and range extraction
- `utils/date_harmonizer.py` - Date format harmonization to ISO 8601
- `utils/metadata.py` - JSON-based metadata storage
- `utils/async_processor.py` - Background processing