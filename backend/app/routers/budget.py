from fastapi import APIRouter, Depends
from app.schemas import ResponseOut
from app.config.db_config import AsyncSession
from app.crud.budget import BudgetRepository
from app.core.token import AuthHandler
from app.services.budget import BudgetService
from app.core.dependencies import get_session
from app.schemas.budget import SetBudgetInput, BudgetOut, BudgetsOut

router = APIRouter(prefix="/budget", tags=["budget"])


#设置预算
@router.post("/set", response_model=ResponseOut)
async def set_budget(
    data: SetBudgetInput,
    session: AsyncSession = Depends(get_session),
    user_id: int = Depends(AuthHandler().auth_access_denpendency),
):
    repo = BudgetRepository(session=session)
    service = BudgetService(repo=repo)
    await service.set_budget(user_id=user_id, adcode=data.adcode, category=data.category, amount=data.amount, custom_category=data.custom_category)
    return ResponseOut()


#获取预算（可选按城市过滤）
@router.get("", response_model=BudgetsOut)
async def get_budgets(
    adcode: str | None = None,
    session: AsyncSession = Depends(get_session),
    user_id: int = Depends(AuthHandler().auth_access_denpendency),
):
    repo = BudgetRepository(session=session)
    service = BudgetService(repo=repo)
    result = await service.get_budgets(user_id, adcode)
    return BudgetsOut(budgets=result)


#获取单个预算
@router.get("/{budget_id}", response_model=BudgetOut)
async def get_budget(
    budget_id: int,
    session: AsyncSession = Depends(get_session),
    user_id: int = Depends(AuthHandler().auth_access_denpendency),
):
    repo = BudgetRepository(session=session)
    service = BudgetService(repo=repo)
    result = await service.get_budget(user_id=user_id, budget_id=budget_id)
    return result


#删除预算
@router.delete("/{budget_id}", response_model=ResponseOut)
async def delete_budget(
    budget_id: int,
    session: AsyncSession = Depends(get_session),
    user_id: int = Depends(AuthHandler().auth_access_denpendency),
):
    repo = BudgetRepository(session=session)
    service = BudgetService(repo=repo)
    await service.delete_budget(user_id=user_id, budget_id=budget_id)
    return ResponseOut()
