import streamlit as st
import time
from pathlib import Path

from utils.file_handler import save_uploaded_file, read_file, get_uploaded_files, delete_file, UPLOADS_DIR
from utils.metadata import MetadataManager
from utils.async_processor import start_background_processing, reprocess_with_date_column

st.set_page_config(page_title="File Upload Demo", page_icon="📁", layout="wide")

st.title("📁 File Upload & Date Analysis")
st.markdown("Upload CSV or Excel files to automatically detect date ranges.")


def main():
    metadata_manager = MetadataManager()

    # File upload section
    st.header("Upload File")

    # Option to pre-specify date column
    pre_specified_date_col = st.text_input(
        "Date column name (optional)",
        value="",
        help="Optionally specify the exact name of the date column before uploading. Leave empty for auto-detection."
    )

    uploaded_file = st.file_uploader(
        "Choose a CSV or Excel file",
        type=["csv", "xlsx", "xls"],
        help="Upload a file to analyze its date columns"
    )

    if uploaded_file is not None:
        # Check if this is a new upload
        if "last_uploaded" not in st.session_state or st.session_state.last_uploaded != uploaded_file.name:
            # Save the file
            file_path = save_uploaded_file(uploaded_file)

            # Create metadata entry
            metadata_manager.create(uploaded_file.name, uploaded_file.size)

            # Start async processing with optional pre-specified date column
            specified_col = pre_specified_date_col.strip() if pre_specified_date_col else None
            start_background_processing(file_path, specified_col)

            st.session_state.last_uploaded = uploaded_file.name
            st.success(f"✅ File '{uploaded_file.name}' uploaded successfully! Processing started...")

    st.divider()

    # Display uploaded files and their metadata
    st.header("Uploaded Files")

    uploaded_files = get_uploaded_files()

    if not uploaded_files:
        st.info("No files uploaded yet. Upload a file above to get started.")
        return

    # Auto-refresh while processing
    all_metadata = metadata_manager.get_all()
    has_pending = any(m.status in ("pending", "processing") for m in all_metadata.values())

    for file_path in sorted(uploaded_files, key=lambda p: p.stat().st_mtime, reverse=True):
        filename = file_path.name
        metadata = metadata_manager.get(filename)

        with st.expander(f"📄 {filename}", expanded=True):
            col1, col2 = st.columns([2, 1])

            with col1:
                # Display file preview
                st.subheader("File Preview")
                try:
                    df = read_file(file_path, nrows=100)
                    # Convert object columns to string to avoid Arrow serialization issues
                    for col in df.columns:
                        if df[col].dtype == "object":
                            df[col] = df[col].astype(str)
                    st.dataframe(df, height=300)
                except Exception as e:
                    st.error(f"Error reading file: {e}")

            with col2:
                # Display metadata
                st.subheader("Metadata")

                if metadata:
                    # Status indicator
                    status = metadata.status
                    if status == "pending":
                        st.warning("⏳ Status: Pending")
                    elif status == "processing":
                        st.info("🔄 Status: Processing...")
                    elif status == "completed":
                        st.success("✅ Status: Completed")
                    elif status == "error":
                        st.error(f"❌ Status: Error - {metadata.error_message}")

                    st.markdown(f"**Upload Time:** {metadata.upload_time[:19].replace('T', ' ')}")
                    st.markdown(f"**File Size:** {metadata.file_size:,} bytes")

                    if status == "completed":
                        if metadata.date_column:
                            col_label = f"`{metadata.date_column}`"
                            if metadata.user_specified_date_column:
                                col_label += " (user specified)"
                            else:
                                col_label += " (auto-detected)"
                            st.markdown(f"**Date Column:** {col_label}")
                            if metadata.earliest_date:
                                st.markdown(f"**Earliest Date:** {metadata.earliest_date[:10]}")
                            if metadata.latest_date:
                                st.markdown(f"**Latest Date:** {metadata.latest_date[:10]}")
                        else:
                            st.info("No date column detected in this file.")

                        # Allow changing the date column
                        st.markdown("---")
                        st.markdown("**Change Date Column**")
                        try:
                            df_cols = read_file(file_path, nrows=1)
                            columns = ["(None - no date column)"] + list(df_cols.columns)
                            current_idx = 0
                            if metadata.date_column and metadata.date_column in df_cols.columns:
                                current_idx = columns.index(metadata.date_column)

                            new_date_col = st.selectbox(
                                "Select date column",
                                columns,
                                index=current_idx,
                                key=f"date_col_{filename}",
                                help="Choose a different column to use as the date field"
                            )

                            if st.button("Apply", key=f"apply_date_{filename}"):
                                if new_date_col == "(None - no date column)":
                                    # Update metadata to have no date column
                                    metadata_manager.update(
                                        filename,
                                        date_column=None,
                                        earliest_date=None,
                                        latest_date=None,
                                        user_specified_date_column=True
                                    )
                                    st.rerun()
                                elif new_date_col != metadata.date_column:
                                    # Reprocess with the new date column
                                    metadata_manager.update(filename, status="processing")
                                    reprocess_with_date_column(file_path, new_date_col)
                                    st.rerun()
                        except Exception as e:
                            st.error(f"Error loading columns: {e}")
                else:
                    st.warning("No metadata found for this file.")

                # Delete button
                if st.button("🗑️ Delete", key=f"delete_{filename}"):
                    try:
                        delete_file(filename)
                        metadata_manager.delete(filename)
                        if st.session_state.get("last_uploaded") == filename:
                            del st.session_state.last_uploaded
                        st.session_state["just_deleted"] = True
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error deleting file: {e}")

    # Auto-refresh if there are pending files (skip if we just deleted)
    if has_pending and not st.session_state.get("just_deleted"):
        time.sleep(1)
        st.rerun()

    # Clear the deletion flag
    if st.session_state.get("just_deleted"):
        st.session_state["just_deleted"] = False


if __name__ == "__main__":
    main()
