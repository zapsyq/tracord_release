"""聊天 agent：闲聊，高温度自然对话"""
from langchain.agents import create_agent
from app.agent.model.factory import chat_model
from app.agent.middleware import log_before_model, monitor_tool
from app.agent.utils.prompt_loader import load_prompt


def build_chat_agent():
    return create_agent(
        model=chat_model,
        tools=[],
        system_prompt=load_prompt("chat"),
        middleware=[log_before_model, monitor_tool],
    )
