"""Storage inventory and streaming downloads, without public object URLs."""

import hashlib
from pathlib import Path
from urllib.parse import quote

import httpx

from scripts.ops.common import OpsError, private_dir


def safe_key(key):
    if (
        not key
        or key.startswith("/")
        or "\\" in key
        or "\x00" in key
        or any(p in {"", ".", ".."} for p in key.split("/"))
    ):
        raise OpsError("unsafe_object_key")
    return key


class Storage:
    def __init__(self, settings, client=None):
        self.client = client or httpx.Client(
            base_url=settings.secrets["SUPABASE_URL"].rstrip("/") + "/storage/v1",
            headers=settings.storage_headers,
            timeout=60,
        )

    def close(self):
        self.client.close()

    def buckets(self):
        response = self.client.get("/bucket")
        response.raise_for_status()
        return response.json()

    def inventory(self, bucket):
        safe_key(bucket)
        pending, seen, objects = [""], set(), {}
        while pending:
            prefix = pending.pop()
            if prefix in seen:
                raise OpsError("cyclic_storage_listing")
            seen.add(prefix)
            offset = 0
            while True:
                response = self.client.post(
                    "/object/list/" + bucket,
                    json={
                        "prefix": prefix,
                        "limit": 100,
                        "offset": offset,
                        "sortBy": {"column": "name", "order": "asc"},
                    },
                )
                response.raise_for_status()
                rows = response.json()
                if not isinstance(rows, list):
                    raise OpsError("invalid_storage_listing")
                for item in rows:
                    name = safe_key(item["name"])
                    if "/" in name:
                        raise OpsError("invalid_storage_listing_name")
                    key = safe_key(prefix + name)
                    if item.get("id") is None:
                        pending.append(key + "/")
                    else:
                        if key in objects:
                            raise OpsError("duplicate_storage_listing")
                        objects[key] = item
                if len(rows) < 100:
                    break
                offset += len(rows)
        return objects

    def download(self, bucket, key, target):
        safe_key(bucket)
        safe_key(key)
        private_dir(Path(target).parent)
        digest = hashlib.sha256()
        size = 0
        with self.client.stream(
            "GET", "/object/authenticated/" + bucket + "/" + quote(key, safe="/")
        ) as response:
            response.raise_for_status()
            with Path(target).open("xb") as output:
                Path(target).chmod(0o600)
                for chunk in response.iter_bytes(65536):
                    output.write(chunk)
                    digest.update(chunk)
                    size += len(chunk)
        return {"bytes": size, "sha256": digest.hexdigest()}


def fingerprint(item):
    """No cache reuse if the server omits strong version metadata."""
    metadata = item.get("metadata") or {}
    etag = metadata.get("eTag") or metadata.get("etag")
    updated = item.get("updated_at")
    size = metadata.get("size")
    if not item.get("id") or not etag or not updated or not isinstance(size, int):
        return None
    return {"id": item["id"], "etag": etag, "updated_at": updated, "bytes": size}
