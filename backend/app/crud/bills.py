#导入会话工厂
from app.config.db_config import AsyncSession
#获取操作数据库的方法(select:参数里填写要查询的对象)
from sqlalchemy import select
#导入账单模型
from app.models.bills import Bill

from decimal import Decimal

class BillsRepository:
    #效果同操作用户数据库
    def __init__(self, session: AsyncSession):
        self.session = session

    #添加账单
    async def add_bill(self, trip_id: int, amount: Decimal, category: int, custom_category: str | None = None):
        async with self.session.begin():
            bills = Bill(trip_id=trip_id, amount=amount, category=category, custom_category=custom_category)
            self.session.add(bills)
            return bills
        
    #获取旅行账单
    async def get_trip_bills(self, trip_id: int):
        async with self.session.begin():
            stmt = select(Bill).where(Bill.trip_id == trip_id).order_by(Bill.update_time.desc())
            result = await self.session.scalars(stmt)
            return result.all()
        
    #获取单个账单
    async def get_bill(self, bill_id: int):
        async with self.session.begin():
            stmt = select(Bill).where(Bill.id == bill_id)
            return await self.session.scalar(stmt)
        
    #删除单个账单
    async def delete_bill(self, bill_id: int):
        async with self.session.begin():
            stmt = select(Bill).where(Bill.id == bill_id)
            bill = await self.session.scalar(stmt)
            if bill:
                await self.session.delete(bill)
                return True 
            return False
        
    #删除旅行账单
    async def delete_trip_bill(self, trip_id: int):
        async with self.session.begin():
            stmt = select(Bill).where(Bill.trip_id == trip_id)
            result = await self.session.scalars(stmt)
            bills = result.all()
            if bills:
                for bill in bills:
                    await self.session.delete(bill)
                return True 
            return False

    #修改账单
    async def update_bill(self, bill_id: int, amount: Decimal, category: int, custom_category: str | None = None):
        async with self.session.begin():
            stmt = select(Bill).where(Bill.id == bill_id)
            bill = await self.session.scalar(stmt)
            if bill:
                bill.amount = amount
                bill.category = category
                bill.custom_category = custom_category
                return bill
            return None