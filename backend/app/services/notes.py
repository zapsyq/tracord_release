from app.crud.notes import NotesRepository
from app.crud.trips import TripsRepository
from fastapi import HTTPException


class NotesService:
    def __init__(self, repo: NotesRepository, trip_repo: TripsRepository):
        self.repo = repo                # notes表的数据库操作
        self.trip_repo = trip_repo      # trips表的数据库操作(校验旅行归属用)

    #添加笔记
    async def add_note(self, user_id: int, trip_id: int, content: str):
        trip = await self.trip_repo.get_trip(user_id=user_id, trip_id=trip_id)
        if not trip:
            raise HTTPException(status_code=400, detail="旅行不存在")
        return await self.repo.add_note(trip_id=trip_id, content=content)

    #获取旅行内所有笔记
    async def get_trip_notes(self, user_id: int, trip_id: int):
        trip = await self.trip_repo.get_trip(user_id=user_id, trip_id=trip_id)
        if not trip:
            raise HTTPException(status_code=400, detail="旅行不存在")
        return await self.repo.get_trip_notes(trip_id)

    #获取单个笔记
    async def get_note(self, user_id: int, note_id: int):
        note = await self.repo.get_note(note_id)
        if not note:
            raise HTTPException(status_code=400, detail="笔记不存在")
        trip = await self.trip_repo.get_trip(user_id=user_id, trip_id=note.trip_id)
        if not trip:
            raise HTTPException(status_code=400, detail="旅行不存在")
        return note

    #删除笔记
    async def delete_note(self, user_id: int, note_id: int):
        note = await self.repo.get_note(note_id)
        if not note:
            raise HTTPException(status_code=400, detail="笔记不存在")
        trip = await self.trip_repo.get_trip(user_id=user_id, trip_id=note.trip_id)
        if not trip:
            raise HTTPException(status_code=400, detail="旅行不存在")
        return await self.repo.delete_note(note_id)
