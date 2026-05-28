from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)
class ActiveModel:
    name: str
    path: Path
    classes: tuple[str, ...] = ()
    promoted_at: str = ""
    source: str = ""
