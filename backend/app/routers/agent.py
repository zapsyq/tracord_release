from app.core.token import AuthHandler
from fastapi import APIRouter, Depends
from app.config.db_config import AsyncSession
from app.core.dependencies import get_session
from app.crud.cities import CitiesRepository
from app.services.cities import CitiesService
from app.agent.tracord_agent import TracordAgent
from app.schemas.agent import ChatRequest
from fastapi.responses import StreamingResponse
from app.crud.trips import TripsRepository
from app.services.trips import TripsService
from app.crud.bills import BillsRepository
from app.services.bills import BillsService
from app.crud.notes import NotesRepository

router = APIRouter(prefix="/agent", tags=["agent"])
@router.post("/chat")
async def chat(
    request: ChatRequest,
    session: AsyncSession = Depends(get_session),
    user_id: int = Depends(AuthHandler().auth_access_denpendency)
):
    
    cities_repo = CitiesRepository(session=session)
    trips_repo = TripsRepository(session=session)
    bills_repo = BillsRepository(session=session)
    notes_repo = NotesRepository(session=session)
    city_service = CitiesService(cities_repo, trips_repo, bills_repo, notes_repo)
    trip_service = TripsService(trips_repo, bills_repo, notes_repo)
    bill_service = BillsService(bills_repo, trips_repo)

    agent = TracordAgent(
        city_service = city_service,
        trip_service = trip_service,
        bill_service = bill_service,
        user_id = user_id
    )

    return StreamingResponse(
        agent.execute_stream(request.query),
        media_type="text/plain"
)