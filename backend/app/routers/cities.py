from fastapi import APIRouter, Depends
from app.schemas.cities import LightCityOut, LightCityInput
from app.schemas import ResponseOut
from app.config.db_config import AsyncSession
from app.core.dependencies import get_session
from app.core.token import AuthHandler
from app.crud.cities import CitiesRepository
from app.crud.trips import TripsRepository
from app.crud.bills import BillsRepository
from app.crud.notes import NotesRepository
from app.services.cities import CitiesService

router = APIRouter(prefix="/cities", tags=["cities"])

#获取已点亮城市
@router.get("/lighted", response_model=LightCityOut)
async def get_lighted_cities(
    session: AsyncSession = Depends(get_session),
    user_id: int = Depends(AuthHandler().auth_access_denpendency)
):
    cities_repo = CitiesRepository(session=session)
    trip_repo = TripsRepository(session=session)
    bills_repo = BillsRepository(session=session)
    service = CitiesService(cities_repo, trip_repo, bills_repo)
    lighted_cities = await service.get_lighted_cities(user_id=user_id)
    return LightCityOut(
        adcode=lighted_cities
    )

#点亮城市
@router.post("/light", response_model=ResponseOut)
async def light_city(
    data: LightCityInput,
    session: AsyncSession = Depends(get_session),
    user_id: int = Depends(AuthHandler().auth_access_denpendency),
):
    cities_repo = CitiesRepository(session=session)
    trip_repo = TripsRepository(session=session)
    bills_repo = BillsRepository(session=session)
    service = CitiesService(cities_repo, trip_repo, bills_repo)
    await service.light_city(user_id=user_id, adcode=data.adcode)
    return ResponseOut()

#取消点亮城市
@router.delete("/{adcode}", response_model=ResponseOut)
async def unlight_city(
    adcode: str,
    session: AsyncSession = Depends(get_session),
    user_id: int = Depends(AuthHandler().auth_access_denpendency),
):
    cities_repo = CitiesRepository(session=session)
    trip_repo = TripsRepository(session=session)
    bills_repo = BillsRepository(session=session)
    notes_repo = NotesRepository(session=session)
    service = CitiesService(cities_repo, trip_repo, bills_repo, notes_repo)
    await service.unlight_city(user_id=user_id, adcode=adcode)
    return ResponseOut()