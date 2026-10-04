import hashlib
from pathlib import Path


def calculate_file_hash(
    file_path: Path,
    chunk_size: int = 1024 * 1024,
) -> str:
    """Calculate the SHA-256 hash of a file."""

    sha256 = hashlib.sha256()

    with file_path.open("rb") as file:
        while chunk := file.read(chunk_size):
            sha256.update(chunk)

    return sha256.hexdigest()


def save_file(
    content: bytes,
    output_path: Path,
) -> Path:
    """Save binary content to a file."""

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path.write_bytes(content)

    return output_path