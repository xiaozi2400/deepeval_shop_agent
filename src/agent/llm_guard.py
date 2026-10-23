"""上游 OpenAI 兼容网关的业务错误守卫。

MiniMax 这类网关在 Token Plan 额度受限时，仍返回 HTTP 200，
但把 choices 置空、把真实原因放进 base_resp：

    {"choices": null, "base_resp": {"status_code": 2056, "status_msg": "已达用量上限"}}

LangChain 的 ChatOpenAI 不认识 base_resp，于是两条路径表现完全不同：

- 非流式：抛 "null value for 'choices'" 的 TypeError，看不出真实原因
- 流式：把这一行转成 content 为空的正常 chunk，错误彻底消失

流式那条是应用里的静默失败：调用方以为模型没说话，
LangSmith 上对应的 LLM span 也是空输出且没有 error。

守卫在原始响应转换的位置把业务错误挑出来，抛成 UpstreamLLMError，
让调用方拿到上游的真实原因。
"""
from typing import Any

from langchain_openai import ChatOpenAI


class UpstreamLLMError(RuntimeError):
    """上游网关返回的业务错误。

    Attributes:
        status_code: 网关的业务状态码，非零表示请求没被真正执行
        status_msg: 网关给出的中文原因
    """

    def __init__(self, status_code: int, status_msg: str):
        self.status_code = status_code
        self.status_msg = status_msg
        super().__init__(f"上游模型网关返回错误 {status_code}：{status_msg}")


def _business_error(payload: dict[str, Any] | None) -> UpstreamLLMError | None:
    """从原始响应里读出业务错误，没有则返回 None。

    Args:
        payload: 网关返回的原始响应体

    Returns:
        业务错误；响应正常时为 None
    """
    if not payload:
        return None
    base_resp = payload.get("base_resp")
    if not isinstance(base_resp, dict):
        return None
    status_code = base_resp.get("status_code")
    if not status_code:
        return None
    return UpstreamLLMError(status_code, base_resp.get("status_msg") or "")


class GuardedChatOpenAI(ChatOpenAI):
    """把上游业务错误从响应里挑出来，抛成 UpstreamLLMError。"""

    def _convert_chunk_to_generation_chunk(
        self,
        chunk: dict,
        default_chunk_class: type,
        base_generation_info: dict | None,
    ):
        error = _business_error(chunk)
        if error is not None:
            raise error
        return super()._convert_chunk_to_generation_chunk(
            chunk, default_chunk_class, base_generation_info
        )

    def _create_chat_result(self, response, generation_info: dict | None = None):
        payload = response if isinstance(response, dict) else response.model_dump()
        error = _business_error(payload)
        if error is not None:
            raise error
        return super()._create_chat_result(response, generation_info)
