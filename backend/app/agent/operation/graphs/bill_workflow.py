"""
自动点亮城市 + 记账 LangGraph workflow
流程: 检查城市是否点亮 → 没亮就点亮 → 没旅行就创建 → 记账
"""
from typing import TypedDict                                  # 定义共享笔记本的结构
from langgraph.graph import StateGraph, END                   # 画图工具: StateGraph(图纸), END(终点)
from app.core.constants import CITY_ADCODE_MAP                # 城市名→编码对照表
from fastapi import HTTPException


class BillState(TypedDict):                                    # 共享笔记本, 图中所有节点都能读写
    user_id: int                                               # 谁在操作
    city_name: str                                             # 哪个城市, 如"杭州"
    bills: list[dict]                                          # 消费明细列表, 每笔含 amount/category
    adcode: str                                                # 城市编码, 如杭州="330100", 由查表得到
    is_lit: bool                                               # 城市是否已点亮, 由 _check_city 填充, 路由用
    result: str                                                # 最终返回给用户的话, 如"记账成功"


class AutoBillGraph:
    """把检查→开灯→创旅行→记账焊在一起的图, 对外只露一个run()方法"""

    def __init__(self, city_service, trip_service, bill_service):
        self.city_svc = city_service                           # 城市相关的数据库操作
        self.trip_svc = trip_service                           # 旅行相关的数据库操作
        self.bill_svc = bill_service                           # 账单相关的数据库操作
        self.graph = self._build()                             # 初始化时就把图画好, 编译存起来

    # ═══════════════ 四个步骤（节点） ═══════════════

    async def _check_city(self, state: BillState):                                  # 步骤1: 查城市灯亮没亮
        adcode = CITY_ADCODE_MAP.get(state["city_name"])                            # "杭州" → "330100"
        if not adcode:                                                              # 查不到说明用户说的不是支持的城市
            return {"result": f"未找到城市: {state['city_name']}", "adcode": ""}     # result非空会触发走END
        is_lit = await self.city_svc.city_repo.is_lighted(                          # 查数据库 light_cities 表
            state["user_id"], adcode)                                               # 看这个用户有没有点亮过这个城市
        return {"adcode": adcode, "is_lit": is_lit}                                 # 把编码和亮没亮写回笔记本

    async def _light_city(self, state: BillState):                  # 步骤2: 点亮城市(service自带创建旅行+失败回滚)
        try:
            await self.city_svc.light_city(state["user_id"], state["adcode"])
        except HTTPException as e:
            # 城市已点亮（检查步骤可能误判）时直接跳过，继续记账
            if e.status_code == 400 and "已点亮" in str(e.detail):
                return {}
            raise
        return {}

    async def _add_bill(self, state: BillState):               # 步骤3: 真正写账单(循环写多笔)
        if state.get("result"):                                # 前面步骤已经出错了, 直接跳过
            return {}
        if not state.get("bills"):                             # 空列表防御: 没有可记账的消费
            return {"result": "没有需要记录的消费"}
        from decimal import Decimal                            # 金额用 Decimal 保证精度, 不用 float
        try:
            trip = await self.trip_svc.get_latest_trip(        # 取该城市最新的一条旅行
                state["user_id"], state["adcode"])
            # 逐笔记账, 收集成败; 部分失败也要如实上报, 不整体报错
            success, failed = [], []
            total = 0.0
            for i, b in enumerate(state["bills"], 1):
                try:
                    await self.bill_svc.add_bill(              # 调 service 写 bills 表
                        user_id=state["user_id"],
                        trip_id=trip.id,                       # 账单挂在哪个旅行下面
                        amount=Decimal(str(b["amount"])),      # float → string → Decimal, 避免浮点误差
                        category=b["category"],
                    )
                    success.append(b)
                    total += float(b["amount"])
                except HTTPException as e:
                    failed.append(f"第{i}笔({_fmt(float(b['amount']))}元)失败：{e.detail}")
                except Exception as e:
                    failed.append(f"第{i}笔({_fmt(float(b['amount']))}元)失败：{str(e)}")
            # 攒段拼装: 成功在前, 失败在后
            parts = []
            if success: parts.append(f"在{state['city_name']}记账{len(success)}笔共{_fmt(total)}元成功")
            if failed: parts.append("；".join(failed))
            return {"result": "；".join(parts)}
        except Exception as e:
            return {"result": f"记账失败: {str(e)}"}

    # ═══════════════ 岔路口（路由） ═══════════════

    def _route_after_check(self, state: BillState):            # 检查完城市后决定走哪条路
        if state.get("result"):                                # result 非空说明城市名无效, 直接结束
            return END
        if state.get("is_lit"):                                # 灯已经亮了 → 跳过开灯, 直接去确保旅行
            return "add_bill"
        return "light_city"                                    # 灯没亮 → 先去开灯

    # ═══════════════ 画图（连线） ═══════════════

    def _build(self):
        g = StateGraph(BillState)                               # 拿张空图纸, 笔记本格式是 BillState
        g.add_node("check_city", self._check_city)              # 画方框1: 检查城市
        g.add_node("light_city", self._light_city)              # 画方框2: 开灯
        g.add_node("add_bill", self._add_bill)                  # 画方框3: 记账
        g.set_entry_point("check_city")                         # 入口: 从检查城市开始
        g.add_conditional_edges(                                # 从检查城市出来的岔路口:
            "check_city",                                       # 起点
            self._route_after_check,                            # 看笔记本决定走哪边
            {"light_city": "light_city",                        # 返回"light_city" → 去开灯
             "add_bill": "add_bill",                            # 返回"add_bill" → 直接记账
             END: END})                                         # 返回END → 直接结束(城市无效)
        g.add_edge("light_city", "add_bill")                    # 线: 开完灯 → 记账
        g.add_edge("add_bill", END)                             # 线: 记完账 → 结束
        return g.compile()                                      # 编译, 把图变成可以执行的程序

    # ═══════════════ 对外入口 ═══════════════

    async def run(self, user_id: int, city_name: str, bills: list[dict]):
        state: BillState = {                                   # 建一个全新的笔记本, 填好初始数据
            "user_id": user_id,
            "city_name": city_name,
            "bills": bills,
            "adcode": "",                                      # 等检查城市时填充
            "is_lit": False,                                   # 等检查城市时填充
            "result": ""                                       # 等记账成功时填充
        }
        result = await self.graph.ainvoke(state)               # 把笔记本丢进图, 让它按箭头跑
        return result["result"]                                # 拿出最终结果返回给调用者


def _fmt(amount: float) -> str:
    """990.0 → 990, 990.5 → 990.5, 去掉多余的0"""
    return f"{amount:.2f}".rstrip("0").rstrip(".")
