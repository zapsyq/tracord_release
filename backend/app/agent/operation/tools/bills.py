from langchain_core.tools import tool
from app.services.bills import BillsService
from app.services.trips import TripsService
from app.agent.utils.logger_handler import logger
from app.core.constants import CITY_ADCODE_MAP, CATEGORY_ENUM_MAP
from app.agent.operation.schemas.cities import CityInput

#账单查询工具，查找某城市的最新旅行账单
def bill_tools(bill_service: BillsService, trip_service: TripsService, user_id: int):
    @tool(
        args_schema=CityInput,
        description="查询用户在指定城市的真实账单，返回按分类汇总的消费明细和总计。必须根据工具返回的数据回答。禁止编造不存在的消费记录。",
        # return_direct: 账单是数字类数据, 代码按分类汇总更准确, 直接透传给用户(模型复述可能改错金额)
        return_direct=True
    )
    async def get_bills(city_name: str):
        try:
            logger.info(f"用户{user_id}请求查看自己的消费账单")
            adcode = CITY_ADCODE_MAP.get(city_name)
            if not adcode:
                logger.warning(f"未找到{city_name}的城市编码")
                return f"未找到{city_name}的城市编码"
            trip = await trip_service.get_latest_trip(user_id=user_id, adcode=adcode)
            if not trip:
                logger.warning(f"未找到用户旅行记录")
                return f"当前没有旅行记录, 请先创建旅行"
            result = await bill_service.get_trip_bills(user_id=user_id, trip_id=trip.id)
            logger.info(f"用户{user_id}请求查看自己的消费账单成功")

            if not result:
                return "该城市暂无账单记录"
            # 按分类汇总: 数字在代码里算, 不让模型复述
            summary: dict[str, float] = {}
            total = 0.0
            for bill in result:
                category_name = (
                    bill.custom_category
                    if bill.category == 6 and bill.custom_category
                    else CATEGORY_ENUM_MAP.get(bill.category, "其他")
                )
                amount = float(bill.amount)
                summary[category_name] = summary.get(category_name, 0.0) + amount
                total += amount
            parts = [f"{name} {_fmt_money(amt)}元" for name, amt in summary.items()]
            parts.append(f"总计 {_fmt_money(total)}元")
            return "，".join(parts)

        except Exception as e:
            logger.error(f"用户{user_id}请求查看自己的消费账单失败: {e}", exc_info=True)
            return "查看自己的消费账单失败"

    return get_bills


def _fmt_money(amount: float) -> str:
    """50.0 → 50, 49.5 → 49.5, 保留最多2位小数"""
    return f"{amount:.2f}".rstrip("0").rstrip(".")
