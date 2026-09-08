#从上级文件夹导入base类
from .base import Base

#导入数据库与模型之间的映射关系
from sqlalchemy.orm import Mapped, mapped_column

#导入控制数据库的变量类型
from sqlalchemy import Integer, ForeignKey, SmallInteger, Index, Numeric, String

from decimal import Decimal

class Bill(Base):
    #定义表名
    __tablename__ = "bills"

    #定义字段
    #属于哪一次旅行, 关联旅行表
    trip_id: Mapped[int] = mapped_column(Integer, ForeignKey("trips.id"), nullable=False)
    #消费分类(1交通, 2餐饮, 3购物, 4住宿, 5娱乐, 6其他)
    category: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    #当category=6时填写自定义分类
    custom_category: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True
    )
    #消费金额
    amount: Mapped[Decimal] = mapped_column(Numeric(10,2), nullable=False)
    
    __table_args__ = (
        Index("idx_trip", "trip_id"),
    )

