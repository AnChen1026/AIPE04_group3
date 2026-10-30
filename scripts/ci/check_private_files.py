"""Fail when Git tracks operational secrets, backups or private key files.

Print paths only, never file contents. Run from the repository root.
"""

import subprocess
from pathlib import PurePosixPath

EXAMPLES = {".env.example", ".env.cloud.example", ".env.ops.example.json"}
# Existing public Vite toggle; content remains covered by Gitleaks.
PUBLIC_CONFIGS = {"frontend/.env.development"}


def forbidden(name: str) -> bool:
    path = PurePosixPath(name)
    return (
        (path.name.startswith(".env") and path.name not in EXAMPLES and name not in PUBLIC_CONFIGS)
        or "db-backups" in path.parts
        or path.suffix.lower() in {".dump", ".pem", ".key", ".p12", ".pfx", ".crt"}
        or path.name in {"id_rsa", "id_ed25519", "credentials.json", "service-account.json"}
    )


def main():
    files = subprocess.check_output(["git", "ls-files", "-z"]).decode().split("\0")
    rejected = [name for name in files if name and forbidden(name)]
    for name in rejected:
        print(f"Private file must not be tracked: {name}")
    if rejected:
        raise SystemExit(1)
    print("No private configuration, backups or key files tracked.")


if __name__ == "__main__":
    main()
