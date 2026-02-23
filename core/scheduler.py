import logging
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo
from apscheduler.schedulers.background import BackgroundScheduler

from core.db import Database
from core.monitor import run_check_for_link
from core.timezone_map import tz_for_region
from core.backup import run_backup

log = logging.getLogger("scheduler")

def _within_window(local_dt: datetime, start_h=1, end_h=5) -> bool:
    t = local_dt.time()
    return time(start_h, 0) <= t < time(end_h, 0)

class SchedulerService:
    def __init__(self, db: Database):
        self.db = db
        self.sched = BackgroundScheduler()
        self.running = False

    def start(self):
        if self.running:
            return
        self.sched.add_job(self.tick, "interval", minutes=10, id="tick")
        self.sched.add_job(run_backup, "interval", hours=24, id="backup")
        self.sched.start()
        self.running = True
        log.info("Scheduler started")

    def stop(self):
        if not self.running:
            return
        self.sched.shutdown(wait=False)
        self.running = False
        log.info("Scheduler stopped")

    def tick(self):
        rows = self.db.query("SELECT * FROM links")
        now_utc = datetime.utcnow().replace(tzinfo=ZoneInfo("UTC"))

        for link in rows:
            last_ok = link["last_ok_at"]
            last_ok_dt = None
            if last_ok:
                try:
                    last_ok_dt = datetime.fromisoformat(last_ok).replace(tzinfo=ZoneInfo("UTC"))
                except Exception:
                    last_ok_dt = None

            tz = link["tz_override"] or tz_for_region(link["region"])
            try:
                local_now = now_utc.astimezone(ZoneInfo(tz))
            except Exception:
                local_now = now_utc.astimezone(ZoneInfo("Europe/Moscow"))
                tz = "Europe/Moscow"

            if not _within_window(local_now, 1, 5):
                continue

            if last_ok_dt:
                last_local = last_ok_dt.astimezone(ZoneInfo(tz)).date()
                if last_local == local_now.date():
                    continue

            if link["consecutive_failures"] > 0 and link["consecutive_failures"] < 3:
                last_check = link["last_check_at"]
                if last_check:
                    try:
                        last_check_dt = datetime.fromisoformat(last_check).replace(tzinfo=ZoneInfo("UTC"))
                        if now_utc - last_check_dt < timedelta(minutes=30):
                            continue
                    except Exception:
                        pass

            log.info("Running check for link_id=%s tz=%s local=%s", link["id"], tz, local_now.isoformat())
            run_check_for_link(self.db, link["id"])
