import ssl
from types import SimpleNamespace

from scripts.ops import notify
from scripts.ops.common import atomic_json, read_json


def config(tmp_path):
    (tmp_path / "app-password").write_text("abcd efgh ijkl mnop")
    return SimpleNamespace(
        root=tmp_path,
        state_dir=tmp_path,
        values={
            "notification_channel": "gmail",
            "gmail_sender": "sender@gmail.com",
            "notification_to": "recipient@gmail.com",
            "gmail_app_password_file": "app-password",
            "site_url": "https://site.example",
        },
    )


def test_gmail_uses_verified_tls_and_only_intended_recipient(tmp_path):
    settings = config(tmp_path)
    seen = {}

    class SMTP:
        def __init__(self, host, port, **kwargs):
            assert (host, port) == ("smtp.gmail.com", 465)
            assert kwargs["context"].check_hostname
            assert kwargs["context"].verify_mode == ssl.CERT_REQUIRED

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def login(self, user, password):
            assert user == "sender@gmail.com" and password == "abcdefghijklmnop"

        def send_message(self, mail):
            seen["mail"] = mail
            return {}

    notify.deliver(
        settings,
        [{"level": "test", "code": "gmail_connection_test", "details": {}}],
        smtp_factory=SMTP,
    )
    assert seen["mail"]["To"] == "recipient@gmail.com"
    assert "abcdefghijklmnop" not in seen["mail"].as_string()


def test_failed_delivery_keeps_outbox_and_does_not_log_secret(tmp_path, monkeypatch):
    settings = config(tmp_path)
    events = [{"code": "db", "level": "critical", "details": {}}]
    atomic_json(tmp_path / "notification-outbox.json", events)

    def fail(*args):
        raise RuntimeError("secret-password")

    monkeypatch.setattr(notify, "deliver", fail)
    result = notify.flush_outbox(settings)
    assert result["status"] == "failed"
    assert read_json(tmp_path / "notification-outbox.json") == events
    assert "secret-password" not in str(result)


def test_success_acknowledges_only_sent_events(tmp_path, monkeypatch):
    settings = config(tmp_path)
    events = [{"code": str(i), "level": "warning", "details": {}} for i in range(7)]
    atomic_json(tmp_path / "notification-outbox.json", events)
    monkeypatch.setattr(notify, "deliver", lambda *args: None)
    result = notify.flush_outbox(settings)
    assert result["sent"] == 5
    assert read_json(tmp_path / "notification-outbox.json") == events[5:]
