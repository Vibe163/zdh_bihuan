import uuid

from fastapi import APIRouter,HTTPException
from pydantic import BaseModel
from browser_session import Browser
from session_manager import manager
router = APIRouter(prefix="/login", tags=["登录自动化模块"])

class CreateSession(BaseModel):
    session_id: str

class EmailPassword(BaseModel):
    session_id: str
    email: str
    password: str


def short_error(e: Exception, limit: int = 200) -> str:
    msg = getattr(e, "msg", None) or str(e)
    msg = " ".join(msg.split())
    return msg[:limit]



@router.post("/one",response_model=CreateSession)
def one():
    session_id = str(uuid.uuid4()) # 生成session_id
    return {"session_id": session_id}



@router.post("/two", response_model=CreateSession)
def two(data: EmailPassword):
    b = None
    try:
        b = Browser()
        b.open_login_page()
        b.login_email_password(data.email, data.password)
        manager.add(data.session_id, b)
    except Exception as e:
        manager.remove(data.session_id)
        if b:
            try:
                b.close()
            except Exception:
                pass
        raise HTTPException(status_code=400, detail="登录失败：" + short_error(e))

    return {"session_id": data.session_id}

