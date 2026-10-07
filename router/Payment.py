from fastapi import APIRouter, Depends, HTTPException
from session_manager import manager
from core.response import success_response
from core.common import CreateSession,short_error,translate_error
from core.security import verify_admin_token

router = APIRouter(prefix="/payment", tags=["付款模块"])



# 接口1：结账 —— 选套餐、点结账，停在目标网站的付款二维码页
@router.post("/start")
def start(data: CreateSession):
    with manager.session_lock(data.session_id):
        b = manager.get(data.session_id)
        if not b:
            raise HTTPException(status_code=404, detail="浏览器不存在，请先登录或注册")
        if b.payment_started:
            raise HTTPException(status_code=400, detail="已停在付款二维码页，请勿重复提交")
        try:
            b.payment_one()    # 关弹窗
            b.payment_two()    # 购买订阅、选套餐
            b.payment_three()  # 点击下单
            b.payment_four()   # 选微信、点结账，停在付款二维码页
            b.payment_five()   # 截图保存付款二维码
        except Exception as e:
            manager.close_and_remove(data.session_id)
            raise HTTPException(status_code=400, detail="结账失败：" + translate_error(e))
        b.payment_started = True
    return success_response(data={"session_id": data.session_id, "message": "已停在付款二维码页，请完成付款"})


# 接口2：代付完成 —— 你付完款点这个，程序拿链接、然后自动关浏览器
@router.post("/confirm", dependencies=[Depends(verify_admin_token)])
def confirm(data: CreateSession):
    with manager.session_lock(data.session_id):
        cached = manager.get_link(data.session_id)  # 先看有没有已缓存的链接（双击/重复）
        if cached:
            return success_response(data={"url": cached})

        b = manager.get(data.session_id)
        if not b:
            raise HTTPException(status_code=404, detail="浏览器不存在，请先登录或注册")
        try:
            link_url = b.payment_six()  # 继续：回仪表盘、拿订阅链接
        except Exception as e:
            manager.close_and_remove(data.session_id)
            raise HTTPException(status_code=400, detail="获取订阅链接失败：" + translate_error(e))
        if not link_url:
            raise HTTPException(status_code=400, detail="未获取到订阅链接，请确认是否已完成付款")

        manager.set_link(data.session_id, link_url)  # 缓存链接（独立于浏览器）
        manager.close_and_remove(data.session_id)    # 链接到手、浏览器使命结束，立刻关掉
    return success_response(data={"url": link_url})


# 通用关闭浏览器接口（运营/兜底用，需管理令牌）
@router.post("/close", dependencies=[Depends(verify_admin_token)])
def close_browser(data: CreateSession):
    with manager.session_lock(data.session_id):
        manager.close_and_remove(data.session_id)
    return success_response(data={"session_id": data.session_id})
