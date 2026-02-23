from PySide6.QtWidgets import (
    QDialog, QFormLayout, QLineEdit, QTextEdit, QDialogButtonBox,
    QMessageBox, QTableWidget, QTableWidgetItem, QVBoxLayout, QCheckBox
)
from core.util import validate_url
from core.mailer import save_smtp_secret
from core.db import Database

class LinkDialog(QDialog):
    def __init__(self, parent=None, initial=None):
        super().__init__(parent)
        self.setWindowTitle("Ссылка на дело")
        self.initial = initial or {}

        form = QFormLayout(self)
        self.ed_url = QLineEdit(self.initial.get("url", ""))
        self.ed_pl = QLineEdit(self.initial.get("plaintiff", ""))
        self.ed_df = QLineEdit(self.initial.get("defendant", ""))
        self.ed_court = QLineEdit(self.initial.get("court", ""))
        self.ed_num = QLineEdit(self.initial.get("case_number", ""))
        self.ed_region = QLineEdit(self.initial.get("region", ""))
        self.ed_tz = QLineEdit(self.initial.get("tz_override", "") or "")
        self.ed_comment = QTextEdit(self.initial.get("comment", ""))

        form.addRow("Ссылка", self.ed_url)
        form.addRow("Истец", self.ed_pl)
        form.addRow("Ответчик", self.ed_df)
        form.addRow("Суд", self.ed_court)
        form.addRow("Номер дела", self.ed_num)
        form.addRow("Комментарий", self.ed_comment)
        form.addRow("Субъект РФ", self.ed_region)
        form.addRow("Timezone override (опц.)", self.ed_tz)

        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        form.addRow(btns)

    def get_data(self):
        return {
            "url": self.ed_url.text().strip(),
            "plaintiff": self.ed_pl.text().strip(),
            "defendant": self.ed_df.text().strip(),
            "court": self.ed_court.text().strip(),
            "case_number": self.ed_num.text().strip(),
            "comment": self.ed_comment.toPlainText().strip(),
            "region": self.ed_region.text().strip(),
            "tz_override": self.ed_tz.text().strip() or None
        }

    def accept(self):
        d = self.get_data()
        try:
            d["url"] = validate_url(d["url"])
            for k in ["plaintiff","defendant","court","case_number","comment","region"]:
                if not d[k]:
                    raise ValueError(f"Поле '{k}' обязательно.")
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", str(e))
            return
        super().accept()

class SmtpDialog(QDialog):
    def __init__(self, db: Database, parent=None):
        super().__init__(parent)
        self.db = db
        self.setWindowTitle("Настройки SMTP")

        form = QFormLayout(self)
        self.host = QLineEdit(self._get("smtp.host"))
        self.port = QLineEdit(self._get("smtp.port") or "587")
        self.username = QLineEdit(self._get("smtp.username"))
        self.password = QLineEdit("")
        self.password.setEchoMode(QLineEdit.Password)
        self.use_tls = QCheckBox("STARTTLS")
        self.use_tls.setChecked((self._get("smtp.use_tls") or "1") == "1")
        self.sender = QLineEdit(self._get("smtp.sender"))
        self.recipient = QLineEdit(self._get("smtp.recipient"))

        form.addRow("SMTP host", self.host)
        form.addRow("SMTP port", self.port)
        form.addRow("Username", self.username)
        form.addRow("Password (сохранится в Windows Vault)", self.password)
        form.addRow("", self.use_tls)
        form.addRow("Sender email", self.sender)
        form.addRow("Recipient email", self.recipient)

        btns = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        btns.accepted.connect(self.save)
        btns.rejected.connect(self.reject)
        form.addRow(btns)

    def _get(self, key: str) -> str:
        r = self.db.query_one("SELECT value FROM settings WHERE key=?", (key,))
        return r["value"] if r else ""

    def _set(self, key: str, value: str):
        self.db.execute(
            "INSERT INTO settings(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (key, value)
        )

    def save(self):
        try:
            port = int(self.port.text().strip())
        except Exception:
            QMessageBox.warning(self, "Ошибка", "Port должен быть числом.")
            return

        self._set("smtp.host", self.host.text().strip())
        self._set("smtp.port", str(port))
        self._set("smtp.username", self.username.text().strip())
        self._set("smtp.use_tls", "1" if self.use_tls.isChecked() else "0")
        self._set("smtp.sender", self.sender.text().strip())
        self._set("smtp.recipient", self.recipient.text().strip())

        pwd = self.password.text()
        if pwd and self.username.text().strip():
            save_smtp_secret(self.username.text().strip(), pwd)

        QMessageBox.information(self, "OK", "Сохранено.")
        self.accept()

class HistoryDialog(QDialog):
    def __init__(self, db: Database, parent=None):
        super().__init__(parent)
        self.db = db
        self.setWindowTitle("История изменений")

        layout = QVBoxLayout(self)
        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(["Дата", "Суд", "Номер дела", "Истец", "Ответчик", "Описание"])
        layout.addWidget(self.table)

        self.load()

        btns = QDialogButtonBox(QDialogButtonBox.Close)
        btns.rejected.connect(self.reject)
        btns.accepted.connect(self.accept)
        layout.addWidget(btns)

    def load(self):
        rows = self.db.query("""
            SELECT c.detected_at, l.court, l.case_number, l.plaintiff, l.defendant, c.summary
            FROM changes c
            JOIN links l ON l.id=c.link_id
            ORDER BY c.detected_at DESC
            LIMIT 500
        """)
        self.table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            vals = [r["detected_at"], r["court"], r["case_number"], r["plaintiff"], r["defendant"], r["summary"]]
            for j, v in enumerate(vals):
                self.table.setItem(i, j, QTableWidgetItem(str(v)))
        self.table.resizeColumnsToContents()

class ScheduleDialog(QDialog):
    def __init__(self, db: Database, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Расписание проверок (MVP)")
        form = QFormLayout(self)

        info = QLineEdit("Проверка 01:00–05:00 локального времени суда; 1 раз/сутки/ссылка; ретраи каждые 30 минут; проблемная ссылка после 3 ошибок.")
        info.setReadOnly(True)
        form.addRow("Текущие правила", info)

        btns = QDialogButtonBox(QDialogButtonBox.Close)
        btns.rejected.connect(self.reject)
        btns.accepted.connect(self.accept)
        form.addRow(btns)
