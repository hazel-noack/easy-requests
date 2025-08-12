from typing import Iterable
import os
from pathlib import Path


def get_cache_dirs() -> Iterable[Path]:   
    for element in Path(os.getcwd()).iterdir():
        if not element.is_dir:
            continue

        if not (element / "cache_metadata.db").exists():
            continue

        print("found cache dir:", element)
        yield element