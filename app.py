import streamlit as st
import time
from pathlib import Path

from utils.file_handler import save_uploaded_file, read_file, get_uploaded_files, delete_file
from utils.metadata import MetadataManager
from utils.async_processor import start_background_processing

st.set_page_config(page_title="File Upload Demo", page_icon="📁", layout="wide")

st.title("📁 File Upload & Date Analysis")
st.markdown("Upload CSV or Excel files to automatically detect date ranges.")


def main():
    metadata_manager = MetadataManager()

    # File upload section
    st.header("Upload File")
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

            # Start async processing
            start_background_processing(file_path)

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
                            st.markdown(f"**Date Column:** `{metadata.date_column}`")
                            if metadata.earliest_date:
                                st.markdown(f"**Earliest Date:** {metadata.earliest_date[:10]}")
                            if metadata.latest_date:
                                st.markdown(f"**Latest Date:** {metadata.latest_date[:10]}")
                        else:
                            st.info("No date column detected in this file.")
                else:
                    st.warning("No metadata found for this file.")

                # Delete button
                if st.button("🗑️ Delete", key=f"delete_{filename}"):
                    delete_file(filename)
                    metadata_manager.delete(filename)
                    if st.session_state.get("last_uploaded") == filename:
                        del st.session_state.last_uploaded
                    st.rerun()

    # Auto-refresh if there are pending files
    if has_pending:
        time.sleep(1)
        st.rerun()


if __name__ == "__main__":
    main()
