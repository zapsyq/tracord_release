from app.crud.cities import CitiesRepository
from fastapi import HTTPException
from app.crud.trips import TripsRepository

class CitiesService:
    def __init__(self, city_repo: CitiesRepository, trip_repo: TripsRepository, bills_repo, notes_repo=None):
        self.city_repo = city_repo          # cities表的数据库操作
        self.trip_repo = trip_repo          # trips表的数据库操作
        self.bills_repo = bills_repo        # bills表的数据库操作(取消点亮时检查账单用)
        self.notes_repo = notes_repo        # notes表的数据库操作(取消点亮时检查笔记用)

    #获取已点亮城市
    async def get_lighted_cities(self, user_id: int):        
        lighted_cities = await self.city_repo.get_light_cities(user_id=user_id)
        return lighted_cities

    #点亮城市自动添加旅行记录
    async def light_city(self, user_id: int, adcode: str):
        is_lighted = await self.city_repo.is_lighted(user_id=user_id, adcode=adcode)
        if is_lighted:
            raise HTTPException(status_code=400, detail="该城市已点亮")
        result = await self.city_repo.light_cities(user_id=user_id, adcode=adcode)
        if not result:
            raise HTTPException(status_code=400, detail="点亮城市失败")
        try:
            await self.trip_repo.add_trip(adcode=adcode, user_id=user_id)
        except Exception:
            # 旅行创建失败，回滚点亮记录
            await self.city_repo.unlight_cities(user_id, adcode)
            raise HTTPException(status_code=500, detail="点亮城市失败")
        return result

    #取消点亮城市 (检查账单后再删旅行+城市)
    async def unlight_city(self, user_id: int, adcode: str):
        trips = await self.trip_repo.get_city_trips(user_id, adcode)
        if not trips:
            raise HTTPException(status_code=400, detail="该城市未点亮")

        for trip in trips:
            bills = await self.bills_repo.get_trip_bills(trip.id)
            if bills:
                raise HTTPException(status_code=400, detail="该城市有消费记录, 请先删除账单后再取消点亮")
            notes = await self.notes_repo.get_trip_notes(trip.id)
            if notes:
                raise HTTPException(status_code=400, detail="该城市有笔记记录, 请先删除笔记后再取消点亮")

        for trip in trips:
            await self.trip_repo.delete_trip(user_id, trip.id)

        result = await self.city_repo.unlight_cities(user_id, adcode)
        if not result:
            raise HTTPException(status_code=400, detail="取消点亮失败")
        return result