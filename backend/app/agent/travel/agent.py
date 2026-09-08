"""旅游 agent：行程规划 + RAG 攻略"""
from langchain.agents import create_agent
from app.agent.model.factory import chat_model
from app.agent.middleware import log_before_model, monitor_tool
from app.agent.utils.prompt_loader import load_prompt
from app.agent.travel.tools.travel_plan import travel_plan
from app.agent.travel.tools.rag import rag_summary


def build_travel_agent():
    return create_agent(
        model=chat_model,
        tools=[travel_plan, rag_summary],
        system_prompt=load_prompt("travel"),
        middleware=[log_before_model, monitor_tool],
    )
