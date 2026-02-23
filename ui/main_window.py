from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTableWidget, QTableWidgetItem, QMessageBox
)
from core.db import Database
from ui.dialogs import LinkDialog, SmtpDialog, HistoryDialog, ScheduleDialog

COLS = ["Ссылка", "Истец", "Ответчик", "Суд", "Номер дела", "Комментарий", "Субъект РФ", "TZ", "Статус"]

class MainWindow(QMainWindow):
    def __init__(self, db: Database, scheduler):
        super().__init__()
        self.db = db
        self.scheduler = scheduler
        self.setWindowTitle("GAS Monitor (MVP 0.2)")

        root = QWidget()
        self.setCentralWidget(root)

        layout = QVBoxLayout(root)
        top = QHBoxLayout()

        btn_add = QPushButton("Добавить")
        btn_edit = QPushButton("Редактировать")
        btn_del = QPushButton("Удалить")
        btn_hist = QPushButton("История изменений")
        btn_smtp = QPushButton("SMTP")
        btn_sched = QPushButton("Расписание")
        btn_refresh = QPushButton("Обновить")

        btn_add.clicked.connect(self.add_link)
        btn_edit.clicked.connect(self.edit_link)
        btn_del.clicked.connect(self.delete_link)
        btn_hist.clicked.connect(self.open_history)
        btn_smtp.clicked.connect(self.open_smtp)
        btn_sched.clicked.connect(self.open_schedule)
        btn_refresh.clicked.connect(self.refresh)

        for b in [btn_add, btn_edit, btn_del, btn_hist, btn_smtp, btn_sched, btn_refresh]:
            top.addWidget(b)
        top.addStretch(1)

        self.table = QTableWidget(0, len(COLS))
        self.table.setHorizontalHeaderLabels(COLS)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)

        layout.addLayout(top)
        layout.addWidget(self.table)

        self.refresh()

    def refresh(self):
        rows = self.db.query("SELECT * FROM links ORDER BY updated_at DESC")
        self.table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            vals = [
                r["url"], r["plaintiff"], r["defendant"], r["court"],
                r["case_number"], r["comment"], r["region"],
                r["tz_override"] or "", r["status"]
            ]
            for j, v in enumerate(vals):
                it = QTableWidgetItem(str(v))
                if j == 8:
                    if v == "problem":
                        it.setBackground(Qt.red)
                    elif v == "error":
                        it.setBackground(Qt.yellow)
                self.table.setItem(i, j, it)
        self.table.resizeColumnsToContents()

    def _selected_link_id(self):
        sel = self.table.selectionModel().selectedRows()
        if not sel:
            return None
        row = sel[0].row()
        url = self.table.item(row, 0).text()
        r = self.db.query_one("SELECT id FROM links WHERE url=? ORDER BY id DESC", (url,))
        return r["id"] if r else None

    def add_link(self):
        dlg = LinkDialog(self)
        if dlg.exec():
            data = dlg.get_data()
            self.db.execute("""
                INSERT INTO links(url, plaintiff, defendant, court, case_number, comment, region, tz_override)
                VALUES(?,?,?,?,?,?,?,?)
            """, (
                data["url"], data["plaintiff"], data["defendant"], data["court"],
                data["case_number"], data["comment"], data["region"], data["tz_override"] or None
            ))
            self.refresh()

    def edit_link(self):
        link_id = self._selected_link_id()
        if not link_id:
            QMessageBox.information(self, "Выбор", "Выберите строку в таблице.")
            return
        r = self.db.query_one("SELECT * FROM links WHERE id=?", (link_id,))
        dlg = LinkDialog(self, initial=dict(r))
        if dlg.exec():
            data = dlg.get_data()
            self.db.execute("""
                UPDATE links SET url=?, plaintiff=?, defendant=?, court=?, case_number=?, comment=?, region=?, tz_override=?,
                updated_at=datetime('now')
                WHERE id=?
            """, (
                data["url"], data["plaintiff"], data["defendant"], data["court"],
                data["case_number"], data["comment"], data["region"], data["tz_override"] or None, link_id
            ))
            self.refresh()

    def delete_link(self):
        link_id = self._selected_link_id()
        if not link_id:
            QMessageBox.information(self, "Выбор", "Выберите строку в таблице.")
            return
        if QMessageBox.question(self, "Удаление", "Удалить выбранную ссылку?") == QMessageBox.Yes:
            self.db.execute("DELETE FROM links WHERE id=?", (link_id,))
            self.refresh()

    def open_history(self):
        HistoryDialog(self.db, self).exec()

    def open_smtp(self):
        SmtpDialog(self.db, self).exec()

    def open_schedule(self):
        ScheduleDialog(self.db, self).exec()
