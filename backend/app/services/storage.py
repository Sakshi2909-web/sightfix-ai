import os
import shutil
import uuid
from pathlib import Path
from typing import BinaryIO
from app.config import settings


class StorageService:
    def __init__(self, base_dir: Path | None = None):
        self.base_dir = base_dir or settings.storage_path
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def save_file(self, file_obj: BinaryIO | bytes, filename: str, subfolder: str = "attachments") -> str:
        folder = self.base_dir / subfolder
        folder.mkdir(parents=True, exist_ok=True)

        ext = Path(filename).suffix
        unique_name = f"{uuid.uuid4()}{ext}"
        target_path = folder / unique_name

        if isinstance(file_obj, bytes):
            with open(target_path, "wb") as f:
                f.write(file_obj)
        else:
            with open(target_path, "wb") as f:
                shutil.copyfileobj(file_obj, f)

        # Return relative or normalized storage path
        return str(target_path.resolve())

    def read_file(self, storage_path: str) -> bytes:
        p = Path(storage_path)
        if not p.exists():
            raise FileNotFoundError(f"Storage file not found: {storage_path}")
        return p.read_bytes()

    def delete_file(self, storage_path: str) -> None:
        p = Path(storage_path)
        if p.exists():
            p.unlink()


storage_service = StorageService()
