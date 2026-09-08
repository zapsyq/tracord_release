# -*- coding: utf-8 -*-
"""
微调训练数据生成脚本（LLaMA-Factory / Qwen tool calling）

你只需要在 build_examples() 里填「对话数据」，其余全是现成的：
  - system prompt 自动从 backend/app/agent/prompts/ 读取，和部署一致（改了 prompt 文件脚本自动跟着变）
  - 工具定义自动从代码里的 @tool 提取，description 和参数 schema 跟代码完全一致

填一条样本的样子：
    add(OPERATION_PROMPT, OPERATION_TOOLS, [
        H("点亮城市北海"),                          # 用户说的话
        CALL("light_city", {"city_names": ["北海"]}),  # 模型该调什么工具、传什么参数
        O("点亮城市北海成功"),                       # 工具实际返回
        A("点亮城市北海成功"),                       # 最终回答用户
    ])

四个角色（同一个 0.8b 模型要演 4 个角色，都要覆盖）：
  supervisor  → system=INTENT_PROMPT,    tools=SUPERVISOR_TOOLS  （意图路由）
  travel      → system=TRAVEL_PROMPT,    tools=TRAVEL_TOOLS      （调 travel_plan）
  operation   → system=OPERATION_PROMPT, tools=OPERATION_TOOLS   （调具体工具）
  chat        → system=CHAT_PROMPT,      tools=[]                （不调工具、直接回复）

注意：无参数工具（InjectedState）CALL 时可不传 args，会自动填 arguments: {}。

运行：python scripts/gen_finetune_data.py
输出：backend/train_data/tool_calling_train.jsonl（追加写：每次跑把 build_examples() 里的样本追加进文件，文件累积）
注意：build_examples() 里只放「这一批新加的」样本，生成过的就删掉，不然会重复
"""

import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(BASE))  # backend/ 目录，让 app.* 能 import

from langchain_core.utils.function_calling import convert_to_openai_tool


# ---- system prompt（自动读真实文件，和部署一致）----
PROMPT_DIR = os.path.join(BASE, "..", "app", "agent", "prompts")


def _load(name):
    with open(os.path.join(PROMPT_DIR, name), encoding="utf-8") as f:
        return f.read()


INTENT_PROMPT = _load("intent_prompt.txt")
TRAVEL_PROMPT = _load("travel_prompt.txt")
OPERATION_PROMPT = _load("operation_prompt.txt")
CHAT_PROMPT = _load("chat_prompt.txt")


# ---- 工具定义：从代码里的 @tool 自动提取 ----
def _to_openai(tool):
    """把 LangChain 工具转成 OpenAI function calling 格式（name/description/parameters）。"""
    return convert_to_openai_tool(tool)["function"]


# travel 工具（模块级 @tool，直接 import）
from app.agent.travel.tools.travel_plan import travel_plan
from app.agent.travel.tools.rag import rag_summary

# operation 工具（工厂函数传 None 拿定义；name/description/args_schema 不依赖 service 实例）
from app.agent.operation.tools.cities import city_tools
from app.agent.operation.tools.bills import bill_tools
from app.agent.operation.tools.smart_bill import smart_add_bill_tool

# supervisor 的 3 个子 agent 工具（传 None 拿定义）
from app.agent.tracord_agent import build_supervisor_tools

TRAVEL_TOOLS = [_to_openai(travel_plan), _to_openai(rag_summary)]
OPERATION_TOOLS = (
    [_to_openai(t) for t in city_tools(None, 1)]
    + [_to_openai(bill_tools(None, None, 1))]
    + [_to_openai(smart_add_bill_tool(None, None, None, 1))]
)
SUPERVISOR_TOOLS = [_to_openai(t) for t in build_supervisor_tools(None, None, None)]


# ---- 消息构造 ----
def H(text):
    """human：用户说的话"""
    return {"from": "human", "value": text}


def CALL(name, args=None):
    """function_call：模型调工具（args 是参数 dict，无参数工具可省略）"""
    return {"from": "function_call", "value": json.dumps({"name": name, "arguments": args or {}}, ensure_ascii=False)}


