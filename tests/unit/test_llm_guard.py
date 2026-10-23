"""上游网关业务错误的守卫测试

上游 OpenAI 兼容网关在额度受限时返回 HTTP 200 + choices=null，
真实原因放在 base_resp。守卫要把它翻译成 UpstreamLLMError。
"""
import pytest
from langchain_core.messages import AIMessageChunk

from src.agent.llm_guard import GuardedChatOpenAI, UpstreamLLMError


def make_llm() -> GuardedChatOpenAI:
    return GuardedChatOpenAI(model="gpt-4o-mini", api_key="test-key")


ERROR_CHUNK = {
    "id": "chunk-1",
    "choices": None,
    "created": 0,
    "model": "MiniMax-M3.1-Flash-Preview",
    "object": "chat.completion",
    "base_resp": {
        "status_code": 2056,
        "status_msg": "已达到 Token Plan 用量上限：请升级 Token Plan 套餐或购买积分补充用量。",
    },
}

NORMAL_CHUNK = {
    "id": "chunk-2",
    "choices": [
        {
            "index": 0,
            "delta": {"role": "assistant", "content": "您好"},
            "finish_reason": "stop",
        }
    ],
    "created": 0,
    "model": "MiniMax-M3.1-Flash-Preview",
    "object": "chat.completion.chunk",
}


class TestStreamChunk:
    def test_business_error_raises(self):
        llm = make_llm()
        with pytest.raises(UpstreamLLMError) as exc:
            llm._convert_chunk_to_generation_chunk(ERROR_CHUNK, AIMessageChunk, {})
        assert exc.value.status_code == 2056
        assert "Token Plan" in exc.value.status_msg

    def test_normal_chunk_passes_through(self):
        llm = make_llm()
        chunk = llm._convert_chunk_to_generation_chunk(NORMAL_CHUNK, AIMessageChunk, {})
        assert chunk.message.content == "您好"
        assert chunk.generation_info["finish_reason"] == "stop"

    def test_success_status_code_is_not_an_error(self):
        llm = make_llm()
        payload = dict(NORMAL_CHUNK)
        payload["base_resp"] = {"status_code": 0, "status_msg": ""}
        chunk = llm._convert_chunk_to_generation_chunk(payload, AIMessageChunk, {})
        assert chunk.message.content == "您好"


class TestNonStreamResponse:
    def test_business_error_raises(self):
        llm = make_llm()
        response = {
            "id": "resp-1",
            "choices": None,
            "created": 0,
            "model": "MiniMax-M3.1-Flash-Preview",
            "object": "chat.completion",
            "base_resp": {"status_code": 2056, "status_msg": "额度不足"},
        }
        with pytest.raises(UpstreamLLMError) as exc:
            llm._create_chat_result(response, {})
        assert exc.value.status_code == 2056

    def test_normal_response_passes_through(self):
        llm = make_llm()
        response = {
            "id": "resp-2",
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": "您好"},
                    "finish_reason": "stop",
                }
            ],
            "created": 0,
            "model": "MiniMax-M3.1-Flash-Preview",
            "object": "chat.completion",
        }
        result = llm._create_chat_result(response, {})
        assert result.generations[0].message.content == "您好"
