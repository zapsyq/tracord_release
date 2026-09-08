from datetime import datetime

from fastapi import APIRouter, Depends
from app.schemas import ResponseOut
from app.config.db_config import AsyncSession
from app.crud.plans import PlanRepository
from app.core.token import AuthHandler
from app.services.plans import PlanService
from app.core.dependencies import get_session
from app.schemas.plans import SetPlanInput, PlanOut

router = APIRouter(prefix="/plans", tags=["plans"])


#新增或更新计划
@router.post("/set", response_model=ResponseOut)
async def set_plan(
    data: SetPlanInput,
    session: AsyncSession = Depends(get_session),
    user_id: int = Depends(AuthHandler().auth_access_denpendency),
):
    repo = PlanRepository(session=session)
    service = PlanService(repo=repo)
    await service.set_plan(user_id=user_id, adcode=data.adcode, content=data.content)
    return ResponseOut()


#获取某城市计划
@router.get("/{adcode}", response_model=PlanOut)
async def get_plan(
    adcode: str,
    session: AsyncSession = Depends(get_session),
    user_id: int = Depends(AuthHandler().auth_access_denpendency),
):
    repo = PlanRepository(session=session)
    service = PlanService(repo=repo)
    result = await service.get_plan(user_id=user_id, adcode=adcode)
    if not result:
        return PlanOut(id=0, adcode=adcode, content="", update_time=datetime.now())
    return result


#获取用户所有计划
@router.get("", response_model=list[PlanOut])
async def get_plans(
    session: AsyncSession = Depends(get_session),
    user_id: int = Depends(AuthHandler().auth_access_denpendency),
):
    repo = PlanRepository(session=session)
    service = PlanService(repo=repo)
    result = await service.get_plans(user_id)
    return result


#删除计划
@router.delete("/{plan_id}", response_model=ResponseOut)
async def delete_plan(
    plan_id: int,
    session: AsyncSession = Depends(get_session),
    user_id: int = Depends(AuthHandler().auth_access_denpendency),
):
    repo = PlanRepository(session=session)
    service = PlanService(repo=repo)
    await service.delete_plan(user_id=user_id, plan_id=plan_id)
    return ResponseOut()
