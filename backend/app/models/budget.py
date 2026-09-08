#从上级文件夹导入base类
from .base import Base

#导入数据库与模型之间的映射关系
from sqlalchemy.orm import Mapped, mapped_column

from decimal import Decimal

#导入控制数据库的变量类型
from sqlalchemy import Integer, ForeignKey, SmallInteger, Index, Numeric, String

class Budget(Base):
    __tablename__ = "budgets"

    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    #城市代码
    adcode: Mapped[str] = mapped_column(String(20), nullable=False)
    #预算分类(1交通, 2餐饮, 3购物, 4住宿, 5娱乐, 6其他)
    category: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    #当category=6时填写自定义分类
    custom_category: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True
    )
    #消费金额
    amount: Mapped[Decimal] = mapped_column(Numeric(10,2), nullable=False)
    
    __table_args__ = (
        Index("idx_user_city", "user_id", "adcode"),
    )
