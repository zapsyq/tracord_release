"""
高德地图 POI 搜索 — 景点 + 餐厅
Key: .env 的 AMAP_KEY
测试: python -m app.agent.travel.data_source.amap_client
"""
import os
import httpx
from dotenv import load_dotenv
load_dotenv()
from app.agent.utils.logger_handler import logger


class AmapClient:
    """高德 POI 搜索"""

    def __init__(self):
        self.key = os.getenv("AMAP_KEY", "")
        if not self.key:
            logger.warning("AMAP_KEY 未设置")
        self._client = httpx.AsyncClient(
            base_url="https://restapi.amap.com", timeout=10.0
        )

    # ── 搜景点 ──

    async def search_attractions(
        self, city: str, keyword: str = "热门景点", limit: int = 30
    ) -> list[dict]:
        """
        keyword 默认 "热门景点"，搜全城热门，按热度+评分排序。
        返回字段顺序与 attractions.json 一致：city, name, price, rating, type, lat, lon, opentime, endtime, recommendmintime, recommendmaxtime
        """
        results = []
        page = 1
        while len(results) < limit:
            try:
                resp = await self._client.get("/v3/place/text", params={
                    "key": self.key, "keywords": keyword, "city": city,
                    "types": "110000",
                    "offset": min(limit - len(results), 25), "page": page,
                })
                pois = resp.json().get("pois", [])
                for p in pois:
                    loc = p.get("location", "0,0").split(",")
                    ext = p.get("biz_ext", {})
                    results.append({
                        "city": city,
                        "name": p.get("name", ""),
                        "price": 0.0,
                        "rating": _f(ext.get("rating")),
                        "type": _attraction_type(p),
                        "lat": float(loc[1]) if len(loc) >= 2 else 0.0,
                        "lon": float(loc[0]) if len(loc) >= 2 else 0.0,
                        "opentime": "08:00",
                        "endtime": "18:00",
                        "recommendmintime": 1.0,
                        "recommendmaxtime": 3.0,
                    })
                page += 1
                if len(pois) < 25:
                    break
            except Exception as e:
                logger.error("高德景点异常: %s -> %s", city, e)
                break
        logger.info("[高德景点] %s: %s条", city, len(results))
        return results

    # ── 搜餐厅 ──

    async def search_restaurants(
        self, city: str, keyword: str, limit: int = 30
    ) -> list[dict]:
        """
        keyword="火锅"/"川菜"，返回 name, rating, price(人均), lat, lon
        """
        results = []
        page = 1
        while len(results) < limit:
            try:
                resp = await self._client.get("/v3/place/text", params={
                    "key": self.key, "keywords": keyword, "city": city,
                    "types": "050000",
                    "offset": min(limit - len(results), 25), "page": page,
                })
                pois = resp.json().get("pois", [])
                for p in pois:
                    loc = p.get("location", "0,0").split(",")
                    ext = p.get("biz_ext", {})
                    results.append({
                        "name": p.get("name", ""),
                        "city": city,
                        "cuisine": keyword,
                        "rating": _f(ext.get("rating")),
                        "price": _f(ext.get("cost")),
                        "lat": float(loc[1]) if len(loc) >= 2 else 0.0,
                        "lon": float(loc[0]) if len(loc) >= 2 else 0.0,
                        "opentime": "08:00",
                        "endtime": "22:00",
                    })
                page += 1
                if len(pois) < 25:
                    break
            except Exception as e:
                logger.error("高德餐厅异常: %s %s -> %s", city, keyword, e)
                break
        logger.info("[高德餐厅] %s %s: %s条", city, keyword, len(results))
        return results

    async def close(self):
        await self._client.aclose()


# ── 工具函数 ──

def _f(v) -> float:
    try:
        return float(v or 0)
    except (ValueError, TypeError):
        return 0.0


def _attraction_type(poi: dict) -> str:
    t = poi.get("type", "")
    for kw, tp in [
        ("博物馆", "博物馆"), ("寺庙", "历史古迹"), ("道观", "历史古迹"),
        ("公园", "公园"), ("游乐", "游乐园"), ("古镇", "历史古迹"),
        ("古城", "历史古迹"), ("商业街", "商业街区"), ("步行街", "商业街区"),
        ("山", "自然风光"), ("湖", "自然风光"),
    ]:
        if kw in t:
            return tp
    return "景点"


# ── 测试 ──

async def _test():
    print("===== 高德客户端 =====\n")
    c = AmapClient()
    if not c.key:
        print("AMAP_KEY not set")
        return
    print("[景点] 成都")
    for a in (await c.search_attractions("成都", limit=5))[:5]:
        print("  %s [%.1f]" % (a["name"], a["rating"]))
    print("\n[餐厅] 成都火锅")
    for r in (await c.search_restaurants("成都", "火锅", limit=5))[:5]:
        print("  %s [%.1f] 人均:%.0f" % (r["name"], r["rating"], r["price"]))
    await c.close()
    print("\n===== 完成 =====")

if __name__ == "__main__":
    import asyncio
    asyncio.run(_test())
