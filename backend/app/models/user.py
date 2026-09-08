#从上级文件夹导入base类
from .base import Base

#导入数据库与模型之间的映射关系
from sqlalchemy.orm import Mapped, mapped_column

#导入控制数据库的变量类型
from sqlalchemy import String

#导入密码加密模块
from pwdlib import PasswordHash

#创建密码加密对象
password_hash = PasswordHash.recommended()

class User(Base):
    #定义表名
    __tablename__ = "users"

    #定义字段
    email: Mapped[str] = mapped_column(String(100), unique=True)
    username: Mapped[str] = mapped_column(String(100), nullable=False)
    _password: Mapped[str] = mapped_column(String(200))
    #头像
    avatar: Mapped[str | None] = mapped_column(String(200), nullable=True)

    #构造函数
    def __init__(self, *args, **kwargs):
        password = kwargs.pop("password")
        #初始化Base类
        super().__init__(*args, **kwargs)
        if password: 
            self.password = password

    #方法1：如果未赋值，获取对象存储的加密后的密码属性
    @property
    def password(self):
        return self._password
    
    #方法2：如果赋值，则将密码进行加密，并保存到对象属性中
    @password.setter
    def password(self, raw_password):
        self._password = password_hash.hash(raw_password)

    #方法3：验证密码
    def check_password(self, raw_password):
        return password_hash.verify(raw_password, self.password)
    