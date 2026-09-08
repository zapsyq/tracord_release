from datetime import datetime

from pydantic import BaseModel, Field
from typing import Annotated, List

Adcode = Annotated[str, Field(..., min_length=6, max_length=20, description="城市编码")]

class TripInput(BaseModel):
    adcode: Adcode

class TripOut(BaseModel):
    id: int
    adcode: Adcode
    create_time: datetime

    class Config:
        from_attributes = True

class TripsOut(BaseModel):
    trips: List[TripOut]
