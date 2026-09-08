from pydantic import BaseModel, Field
from typing import List


class AddNoteInput(BaseModel):
    trip_id: int
    content: str = Field(default="", max_length=5000, description="笔记内容")


class NoteOut(BaseModel):
    id: int
    trip_id: int
    content: str

    class Config:
        from_attributes = True


class NotesOut(BaseModel):
    notes: List[NoteOut]
