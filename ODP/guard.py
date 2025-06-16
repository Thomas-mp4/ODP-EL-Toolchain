# guard.py
from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class Guard:
    raw: str

    def evaluate(self, context: Dict[str, Any]) -> bool:
        try:
            return bool(eval(self.raw, context))
        except Exception as e:
            print(f"  - (Guard) Evaluation error in '{self.raw}': {e}")
            return False

    def __repr__(self):
        return f"Guard({self.raw!r})"
