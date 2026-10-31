"""Separate operator preferences from existing cloud secrets."""

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlsplit

from sqlalchemy.engine import make_url

from scripts.ops.common import OpsError, private_dir

DEFAULTS = {
    "cloud_config": ".env.cloud.json",
    "backup_root": "db-backups/managed",
    "site_url": "https://aipe04-group3-staging.onrender.com",
    "keep": 7,
    "warning_pct": 70,
    "critical_pct": 85,
    "database_budget_bytes": 500_000_000,
    "storage_budget_bytes": 1_000_000_000,
    "max_backup_age_hours": 36,
    "alert_cooldown_hours": 24,
    "timezone": "Asia/Taipei",
    "docker_path": "/usr/local/bin/docker",
    "notification_channel": "none",
    "gmail_sender": "",
    "notification_to": "",
    "gmail_app_password_file": ".env.ops.gmail-app-password",
}
BUCKETS = ("teaching-files", "profile-images", "teacher-proofs")


@dataclass
class Settings:
    root: Path
    values: dict
    secrets: dict = field(repr=False)
    pg: dict = field(repr=False)
    source_id: str

    @classmethod
    def load(cls, filename):
        filename = Path(filename).resolve()
        values = json.loads(filename.read_text())
        if not isinstance(values, dict) or set(values) - set(DEFAULTS):
            raise OpsError("invalid_ops_config")
        values = DEFAULTS | values
        if (
            not 1 <= values["keep"] <= 365
            or not 0 < values["warning_pct"] < values["critical_pct"] <= 100
        ):
            raise OpsError("invalid_retention_or_thresholds")
        for key in (
            "database_budget_bytes",
            "storage_budget_bytes",
            "max_backup_age_hours",
            "alert_cooldown_hours",
        ):
            if not isinstance(values[key], (int, float)) or values[key] <= 0:
                raise OpsError("invalid_budget_or_interval")
        if values["timezone"] != "Asia/Taipei" or values[
            "notification_channel"
        ] not in {"none", "gmail"}:
            raise OpsError("invalid_timezone_or_notification_channel")
        if values["notification_channel"] == "gmail":
            from email_validator import EmailNotValidError, validate_email

            try:
                for key in ("gmail_sender", "notification_to"):
                    values[key] = validate_email(
                        values[key], check_deliverability=False
                    ).normalized
            except EmailNotValidError:
                raise OpsError("invalid_notification_email") from None
        site = urlsplit(values["site_url"])
        if (
            site.scheme != "https"
            or not site.hostname
            or site.username
            or site.query
            or site.fragment
            or site.path not in {"", "/"}
        ):
            raise OpsError("invalid_site_url")
        root = filename.parent
        secrets = json.loads((root / values["cloud_config"]).read_text())
        if secrets.get("APP_ENV") != "staging":
            raise OpsError("staging_config_required")
        url = make_url(secrets["DATABASE_URL"])
        if (
            url.drivername != "postgresql+psycopg"
            or url.query.get("sslmode") != "verify-full"
        ):
            raise OpsError("verified_tls_required")
        storage = urlsplit(secrets["SUPABASE_URL"])
        if (
            storage.scheme != "https"
            or not storage.hostname
            or storage.path not in {"", "/"}
            or storage.username
            or storage.query
            or storage.fragment
        ):
            raise OpsError("invalid_storage_origin")
        identity = f"{url.host}:{url.port or 5432}/{url.database}|{storage.netloc}"
        sid = hashlib.sha256(identity.encode()).hexdigest()[:16]
        state_dir = private_dir(root / values["backup_root"] / "state" / sid)
        cert = secrets.get("SUPABASE_DB_CA_CERT")
        if not cert or "-----BEGIN CERTIFICATE-----" not in cert:
            raise OpsError("database_ca_required")
        ca = state_dir / "database-ca.crt"
        ca.write_text(cert)
        ca.chmod(0o600)
        pg = {
            "host": url.host,
            "port": url.port or 5432,
            "dbname": url.database,
            "user": url.username,
            "password": url.password,
            "sslmode": "verify-full",
            "sslrootcert": str(ca),
            "connect_timeout": 15,
        }
        return cls(root, values, secrets, pg, sid)

    @property
    def backup_root(self):
        return self.root / self.values["backup_root"] / self.source_id

    @property
    def state_dir(self):
        return self.root / self.values["backup_root"] / "state" / self.source_id

    @property
    def docker(self):
        path = self.values["docker_path"]
        if not Path(path).is_absolute() or not Path(path).is_file():
            raise OpsError("docker_executable_missing")
        return path

    @property
    def storage_headers(self):
        key = self.secrets["SUPABASE_SECRET_KEY"]
        headers = {"apikey": key, "Accept-Encoding": "identity"}
        if key.count(".") == 2:
            headers["Authorization"] = "Bearer " + key
        return headers
