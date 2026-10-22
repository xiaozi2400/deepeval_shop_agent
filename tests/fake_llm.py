"""假模型：按预设脚本吐出带 function call 的回复，用来测试 ReAct 循环与意图回读"""
from typing import Any

from langchain_core.callbacks import CallbackManagerForLLMRun
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.outputs import ChatGeneration, ChatResult


class FakeToolCallingModel(BaseChatModel):
    """按顺序返回预设的 AIMessage

    第一条通常是带 tool_calls 的消息，触发工具调用；
    第二条是收尾的最终回复。
    """

    responses: list[AIMessage] = []
    calls: list[list[BaseMessage]] = []

    def bind_tools(self, tools: list[Any], **kwargs: Any) -> "FakeToolCallingModel":
        return self

    def _generate(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: CallbackManagerForLLMRun | None = None,
        **kwargs: Any,
    ) -> ChatResult:
        self.calls.append(list(messages))
        if not self.responses:
            return ChatResult(generations=[ChatGeneration(message=AIMessage(content=""))])
        return ChatResult(generations=[ChatGeneration(message=self.responses.pop(0))])

    @property
    def _llm_type(self) -> str:
        return "fake-tool-calling"
