from app.crud.budget import BudgetRepository
from app.services.bills import check_category
from fastapi import HTTPException


class BudgetService:
    def __init__(self, repo: BudgetRepository):
        self.repo = repo    # budgets表的数据库操作

    #设置预算
    async def set_budget(self, user_id: int, adcode: str, category: int, amount, custom_category: str | None = None):
        check_category(category, custom_category)
        return await self.repo.set_budget(user_id=user_id, adcode=adcode, category=category, amount=amount, custom_category=custom_category)

    #获取预算（可选按城市过滤）
    async def get_budgets(self, user_id: int, adcode: str | None = None):
        return await self.repo.get_budgets(user_id, adcode)

    #获取单个预算
    async def get_budget(self, user_id: int, budget_id: int):
        result = await self.repo.get_budget(user_id, budget_id)
        if not result:
            raise HTTPException(status_code=400, detail="预算不存在")
        return result

    #删除预算
    async def delete_budget(self, user_id: int, budget_id: int):
        result = await self.repo.delete_budget(user_id, budget_id)
        if not result:
            raise HTTPException(status_code=400, detail="预算不存在")
        return result
