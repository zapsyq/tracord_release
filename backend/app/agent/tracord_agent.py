from typing import Annotated
from langchain.agents import create_agent
from langchain_core.tools import tool
from langgraph.prebuilt import InjectedState
from app.agent.model.factory import supervisor_model
from app.agent.utils.prompt_loader import load_prompt
from app.agent.utils.logger_handler import logger
from app.agent.middleware import (
    log_before_model, monitor_tool, force_tool_choice,
    harness_route, ANSWER_PREFIX, FAIL_PREFIX, GIVE_UP_MSG,
)
from app.agent.operation.agent import build_operation_agent
from app.agent.travel.agent import build_travel_agent
from app.agent.chat.agent import build_chat_agent

# 递归上限：超过就判定死循环，强制停止
RECURSION_LIMIT = 8

# 子agent回复命中这些 → 验收判定为"没解决问题"(harness黑名单)
# 只收"真崩溃"(异常兜底的原话), 不收正常业务回答(没有记录/未找到城市/部分失败):
# 拉黑=摘掉换人重答, 正常回答换人也答不出更好的; 部分失败话术会子串撞车误判
FAIL_TEXTS = (
    "无法规划", "规划失败", "处理时出了点问题",      # travel
    "暂时没找到相关资料",                            # rag 知识库miss(非旅行问题/攻略未覆盖) → 折返换chat
    "记账失败", "点亮城市失败",                      # operation 崩溃
    "查看自己的消费账单失败", "查看自己曾经去过的城市失败",
)


def build_supervisor_tools(travel_agent, operation_agent, chat_agent, exclude=None):
    """创建 supervisor 的 3 个子 agent 工具。exclude: 要摘掉的子助手名集合
    (如 {"travel_agent"}), harness 重启时用它堵死再选同一条错路的可能。

    传 None 也能拿到工具定义（供 scripts/gen_finetune_data.py 提取 tool 描述用），
    因为 name/description/args_schema 来自 @tool 装饰器，不依赖 agent 实例。
    """
    def _first_user_query(state: dict) -> str:
        """从 state 取用户原始输入：统一走 InjectedState，避免模型转述失真"""
        msgs = state.get("messages", [])
        return msgs[0].content if msgs else ""

    def _is_fail(text: str) -> bool:
        """验收: 空回复或命中失败黑名单 → 没解决问题"""
        if not text or not text.strip():
            return True
        return any(t in text for t in FAIL_TEXTS)

    async def _run_subagent(agent, query: str) -> tuple[bool, str]:
        """把用户原话丢给子 agent，返回 (是否成功, 最终回复)。
        异常也转成失败，交给 harness 折返，而不是炸掉整条链路。
        """
        try:
            result = await agent.ainvoke(
                {"messages": [{"role": "user", "content": query}]},
                config={"recursion_limit": RECURSION_LIMIT},
            )
            msgs = result.get("messages", [])
            text = msgs[-1].content if msgs else ""
        except Exception as e:
            logger.error(f"[_run_subagent] 子agent执行异常: {e}")
            return False, f"执行出错: {e}"
        return not _is_fail(text), text

    def _wrap_result(ok: bool, agent_name: str, text: str) -> str:
        """把子agent结果包成 harness 标记: 成功直出 / 失败带原因折返"""
        if ok:
            return ANSWER_PREFIX + text
        return f"{FAIL_PREFIX}{agent_name}::{text[:100]}"

    @tool(description="处理旅行规划、行程推荐、攻略")
    async def travel_agent_tool(state: Annotated[dict, InjectedState()]) -> str:
        ok, text = await _run_subagent(travel_agent, _first_user_query(state))
        return _wrap_result(ok, "travel_agent", text)

    @tool(description="处理记账、点亮城市、查账单")
    async def operation_agent_tool(state: Annotated[dict, InjectedState()]) -> str:
        ok, text = await _run_subagent(operation_agent, _first_user_query(state))
        return _wrap_result(ok, "operation_agent", text)

    @tool(description="处理闲聊、日常对话")
    async def chat_agent_tool(state: Annotated[dict, InjectedState()]) -> str:
        ok, text = await _run_subagent(chat_agent, _first_user_query(state))
        return _wrap_result(ok, "chat_agent", text)

    tools = [travel_agent_tool, operation_agent_tool, chat_agent_tool]
    if exclude:
        # 工具名 = 子助手名 + "_tool"
        bad = {n + "_tool" for n in exclude}
        tools = [t for t in tools if t.name not in bad]
    return tools


class TracordAgent:
    def __init__(self, city_service, trip_service, bill_service, user_id: int):
        self.travel_agent = build_travel_agent()
        self.operation_agent = build_operation_agent(city_service, trip_service, bill_service, user_id)
        self.chat_agent = build_chat_agent()
        # 完整版 supervisor(三个子助手都在), 供直接调用; 生产链路走 execute_stream
        self.supervisor = self._make_supervisor()

    def _make_supervisor(self, exclude=None):
        """构建 supervisor。exclude=失败子助手集合: 摘掉对应工具,
        重启后模型想再选同一条错路也选不了。"""
        return create_agent(
            model=supervisor_model,
            tools=build_supervisor_tools(self.travel_agent, self.operation_agent, self.chat_agent, exclude),
            system_prompt=load_prompt("intent"),
            middleware=[log_before_model, monitor_tool, force_tool_choice, harness_route],
        )

    async def execute_stream(self, query: str):
        """harness 主循环:
        正常 → 答案直出;
        某个子助手失败 → 摘掉它、重开一轮全新对话让模型重选
          (每轮对模型都是最熟悉的单轮形态, 不会复读; 工具被摘, 错路走不了第二次);
        travel+operation 都失败 → 固定话术收尾, 不让 chat 硬接业务问题。
        """
        failed = set()
        for attempt in range(3):
            try:
                result = await self._make_supervisor(exclude=set(failed)).ainvoke(
                    {"messages": [{"role": "user", "content": query}]},
                    config={"recursion_limit": RECURSION_LIMIT},
                )
            except Exception as e:
                # 工具执行异常(如本地模型上下文溢出 500) → 友好提示, 不让流中断
                logger.error(f"[execute_stream] 执行异常: {e}", exc_info=True)
                yield "抱歉，处理时出了点问题，可能是输入过长，请简化后重试。"
                return
            msgs = result.get("messages", [])
            answer = msgs[-1].content if msgs and msgs[-1].content else ""
            if not answer:
                # 模型吐了空回复: 没有失败标记可拆, 直接重试, 3轮耗尽走兜底话术
                logger.warning(f"[execute_stream] 第{attempt + 1}轮空回复, 重试")
                continue
            if not answer.startswith(FAIL_PREFIX):
                yield answer
                return
            _, name, _ = answer.split("::", 2)
            failed.add(name)
            logger.warning(f"[execute_stream] 第{attempt + 1}轮 {name} 失败, 摘掉后重开")
            if {"travel_agent", "operation_agent"} <= failed:
                break
        yield GIVE_UP_MSG
