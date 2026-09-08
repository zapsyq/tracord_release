from datetime import datetime

from pydantic import BaseModel, Field


class SetPlanInput(BaseModel):
    adcode: str = Field(min_length=6, max_length=20, description="城市编码")
    content: str = Field(default="", max_length=10000, description="计划内容")


class PlanOut(BaseModel):
    id: int
    adcode: str
    content: str
    update_time: datetime

    class Config:
        from_attributes = True
