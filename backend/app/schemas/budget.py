from datetime import datetime
from decimal import Decimal
from typing import List

from pydantic import BaseModel, Field


class SetBudgetInput(BaseModel):
    adcode: str = Field(min_length=6, max_length=20, description="城市编码")
    category: int = Field(ge=1, le=6, description="预算分类")
    custom_category: str | None = Field(default=None, max_length=50, description="自定义分类(category=6时)")
    amount: Decimal = Field(gt=0, description="预算金额")


class BudgetOut(BaseModel):
    id: int
    adcode: str
    category: int
    custom_category: str | None = None
    amount: Decimal
    update_time: datetime

    class Config:
        from_attributes = True


class BudgetsOut(BaseModel):
    budgets: List[BudgetOut]
