"""
旅行规划工具: 调 solve() 生成行程单, return_direct 直接作为最终答案
不接收 query 参数, 用 InjectedState 从 state 读用户原始消息, 避免 LLM 改写
返回值: ⟦PLAN⟧{精简JSON}⟦/PLAN⟧ (前端时间轴卡片数据)
规划失败/无行程时返回 warning 原文, 照旧触发 harness 黑名单重试
"""
import json
from typing import Annotated
from langchain_core.tools import tool
from langgraph.prebuilt import InjectedState
from app.agent.travel.services.travel_plan_tool import solve, plan_to_frontend


@tool(description="根据用户的旅行需求生成行程规划。用户提到想去某地玩/旅行/规划时调用。", return_direct=True)
async def travel_plan(state: Annotated[dict, InjectedState()]) -> str:
    msgs = state.get("messages", [])
    query = msgs[0].content if msgs else ""
    plan = await solve(query)
    payload = plan_to_frontend(plan)
    if payload:
        return f"⟦PLAN⟧{json.dumps(payload, ensure_ascii=False, separators=(',', ':'))}⟦/PLAN⟧"
    return plan.get("warning", "无法规划")
