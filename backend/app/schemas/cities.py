from pydantic import BaseModel, Field
from typing import Annotated, List

Adcode = Annotated[str, Field(..., min_length=6, max_length=20, description="城市编码")]

class LightCityInput(BaseModel):
    adcode: Adcode

class LightCityOut(BaseModel):
    adcode: List[Adcode]