def O(text):
    """observation：工具返回结果"""
    return {"from": "observation", "value": text}


def A(text):
    """gpt：最终回答用户的话"""
    return {"from": "gpt", "value": text}


# ---- 写文件 ----
OUTPUT = os.path.join(BASE, "..", "train_data", "tool_calling_train.jsonl")


def add(system, tools, messages, path=OUTPUT):
    """把一条样本序列化并写进 jsonl 文件（build_examples 开头已清空旧文件）。"""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    line = {
        "system": system,
        "tools": json.dumps(tools, ensure_ascii=False) if tools else "",
        "messages": messages,
    }
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(line, ensure_ascii=False) + "\n")
    first = messages[0]["value"] if messages else ""
    print(f"[ok] {first[:30]}...")


def build_examples():
    """↓↓↓ 在这里填「这一批要追加的」样本（已生成过的从脚本里删掉，避免重复）↓↓↓"""

    # # ① supervisor：学意图路由
    # add(INTENT_PROMPT, SUPERVISOR_TOOLS, [
    #     H("徐州周末去哪里逛逛"),
    #     CALL("travel_agent_tool"),
    #     O("旅行Agent调用成功"),
    #     A("旅行Agent调用成功"),
    # ])
    # add(INTENT_PROMPT, SUPERVISOR_TOOLS, [
    #     H("在天津吃火锅花了120"),
    #     CALL("operation_agent_tool"),
    #     O("软件操作Agent调用成功"),
    #     A("软件操作Agent调用成功"),
    # ])
    # add(INTENT_PROMPT, SUPERVISOR_TOOLS, [
    #     H("你怎么知道这么多"),
    #     CALL("chat_agent_tool"),
    #     O("聊天Agent调用成功"),
    #     A("聊天Agent调用成功"),
    # ])

    # # ② travel：学调 travel_plan（无参数）
    # add(TRAVEL_PROMPT, TRAVEL_TOOLS, [
    #     H("帮我设计一个五天的桂林行"),
    #     CALL("travel_plan"),
    #     O("旅行规划工具调用成功"),
    #     A("旅行规划工具调用成功"),
    # ])
    # add(TRAVEL_PROMPT, TRAVEL_TOOLS, [
    #     H("去大理古城有什么注意的事项吗"),
    #     CALL("rag_summary"),
    #     O("旅行知识库工具调用成功"),
    #     A("旅行知识库工具调用成功"),
    # ])

    # # operation：学调具体工具
    # add(OPERATION_PROMPT, OPERATION_TOOLS, [
    #     H("沈阳也去过一次"),
    #     CALL("light_city", {"city_names": ["沈阳"]}),
    #     O("沈阳之前已点亮过"),
    #     A("我看到您去过沈阳啦！好玩吗？"),
    # ])
    # add(OPERATION_PROMPT, OPERATION_TOOLS, [
    #     H("在上海打车花了65块"),
    #     CALL("add_bill", {"city_name": "上海", "bills": [{"amount": 65, "category": 1}]}),
    #     O("在上海记账1笔共65元成功"),
    #     A("上海打车65块确实不便宜哎，下次可以坐地铁省点。"),
    # ])
    # add(OPERATION_PROMPT, OPERATION_TOOLS, [
    #     H("查一下厦门的账单明细"),
    #     CALL("get_bills", {"city_name": "厦门"}),
    #     O("账单查询工具调用成功"),
    #     A("账单查询工具调用成功"),
    # ])
    # add(OPERATION_PROMPT, OPERATION_TOOLS, [
    #     H("我有去过哪里吗"),
    #     CALL("get_lighted_cities"),
    #     O('[]'),
    #     A("你还没有点亮任何城市呢，什么时候出去走走呀！"),
    # ])

    #  chat：学不调工具、直接回复（tools 为空）
    add(CHAT_PROMPT, [], [
        H("我现在只想躺在家里睡觉"),
        A("好好休息也很重要呀，等精神恢复了再计划下一次出行！"),
    ])

    print("done")


if __name__ == "__main__":
    build_examples()
