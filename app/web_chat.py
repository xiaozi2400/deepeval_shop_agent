"""电商客服Agent Web聊天界面

会话以 Streamlit session 为单位，session id 直接当作 Agent 的 thread_id，
这样"这个多少钱"这类依赖上一轮的表述在界面上才真的可用。

启动：
    streamlit run app/web_chat.py
"""
import sys
import uuid
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.agent.llm_guard import UpstreamLLMError
from src.agent.react_agent import ReactCustomerServiceAgent

st.set_page_config(
    page_title="电商客服助手",
    page_icon="🤖",
    layout="centered"
)

st.title("🤖 电商客服助手")
st.caption("基于 LangChain ReAct 的智能客服系统")

REPLYING_STATUS = (
    '<div style="text-align:left; font-size:0.7rem; color:#9a9a9a; '
    'margin-top:2px;">🤔 正在回复…</div>'
)


def init_session_state():
    """初始化会话状态"""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "thread_id" not in st.session_state:
        st.session_state.thread_id = f"web-{uuid.uuid4()}"
    if "agent" not in st.session_state:
        try:
            st.session_state.agent = ReactCustomerServiceAgent()
        except ValueError as e:
            st.error(f"初始化失败: {e}")
            st.info("请确保已设置 OPENAI_API_KEY 环境变量")
            st.stop()


def stream_agent_response(user_message: str):
    """流式获取Agent回复"""
    try:
        produced = False
        for piece in st.session_state.agent.stream(user_message, user_id=st.session_state.thread_id):
            produced = True
            yield piece
        if not produced:
            yield "抱歉，我没有收到回复。"
    except UpstreamLLMError as e:
        # 上游网关拒了这次请求（额度、限流等）。说清楚原因，
        # 否则用户只看到"我没有收到回复"，排查只能去翻 LangSmith。
        yield f"模型服务暂时不可用（错误码 {e.status_code}）：{e.status_msg}"
    except Exception as e:
        yield f"处理消息时出错: {e}"


def main():
    init_session_state()

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt := st.chat_input("请输入您的问题...", key="chat_input"):
        with st.chat_message("user"):
            st.markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})

        with st.chat_message("assistant"):
            response_container = st.empty()
            status_container = st.empty()
            status_container.markdown(REPLYING_STATUS, unsafe_allow_html=True)

            full_response = ""
            for piece in stream_agent_response(prompt):
                full_response += piece
                response_container.markdown(full_response + "▌")

            response_container.markdown(full_response)
            status_container.empty()

        st.session_state.messages.append({"role": "assistant", "content": full_response})


if __name__ == "__main__":
    main()
