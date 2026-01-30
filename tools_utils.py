from typing import Optional
from functools import lru_cache
from seedir.folderstructure import listdir_fullpath
import pathlib
import seedir as sd

@lru_cache(maxsize=20)
def get_directory_diag(directory: str, depth: Optional[int] = 3):
    """Creates a directory diagnostic using seedir."""
    excluded_patterns = get_excluded_patterns()
    diag_string = sd.seedir(
        directory,
        style="lines",
        depthlimit=depth,
        exclude_list=excluded_patterns,
    )
    return diag_string

def get_excluded_patterns(gitignore_name: str = ".gitignore") -> list:
    """
    Reads patterns from .gitignore and adds common system exclusions.
    """
    gitignore_path = pathlib.Path(gitignore_name)
    exclude_list = {".git", "__pycache__", ".venv", ".DS_Store"}

    if gitignore_path.exists():
        try:
            with gitignore_path.open("r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#") or line.startswith("!"):
                        continue
                    pattern = line.rstrip("/")
                    exclude_list.add(pattern)
        except (PermissionError, IOError):
            pass

    return list(exclude_list)
