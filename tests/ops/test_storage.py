import httpx
import pytest

from scripts.ops.common import OpsError
from scripts.ops.storage import Storage, fingerprint, safe_key


@pytest.mark.parametrize(
    "key", ["../escape", "/absolute", "folder/../x", "x\\y", "folder//x"]
)
def test_unsafe_keys_rejected(key):
    with pytest.raises(OpsError):
        safe_key(key)


def test_nested_and_paginated_inventory():
    offsets = []

    def handler(request):
        import json

        body = json.loads(request.content)
        offsets.append((body["prefix"], body["offset"]))
        if body["prefix"] == "":
            return httpx.Response(200, json=[{"id": None, "name": "nested"}])
        if body["offset"] == 0:
            return httpx.Response(
                200, json=[{"id": str(i), "name": f"{i:03}.wav"} for i in range(100)]
            )
        return httpx.Response(200, json=[{"id": "last", "name": "last.wav"}])

    client = httpx.Client(
        base_url="https://example.com", transport=httpx.MockTransport(handler)
    )
    storage = Storage(None, client=client)
    inventory = storage.inventory("teaching-files")
    assert len(inventory) == 101 and "nested/last.wav" in inventory
    assert ("nested/", 100) in offsets


def test_incomplete_versions_never_reuse_and_same_size_changed_version_differs():
    assert fingerprint({"id": "x", "metadata": {"size": 4}}) is None
    original = {
        "id": "x",
        "updated_at": "one",
        "metadata": {"size": 4, "eTag": "before"},
    }
    changed = original | {"metadata": {"size": 4, "eTag": "after"}}
    assert fingerprint(original) != fingerprint(changed)
