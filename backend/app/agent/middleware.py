from langchain.agents.middleware import wrap_tool_call, before_model, wrap_model_call
from langchain.agents.middleware.types import ModelResponse
from langchain.tools.tool_node import ToolCallRequest
from langchain_core.messages import ToolMessage, AIMessage
from langgraph.types import Command
from typing import Callable
from app.agent.utils.logger_handler import logger
from langchain.agents import AgentState
from langgraph.runtime import Runtime


#强制路由层必须调用工具(只看意图, 不许直接回答)。
#微调模型在 --reasoning off 下对模糊问候(如"你好")会随机输出路由名裸文本
#而不是发起工具调用, tool_choice=required 强制模型每次必选一个子助手。temp配0.1。
@wrap_model_call
async def force_tool_choice(request, handler):
    request.tool_choice = "required"
    return await handler(request)


# ===== harness: 子agent结果验收 =====
#工具用这两个标记回传结果, harness 据此决定 直出/重启
ANSWER_PREFIX = "__ANSWER__::"
FAIL_PREFIX = "__FAIL__::"
#所有子助手都失败后的固定话术
GIVE_UP_MSG = "抱歉，没太理解你的意思。你是想规划旅行行程，还是记一笔账或查账单？"


@wrap_model_call
async def harness_route(request, handler):
    """子agent结果验收层(harness核心), 在模型开口前拦截:
    - 成功(__ANSWER__) → 短路直出, 不给小模型转述原答案的机会
    - 失败(__FAIL__) → 不喂回给模型(实测 0.8B 没训过折返对话, 会复读成裸文本),
      把失败标记原样抛出, 由外层 execute_stream 摘掉失败子助手、重开一轮全新对话
    """
    msgs = request.messages
    last = msgs[-1] if msgs else None
    if isinstance(last, ToolMessage) and isinstance(last.content, str):
        # 成功: 短路, 答案原样给用户
        if last.content.startswith(ANSWER_PREFIX):
            answer = last.content[len(ANSWER_PREFIX):]
            logger.info(f"[harness] 验收通过, 短路直出 ({len(answer)}字)")
            return ModelResponse(result=[AIMessage(content=answer)])
        # 失败: 原样抛给外层重启
        if last.content.startswith(FAIL_PREFIX):
            _, agent_name, reason = last.content.split("::", 2)
            logger.warning(f"[harness] {agent_name} 失败({reason}), 交给外层重启")
            return ModelResponse(result=[AIMessage(content=last.content)])
    return await handler(request)

#工具执行的监控
@wrap_tool_call
async def monitor_tool(
    #请求的数据封装(用户输入的参数)
    request: ToolCallRequest,
    #执行的函数本身(函数)
    handler: Callable[[ToolCallRequest], ToolMessage | Command],
) -> ToolMessage | Command:

    logger.info(f"[tool_monitor] 执行工具: {request.tool_call["name"]}")
    logger.info(f"[tool_monitor] 传入参数: {request.tool_call["args"]}")
    try:
        result = await handler(request)
        logger.info(f"[tool_monitor] 工具{request.tool_call["name"]}调用成功")
        return result
    except Exception as e:
        logger.error(f"[tool_monitor] 工具执行异常: 原因: {str(e)}")
        raise e


#在模型执行前输出日志
@before_model
def log_before_model(
    #整个agent中的状态记录
    state: AgentState,
    #记录了整个执行过程中的上下文信息
    runtime: Runtime,
):
    logger.info(f"[log_before_model]即将调用模型, 带有{len(state["messages"])}条信息")
    logger.debug(f"[log_before_model] {type(state["messages"][-1]).__name__}: {state["messages"][-1].content.strip()}")

    return None
