from fastapi import APIRouter,Depends,HTTPException
from sqlmodel import Session,select
from db.database import get_db
from pydantic import BaseModel, Field
from db.models import Register
import uuid

from automation.browser_session import Browser, VerifyCodeError
from automation.session_manager import manager
from core.response import success_response
from core.common import CreateSession,short_error,translate_error
from core.crypto import encrypt_password

router = APIRouter(prefix="/register", tags=["自动化注册模块"])


class EmailPassword(BaseModel):
    session_id: str
    username: str = Field(min_length=1, max_length=64, description="邮箱用户名，不含@")
    email_suffix: str = Field(pattern=r'^@(qq|gmail|163|icloud|outlook)\.com$', description="请选择邮箱后缀")
    password: str = Field(min_length=6, description="密码至少6位")


class verify_num(BaseModel):
    session_id: str
    verify_num: str = Field(pattern=r'^\d{6}$', description="验证码必须是6位数字")

@router.post("/one")
def one(db: Session = Depends(get_db)):
    session_id = str(uuid.uuid4())
    account = Register(session_id=session_id)
    db.add(account)
    db.commit()
    return success_response(data={"session_id": session_id})


@router.post("/two")
def two(data: EmailPassword, db: Session = Depends(get_db)):
    with manager.session_lock(data.session_id):
        stmt = select(Register).where(Register.session_id == data.session_id)
        task = db.exec(stmt).first()
        if not task:
            raise HTTPException(status_code=404, detail="会话不存在")
        if task.status != "init":
            raise HTTPException(status_code=400, detail="流程脱轨，请勿重复提交")

        full_email = data.username + data.email_suffix  # 拼成完整邮箱，如 abc@qq.com
        task.email = full_email
        task.password = encrypt_password(data.password)  # 加密后再存库

        b = None
        try:
            b = Browser()
            b.open_register_page()
            b.fill_email_and_pwd(data.username, data.email_suffix, data.password)
            manager.add(data.session_id, b)
            task.status = "filling"
        except Exception as e:
            task.status = "register_fail"
            task.error_msg = translate_error(e)
            manager.remove(data.session_id)
            if b:
                try:
                    b.close()
                except Exception:
                    pass
            db.commit()   # 先把失败状态、错误原因落库，以后能查
            raise HTTPException(status_code=400, detail="注册失败：" + translate_error(e))

        db.commit()
        return success_response(data={"session_id": task.session_id})






@router.post("/three")
def three(data: CreateSession,db: Session = Depends(get_db)):
    with manager.session_lock(data.session_id):
        # 判断session_id和状态码是否为：filling
        stmt = select(Register).where(Register.session_id == data.session_id)  # 编写查询条件
        task = db.exec(stmt).first()  # 执行查询
        if not task:
            raise HTTPException(status_code=404, detail="会话不存在")

        if task.status != "filling":
            raise HTTPException(status_code=400, detail="流程脱轨，请勿重复提交")

        b = manager.get(data.session_id)  # 取出存在内存里已经启动的浏览器
        if not b:
            raise HTTPException(status_code=404, detail="浏览器不存在，请重新走流程")
        try:
            b.click_verify_button() # 自动点击发送验证码按钮
            task.status = "waiting_code"  # 更新状态
        except Exception as e:
            task.status = "register_fail"
            task.error_msg = translate_error(e)
            manager.remove(data.session_id)  # 浏览器可能半开，清理掉
            if b:
                try:
                    b.close()
                except Exception:
                    pass
            db.commit()
            raise HTTPException(status_code=400, detail="发送验证码失败：" + translate_error(e))

        db.commit() # 直接commit，它发现对象变了，就自动发 UPDATE。不用再 add 一次。
        return success_response(data={"session_id": task.session_id})



@router.post("/four")
def four(data: verify_num, db: Session = Depends(get_db)):
    with manager.session_lock(data.session_id):
        stmt = select(Register).where(Register.session_id == data.session_id)
        task = db.exec(stmt).first()
        if not task:
            raise HTTPException(status_code=404, detail="会话不存在")
        if task.status != "waiting_code":
            raise HTTPException(status_code=400, detail="流程脱轨，请勿重复提交")

        b = manager.get(data.session_id)
        if not b:
            raise HTTPException(status_code=404, detail="浏览器不存在，请重新走流程")

        try:
            b.enter_verify_and_click(data.verify_num)
            task.status = "finished"
        except VerifyCodeError:
            # 红标签：浏览器留着、状态还是 waiting_code，改完能再交
            raise HTTPException(status_code=400, detail="验证码错误，请重新输入")
        except Exception as e:
            # 蓝标签：环境崩了，置失败、关浏览器
            task.status = "register_fail"
            task.error_msg = translate_error(e)
            manager.remove(data.session_id)
            if b:
                try:
                    b.close()
                except Exception:
                    pass
            db.commit()
            raise HTTPException(status_code=400, detail="注册失败：" + translate_error(e))

        db.commit()
        return success_response(data={"session_id": task.session_id})




@router.post("/five")
def five(data: CreateSession,db: Session = Depends(get_db)):
    with manager.session_lock(data.session_id):
        stmt = select(Register).where(Register.session_id == data.session_id)
        task = db.exec(stmt).first()
        if not task:
            raise HTTPException(status_code=404, detail="会话不存在")
        if task.status == "over":
            # 已经收尾过（重复提交/双击）：直接返回成功，不再重复关浏览器
            return success_response(data={"session_id": task.session_id, "message": "已完成"})
        if task.status != "finished":
            raise HTTPException(status_code=400, detail="流程脱轨")

        # 取出存在内存里已经启动的浏览器
        b = manager.get(data.session_id)
        if not b:
            raise HTTPException(status_code=404, detail="浏览器不存在，请重新走流程")

        #销毁当前浏览器
        manager.close_and_remove(data.session_id)  # 关+删，关失败也不中断后面的收尾
        task.status = "over"
        db.commit()
        return success_response(data={"session_id": task.session_id})



@router.get("/polling") # GET接口，直接用session_id 直接写在括号里（这叫 query 参数），不用建模型、不用填 body
def polling(session_id: str,db: Session = Depends(get_db)):
    stmt = select(Register).where(Register.session_id == session_id)
    task = db.exec(stmt).first()
    if not task:
        raise HTTPException(status_code=404, detail="会话不存在")
    return success_response(data={
        "session_id": task.session_id,
        "status": task.status,
        "error_msg": task.error_msg,
    })













