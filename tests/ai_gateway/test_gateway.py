"""Public boundary checks for the local model gateway."""

from fastapi.testclient import TestClient


def test_unauthenticated_request_cannot_reach_local_model(monkeypatch):
    monkeypatch.setenv("AI_GATEWAY_TOKEN", "a" * 48)
    from scripts.local_ai_gateway import create_app

    with TestClient(create_app()) as client:
        response = client.post(
            "/v1/chat/completions",
            json={"model": "qwen3:4b-instruct-2507-q4_K_M", "messages": []},
        )
    assert response.status_code == 401


def test_gateway_only_forwards_allowed_models_and_operations(monkeypatch):
    import httpx

    from scripts.local_ai_gateway import create_app

    monkeypatch.setenv("AI_GATEWAY_TOKEN", "b" * 48)
    calls = []

    def upstream(request):
        calls.append((request.url.path, request.read()))
        return httpx.Response(200, json={"choices": [{"message": {"content": "ok"}}]})

    with TestClient(create_app(transport=httpx.MockTransport(upstream))) as client:
        headers = {"Authorization": "Bearer " + "b" * 48}
        rejected = client.post(
            "/v1/chat/completions",
            headers=headers,
            json={"model": "unapproved", "messages": []},
        )
        ok = client.post(
            "/v1/chat/completions",
            headers=headers,
            json={
                "model": "qwen3:4b-instruct-2507-q4_K_M",
                "messages": [{"role": "user", "content": "你好"}],
            },
        )
    assert rejected.status_code == 422
    assert ok.status_code == 200
    assert ok.json()["choices"][0]["message"]["content"] == "ok"
    assert len(calls) == 1
    assert calls[0][0] == "/v1/chat/completions"


def test_embedding_endpoint_limits_model_and_hides_upstream_failures(monkeypatch):
    import httpx

    from scripts.local_ai_gateway import create_app

    monkeypatch.setenv("AI_GATEWAY_TOKEN", "c" * 48)

    def unavailable(request):
        raise httpx.ConnectError("sensitive upstream address", request=request)

    with TestClient(create_app(transport=httpx.MockTransport(unavailable))) as client:
        headers = {"Authorization": "Bearer " + "c" * 48}
        rejected = client.post(
            "/api/embed", headers=headers, json={"model": "other", "input": ["琴"]}
        )
        failed = client.post(
            "/api/embed",
            headers=headers,
            json={"model": "bge-m3:567m", "input": ["琴"]},
        )
    assert rejected.status_code == 422
    assert failed.status_code == 503
    assert "sensitive upstream address" not in failed.text


def test_embedding_gateway_rejects_model_digest_mismatch(monkeypatch):
    import httpx

    from scripts.local_ai_gateway import create_app

    monkeypatch.setenv("AI_GATEWAY_TOKEN", "d" * 48)
    calls = []

    def handler(request):
        calls.append(request.url.path)
        return httpx.Response(
            200, json={"models": [{"name": "bge-m3:567m", "digest": "e" * 64}]}
        )

    with TestClient(create_app(transport=httpx.MockTransport(handler))) as client:
        response = client.post(
            "/api/embed",
            headers={
                "Authorization": "Bearer " + "d" * 48,
                "X-Embedding-Digest": "f" * 64,
            },
            json={"model": "bge-m3:567m", "input": ["鋼琴"]},
        )
    assert response.status_code == 503
    assert "/api/embed" not in calls


def test_embedding_gateway_accepts_matching_model_digest(monkeypatch):
    import httpx

    from scripts.local_ai_gateway import create_app

    monkeypatch.setenv("AI_GATEWAY_TOKEN", "d" * 48)

    def handler(request):
        if request.url.path == "/api/tags":
            return httpx.Response(
                200, json={"models": [{"name": "bge-m3:567m", "digest": "f" * 64}]}
            )
        return httpx.Response(200, json={"embeddings": [[1.0, 0.0]]})

    with TestClient(create_app(transport=httpx.MockTransport(handler))) as client:
        response = client.post(
            "/api/embed",
            headers={
                "Authorization": "Bearer " + "d" * 48,
                "X-Embedding-Digest": "f" * 64,
            },
            json={"model": "bge-m3:567m", "input": ["鋼琴"]},
        )
    assert response.status_code == 200
    assert response.json()["embeddings"] == [[1.0, 0.0]]


def test_gateway_limits_authenticated_requests_even_when_serial(monkeypatch):
    import httpx

    from scripts.local_ai_gateway import create_app

    monkeypatch.setenv("AI_GATEWAY_TOKEN", "e" * 48)
    handler = lambda request: httpx.Response(200, json={"choices": []})
    with TestClient(
        create_app(transport=httpx.MockTransport(handler), requests_per_minute=2)
    ) as client:
        headers = {"Authorization": "Bearer " + "e" * 48}
        payload = {
            "model": "qwen3:4b-instruct-2507-q4_K_M",
            "messages": [{"role": "user", "content": "hi"}],
        }
        assert (
            client.post(
                "/v1/chat/completions", headers=headers, json=payload
            ).status_code
            == 200
        )
        assert (
            client.post(
                "/v1/chat/completions", headers=headers, json=payload
            ).status_code
            == 200
        )
        assert (
            client.post(
                "/v1/chat/completions", headers=headers, json=payload
            ).status_code
            == 429
        )
