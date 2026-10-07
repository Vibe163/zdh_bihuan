import uuid

from fastapi import APIRouter,HTTPException
from pydantic import BaseModel, Field
from automation.browser_session import Browser, LoginFailError
from automation.session_manager import manager

from core.response import success_response
from core.common import translate_error

router = APIRouter(prefix="/login", tags=["登录自动化模块"])


class EmailPassword(BaseModel):
    session_id: str
    email: str = Field(
        pattern=r'^[^@]+@[^@]+\.[^@]+$',
        description="邮箱格式不正确",
        json_schema_extra={"example": "test@qq.com"}
    )
    password: str = Field(min_length=6, description="密码至少6位")




@router.post("/one")
def one():
    session_id = str(uuid.uuid4()) # 生成session_id
    return success_response(data={"session_id": session_id})


@router.post("/two")
def two(data: EmailPassword):
    # 该会话专用锁：双击/并发时，同一时刻只放一个请求进来
    with manager.session_lock(data.session_id):
        b = manager.get(data.session_id)

        if b is not None:
            # —— 已有浏览器 ——
            if not b.is_alive():
                manager.remove(data.session_id)
                raise HTTPException(status_code=400, detail="浏览器已被关闭，请重新开始")
            if b.is_logged_in():
                # 已经登录成功（重复提交/双击）：直接返回成功，不重复填、不关浏览器
                return success_response(data={"session_id": data.session_id, "message": "登录成功"})
            # 否则是失败后重试，复用这个浏览器，接着往下填
        else:
            # —— 首次：开新浏览器、打开登录页 ——
            b = Browser()
            try:
                b.open_login_page()
            except Exception as e:
                b.close()
                raise HTTPException(status_code=400, detail="登录页面打开失败：" + translate_error(e))
            manager.add(data.session_id, b)

        # 填账号密码、点登录（首次和重试都走这）
        try:
            b.login_email_password(data.email, data.password)
        except LoginFailError:
            raise HTTPException(status_code=400, detail="登录未成功，请检查账号密码或网络后重试")
        except Exception as e:
            manager.close_and_remove(data.session_id)
            raise HTTPException(status_code=400, detail="登录失败：" + translate_error(e))

        return success_response(data={"session_id": data.session_id, "message": "登录成功"})
