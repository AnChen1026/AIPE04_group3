"""LLM 呼叫：可切換 Gemini／OpenAI、逾時或忙碌會重試一次、失敗會回報原因。不連真的服務。"""

import os

import httpx
import pytest

from backend.services import llm

# conftest 的 no_llm 會把這兩個換成假的；這裡先留住真的來測
REAL_WITH_REASON = llm.generate_text_with_reason


@pytest.fixture
def env(monkeypatch):
    for name in (
        "LLM_PROVIDER",
        "PRACTICE_FEEDBACK_LLM_PROVIDER",
        "QUIZ_GENERATION_LLM_PROVIDER",
        "PRACTICE_FEEDBACK_LLM_MODEL",
        "LOCAL_MODEL",
        "AI_COURSE_GATEWAY_URL",
        "AI_COURSE_GATEWAY_TOKEN",
        "GEMINI_MODEL",
        "OPENAI_MODEL",
        "LLM_TIMEOUT_SECONDS",
    ):
        monkeypatch.setenv(name, "")
    monkeypatch.setenv("GEMINI_API_KEY", "gemini-test-key")
    monkeypatch.setenv("OPENAI_API_KEY", "openai-test-key")
    monkeypatch.setattr(llm, "RETRY_WAIT_SECONDS", 0)
    # 不讀專案的 .env，只看這裡設的環境變數
    monkeypatch.setattr(llm, "read_env_value", lambda name: os.environ.get(name) or None)
    return monkeypatch


@pytest.fixture
def calls(env):
    seen = []

    def fake(provider, outcomes):
        def call(api_key, model, system_instruction, content, timeout, temperature):
            seen.append({"provider": provider, "model": model, "timeout": timeout})
            outcome = outcomes.pop(0)
            if isinstance(outcome, Exception):
                raise outcome
            return outcome

        return call

    def setup(gemini=(), openai=()):
        env.setattr(llm, "PROVIDERS", {"gemini": fake("gemini", list(gemini)), "openai": fake("openai", list(openai))})
        return seen

    return setup


def test_預設用Gemini_功能可以自己改用OpenAI(calls, env):
    seen = calls(gemini=["Gemini 回饋"], openai=["OpenAI 回饋"])
    assert REAL_WITH_REASON("系統", "內容") == ("Gemini 回饋", None)
    env.setenv("PRACTICE_FEEDBACK_LLM_PROVIDER", "openai")
    assert REAL_WITH_REASON("系統", "內容", feature=llm.FEATURE_PRACTICE_FEEDBACK) == ("OpenAI 回饋", None)
    # 其他功能（例如課前摘要）不受影響
    assert [item["provider"] for item in seen] == ["gemini", "openai"]
    assert seen[1]["model"] == llm.DEFAULT_MODELS["openai"]


def test_逾時或忙碌會重試一次(calls, env):
    env.setenv("LLM_TIMEOUT_SECONDS", "5")
    seen = calls(gemini=[llm.LLMError("等了 5 秒沒有回應", retryable=True), "第二次成功"])
    assert REAL_WITH_REASON("系統", "內容") == ("第二次成功", None)
    assert len(seen) == 2
    assert seen[0]["timeout"] == 5


def test_一直失敗會回報原因_不能重試的錯誤不重試(calls):
    seen = calls(gemini=[llm.LLMError("504 DEADLINE_EXCEEDED", retryable=True)] * 2)
    text, reason = REAL_WITH_REASON("系統", "內容")
    assert text is None
    assert "504" in reason and "gemini" in reason
    assert len(seen) == llm.MAX_ATTEMPTS

    seen.clear()
    calls(gemini=[llm.LLMError("404 model not found")])
    text, reason = REAL_WITH_REASON("系統", "內容")
    assert text is None and "404" in reason


def test_沒有金鑰或供應商寫錯(calls, env):
    calls()
    env.setenv("GEMINI_API_KEY", "")
    assert REAL_WITH_REASON("系統", "內容") == (None, "沒有設定 GEMINI_API_KEY。")
    env.setenv("LLM_PROVIDER", "claude-typo")
    text, reason = REAL_WITH_REASON("系統", "內容")
    assert text is None and "claude-typo" in reason


