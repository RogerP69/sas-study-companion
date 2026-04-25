import json
from datetime import datetime
from pathlib import Path

LOGS_DIR = Path(__file__).parent.parent / "logs"


class SessionLogger:
    def __init__(self):
        LOGS_DIR.mkdir(exist_ok=True)
        date_str = datetime.now().strftime("%Y-%m-%d")
        self._path = LOGS_DIR / f"session_{date_str}.jsonl"

    def log(
        self,
        trigger: str,
        question: str,
        answer: str,
        explanation: str,
        screenshot: str | None = None,
    ) -> None:
        record = {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "trigger": trigger,
            "question": question,
            "answer": answer,
            "explanation": explanation,
            "screenshot": screenshot,
        }
        with self._path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")

    @property
    def path(self) -> Path:
        return self._path
