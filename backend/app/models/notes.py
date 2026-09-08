#从上级文件夹导入base类
from .base import Base

#导入数据库与模型之间的映射关系
from sqlalchemy.orm import Mapped, mapped_column

#导入控制数据库的变量类型
from sqlalchemy import Integer, ForeignKey, Text


class Note(Base):
    #定义表名
    __tablename__ = "notes"

    #定义字段
    #属于哪一次旅行, 关联旅行表
    trip_id: Mapped[int] = mapped_column(Integer, ForeignKey("trips.id"), nullable=False)
    #笔记内容
    content: Mapped[str] = mapped_column(Text, nullable=False, default="")
