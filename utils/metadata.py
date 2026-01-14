import json
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import Optional

METADATA_FILE = Path(__file__).parent.parent / "uploads" / ".metadata.json"


@dataclass
class FileMetadata:
    filename: str
    upload_time: str
    file_size: int
    status: str  # "pending", "processing", "completed", "error"
    date_column: Optional[str] = None
    earliest_date: Optional[str] = None
    latest_date: Optional[str] = None
    error_message: Optional[str] = None


class MetadataManager:
    """Manage metadata for uploaded files."""

    def __init__(self):
        self.metadata_file = METADATA_FILE

    def _load(self) -> dict[str, dict]:
        if not self.metadata_file.exists():
            return {}
        try:
            with open(self.metadata_file, "r") as f:
                content = f.read()
                if not content.strip():
                    return {}
                return json.loads(content)
        except json.JSONDecodeError:
            return {}

    def _save(self, data: dict[str, dict]) -> None:
        self.metadata_file.parent.mkdir(exist_ok=True)
        with open(self.metadata_file, "w") as f:
            json.dump(data, f, indent=2)

    def create(self, filename: str, file_size: int) -> FileMetadata:
        """Create initial metadata for a newly uploaded file."""
        metadata = FileMetadata(
            filename=filename,
            upload_time=datetime.now().isoformat(),
            file_size=file_size,
            status="pending"
        )
        data = self._load()
        data[filename] = asdict(metadata)
        self._save(data)
        return metadata

    def update(self, filename: str, **kwargs) -> FileMetadata | None:
        """Update metadata for a file."""
        data = self._load()
        if filename not in data:
            return None
        data[filename].update(kwargs)
        self._save(data)
        return FileMetadata(**data[filename])

    def get(self, filename: str) -> FileMetadata | None:
        """Get metadata for a specific file."""
        data = self._load()
        if filename not in data:
            return None
        return FileMetadata(**data[filename])

    def get_all(self) -> dict[str, FileMetadata]:
        """Get metadata for all files."""
        data = self._load()
        return {k: FileMetadata(**v) for k, v in data.items()}

    def delete(self, filename: str) -> bool:
        """Delete metadata for a file."""
        data = self._load()
        if filename not in data:
            return False
        del data[filename]
        self._save(data)
        return True
