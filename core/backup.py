import shutil
from datetime import datetime, timedelta
from pathlib import Path
from core.db import DB_PATH, APP_DIR
import logging

log = logging.getLogger("backup")

def run_backup():
    backups = APP_DIR / "backups"
    backups.mkdir(parents=True, exist_ok=True)

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dst = backups / f"data_{stamp}.sqlite3"
    shutil.copy2(DB_PATH, dst)
    log.info("Backup created: %s", dst)

    cutoff = datetime.now() - timedelta(days=7)
    for p in backups.glob("data_*.sqlite3"):
        try:
            if datetime.fromtimestamp(p.stat().st_mtime) < cutoff:
                p.unlink(missing_ok=True)
        except Exception:
            pass
