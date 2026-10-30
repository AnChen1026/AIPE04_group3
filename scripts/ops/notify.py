"""Operator-approved Gmail SMTP alerts with a durable local outbox."""

import smtplib
import ssl
from email.message import EmailMessage

import certifi

from scripts.ops.common import OpsError, atomic_json, error_details, read_json, utcnow

LABELS = {
    "database_capacity": "資料庫容量",
    "storage_capacity": "物件儲存容量",
    "backup_age": "備份時間",
    "backup_last_run": "最近一次備份",
    "database_probe": "資料庫連線",
    "storage_probe": "物件儲存連線",
    "health_probe": "網站連線",
    "website_response": "網站健康檢查",
    "file_cleanup_backlog": "檔案清理重試",
    "analysis_stuck": "等待過久的評分",
    "analysis_failures": "評分失敗率",
    "backup_probe": "備份紀錄讀取",
    "gmail_connection_test": "Gmail 連線測試",
}
LEVELS = {"critical": "緊急", "warning": "注意", "resolved": "已恢復", "test": "測試"}


def message(settings, events):
    mail = EmailMessage()
    mail["From"] = settings.values["gmail_sender"]
    mail["To"] = settings.values["notification_to"]
    tag = "測試" if all(e["level"] == "test" for e in events) else "監控提醒"
    mail["Subject"] = f"[AIPE04 共用測試站] {tag}"
    lines = ["AIPE04 共用測試站維運通知", settings.values["site_url"], ""]
    for event in events:
        lines.append(
            f"[{LEVELS.get(event['level'], event['level'])}] {LABELS.get(event['code'], event['code'])}"
        )
        lines.append("觀測時間：" + event.get("observed_at", utcnow().isoformat()))
        lines.append("資訊：" + str(event.get("details", {})))
        lines.append("")
    lines.append(
        "此通知不含資料庫密碼、API 金鑰或備份內容。詳細紀錄請查看本機 operations 報告。"
    )
    mail.set_content("\n".join(lines))
    return mail


def password(settings):
    try:
        value = "".join(
            (settings.root / settings.values["gmail_app_password_file"])
            .read_text()
            .split()
        )
    except FileNotFoundError:
        raise OpsError("gmail_authorization_required") from None
    if len(value) != 16 or not value.isascii() or not value.isalnum():
        raise OpsError("gmail_authorization_required")
    return value


def deliver(settings, events, smtp_factory=None):
    if settings.values["notification_channel"] != "gmail":
        raise OpsError("notification_not_configured")
    app_password = password(settings)
    # TLS certificate and hostname verification are enabled; endpoint is fixed to Google.
    with (smtp_factory or smtplib.SMTP_SSL)(
        "smtp.gmail.com",
        465,
        context=ssl.create_default_context(cafile=certifi.where()),
        timeout=30,
    ) as smtp:
        smtp.login(settings.values["gmail_sender"], app_password)
        refused = smtp.send_message(message(settings, events))
        if refused:
            raise OpsError("gmail_recipient_refused")


def flush_outbox(settings):
    path = settings.state_dir / "notification-outbox.json"
    pending = read_json(path, [])
    if settings.values["notification_channel"] == "none":
        return {"status": "not_configured", "pending": len(pending)}
    try:
        password(settings)
    except OpsError:
        return {"status": "authorization_required", "pending": len(pending)}
    if not pending:
        return {"status": "idle", "pending": 0}
    batch = pending[:5]
    try:
        deliver(settings, batch)
    except Exception as error:  # noqa: BLE001 - delivery failures keep events for the next run
        status = {
            "status": "failed",
            "pending": len(pending),
            "observed_at": utcnow().isoformat(),
            "error": error_details(error),
        }
        atomic_json(settings.state_dir / "notification-status.json", status)
        return status
    atomic_json(path, pending[len(batch) :])
    status = {
        "status": "success",
        "sent": len(batch),
        "pending": len(pending) - len(batch),
        "observed_at": utcnow().isoformat(),
    }
    atomic_json(settings.state_dir / "notification-status.json", status)
    return status
