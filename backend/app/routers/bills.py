from fastapi import APIRouter, Depends
from app.schemas import ResponseOut
from app.config.db_config import AsyncSession
from app.crud.bills import BillsRepository
from app.crud.trips import TripsRepository
from app.core.token import AuthHandler
from app.services.bills import BillsService
from app.core.dependencies import get_session
from app.core.constants import CATEGORY_ENUM_MAP
from app.schemas.bills import AddBillInput, BillsOut, UpdateBillInput, BillOut

router = APIRouter(prefix="/bills", tags=["bills"])


#获取消费分类
@router.get("/categories")
async def get_categories():
    return CATEGORY_ENUM_MAP

#添加账单
@router.post("/add", response_model=ResponseOut)
async def add_bill(
    data: AddBillInput, 
    session: AsyncSession = Depends(get_session),
    user_id: int = Depends(AuthHandler().auth_access_denpendency)
):
    bill_repo = BillsRepository(session=session)
    trip_repo = TripsRepository(session=session)
    service = BillsService(repo=bill_repo, trip_repo=trip_repo)
    await service.add_bill(user_id=user_id, trip_id=data.trip_id, amount=data.amount, category=data.category, custom_category=data.custom_category)
    return ResponseOut()

#获取单个账单
@router.get("/{bill_id}", response_model=BillOut)
async def get_bill(
    bill_id: int,
    session: AsyncSession = Depends(get_session),
    user_id: int = Depends(AuthHandler().auth_access_denpendency)
):
    bill_repo = BillsRepository(session=session)
    trip_repo = TripsRepository(session=session)
    service = BillsService(repo=bill_repo, trip_repo=trip_repo)
    result = await service.get_bill(user_id=user_id, bill_id=bill_id)
    return result

#获取旅行内所有账单
@router.get("/trip/{trip_id}", response_model=BillsOut)
async def get_trip_bills(
    trip_id: int,
    session: AsyncSession = Depends(get_session),
    user_id: int = Depends(AuthHandler().auth_access_denpendency)
):
    bill_repo = BillsRepository(session=session)
    trip_repo = TripsRepository(session=session)
    service = BillsService(repo=bill_repo, trip_repo=trip_repo)
    result = await service.get_trip_bills(user_id=user_id, trip_id=trip_id)
    return BillsOut(
        bills=result
    )

#删除账单
@router.delete("/{bill_id}", response_model=ResponseOut)
async def delete_bill(
    bill_id: int,
    session: AsyncSession = Depends(get_session),
    user_id: int = Depends(AuthHandler().auth_access_denpendency)
):
    bill_repo = BillsRepository(session=session)
    trip_repo = TripsRepository(session=session)
    service = BillsService(repo=bill_repo, trip_repo=trip_repo)
    await service.delete_bill(user_id=user_id, bill_id=bill_id)
    return ResponseOut()



#删除旅行内所有账单
@router.delete("/trip/{trip_id}", response_model=ResponseOut)
async def delete_trip_bill(
    trip_id: int,
    session: AsyncSession = Depends(get_session),
    user_id: int = Depends(AuthHandler().auth_access_denpendency)
):
    bill_repo = BillsRepository(session=session)
    trip_repo = TripsRepository(session=session)
    service = BillsService(repo=bill_repo, trip_repo=trip_repo)
    await service.delete_trip_bill(user_id=user_id, trip_id=trip_id)
    return ResponseOut()

#修改账单
@router.put("/{bill_id}", response_model=ResponseOut)
async def update_bill(
    data: UpdateBillInput,
    bill_id: int,
    session: AsyncSession = Depends(get_session),
    user_id: int = Depends(AuthHandler().auth_access_denpendency)
):
    bill_repo = BillsRepository(session=session)
    trip_repo = TripsRepository(session=session)
    service = BillsService(repo=bill_repo, trip_repo=trip_repo)
    await service.update_bill(
        user_id=user_id,
        bill_id=bill_id,
        amount=data.amount,
        category=data.category,
        custom_category=data.custom_category
    )
    return ResponseOut()


