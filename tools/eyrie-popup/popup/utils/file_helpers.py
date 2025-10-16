"""File helper utilities."""

from pathlib import Path
from typing import Optional


def find_file(seqrun_path: Path, directory: str, filename: str) -> Optional[str]:
    """
    Find a file based on directory and filename.
    
    Args:
        seqrun_path: Base sequencing run path
        directory: Directory name relative to seqrun_path
        filename: Name of the file to find
        
    Returns:
        Relative path to the file if found, None otherwise
    """
    file_path = seqrun_path / directory / filename
    if file_path.exists():
        return str(file_path.relative_to(seqrun_path))
    return None
