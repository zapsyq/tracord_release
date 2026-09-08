"""
数据源层: 本地 JSON 优先 → API 兜底 → 追加 JSON
用法:
    df = await load_attractions("成都")
    df = await load_restaurants("成都", "火锅")
"""
import json, asyncio
from collections import Counter
from pathlib import Path
import pandas as pd
from app.agent.travel.data_source.amap_client import AmapClient
from app.agent.utils.logger_handler import logger

DATA_DIR = Path(__file__).parent.parent.parent.parent / "data"
ATTRACTIONS_FILE = DATA_DIR / "attractions.json"
RESTAURANTS_FILE = DATA_DIR / "restaurants.json"
_lock = asyncio.Lock()


def _read_json(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _write_json(path: Path, data: list[dict]):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _append_new(existing: list[dict], new_data: list[dict],
                max_per_city: int = 0) -> list[dict]:
    """追加新数据，超上限则跳过"""
    if max_per_city > 0:
        counts = Counter(d["city"] for d in existing)

    added = []
    for d in new_data:
        if max_per_city > 0 and counts.get(d["city"], 0) >= max_per_city:
            continue
        added.append(d)
        if max_per_city > 0:
            counts[d["city"]] += 1

    return existing + added


async def load_attractions(city: str) -> pd.DataFrame:
    """本地有→直接用 | 本地没有→高德→追加 JSON→返回"""
    async with _lock:
        all_data = _read_json(ATTRACTIONS_FILE)
        local = [d for d in all_data if d["city"] == city]

        if local:
            logger.info(f"[景点] {city}: 本地 {len(local)} 条")
            return pd.DataFrame(local)

        logger.info(f"[景点] {city}: 本地无, 调用高德...")
        client = AmapClient()
        try:
            new_data = await client.search_attractions(city)
        finally:
            await client.close()

        if not new_data:
            return pd.DataFrame()

        all_data = _append_new(all_data, new_data, max_per_city=70)
        _write_json(ATTRACTIONS_FILE, all_data)

        result = [d for d in all_data if d["city"] == city]
        logger.info(f"[景点] {city}: 新增 {len(result)} 条")
        return pd.DataFrame(result)


async def load_restaurants(city: str, cuisine: str = None) -> pd.DataFrame:
    """本地有→直接用 | 本地没有→高德→追加 JSON→返回"""
    async with _lock:
        all_data = _read_json(RESTAURANTS_FILE)
        local = [d for d in all_data if d["city"] == city]
        if cuisine:
            local = [d for d in local if cuisine in d.get("cuisine", "")]

        if local:
            logger.info(f"[餐厅] {city} {cuisine or ''}: 本地 {len(local)} 条")
            return pd.DataFrame(local)

        search_kw = cuisine or f"{city}特色菜"
        logger.info(f"[餐厅] {city} {search_kw}: 本地无, 调用高德...")
        client = AmapClient()
        try:
            new_data = await client.search_restaurants(city, keyword=search_kw)
        finally:
            await client.close()

        if not new_data:
            return pd.DataFrame()

        all_data = _append_new(all_data, new_data, max_per_city=100)
        _write_json(RESTAURANTS_FILE, all_data)

        result = [d for d in all_data if d["city"] == city]
        if cuisine:
            result = [d for d in result if cuisine in d.get("cuisine", "")]
        logger.info(f"[餐厅] {city} {search_kw}: 新增 {len(result)} 条")
        return pd.DataFrame(result)


async def load_hotels(city: str, max_price: float = 9999) -> pd.DataFrame:
    from app.agent.travel.data_source.rollinggo_client import RollingGoClient
    client = RollingGoClient()
    try:
        hotels = await client.search_hotels(city, max_price=max_price)
    finally:
        await client.close()
    if not hotels:
        return pd.DataFrame()
    BED_MAP = {"双人床": 2, "大床房": 2, "单人床": 1, "家庭房": 4, "三人间": 3}
    for h in hotels:
        h["numbed"] = BED_MAP.get(str(h.get("numbed", "")), 2)
    return pd.DataFrame(hotels)


TRANSPORT_FILE = DATA_DIR / "transport.json"


async def load_transport(from_city: str, to_city: str) -> pd.DataFrame:
    """本地有→直接用 | 本地没有→12306→追加 JSON→返回"""
    key = f"{from_city}→{to_city}"
    async with _lock:
        cache = _read_json(TRANSPORT_FILE)
        local = [d for d in cache if d.get("_key") == key]
        if local:
            logger.info(f"[交通] {key}: 本地 {len(local)} 条")
            df = pd.DataFrame(local)
            if "_key" in df.columns:
                df = df.drop(columns=["_key"])
        else:
            from app.agent.travel.data_source.transport_client import search_trains
            from datetime import date, timedelta
            # 12306 提前15天预售，搜14天后的，车次最全
            day = (date.today() + timedelta(days=14)).strftime("%Y-%m-%d")
            df = await search_trains(from_city, to_city, day)
            if df.empty:
                return df
            records = df.to_dict(orient="records")
            for r in records:
                r["_key"] = key
            cache.extend(records)
            _write_json(TRANSPORT_FILE, cache)
            logger.info(f"[交通] {key}: 新增 {len(records)} 条")

        # 字段统一: 规划引擎使用小写字段名
        for old_n, new_n in {"StartCity": "start_city", "EndCity": "end_city"}.items():
            if old_n in df.columns:
                df[new_n] = df[old_n]
        tid = "TrainID" if "TrainID" in df.columns else "train_id"
        if tid in df.columns:
            df["transport_type"] = df[tid].apply(lambda x: "airplane" if str(x).startswith("FL") else "train")
        return df
