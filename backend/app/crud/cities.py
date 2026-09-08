#导入会话工厂
from app.config.db_config import AsyncSession
#获取操作数据库的方法(select:参数里填写要查询的对象)
from sqlalchemy import select, exists
#导入点亮城市模型
from app.models.cities import LightCity

class CitiesRepository:
    #效果同操作用户数据库
    def __init__(self, session: AsyncSession):
        self.session = session

    #获取用户是否点亮过该城市
    async def is_lighted(self, user_id: int, adcode: str):
        async with self.session.begin():
            stmt = select(exists().where(LightCity.user_id == user_id, LightCity.adcode == adcode))
            return await self.session.scalar(stmt)

    #点亮城市
    async def light_cities(self, user_id: int, adcode: str):
        async with self.session.begin():
            cities = LightCity(user_id=user_id, adcode=adcode)
            self.session.add(cities)
            return cities
        
    #获取用户点亮的城市
    async def get_light_cities(self, user_id: int):
        async with self.session.begin():
            lighted_cities = select(LightCity.adcode).where(LightCity.user_id == user_id)
            result =  await self.session.scalars(lighted_cities)
            return result.all()
        
    #删除用户点亮的城市
    async def unlight_cities(self, user_id: int, adcode: str):
        async with self.session.begin():
            stmt = select(LightCity).where(LightCity.user_id == user_id, LightCity.adcode == adcode)
            city = await self.session.scalar(stmt)
            if city:
                await self.session.delete(city)
                return True
            return False
            