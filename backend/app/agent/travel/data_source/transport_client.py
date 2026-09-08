"""
12306 火车票查询 — 直接调 12306 内部接口，零外部依赖
参考: mcp-server-12306 (drfccv)
用法: df = await search_trains("北京", "上海", "2026-08-15")
"""
import re
import pandas as pd
import httpx
from app.agent.utils.logger_handler import logger

# 12306 API endpoints
INIT_URL = "https://kyfw.12306.cn/otn/leftTicket/init"
TICKET_URL = "https://kyfw.12306.cn/otn/leftTicket/queryI"
PRICE_URL = "https://kyfw.12306.cn/otn/leftTicketPrice/queryAllPublicPrice"
STATION_JS = "https://kyfw.12306.cn/otn/resources/js/framework/station_name.js"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/123.0.0.0 Safari/537.36",
    "Referer": "https://kyfw.12306.cn/otn/leftTicket/init",
    "Origin": "https://kyfw.12306.cn",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "X-Requested-With": "XMLHttpRequest",
}

_station_map: dict[str, str] | None = None


def _format_price(raw: str) -> float:
    """12306 价格: 原始值÷10=元 (如 01445→144.5)"""
    if not raw or not raw.strip():
        return 0.0
    try:
        return int(raw.strip()) / 10.0
    except ValueError:
        return 0.0


async def _load_stations() -> dict[str, str]:
    global _station_map
    if _station_map:
        return _station_map
    try:
        async with httpx.AsyncClient(timeout=10) as c:
            resp = await c.get(STATION_JS, headers={"User-Agent": HEADERS["User-Agent"]})
        text = resp.text
        m = re.search(r"station_names\s*=\s*'([^']+)'", text)
        if not m:
            return {}
        _station_map = {}
        for item in m.group(1).split("@"):
            if not item: continue
            parts = item.split("|")
            if len(parts) >= 3 and parts[1] not in _station_map:
                _station_map[parts[1]] = parts[2]
        logger.info(f"[12306] 车站: {len(_station_map)}个")
    except Exception as e:
        logger.error(f"[12306] 车站加载失败: {e}")
        _station_map = {}
    return _station_map


async def search_trains(from_city: str, to_city: str, date: str) -> pd.DataFrame:
    stations = await _load_stations()
    from_code = stations.get(from_city, "")
    to_code = stations.get(to_city, "")
    if not from_code:
        for k, v in stations.items():
            if from_city in k: from_code = v; break
    if not to_code:
        for k, v in stations.items():
            if to_city in k: to_code = v; break
    if not from_code or not to_code:
        logger.warning(f"[12306] 车站未找到: {from_city}→{to_city}")
        return pd.DataFrame()

    try:
        # 1. init 建立会话
        async with httpx.AsyncClient(timeout=15, verify=False, follow_redirects=True) as c:
            await c.get(INIT_URL, headers=HEADERS)

            # 2. 查票
            resp = await c.get(TICKET_URL, headers=HEADERS, params={
                "leftTicketDTO.train_date": date,
                "leftTicketDTO.from_station": from_code,
                "leftTicketDTO.to_station": to_code,
                "purpose_codes": "ADULT",
            })
            data = resp.json()
            tickets = data.get("data", {}).get("result", [])
            station_map = data.get("data", {}).get("map", {})

            # 3. 查票价（同一个 session）
            price_resp = await c.get(PRICE_URL, headers=HEADERS, params={
                "leftTicketDTO.train_date": date,
                "leftTicketDTO.from_station": from_code,
                "leftTicketDTO.to_station": to_code,
                "purpose_codes": "ADULT",
            })
            price_data = price_resp.json()

            # 构建 train_no → 最低票价 映射
            price_map = {}
            for item in price_data.get("data", []):
                dto = item.get("queryLeftNewDTO", {})
                tn = dto.get("train_no", "")
                prices = [
                    _format_price(dto.get(k, ""))
                    for k in ("ze_price", "zy_price", "swz_price",  # 高铁
                              "yz_price", "yw_price", "rw_price")   # 普速
                ]
                valid = [p for p in prices if p > 0]
                if valid and tn:
                    price_map[tn] = min(valid)

        # 4. 解析
        rows = []
        for item in tickets:
            parts = item.split("|")
            if len(parts) < 11: continue
            tn = parts[2]
            cost = price_map.get(tn, 0.0)
            # 存短车次(如 G104)，不存内部 train_no(如 71000G161604)
            m = re.search(r'[GDCKTZYLS]\d{1,4}', str(tn))
            train_code = m.group() if m else tn
            rows.append({
                "From": station_map.get(parts[6], parts[6]),
                "To": station_map.get(parts[7], parts[7]),
                "BeginTime": parts[8],
                "EndTime": parts[9],
                "Duration": parts[10],
                "Cost": cost,
                "TrainID": train_code,
                "StartCity": from_city,
                "EndCity": to_city,
            })

        logger.info(f"[12306] {from_city}→{to_city} {date}: {len(rows)}趟")
        return pd.DataFrame(rows)

    except Exception as e:
        logger.error(f"[12306] {from_city}→{to_city}: {e}")
        return pd.DataFrame()
