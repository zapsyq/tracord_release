#从上级文件夹导入base类
from .base import Base

#导入数据库与模型之间的映射关系
from sqlalchemy.orm import Mapped, mapped_column

#导入控制数据库的变量类型
from sqlalchemy import Integer, ForeignKey, String, Text, Index


class Plan(Base):
    #定义表名
    __tablename__ = "plans"

    #定义字段
    #关联用户表
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    #城市代码
    adcode: Mapped[str] = mapped_column(String(20), nullable=False)
    #计划内容
    content: Mapped[str] = mapped_column(Text, nullable=False, default="")

    __table_args__ = (
        Index("idx_user_adcode", "user_id", "adcode", unique=True),
    )
