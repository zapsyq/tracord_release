#导入pydantic，校验或约束发送的数据
from pydantic import BaseModel, EmailStr, Field, model_validator
from typing import Annotated

username_str = Annotated[str, Field(min_length=3, max_length=20, description="用户名")]
password_str = Annotated[str, Field(min_length=6, max_length=20, description="密码")]

#in代表接收从前端获取的数据
class RegisterIn(BaseModel):
    email: EmailStr
    username: username_str
    password: password_str
    confirm_password: password_str
    code: Annotated[str, Field(min_length=4, max_length=4, description="验证码")]

    #model_validator装饰器，mode="after"表示在数据校验之后执行
    @model_validator(mode="after")
    def check_password(self):
        if self.password != self.confirm_password:
            raise ValueError("密码不一致")
        return self

#定义需要存入数据库的数据类，方便与orm交互
class CreateUserInput(BaseModel):
    email: EmailStr
    username: username_str
    password: password_str

#登录模块校验
class LoginIn(BaseModel):
    email: EmailStr
    password: password_str

class UserOut(BaseModel):
    id: Annotated[int, Field(...)]
    email: EmailStr
    username: username_str

    class Config:
        from_attributes = True

class LoginOut(BaseModel):
    user: UserOut
    access_token: str
    refresh_token: str
