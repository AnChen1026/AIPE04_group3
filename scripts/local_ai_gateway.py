"""Authenticated local-only boundary for the team's Ollama models.

Run behind a separately authenticated HTTPS tunnel; never expose Ollama itself.

Optional environment variables (defaults keep the original AI course-search setup):
  AI_GATEWAY_CHAT_MODELS     comma-separated chat models that may be used, e.g.
                             "qwen3:4b-instruct-2507-q4_K_M,qwen3:14b" (quiz generation and
                             practice feedback can pick one of these).
  AI_GATEWAY_TIMEOUT_SECONDS how long to wait for Ollama (default 60). Larger models on a
                             laptop may need 180 or more.
"""

import asyncio
import hmac
import os
import re
import time
from collections import deque
from typing import Literal

import httpx
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

DEFAULT_CHAT_MODEL = "qwen3:4b-instruct-2507-q4_K_M"


def allowed_chat_models() -> set[str]:
    configured = os.environ.get("AI_GATEWAY_CHAT_MODELS", "")
    models = {item.strip() for item in configured.split(",") if item.strip()}
    return models or {DEFAULT_CHAT_MODEL}


def upstream_timeout() -> float:
    try:
        return min(600.0, max(10.0, float(os.environ.get("AI_GATEWAY_TIMEOUT_SECONDS") or 60)))
    except ValueError:
        return 60.0


class Message(BaseModel):
    model_config = ConfigDict(extra="forbid")
    role: Literal["system", "user", "assistant"]
    content: str = Field(max_length=12000)


class ChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    model: str
    messages: list[Message] = Field(min_length=1, max_length=20)
    temperature: float = Field(default=0, ge=0, le=1)
    max_tokens: int = Field(default=1000, ge=1, le=1400)
    stream: Literal[False] = False
    response_format: dict | None = None
    # "none" turns off hidden reasoning on thinking models (e.g. qwen3.5), which otherwise
    # spends the whole token budget thinking and returns empty content.
    reasoning_effort: Literal["none", "low", "medium", "high"] | None = None

    @field_validator("model")
    @classmethod
    def _allowed_model(cls, value: str) -> str:
        if value not in allowed_chat_models():
            raise ValueError("model not allowed")
        return value


class EmbedRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    model: Literal["bge-m3:567m"]
    input: list[str] = Field(min_length=1, max_length=16)
    truncate: Literal[False] = False


def create_app(transport=None, requests_per_minute=120):
    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
    slot = asyncio.Semaphore(1)
    timestamps = deque()

    async def forward(request: Request, schema, path):
        expected = os.environ.get("AI_GATEWAY_TOKEN", "")
        provided = request.headers.get("authorization", "")
        if len(expected) < 32 or not hmac.compare_digest(
            provided, "Bearer " + expected
        ):
            raise HTTPException(401, "Unauthorized")
        now = time.monotonic()
        while timestamps and now - timestamps[0] >= 60:
            timestamps.popleft()
        if len(timestamps) >= requests_per_minute:
            raise HTTPException(
                429, "Model request limit reached", headers={"Retry-After": "60"}
            )
        timestamps.append(now)
        body = bytearray()
        async for chunk in request.stream():
            body.extend(chunk)
            if len(body) > 65536:
                raise HTTPException(413, "Request too large")
        try:
            payload = schema.model_validate_json(body)
        except (ValidationError, ValueError):
            raise HTTPException(422, "Invalid request") from None
        try:
            await asyncio.wait_for(slot.acquire(), timeout=0.1)
        except TimeoutError:
            raise HTTPException(503, "Model busy") from None
        try:
            async with httpx.AsyncClient(transport=transport, timeout=upstream_timeout()) as client:
                if path == "/api/embed":
                    digest = request.headers.get("x-embedding-digest", "")
                    if not re.fullmatch(r"[a-f0-9]{64}", digest):
                        raise HTTPException(503, "Embedding version unavailable")
                    tags = await client.get("http://127.0.0.1:11434/api/tags")
                    tags.raise_for_status()
                    models = tags.json().get("models", [])
                    if not any(
                        m.get("name") == "bge-m3:567m" and m.get("digest") == digest
                        for m in models
                    ):
                        raise HTTPException(503, "Embedding version mismatch")
                response = await client.post(
                    "http://127.0.0.1:11434" + path,
                    json=payload.model_dump(exclude_none=True),
                )
                response.raise_for_status()
                return response.json()
        except (httpx.HTTPError, ValueError, TypeError, AttributeError):
            raise HTTPException(503, "Model unavailable") from None
        finally:
            slot.release()

    @app.post("/v1/chat/completions")
    async def chat(request: Request):
        return await forward(request, ChatRequest, "/v1/chat/completions")

    @app.post("/api/embed")
    async def embed(request: Request):
        return await forward(request, EmbedRequest, "/api/embed")

    return app


app = create_app()
