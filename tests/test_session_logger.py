import json
from datetime import datetime
from unittest.mock import patch

import session_logger as sl
from session_logger import SessionLogger


def test_log_creates_file(tmp_path):
    with patch.object(sl, "LOGS_DIR", tmp_path):
        logger = SessionLogger()
        logger.log(
            trigger="manual_hotkey",
            question="What does PROC MEANS do?",
            answer="Computes descriptive statistics",
            explanation="PROC MEANS calculates statistics like mean, std, min, max.",
        )
    files = list(tmp_path.glob("session_*.jsonl"))
    assert len(files) == 1


def test_log_record_structure(tmp_path):
    with patch.object(sl, "LOGS_DIR", tmp_path):
        logger = SessionLogger()
        logger.log(trigger="auto_change", question="Q", answer="A", explanation="E")
    record = json.loads(logger.path.read_text(encoding="utf-8").strip())
    assert record["trigger"] == "auto_change"
    assert record["question"] == "Q"
    assert record["answer"] == "A"
    assert record["explanation"] == "E"
    assert record["screenshot"] is None
    assert "timestamp" in record


def test_log_appends_multiple_records(tmp_path):
    with patch.object(sl, "LOGS_DIR", tmp_path):
        logger = SessionLogger()
        for i in range(3):
            logger.log(trigger="manual_hotkey", question=f"Q{i}", answer=f"A{i}", explanation=f"E{i}")
    lines = logger.path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 3


def test_log_filename_is_todays_date(tmp_path):
    with patch.object(sl, "LOGS_DIR", tmp_path):
        logger = SessionLogger()
    expected = datetime.now().strftime("session_%Y-%m-%d.jsonl")
    assert logger.path.name == expected
