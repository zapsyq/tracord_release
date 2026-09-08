# -*- coding: utf-8 -*-
"""
微调模型完整智能体交互式测试（带完整日志）

直接初始化完整 TracordAgent（连数据库），输入问题看智能体输出。
会逐步打印：supervisor 路由 → 子agent → 工具调用（名称+参数）→ 工具返回 → 最终回复。
智能体 middleware 的 [log_before_model]/[tool_monitor] 日志也会实时打到控制台。
不用启动后端服务。
用法：python scripts/test_agent_interactive.py
退出：输入 q
"""

import os
import sys
import asyncio
import json
import logging

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(BASE))  # backend/

# 把 agent logger 的控制台级别调到 DEBUG：
# middleware 的 log_before_model / monitor_tool 会打印每一层（supervisor+子agent）
# 的模型调用内容、工具名称和参数，保证日志完整
_logger = logging.getLogger("agent")
_logger.setLevel(logging.DEBUG)
for h in _logger.handlers:
    h.setLevel(logging.DEBUG)

from app.config.db_config import async_session_factory
from app.crud.cities import CitiesRepository
from app.crud.trips import TripsRepository
from app.crud.bills import BillsRepository
from app.crud.notes import NotesRepository
from app.services.cities import CitiesService
from app.services.trips import TripsService
from app.services.bills import BillsService
from app.agent.tracord_agent import TracordAgent

# 测试用的 user_id（改成你自己的）
USER_ID = 1


def _msg_brief(msg) -> str:
    """把一条消息转成易读的文本"""
    kind = type(msg).__name__
    content = getattr(msg, "content", "")
    if not content:
        content = str(msg)
    return f"[{kind}] {content[:150]}"


async def run_once(agent: TracordAgent, query: str):
    """调用智能体一次，逐步打印执行过程，返回最终回复"""
    print("\n" + "=" * 60)
    print(f"用户: {query}")
    print("=" * 60)

    final = ""
    try:
        async for chunk in agent.execute_stream(query):
            final = chunk
    except Exception as e:
        print(f"❌ 调用失败: {e}")
        return

    print("\n" + "-" * 60)
    print(f"🤖 最终回复: {final}")
    print("-" * 60)



async def main():
    print("=" * 60)
    print("完整智能体交互式测试（连数据库 + 完整日志）")
    print("  输入问题看智能体完整执行过程")
    print("  q = 退出")
    print("=" * 60)

    session = async_session_factory()

    try:
        cities_repo = CitiesRepository(session=session)
        trips_repo = TripsRepository(session=session)
        bills_repo = BillsRepository(session=session)
        notes_repo = NotesRepository(session=session)
        city_service = CitiesService(cities_repo, trips_repo, bills_repo, notes_repo)
        trip_service = TripsService(trips_repo, bills_repo, notes_repo)
        bill_service = BillsService(bills_repo, trips_repo)

        agent = TracordAgent(
            city_service=city_service,
            trip_service=trip_service,
            bill_service=bill_service,
            user_id=USER_ID,
        )
        print(f"✅ 智能体初始化完成 (user_id={USER_ID})\n")

        while True:
            text = input(">>> ").strip()
            if not text:
                continue
            if text == "q":
                break
            await run_once(agent, text)
            print()
    finally:
        await session.close()


if __name__ == "__main__":
    asyncio.run(main())
