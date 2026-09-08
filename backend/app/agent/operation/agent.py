"""操作 agent：点亮城市 + 记账 + 查账单"""
from langchain.agents import create_agent
from app.agent.model.factory import chat_model
from app.agent.middleware import log_before_model, monitor_tool
from app.agent.utils.prompt_loader import load_prompt
from app.agent.operation.tools.cities import city_tools
from app.agent.operation.tools.bills import bill_tools
from app.agent.operation.tools.smart_bill import smart_add_bill_tool


def build_operation_agent(city_service, trip_service, bill_service, user_id):
    city = city_tools(city_service, user_id)
    get_bills = bill_tools(bill_service, trip_service, user_id)
    add_bill = smart_add_bill_tool(city_service, trip_service, bill_service, user_id)
    return create_agent(
        model=chat_model,
        tools=[*city, add_bill, get_bills],
        system_prompt=load_prompt("operation"),
        middleware=[log_before_model, monitor_tool],
    )
