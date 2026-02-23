import sys
from PySide6.QtWidgets import QApplication
from core.db import Database
from core.scheduler import SchedulerService
from core.log import setup_logging
from ui.main_window import MainWindow

def main():
    setup_logging()
    app = QApplication(sys.argv)

    db = Database()
    db.init()

    scheduler = SchedulerService(db)
    scheduler.start()

    w = MainWindow(db, scheduler)
    w.resize(1200, 700)
    w.show()

    rc = app.exec()
    scheduler.stop()
    sys.exit(rc)

if __name__ == "__main__":
    main()
