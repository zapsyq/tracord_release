from pydantic import BaseModel, Field
from decimal import Decimal
from typing import List

class AddBillInput(BaseModel):
    #属于哪次旅行
    trip_id: int

    #消费金额, 数字限制用gt, ge, le
    amount: Decimal = Field(gt=0, description="消费金额")

    #消费分类
    category: int = Field(ge=1, le=6, description="消费分类")

    #自定义分类
    custom_category: str | None = Field(
        default=None,
        max_length=50,
        description="自定义消费分类"
    )


class UpdateBillInput(BaseModel):
    #消费金额
    amount: Decimal = Field(gt=0)

    #消费分类
    category: int = Field(ge=1, le=6)

    #自定义分类
    custom_category: str | None = Field(
        default=None,
        max_length=50,
        description="自定义消费分类"
    )

class BillOut(BaseModel):
    id: int
    amount: Decimal
    category: int
    custom_category: str | None = None

    class Config:
        from_attributes = True


class BillsOut(BaseModel):
    bills: List[BillOut]
