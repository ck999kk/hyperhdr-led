from pathlib import Path
import json
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent
LOG_DIR = BASE_DIR / "logs"
SYSTEM_LOG = LOG_DIR / "system.log"
FEEDBACK_LOG = LOG_DIR / "feedback_log.json"


def _ensure_logs():
    LOG_DIR.mkdir(exist_ok=True)
    if not SYSTEM_LOG.exists():
        SYSTEM_LOG.touch()
    if not FEEDBACK_LOG.exists():
        with FEEDBACK_LOG.open("w") as f:
            json.dump([], f)


def _log(message: str) -> None:
    _ensure_logs()
    timestamp = datetime.now().isoformat()
    with SYSTEM_LOG.open("a") as f:
        f.write(f"{timestamp} - {message}\n")


def run_all_checks() -> None:
    """Run basic code checks across all Python files."""
    _ensure_logs()
    py_files = list(BASE_DIR.rglob("*.py"))
    for pyfile in py_files:
        try:
            text = pyfile.read_text()
        except Exception as exc:
            _log(f"ERROR reading {pyfile}: {exc}")
            continue
        has_try = "try:" in text and "except" in text
        has_return = "return" in text
        logs_system = "system.log" in text
        uses_config = "config.json" in text or "secrets.json" in text
        result = (
            f"FILE {pyfile}: try/except={has_try}, return={has_return}, "
            f"logging={logs_system}, config_use={uses_config}"
        )
        _log(result)
    _log("All checks completed")


def simulate_failure_log() -> None:
    """Append a dummy error entry to feedback_log.json."""
    _ensure_logs()
    try:
        with FEEDBACK_LOG.open("r") as f:
            data = json.load(f)
    except Exception:
        data = []
    data.append({"timestamp": datetime.now().isoformat(), "error": "Dummy error"})
    with FEEDBACK_LOG.open("w") as f:
        json.dump(data, f, indent=2)
    _log("Simulated failure logged")
