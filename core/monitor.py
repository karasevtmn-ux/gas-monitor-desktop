import json
import logging
import hashlib
from datetime import datetime
from typing import Any, Dict, Tuple, List

from core.db import Database
from core.parsers import parse_case
from core.mailer import send_email, load_smtp_secret

log = logging.getLogger("monitor")

def _hash(s: str) -> str:
    return hashlib.sha256((s or "").encode("utf-8")).hexdigest()

def _diff_snap(old: Dict[str, Any], new: Dict[str, Any]) -> Tuple[bool, List[Tuple[str,str]]]:
    changes: List[Tuple[str,str]] = []
    if old.get("tabs") != new.get("tabs"):
        changes.append(("tabs_changed", "Изменился набор/порядок вкладок карточки"))
    old_hash = _hash(old.get("page_text_hash_basis", ""))
    new_hash = _hash(new.get("page_text_hash_basis", ""))
    if old_hash != new_hash:
        changes.append(("content_changed", "Изменилось содержимое карточки (текст/данные)"))
    return (len(changes) > 0, changes)

def _get_smtp(db: Database) -> Dict[str, Any] | None:
    rows = db.query("SELECT key, value FROM settings WHERE key LIKE 'smtp.%'")
    kv = {r["key"]: r["value"] for r in rows}
    if not kv.get("smtp.host") or not kv.get("smtp.sender") or not kv.get("smtp.recipient"):
        return None
    return {
        "host": kv.get("smtp.host", ""),
        "port": int(kv.get("smtp.port", "587")),
        "username": kv.get("smtp.username", ""),
        "use_tls": kv.get("smtp.use_tls", "1") == "1",
        "sender": kv.get("smtp.sender", ""),
        "recipient": kv.get("smtp.recipient", ""),
    }

def run_check_for_link(db: Database, link_id: int):
    link = db.query_one("SELECT * FROM links WHERE id=?", (link_id,))
    if not link:
        return

    started_at = datetime.utcnow().isoformat()
    check_id = db.execute(
        "INSERT INTO checks(link_id, started_at, ok) VALUES(?,?,0)",
        (link_id, started_at)
    ).lastrowid

    try:
        res = parse_case(link["url"])
        new_snap = res.snapshot

        old_row = db.query_one("SELECT snapshot_json FROM snapshots WHERE link_id=?", (link_id,))
        changed = False
        change_items: List[tuple[str,str]] = []

        if old_row:
            old_snap = json.loads(old_row["snapshot_json"])
            changed, change_items = _diff_snap(old_snap, new_snap)
        else:
            changed = False  # первая инициализация без письма

        db.execute(
            "INSERT INTO snapshots(link_id, updated_at, snapshot_json) VALUES(?,?,?) "
            "ON CONFLICT(link_id) DO UPDATE SET updated_at=excluded.updated_at, snapshot_json=excluded.snapshot_json",
            (link_id, datetime.utcnow().isoformat(), json.dumps(new_snap, ensure_ascii=False))
        )

        db.execute("UPDATE checks SET finished_at=?, ok=1 WHERE id=?",
                   (datetime.utcnow().isoformat(), check_id))

        db.execute(
            "UPDATE links SET last_ok_at=?, last_check_at=?, consecutive_failures=0, status='active', updated_at=datetime('now') WHERE id=?",
            (datetime.utcnow().isoformat(), datetime.utcnow().isoformat(), link_id)
        )

        if changed:
            details = {
                "url": link["url"],
                "items": [{"type": t, "summary": s} for (t, s) in change_items],
                "act_texts_count": len(res.act_texts),
            }
            db.execute(
                "INSERT INTO changes(link_id, detected_at, change_type, summary, details) VALUES(?,?,?,?,?)",
                (link_id, datetime.utcnow().isoformat(), "changed",
                 "Обнаружены изменения в карточке дела", json.dumps(details, ensure_ascii=False))
            )

            smtp = _get_smtp(db)
            if smtp:
                pwd = load_smtp_secret(smtp["username"]) if smtp["username"] else ""
                if smtp["username"] and not pwd:
                    raise RuntimeError("Не найден пароль SMTP в защищённом хранилище. Откройте настройки SMTP и сохраните пароль заново.")

                subject = f"[GAS Monitor] Изменения: {link['case_number']} ({link['court']})"
                body = []
                body.append("Обнаружены изменения в карточке дела.")
                body.append("")
                body.append(f"Ссылка: {link['url']}")
                body.append(f"Истец: {link['plaintiff']}")
                body.append(f"Ответчик: {link['defendant']}")
                body.append(f"Суд: {link['court']}")
                body.append(f"Номер дела: {link['case_number']}")
                body.append("")
                body.append("Что изменилось:")
                for (t, s) in change_items:
                    body.append(f"- {s} ({t})")

                if res.act_texts:
                    body.append("")
                    body.append("Текст судебного акта (как распознано системой):")
                    body.append("")
                    body.append(res.act_texts[0][:12000])

                send_email(
                    smtp["host"], smtp["port"], smtp["username"], pwd or "",
                    smtp["use_tls"], smtp["sender"], smtp["recipient"],
                    subject, "\n".join(body)
                )

        log.info("Check OK for link_id=%s url=%s", link_id, link["url"])

    except Exception as e:
        err = str(e)
        log.exception("Check FAILED for link_id=%s: %s", link_id, err)
        db.execute("UPDATE checks SET finished_at=?, ok=0, error=? WHERE id=?",
                   (datetime.utcnow().isoformat(), err, check_id))

        row = db.query_one("SELECT consecutive_failures FROM links WHERE id=?", (link_id,))
        fails = int(row["consecutive_failures"]) + 1 if row else 1
        status = "error"
        if fails >= 3:
            status = "problem"

        db.execute(
            "UPDATE links SET last_check_at=?, consecutive_failures=?, status=?, updated_at=datetime('now') WHERE id=?",
            (datetime.utcnow().isoformat(), fails, status, link_id)
        )

        if fails >= 3:
            smtp = _get_smtp(db)
            if smtp:
                pwd = load_smtp_secret(smtp["username"]) if smtp["username"] else ""
                subject = f"[GAS Monitor] Проблемная ссылка: {link['case_number']} ({link['court']})"
                body = "\n".join([
                    "Ссылка не проходит проверку 3 раза подряд.",
                    "Пожалуйста, откройте ссылку и при необходимости обновите её в приложении.",
                    "",
                    f"Ссылка: {link['url']}",
                    f"Ошибка: {err}",
                ])
                send_email(
                    smtp["host"], smtp["port"], smtp["username"], pwd or "",
                    smtp["use_tls"], smtp["sender"], smtp["recipient"],
                    subject, body
                )
