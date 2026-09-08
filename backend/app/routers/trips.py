from fastapi import APIRouter, Depends
from app.schemas import ResponseOut
from app.config.db_config import AsyncSession
from app.crud.trips import TripsRepository
from app.crud.bills import BillsRepository
from app.crud.notes import NotesRepository
from app.core.token import AuthHandler
from app.services.trips import TripsService
from app.schemas.trips import TripOut, TripInput, TripsOut
from app.core.dependencies import get_session

router = APIRouter(prefix="/trips", tags=["trips"])

#添加旅行
@router.post("/add", response_model=ResponseOut)
async def add_trip(
    data: TripInput, 
    session: AsyncSession = Depends(get_session),
    user_id: int = Depends(AuthHandler().auth_access_denpendency)
):
    trip_repo = TripsRepository(session=session)
    bills_repo = BillsRepository(session=session)
    service = TripsService(repo=trip_repo, bills_repo=bills_repo)
    await service.add_trip(adcode=data.adcode, user_id=user_id)
    return ResponseOut()

#查询所有旅行
@router.get("", response_model=TripsOut)
async def get_trips(
    session: AsyncSession = Depends(get_session),
    user_id: int = Depends(AuthHandler().auth_access_denpendency)
):
    trip_repo = TripsRepository(session=session)
    bills_repo = BillsRepository(session=session)
    service = TripsService(repo=trip_repo, bills_repo=bills_repo)
    result = await service.get_trips(user_id=user_id)
    return TripsOut(trips=result)

#查询单次旅行
@router.get("/{trip_id}", response_model=TripOut)
async def get_trip(
    trip_id: int,
    session: AsyncSession = Depends(get_session),
    user_id: int = Depends(AuthHandler().auth_access_denpendency)
):
    trip_repo = TripsRepository(session=session)
    bills_repo = BillsRepository(session=session)
    service = TripsService(repo=trip_repo, bills_repo=bills_repo)
    result = await service.get_trip(user_id=user_id, trip_id=trip_id)
    return result

#删除旅行
@router.delete("/{trip_id}", response_model=ResponseOut)
async def delete_trip(
    trip_id: int,
    session: AsyncSession = Depends(get_session),
    user_id: int = Depends(AuthHandler().auth_access_denpendency)
):
    trip_repo = TripsRepository(session=session)
    bills_repo = BillsRepository(session=session)
    notes_repo = NotesRepository(session=session)
    service = TripsService(repo=trip_repo, bills_repo=bills_repo, notes_repo=notes_repo)
    await service.delete_trip(user_id=user_id, trip_id=trip_id)
    return ResponseOut()
