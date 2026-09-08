from pydantic import BaseModel, Field

#agent工具校验
class CityInput(BaseModel):
    city_name: str = Field(description="城市名称")

class CityListInput(BaseModel):
    city_names: list[str] = Field(description="要点亮的城市名称列表，支持一次点亮多个城市")