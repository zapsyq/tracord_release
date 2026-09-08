from langchain_core.tools import tool
from app.services.cities import CitiesService
from app.agent.utils.logger_handler import logger
from app.core.constants import CITY_ADCODE_MAP, ADCODE_CITY_MAP
from app.agent.operation.schemas.cities import CityListInput
from fastapi import HTTPException

#城市操作工具
def city_tools(service: CitiesService, user_id: int):
    @tool(
            args_schema=CityListInput,
            # 不加 return_direct: 工具结果回到模型, 让模型生成自然语气回复
            description="当用户想要点亮或记录自己曾经去过某个城市时使用。支持一次点亮多个城市，例如：去过北京、上海、广州。",
    )
    async def light_city(city_names: list[str]) -> str:
        if not city_names:                                     # 空列表防御: 没有要点的城市
            return "没有需要点亮的城市"
        logger.info(f"用户{user_id}请求点亮城市: {city_names}")
        try:
            # 逐个点亮, 收集成败; 部分失败也要如实上报, 不整体报错
            success, already, failed = [], [], []
            for city_name in city_names:
                adcode = CITY_ADCODE_MAP.get(city_name)
                if not adcode:
                    failed.append(city_name)
                    continue
                if await service.city_repo.is_lighted(user_id, adcode):   # 已点亮是正常状态, 不进异常流
                    already.append(city_name)
                    continue
                try:
                    await service.light_city(user_id=user_id, adcode=adcode)
                    success.append(city_name)
                except HTTPException as e:
                    failed.append(f"{city_name}({e.detail})")
                except Exception:
                    failed.append(city_name)
            parts = []
            if success: parts.append(f"点亮城市{'、'.join(success)}成功")
            if already: parts.append(f"{'、'.join(already)}之前已点亮过")
            if failed: parts.append(f"{'、'.join(failed)}点亮失败")
            return "；".join(parts)
        except Exception as e:
            logger.error(f"用户{user_id}请求点亮城市失败: {e}", exc_info=True)
            return "点亮城市失败"

    @tool(description="当用户想要查看自己曾经去过的城市时使用。")
    async def get_lighted_cities() -> str | list[str]:
        try:
            logger.info(f"用户{user_id}请求查看自己曾经去过的城市")
            result = await service.get_lighted_cities(user_id=user_id)
            logger.info(f"用户{user_id}请求查看自己曾经去过的城市成功")
            city_names = [ADCODE_CITY_MAP[adcode] for adcode in result if adcode in ADCODE_CITY_MAP]
            return city_names
        except Exception as e:
            logger.error(f"用户{user_id}请求查看自己曾经去过的城市失败: {e}", exc_info=True)
            return "查看自己曾经去过的城市失败"

    return [light_city, get_lighted_cities]