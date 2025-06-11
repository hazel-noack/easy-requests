from __future__ import annotations
from typing import Optional
import requests


class Connection:
    def __init__(self, session: Optional[requests.Session] = None) -> None:
        self.session = session if session is not None else requests.Session()
