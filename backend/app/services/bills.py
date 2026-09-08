from app.crud.bills import BillsRepository
from app.crud.trips import TripsRepository
from decimal import Decimal
from fastapi import HTTPException

def check_category(category: int, custom_category: str | None):
    if category == 6 and not custom_category:
        raise HTTPException(status_code=400, detail="其他分类必须填写自定义分类")
    if category != 6 and custom_category:
        raise HTTPException(status_code=400, detail="非其他分类不能填写自定义分类")

class BillsService:
    def __init__(self, repo: BillsRepository, trip_repo: TripsRepository):
        self.repo = repo
        self.trip_repo = trip_repo

    #添加账单
    async def add_bill(self, user_id: int, trip_id: int, amount: Decimal, category: int, custom_category: str | None = None):

        trip = await self.trip_repo.get_trip(
            user_id=user_id,
            trip_id=trip_id
        )
        if not trip:
            raise HTTPException(status_code=400, detail="旅行不存在")

        check_category(category, custom_category)

        return await self.repo.add_bill(
            trip_id = trip_id, 
            amount = amount,
            category = category,
            custom_category = custom_category
        )
    
    #获取旅行账单
    async def get_trip_bills(self, user_id: int, trip_id: int):
        trip = await self.trip_repo.get_trip(
            user_id=user_id,
            trip_id=trip_id
        )
        if not trip:
            raise HTTPException(status_code=400, detail="旅行不存在")
        return await self.repo.get_trip_bills(trip_id)
    
    #获取单个账单
    async def get_bill(self, user_id: int, bill_id: int):
        bill = await self.repo.get_bill(bill_id)
        if not bill:
            raise HTTPException(status_code=400, detail="账单不存在")
        trip = await self.trip_repo.get_trip(
            user_id=user_id,
            trip_id=bill.trip_id
        )
        if not trip:
            raise HTTPException(status_code=400, detail="旅行不存在")
        return bill
    
    #删除账单
    async def delete_bill(self, user_id: int, bill_id: int):
        bill = await self.repo.get_bill(bill_id)
        if not bill:
            raise HTTPException(status_code=400, detail="账单不存在")
        trip = await self.trip_repo.get_trip(
            user_id=user_id,
            trip_id=bill.trip_id
        )
        if not trip:
            raise HTTPException(status_code=400, detail="旅行不存在")
        return await self.repo.delete_bill(bill_id)
    
    #删除旅行账单
    async def delete_trip_bill(self, user_id: int, trip_id: int):
        trip = await self.trip_repo.get_trip(
            user_id=user_id,
            trip_id=trip_id
        )
        if not trip:
            raise HTTPException(status_code=400, detail="旅行不存在")
        result = await self.repo.delete_trip_bill(trip_id)
        if not result:
            raise HTTPException(status_code=400, detail="该旅行没有账单")
        return result
    
    #修改账单
    async def update_bill(self, user_id: int, bill_id: int, amount: Decimal, category: int, custom_category: str | None = None):
        bill = await self.repo.get_bill(bill_id)
        if not bill:
            raise HTTPException(status_code=400, detail="账单不存在")
        trip = await self.trip_repo.get_trip(
            user_id=user_id,
            trip_id=bill.trip_id
        )
        if not trip:
            raise HTTPException(status_code=400, detail="旅行不存在")

        check_category(category, custom_category)
    
        return await self.repo.update_bill(
            bill_id = bill_id, 
            amount = amount,
            category = category,
            custom_category = custom_category
        )
