#导入控制数据库操作的父类对象
from sqlalchemy.orm import DeclarativeBase

#导入写约束规范的类
from sqlalchemy import MetaData

#导入控制数据库的变量类型
from sqlalchemy import Integer, DateTime, func

#导入数据库与模型之间的映射关系
from sqlalchemy.orm import Mapped, mapped_column

#python时间模块
from datetime import datetime


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention={

        # 索引
        "ix": "ix_%(column_0_label)s",

        # 唯一约束
        "uq": "uq_%(table_name)s_%(column_0_name)s",

        # 检查约束
        "ck": "ck_%(table_name)s_%(constraint_name)s",

        # 外键约束
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",

        # 主键约束
        "pk": "pk_%(table_name)s"
    })

    #Mapped指python与数据库交互时使用的字段类型，使用标准库的datetime，mapped_column指数据库字段类型
    #创建时间
    create_time: Mapped[datetime] = mapped_column(
        DateTime, 
        default=func.now(), 
        comment="创建时间"
    )
    #更新时间
    update_time: Mapped[datetime] = mapped_column(
        DateTime, 
        default=func.now(), 
        onupdate=func.now(), 
        comment="更新时间"
    )
    id: Mapped[int] = mapped_column(
        Integer, 
        primary_key=True, 
        autoincrement=True, 
    )
   
