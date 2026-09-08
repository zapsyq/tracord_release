from pydantic import BaseModel, Field
from typing import Annotated, Literal

class ResponseOut(BaseModel):
    result: Annotated[Literal["success", "failure"], Field("success", description="请求结果")]
