"""
旅行规划 — 小模型槽位填充 → 规划引擎搜索 → JSON/API 数据源
搜索内核: planner_engine.py, 依据 docs/planner_engine_spec.md 独立实现
数据层: 本地 JSON 优先 → 高德/12306/RollingGo API 兜底
"""

import pandas as pd
from app.agent.utils.logger_handler import logger
from app.agent.travel.services.planner_engine import Planner, sleep_ok

# ═══════════════ 数据加载 ═══════════════

#加载规划所需数据(景点/餐厅/酒店/城际交通), 供规划引擎使用
async def load_data(cons):
    from app.agent.travel.data_source.data_sources import (
        load_attractions, load_restaurants, load_hotels, load_transport
    )
    city = cons.get("target_city", "")
    start_city = cons.get("start_city", "")
    # 目的地没填出来, 不调API, 避免浪费额度
    if not city or city == "?":
        return {"attractions": pd.DataFrame(), "restaurants": pd.DataFrame(),
                "accommodations": pd.DataFrame(), "intercity_transport": pd.DataFrame()}

    df_attractions = await load_attractions(city)
    df_hotels = await load_hotels(city, max_price=cons.get("budget", 5000))
    df_restaurants = await load_restaurants(city)

    if start_city == city:
        df_rides = pd.DataFrame()
    else:
        df_rides_go = await load_transport(start_city, city)
        df_rides_back = await load_transport(city, start_city)
        df_rides = pd.concat([df_rides_go, df_rides_back], ignore_index=True) \
            if not df_rides_go.empty or not df_rides_back.empty else pd.DataFrame()

    return {"attractions": df_attractions, "restaurants": df_restaurants,
            "accommodations": df_hotels, "intercity_transport": df_rides}

# ═══════════════ 规划主流程 ═══════════════

#行程plan → 前端时间轴卡片要的精简JSON, 没有行程返回None
def plan_to_frontend(plan):
    if not plan.get("itinerary"):
        return None
    days = []
    for day in plan.get("itinerary", []):
        acts = []
        for act in day.get("activities", []):
            acts.append({
                "type": act.get("type", ""),                  # train/airplane/intercity/breakfast/lunch/dinner/attraction/accommodation/free
                "position": act.get("position", ""),          # 地点(车站/餐厅/景点/酒店)
                "start": act.get("start", ""),                # 跨城交通: 出发城市
                "end": act.get("end", ""),                    # 跨城交通: 到达城市
                "vehicle": act.get("TrainID", "") or act.get("FlightID", ""),  # 车次/航班号
                "start_time": act.get("start_time", ""),
                "cost": round(float(act.get("cost", 0) or 0), 2),
                "transports": [                               # 市内交通(前往该活动的过程)
                    {"mode": ride.get("mode", ""), "start_time": ride.get("start_time", ""),
                     "cost": round(float(ride.get("cost", 0) or 0), 2)}
                    for ride in act.get("transports", [])
                ],
            })
        days.append({"day": day.get("day", 0), "activities": acts})
    # 总花费口径与 solve() 的预算警告一致: 活动费用 + 各自交通费
    total_cost = sum(act["cost"] + sum(ride["cost"] for ride in act["transports"])
                     for day in days for act in day["activities"])
    return {
        "days": len(days),
        "people": plan.get("people_number", 1),
        "total_cost": round(total_cost, 2),
        "warning": plan.get("warning"),       # 如"预算不足"，可为 None
        "itinerary": days,
    }

#跨城规划 or 同城推荐: 槽位填充 → 加载数据 → 引擎搜索 → 睡眠过滤 → 预算警告
async def solve(query: str):
    from app.agent.travel.services.slot_filler import get_slot_filler
    cons = await get_slot_filler().fill_slots(query)
    logger.info(f"[solve] from={cons['start_city']} to={cons['target_city']} days={cons['days']} budget={cons['budget']}")

    # 无出发地 → 同城模式
    if cons["start_city"] in ("?", ""):
        cons["start_city"] = cons["target_city"]
    if cons["start_city"] == cons["target_city"] and cons["days"] > 1:
        cons["days"] = 1

    data = await load_data(cons)
    logger.info(f"[solve] data: attr={len(data['attractions'])} rest={len(data['restaurants'])} hotel={len(data['accommodations'])} ic={len(data['intercity_transport'])}")

    planner = Planner(cons, data)
    ok, result = planner.search()
    if isinstance(result, list):
        plan = {"people_number": cons["people_number"], "start_city": cons["start_city"],
                "target_city": cons["target_city"], "itinerary": result}
    else:
        plan = result
    plan["search_stats"] = {"nodes": planner.nodes, "backtracks": planner.bt}

    # 引擎已保证时间有序不重叠, 这里只兜底过滤深夜活动
    for day in plan.get("itinerary", []):
        day["activities"] = [act for act in day.get("activities", []) if sleep_ok(act)]

    # 预算警告
    total_cost = sum(act.get("cost", 0) + sum(ride.get("cost", 0) for ride in act.get("transports", []))
                     for day in plan.get("itinerary", []) for act in day.get("activities", []))
    if total_cost > cons.get("budget", 0):
        plan["warning"] = f"预算不足：预计花费 ¥{total_cost:.0f}，超出预算 ¥{total_cost - cons['budget']:.0f}"
    elif not ok:
        plan["warning"] = plan.get("warning", "无法规划")

    return plan
