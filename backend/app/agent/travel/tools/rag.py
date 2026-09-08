from typing import Annotated
from langchain_core.tools import tool
from langgraph.prebuilt import InjectedState
from app.agent.travel.services.rag_service import RagSummaryService

rag = RagSummaryService()

# rag检索工具：原话从 state 透传，避免模型转述失真（与 travel_plan 一致）
@tool(
    description="回答旅行攻略类问题：某地有什么景点、美食推荐、避雷、注意事项等。用户只是问信息、没有要求规划行程时调用。",
    return_direct=True
)
async def rag_summary(state: Annotated[dict, InjectedState()]) -> str:
    msgs = state.get("messages", [])
    query = msgs[0].content if msgs else ""
    # 只查本地攻略知识库; miss 返回失败话术 → harness 黑名单 → 摘掉 travel_agent 重开一轮,
    # 非旅行问题(如"刘备是三国的人物吗")自然进不了 rag, 会折返给 chat
    return rag.rag_summary(query)
