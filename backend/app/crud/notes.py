#导入会话工厂
from app.config.db_config import AsyncSession
#获取操作数据库的方法
from sqlalchemy import select
#导入笔记模型
from app.models.notes import Note


class NotesRepository:
    #效果同操作用户数据库
    def __init__(self, session: AsyncSession):
        self.session = session

    #添加笔记（同Trip只保留一条，自动覆盖）
    async def add_note(self, trip_id: int, content: str):
        async with self.session.begin():
            stmt = select(Note).where(Note.trip_id == trip_id)
            existing = await self.session.scalar(stmt)
            if existing:
                existing.content = content
                return existing
            note = Note(trip_id=trip_id, content=content)
            self.session.add(note)
            return note

    #获取旅行内所有笔记
    async def get_trip_notes(self, trip_id: int):
        async with self.session.begin():
            stmt = select(Note).where(Note.trip_id == trip_id)
            result = await self.session.scalars(stmt)
            return result.all()

    #获取单个笔记
    async def get_note(self, note_id: int):
        async with self.session.begin():
            stmt = select(Note).where(Note.id == note_id)
            return await self.session.scalar(stmt)

    #删除单个笔记
    async def delete_note(self, note_id: int):
        async with self.session.begin():
            stmt = select(Note).where(Note.id == note_id)
            note = await self.session.scalar(stmt)
            if note:
                await self.session.delete(note)
                return True
            return False

    #删除旅行内所有笔记
    async def delete_trip_notes(self, trip_id: int):
        async with self.session.begin():
            stmt = select(Note).where(Note.trip_id == trip_id)
            result = await self.session.scalars(stmt)
            notes = result.all()
            if notes:
                for note in notes:
                    await self.session.delete(note)
                return True
            return False
