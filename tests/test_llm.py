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
