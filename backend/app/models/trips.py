#从上级文件夹导入base类
from .base import Base

#导入数据库与模型之间的映射关系
from sqlalchemy.orm import Mapped, mapped_column

#导入控制数据库的变量类型
from sqlalchemy import String, Integer, ForeignKey

class Trip(Base):
    #定义表名
    __tablename__ = "trips"

    #定义字段
    #用户id，外键关联用户表中的id
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    #城市代码
    adcode: Mapped[str] = mapped_column(String(20), nullable=False)
