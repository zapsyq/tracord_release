"""
RollingGo 酒店搜索 — 按城市搜酒店, 免费无限量
申请 Key: rollinggo.store/apply  |  Key 在 .env: ROLLINGGO_KEY
测试: python -m app.agent.travel.data_source.rollinggo_client
"""
import os, httpx, json
from dotenv import load_dotenv
load_dotenv()
from app.agent.utils.logger_handler import logger


class RollingGoClient:
    """按城市搜酒店，免费无限量"""

    def __init__(self):
        self.api_key = os.getenv("ROLLINGGO_KEY", "")
        if not self.api_key:
            logger.warning("ROLLINGGO_KEY 未设置")
        self._client = httpx.AsyncClient(
            base_url="https://mcp.rollinggo.cn",
            timeout=15.0,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
                "Authorization": f"Bearer {self.api_key}",
            },
        )

    async def search_hotels(
        self, city: str, max_price: float = 9999, guests: int = 2, limit: int = 20
    ) -> list[dict]:
        """
        按城市搜酒店
        返回 [{name, price, lat, lon, numbed}, ...]
        """
        try:
            resp = await self._client.post("/mcp", json={
                "jsonrpc": "2.0", "id": 1, "method": "tools/call",
                "params": {
                    "name": "searchHotels",
                    "arguments": {
                        "place": city,
                        "placeType": "城市",
                        "originQuery": f"{city}酒店",
                        "filterOptions": {
                            "maxPricePerNight": max_price,
                        },
                    },
                },
            })
            data = resp.json()
            content = data.get("result", {}).get("content", [])
            if not content:
                return self._fallback(city)

            text = content[0].get("text", "")
            try:
                hotels_data = json.loads(text)
                hotels = hotels_data.get("hotelInformationList", [])
            except json.JSONDecodeError:
                return self._fallback(city)

            if not hotels:
                return self._fallback(city)

            return [
                {
                    "name": h.get("name", ""),
                    "city": city,
                    "price": float(h.get("price", {}).get("lowestPrice", 200)),
                    "lat": float(h.get("latitude", 0)),
                    "lon": float(h.get("longitude", 0)),
                    "numbed": "双人床",
                }
                for h in hotels[:limit]
            ]

        except Exception as e:
            logger.error("RollingGo异常: %s -> %s", city, e)
            return self._fallback(city)

    def _fallback(self, city: str) -> list[dict]:
        return [
            {
                "name": f"{city}快捷酒店",
                "city": city,
                "price": 200,
                "lat": 0,
                "lon": 0,
                "numbed": "双人床",
            }
        ]

    async def close(self):
        await self._client.aclose()


# 测试
async def _test():
    print("===== RollingGo =====\n")
    c = RollingGoClient()
    if not c.api_key:
        print("ROLLINGGO_KEY 未设置")
        return
    hotels = await c.search_hotels("成都", max_price=500, limit=5)
    print("成都酒店:")
    for h in hotels:
        print(f"  {h['name']} Y{h['price']} ({h['lat']},{h['lon']})")
    await c.close()
    print("\n===== 完成 =====")

if __name__ == "__main__":
    import asyncio
    asyncio.run(_test())
