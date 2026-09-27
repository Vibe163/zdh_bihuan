from fastapi import APIRouter
from pydantic import BaseModel
from session_manager import manager


router = APIRouter(prefix="/payment", tags=["付款模块"])

class CreateSession(BaseModel):
    session_id: str

# 付款接口
@router.post("/Payment")
def payment(data:CreateSession):
    b = manager.get(data.session_id) # 用同一个session_id取出同一个浏览器继续使用
    b.payment_one()
    b.payment_two()
    b.payment_three()
    b.payment_four()
    b.payment_five()

    link_url = b.payment_six() # 调用浏览器模块里的自动化付款模块

    return f"订阅链接为：{link_url}"

# 通用关闭浏览器接口（登录路径不建任务表，用它关闭；注册路径仍用 /register/five）
@router.post("/close", response_model=CreateSession)
def close_browser(data: CreateSession):
    b = manager.get(data.session_id)
    if b:
        try:
            b.close()
        except Exception:
            pass
    manager.remove(data.session_id)
    return {"session_id": data.session_id}