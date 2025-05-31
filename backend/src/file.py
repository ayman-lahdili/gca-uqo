from abc import ABC, abstractmethod
import io
import zipfile
from fastapi import UploadFile
from fastapi.responses import FileResponse, StreamingResponse
from pathlib import Path

import shutil


class StorageProvider(ABC):
    """Abstract base class for storage providers"""

    @abstractmethod
    def save_file(self, filename: str, upload: UploadFile) -> None:
        """Save content to a file at the specified path"""
        pass

    @abstractmethod
    def read_file(self, filename: str) -> FileResponse:
        """Read content from a file at the specified path"""
        pass

    @abstractmethod
    def delete_file(self, filename: str) -> None:
        """Delete a file at the specified path"""
        pass

    @abstractmethod
    def file_exists(self, filename: str) -> bool:
        """Check if a file exists at the specified path"""
        pass

    @abstractmethod
    def zip_files(self, zip_file_name: str, filenames: list[str]) -> StreamingResponse:
        """Create a zip file from a list of filenames"""
        pass


class LocalStorageProvider(StorageProvider):
    def __init__(self, base_directory: str) -> None:
        self.base_directory: Path = Path(base_directory)
        Path(self.base_directory).mkdir(parents=True, exist_ok=True)

    def save_file(self, filename: str, upload: UploadFile) -> None:
        file_path = self.base_directory / filename

        with file_path.open("wb") as buffer:
            shutil.copyfileobj(upload.file, buffer)

    def read_file(self, filename: str) -> FileResponse:
        found_files = list(self.base_directory.glob(filename))

        if not found_files:
            raise FileNotFoundError(f"File not found: {filename}")

        return FileResponse(
            path=found_files[0],
            filename=filename,
            media_type="application/octet-stream",
        )

    def delete_file(self, filename: str) -> None:
        found_files = list(self.base_directory.glob(filename))
        if not found_files:
            return

        for file_path in found_files:
            file_path.unlink()  # Delete the file

    def file_exists(self, filename: str) -> bool:
        found_files = list(self.base_directory.glob(filename))
        return len(found_files) > 0

    def zip_files(self, zip_file_name: str, filenames: list[str]) -> StreamingResponse:
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for file_name in filenames:
                found_files = list(self.base_directory.glob(file_name))

                if not found_files:
                    # Skip students with no resume file, or optionally raise an error
                    continue

                resume_path = found_files[0]
                zip_file.write(resume_path, arcname=resume_path.name)
        zip_buffer.seek(0)

        return StreamingResponse(
            zip_buffer,
            media_type="application/zip",
            headers={
                "Content-Disposition": f"attachment; filename={zip_file_name}.zip"
            },
        )