def test_OpenAI的回應與錯誤(env):
    def fake_post(url, headers, json, timeout):
        assert headers["Authorization"] == "Bearer openai-test-key"
        assert json["messages"][0] == {"role": "system", "content": "系統"}
        request = httpx.Request("POST", url)
        if json["messages"][1]["content"] == "忙碌":
            return httpx.Response(429, json={"error": {"message": "Rate limit"}}, request=request)
        return httpx.Response(200, json={"choices": [{"message": {"content": " 很好！ "}}]}, request=request)

    env.setattr(httpx, "post", fake_post)
    env.setenv("LLM_PROVIDER", "openai")
    assert REAL_WITH_REASON("系統", "內容") == ("很好！", None)
    text, reason = REAL_WITH_REASON("系統", "忙碌")
    assert text is None and "429" in reason


def test_AI出題預設用OpenAI_不跟全站設定_可以單獨改回Gemini(env):
    env.setenv("LLM_PROVIDER", "gemini")
    assert llm.provider_for(llm.FEATURE_QUIZ_GENERATION) == "openai"
    assert llm.provider_for(llm.FEATURE_LESSON_SUMMARY) == "gemini"
    env.setenv("QUIZ_GENERATION_LLM_PROVIDER", "gemini")
    assert llm.provider_for(llm.FEATURE_QUIZ_GENERATION) == "gemini"


def test_本機千問_練習回饋可以選本機與指定模型_經過閘道(env):
    seen = {}

    def fake_post(url, headers, json, timeout):
        seen.update(url=url, headers=headers, json=json)
        request = httpx.Request("POST", url)
        return httpx.Response(200, json={"choices": [{"message": {"content": " 節奏穩定！ "}}]}, request=request)

    env.setattr(httpx, "post", fake_post)
    env.setenv("PRACTICE_FEEDBACK_LLM_PROVIDER", "local")
    env.setenv("PRACTICE_FEEDBACK_LLM_MODEL", "qwen3:14b")
    env.setenv("AI_COURSE_GATEWAY_URL", "https://gateway.example.com/")
    env.setenv("AI_COURSE_GATEWAY_TOKEN", "t" * 48)
    assert REAL_WITH_REASON("系統", "內容", feature=llm.FEATURE_PRACTICE_FEEDBACK) == ("節奏穩定！", None)
    assert seen["url"] == "https://gateway.example.com/v1/chat/completions"
    assert seen["headers"]["Authorization"] == "Bearer " + "t" * 48
    assert seen["json"]["model"] == "qwen3:14b"
    assert seen["json"]["max_tokens"] <= 1400
    assert seen["json"]["reasoning_effort"] == "none"
    # 沒指定模型就用預設的千問 4B
    env.setenv("PRACTICE_FEEDBACK_LLM_MODEL", "")
    REAL_WITH_REASON("系統", "內容", feature=llm.FEATURE_PRACTICE_FEEDBACK)
    assert seen["json"]["model"] == llm.DEFAULT_MODELS["local"]


def test_本機閘道沒設好或忙碌時說明原因(env):
    env.setenv("LLM_PROVIDER", "local")
    text, reason = REAL_WITH_REASON("系統", "內容")
    assert text is None and "AI_COURSE_GATEWAY_TOKEN" in reason
    env.setenv("AI_COURSE_GATEWAY_TOKEN", "t" * 48)
    env.setenv("AI_COURSE_GATEWAY_URL", "http://example.com")
    text, reason = REAL_WITH_REASON("系統", "內容")
    assert text is None and "https" in reason

    def busy(url, headers, json, timeout):
        return httpx.Response(503, json={"detail": "Model busy"}, request=httpx.Request("POST", url))

    env.setattr(httpx, "post", busy)
    env.setenv("AI_COURSE_GATEWAY_URL", "http://127.0.0.1:18763")
    text, reason = REAL_WITH_REASON("系統", "內容")
    assert text is None and "503" in reason and "忙碌" in reason


def test_Docker裡的後端可以用hostdockerinternal連到電腦上的閘道(env):
    env.setenv("AI_COURSE_GATEWAY_URL", "http://host.docker.internal:18763")
    assert llm._gateway_url() == "http://host.docker.internal:18763"
    env.setenv("AI_COURSE_GATEWAY_URL", "http://gateway.example.com")
    assert llm._gateway_url() is None
