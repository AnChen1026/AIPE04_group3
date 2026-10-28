"""Fail closed before migrations; never print secrets."""

from pathlib import Path

from sqlalchemy.engine import make_url

from backend.core.config import read_env_value


def validate():
    if read_env_value("APP_ENV") != "staging":
        raise RuntimeError("This deployment is configured for staging only")
    if read_env_value("STORAGE_BACKEND") != "supabase":
        raise RuntimeError("Cloud deployment requires Supabase Storage")
    url = make_url(read_env_value("DATABASE_URL") or "")
    if (
        url.drivername != "postgresql+psycopg"
        or url.query.get("sslmode") != "verify-full"
    ):
        raise RuntimeError(
            "Cloud database requires postgresql+psycopg and sslmode=verify-full"
        )
    cert = read_env_value("SUPABASE_DB_CA_CERT")
    if cert:
        if (
            "-----BEGIN CERTIFICATE-----" not in cert
            or url.query.get("sslrootcert") != "/tmp/supabase-ca.crt"
        ):
            raise RuntimeError(
                "Set sslrootcert=/tmp/supabase-ca.crt for SUPABASE_DB_CA_CERT"
            )
        Path("/tmp/supabase-ca.crt").write_text(cert)
    if not url.host or url.host in {"localhost", "127.0.0.1", "postgres"}:
        raise RuntimeError("Cloud database host is required")
    if (read_env_value("SESSION_HTTPS_ONLY") or "").lower() != "true":
        raise RuntimeError("Cloud deployment requires Secure cookies")
    secret = read_env_value("SESSION_SECRET_KEY") or ""
    if len(secret) < 32 or secret == "replace-with-a-long-random-string":
        raise RuntimeError(
            "SESSION_SECRET_KEY must be a unique random secret of at least 32 characters"
        )
    from backend.core.storage import _connection

    _connection()


if __name__ == "__main__":
    validate()
    print("Cloud configuration validated (secrets hidden).")
