from fastapi import FastAPI


from router.register import router as register
from router.login import router as login
from router.Payment import router as payment

from contextlib import asynccontextmanager # `asynccontextmanager`：给你异步版本的「进入 / 退出」回调
from database import create_db_and_tables

from fastapi.responses import FileResponse
from pathlib import Path
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 服务启动前执行
    create_db_and_tables()
    yield
    # 服务关闭时执行

app = FastAPI(lifespan=lifespan)

# 允许本地 HTML 页面跨域调用接口（演示用）
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# 挂载注册模块
app.include_router(register)
#登录模块
app.include_router(login)
# 付款模块
app.include_router(payment)



@app.get("/")
def start():
    return FileResponse(Path(__file__).parent / "index.html") # 用绝对路径

@app.get("/app")
def app_page():
    return FileResponse(Path(__file__).parent / "register.html") # 新版三步注册页面