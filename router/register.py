from fastapi import APIRouter,Depends,HTTPException
from sqlmodel import Session,select
from database import get_db
from pydantic import BaseModel
from model import Register
import uuid

from browser_session import Browser
from session_manager import manager

router = APIRouter(prefix="/register", tags=["自动化注册模块"])

def short_error(e: Exception, limit: int = 200) -> str:
    msg = getattr(e, "msg", None) or str(e)
    msg = " ".join(msg.split())
    return msg[:limit]



class CreateSession(BaseModel):
    session_id: str

class EmailPassword(BaseModel):
    session_id: str
    email: str
    password: str

class verify_num(BaseModel):
    session_id: str
    verify_num: int

@router.post("/one",response_model=CreateSession) # `response_model` 的作用：规定这个接口返回给前端的数据格式，并自动过滤、校验
def one(db: Session = Depends(get_db)):
    session_id = str(uuid.uuid4()) # 生成session_id
    account = Register(session_id = session_id) # 存入数据库的Register表里
    db.add(account) # 执行添加
    db.commit() # 执行提交
    return {"session_id": session_id} # 必须返回这种格式：否则response_model=CreateSession 校验不过



@router.post("/two",response_model=CreateSession)
def two(data: EmailPassword, db: Session = Depends(get_db)):
    # 判断session_id和状态码是否为：init
    stmt = select(Register).where(Register.session_id == data.session_id) # 编写查询条件
    task = db.exec(stmt).first() # 执行查询
    if not task:
        raise HTTPException(status_code=404,detail="会话不存在")
    if task.status != "init":
        raise HTTPException(status_code=400,detail="流程脱轨")

    # 把邮箱和密码存入Register表
    task.email = data.email
    task.password = data.password

    b = None
    try:
        b = Browser() # 启动自动化浏览器
        b.open_register_page() # 打开指定网址
        b.fill_email_and_pwd(data.email, data.password) # 自动化输入邮箱和密码
        # 存入浏览器
        manager.add(data.session_id, b)
        task.status = "filling"
    except Exception as e:
        task.status = "register_fail"
        task.error_msg = short_error(e)  # 异常文本可能很长，截断，别超255
        manager.remove(data.session_id)  # 浏览器可能半开，清理掉
        if b:
            try:
                b.close()
            except Exception:
                pass

    db.commit()
    return {"session_id": task.session_id}





@router.post("/three",response_model=CreateSession)
def three(data: CreateSession,db: Session = Depends(get_db)):
    # 判断session_id和状态码是否为：filling
    stmt = select(Register).where(Register.session_id == data.session_id)  # 编写查询条件
    task = db.exec(stmt).first()  # 执行查询
    if not task:
        raise HTTPException(status_code=404, detail="会话不存在")

    if task.status != "filling":
        raise HTTPException(status_code=400, detail="流程脱轨")

    b = manager.get(data.session_id)  # 取出存在内存里已经启动的浏览器
    if not b:
        raise HTTPException(status_code=404, detail="浏览器不存在，请重新走流程")
    try:
        b.click_verify_button() # 自动点击发送验证码按钮
        task.status = "waiting_code"  # 更新状态
    except Exception as e:
        task.status = "register_fail"
        task.error_msg = short_error(e)
        manager.remove(data.session_id)  # 浏览器可能半开，清理掉
        if b:
            try:
                b.close()
            except Exception:
                pass


    db.commit() # 直接commit，它发现对象变了，就自动发 UPDATE。不用再 add 一次。
    return {"session_id": task.session_id}



@router.post("/four",response_model=CreateSession)
def four(data: verify_num,db: Session = Depends(get_db)):
    stmt = select(Register).where(Register.session_id == data.session_id)
    task = db.exec(stmt).first()
    if not task:
        raise HTTPException(status_code=404, detail="会话不存在")
    if task.status != "waiting_code":
        raise HTTPException(status_code=400, detail="流程脱轨")

    # 取出存在内存里已经启动的浏览器
    b = manager.get(data.session_id)
    if not b:
        raise HTTPException(status_code=404, detail="浏览器不存在，请重新走流程")

    try:
        b.enter_verify_and_click(data.verify_num)
        task.status = "finished"
    except Exception as e:
        task.status = "register_fail"
        task.error_msg = short_error(e)
        manager.remove(data.session_id)  # 浏览器可能半开，清理掉
        if b:
            try:
                b.close()
            except Exception:
                pass

    db.commit()
    return {"session_id": task.session_id}



@router.post("/five")
def five(data: CreateSession,db: Session = Depends(get_db)):
    stmt = select(Register).where(Register.session_id == data.session_id)
    task = db.exec(stmt).first()
    if not task:
        raise HTTPException(status_code=404, detail="会话不存在")
    if task.status != "finished":
        raise HTTPException(status_code=400, detail="流程脱轨")

    # 取出存在内存里已经启动的浏览器
    b = manager.get(data.session_id)
    if not b:
        raise HTTPException(status_code=404, detail="浏览器不存在，请重新走流程")

    #销毁当前浏览器
    b.close()
    manager.remove(data.session_id)  # 把浏览器从 manager 移除，不然会一直占内存
    task.status = "over"
    db.commit()
    return {"session_id": task.session_id}


@router.get("/polling") # GET接口，直接用session_id 直接写在括号里（这叫 query 参数），不用建模型、不用填 body
def polling(session_id: str,db: Session = Depends(get_db)):
    stmt = select(Register).where(Register.session_id == session_id)
    task = db.exec(stmt).first()
    if not task:
        raise HTTPException(status_code=404, detail="会话不存在")
    return {
        "session_id": task.session_id,
        "status": task.status,
        "error_msg": task.error_msg,
    }












