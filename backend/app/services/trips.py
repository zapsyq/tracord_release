from app.crud.trips import TripsRepository
from fastapi import HTTPException


class TripsService:
    def __init__(self, repo: TripsRepository, bills_repo, notes_repo=None):
        self.repo = repo
        self.bills_repo = bills_repo    # bills表的数据库操作(删除旅行时检查账单用)
        self.notes_repo = notes_repo    # notes表的数据库操作(删除旅行时检查笔记用)
    
    #添加旅行
    async def add_trip(self, adcode: str, user_id: int):
        add_trip = await self.repo.add_trip(user_id, adcode)
        if not add_trip:
            raise HTTPException(status_code=400, detail="添加旅行失败")
        return add_trip

    #查询城市内最新的旅行
    async def get_latest_trip(self, user_id: int, adcode: str):
        trips = await self.repo.get_city_trips(user_id, adcode)
        if not trips:
            raise HTTPException(status_code=400, detail="该城市暂无旅行记录")
        # get_city_trips 已按 create_time 降序，第一条即最新
        return trips[0]
    
    #查询所有旅行
    async def get_trips(self, user_id: int):
        trips = await self.repo.get_trips(user_id)
        return trips
    
    #查询单次旅行
    async def get_trip(self, user_id: int, trip_id: int):
        trip = await self.repo.get_trip(user_id, trip_id)
        if not trip:
            raise HTTPException(status_code=400, detail="查询旅行失败")
        return trip
    
    #删除旅行
    async def delete_trip(self, user_id: int, trip_id: int):
        # 检查旅行下是否有账单
        bills = await self.bills_repo.get_trip_bills(trip_id)
        if bills:
            raise HTTPException(status_code=400, detail="该旅行有消费记录, 请先删除账单后再删除旅行")
        # 检查旅行下是否有笔记
        if self.notes_repo:
            notes = await self.notes_repo.get_trip_notes(trip_id)
            if notes:
                raise HTTPException(status_code=400, detail="该旅行有笔记记录, 请先删除笔记后再删除旅行")
        delete_trip = await self.repo.delete_trip(user_id, trip_id)
        if not delete_trip:
            raise HTTPException(status_code=400, detail="删除旅行失败")
        return delete_trip

