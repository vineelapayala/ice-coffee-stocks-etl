import hashlib
from pathlib import Path


def calculate_file_hash(
    file_path: Path,
    chunk_size: int = 1024 * 1024,
) -> str:
    """
    Calculate the SHA-256 hash of a file.

    The file is read in chunks to avoid loading the
    entire file into memory.

    Args:
        file_path: Path to the file.
        chunk_size: Number of bytes to read per chunk.

    Returns:
        Hexadecimal SHA-256 hash of the file.
    """

    sha256 = hashlib.sha256()

    with file_path.open("rb") as file:
        while chunk := file.read(chunk_size):
            sha256.update(chunk)

    return sha256.hexdigest()