"""电商客服Agent Web聊天界面"""
import time

import streamlit as st

from src.agent.customer_service_agent import CustomerServiceAgent

# 页面配置
st.set_page_config(
    page_title="电商客服助手",
    page_icon="🤖",
    layout="centered"
)

st.title("🤖 电商客服助手")
st.caption("基于 LangGraph 的智能客服系统")


def init_session_state():
    """初始化会话状态"""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "agent" not in st.session_state:
        try:
            st.session_state.agent = CustomerServiceAgent()
        except ValueError as e:
            st.error(f"初始化失败: {e}")
            st.info("请确保已设置 OPENAI_API_KEY 环境变量")
            st.stop()


def get_agent_response(user_message: str) -> str:
    """获取Agent回复"""
    try:
        result = st.session_state.agent.invoke(user_message)
        messages = result.get("messages", [])
        if messages:
            return messages[-1].content
        return "抱歉，我没有收到回复。"
    except Exception as e:
        return f"处理消息时出错: {e}"


def stream_agent_response(user_message: str):
    """流式获取Agent回复"""
    try:
        full_response = ""
        for node_output in st.session_state.agent.stream(user_message):
            # 从节点输出中提取AI消息
            for node_state in node_output.values():
                if "messages" in node_state:
                    messages = node_state["messages"]
                    if messages:
                        content = messages[-1].content
                        if content:
                            full_response = content
                            yield content
                            time.sleep(0.03)
        if not full_response:
            yield "抱歉，我没有收到回复。"
    except Exception as e:
        yield f"处理消息时出错: {e}"


def main():
    init_session_state()

    # 显示聊天历史
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # 处理用户输入
    if prompt := st.chat_input("请输入您的问题...", key="chat_input"):
        # 显示用户消息
        with st.chat_message("user"):
            st.markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})

        # 调用Agent获取回复（流式）
        with st.chat_message("assistant"):
            response_container = st.empty()
            full_response = ""

            for chunk in stream_agent_response(prompt):
                full_response += chunk
                response_container.markdown(full_response + "▌")

            response_container.markdown(full_response)
        st.session_state.messages.append({"role": "assistant", "content": full_response})

        # 重新渲染以更新输入框
        st.rerun()


if __name__ == "__main__":
    main()
