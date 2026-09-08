"""智能记账工具: 用LangGraph自动处理城市点亮+旅行创建+记账"""
from langchain_core.tools import tool                      # 把函数变成LangChain能识别的"按钮"
from app.agent.utils.logger_handler import logger          # 打日志用
from app.agent.operation.schemas.bills import BillInput, BillItem  # 按钮参数格式(city_name, bills)
from app.agent.operation.graphs.bill_workflow import AutoBillGraph   # 画好的流程图(检查→开灯→创旅行→记账)


def smart_add_bill_tool(city_service, trip_service, bill_service, user_id: int):
    """包一个"智能记账"按钮, 里面跑 LangGraph 图"""

    graph = AutoBillGraph(city_service, trip_service, bill_service)  # 把图画好, 传入数据库操作对象

    @tool(
        args_schema=BillInput,
        # 不加 return_direct: 工具结果回到模型, 让模型生成自然语气回复
        description="当用户需要记录消费时使用。例如：吃饭花了50，打车30，酒店500。支持一次记录多笔消费（如：吃饭两百住宿七百门票90）。工具会自动关联该城市最新旅行。如果城市未点亮会自动点亮，无需用户手动操作。",
    )
    async def add_bill(
        city_name: str,
        bills: list[BillItem],
    ) -> str:
        try:
            logger.info(f"[SmartBill] 用户{user_id} {city_name} {len(bills)}笔")
            # 统一转成 dict 再进图, 避免 BillItem 对象和 dict 混用
            result = await graph.run(
                user_id=user_id, city_name=city_name,
                bills=[b.model_dump() for b in bills],
            )
            logger.info(f"[SmartBill] 结果: {result}")
            return result
        except Exception as e:
            logger.error(f"[SmartBill] 失败: {e}", exc_info=True)
            return f"记账失败: {e}"

    return add_bill
