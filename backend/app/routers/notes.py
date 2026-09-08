from fastapi import APIRouter, Depends
from app.schemas import ResponseOut
from app.config.db_config import AsyncSession
from app.crud.notes import NotesRepository
from app.crud.trips import TripsRepository
from app.core.token import AuthHandler
from app.services.notes import NotesService
from app.core.dependencies import get_session
from app.schemas.notes import AddNoteInput, NoteOut, NotesOut

router = APIRouter(prefix="/notes", tags=["notes"])


#添加笔记
@router.post("/add", response_model=ResponseOut)
async def add_note(
    data: AddNoteInput,
    session: AsyncSession = Depends(get_session),
    user_id: int = Depends(AuthHandler().auth_access_denpendency),
):
    repo = NotesRepository(session=session)
    trip_repo = TripsRepository(session=session)
    service = NotesService(repo=repo, trip_repo=trip_repo)
    await service.add_note(user_id=user_id, trip_id=data.trip_id, content=data.content)
    return ResponseOut()


#获取旅行内所有笔记
@router.get("/trip/{trip_id}", response_model=NotesOut)
async def get_trip_notes(
    trip_id: int,
    session: AsyncSession = Depends(get_session),
    user_id: int = Depends(AuthHandler().auth_access_denpendency),
):
    repo = NotesRepository(session=session)
    trip_repo = TripsRepository(session=session)
    service = NotesService(repo=repo, trip_repo=trip_repo)
    result = await service.get_trip_notes(user_id=user_id, trip_id=trip_id)
    return NotesOut(notes=result)


#获取单个笔记
@router.get("/{note_id}", response_model=NoteOut)
async def get_note(
    note_id: int,
    session: AsyncSession = Depends(get_session),
    user_id: int = Depends(AuthHandler().auth_access_denpendency),
):
    repo = NotesRepository(session=session)
    trip_repo = TripsRepository(session=session)
    service = NotesService(repo=repo, trip_repo=trip_repo)
    result = await service.get_note(user_id=user_id, note_id=note_id)
    return result


#删除笔记
@router.delete("/{note_id}", response_model=ResponseOut)
async def delete_note(
    note_id: int,
    session: AsyncSession = Depends(get_session),
    user_id: int = Depends(AuthHandler().auth_access_denpendency),
):
    repo = NotesRepository(session=session)
    trip_repo = TripsRepository(session=session)
    service = NotesService(repo=repo, trip_repo=trip_repo)
    await service.delete_note(user_id=user_id, note_id=note_id)
    return ResponseOut()
