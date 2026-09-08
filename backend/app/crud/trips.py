#导入会话工厂
from app.config.db_config import AsyncSession
#导入点亮城市模型
from app.models.trips import Trip
from sqlalchemy import select

class TripsRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    #查询城市内的所有旅行
    async def get_city_trips(self, user_id: int, adcode: str):
        async with self.session.begin():
            stmt = select(Trip).where(Trip.user_id == user_id, Trip.adcode == adcode).order_by(Trip.create_time.desc())
            result = await self.session.scalars(stmt)
            return result.all()
    #查询所有旅行
    async def get_trips(self, user_id: int):
        async with self.session.begin():
            stmt = select(Trip).where(Trip.user_id == user_id).order_by(Trip.create_time.desc())
            result = await self.session.scalars(stmt)
            return result.all() 

    #查询单次旅行
    async def get_trip(self, user_id: int, trip_id: int):
        async with self.session.begin():
            stmt = select(Trip).where(Trip.user_id == user_id, Trip.id == trip_id)
            result = await self.session.scalar(stmt)
            return result
    
    #添加旅行
    async def add_trip(self, user_id: int, adcode: str):
        async with self.session.begin():
            trip = Trip(user_id=user_id, adcode=adcode)
            self.session.add(trip)
            await self.session.flush()
            return trip
        
    #删除旅行
    async def delete_trip(self, user_id: int, trip_id: int):
        async with self.session.begin():
            stmt = select(Trip).where(Trip.user_id == user_id, Trip.id == trip_id)
            trip = await self.session.scalar(stmt)
            if trip:
                await self.session.delete(trip)
                return True 
            return False