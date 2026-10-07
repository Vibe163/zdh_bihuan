import logging  # 导入日志工具：把运行信息、错误正式记录下来，替代 print
from contextlib import asynccontextmanager  # 导入异步上下文管理器：用来写"启动时、关闭时"自动执行的代码
from pathlib import Path  # 导入路径工具：用来拼文件路径，比手写字符串更稳

from fastapi import FastAPI  # 导入 FastAPI 主类：用它创建后端应用
from fastapi.exceptions import RequestValidationError  # 导入"参数校验失败"异常：就是 422 那个
from fastapi.middleware.cors import CORSMiddleware  # 导入跨域中间件：允许别的网页来调你的接口
from fastapi.responses import FileResponse  # 导入文件响应：把 HTML、图标这种文件返回给浏览器
from starlette.exceptions import HTTPException as StarletteHTTPException  # 导入 HTTP 异常（400/404），起别名防重名

from db.database import create_db_and_tables, reset_stuck_tasks  # 导入建表和重启恢复函数：启动时调用
from core.exception_handler import (  # 从异常处理模块，一次导入三个处理器
    http_exception_handler,  # 处理器一：管你主动抛出的 HTTP 异常（400、404）
    validation_exception_handler,  # 处理器二：管参数校验失败（422）
    global_exception_handler,  # 处理器三：兜底，管所有没料到的崩溃（500）
)
from core.logger import setup_logging  # 导入日志配置函数：启动时调用一次
from api.register_zdh import router as register  # 导入注册模块的路由，起名 register
from api.login_zdh import router as login  # 导入登录模块的路由，起名 login
from api.payment_zdh import router as payment  # 导入付款模块的路由，起名 payment

from automation.session_manager import manager

from core.config import settings

# 配置日志：控制台 + 文件双输出，文件按天轮转（全量留15天、错误留30天）
setup_logging()


@asynccontextmanager  # 把下面函数变成"异步上下文管理器"，才能挂给 lifespan
async def lifespan(app: FastAPI):  # 生命周期函数：启动、关闭时各执行一段；app 是当前应用
    create_db_and_tables()  # 启动时：把数据库表建好
    reset_stuck_tasks()     # 启动时：把上次没走完的会话判失败
    yield  # 分界点：这行之前=启动时执行，这行之后=关闭时执行
    # 关闭时要做的 close_all（一次性关所有浏览器），下一步再加
    manager.close_all() # # 服务关闭时：关掉所有还开着的浏览器，不留孤儿


app = FastAPI(lifespan=lifespan)  # 创建后端应用实例，并把生命周期函数挂给它

# 下面三行注册异常处理器：告诉应用"遇到对应异常，就交给对应函数处理"
app.add_exception_handler(StarletteHTTPException, http_exception_handler)  # HTTP 异常 → 第一个处理器
app.add_exception_handler(RequestValidationError, validation_exception_handler)  # 422 → 第二个处理器
app.add_exception_handler(Exception, global_exception_handler)  # 任何其他异常 → 第三个兜底

app.add_middleware(  # 给应用添加跨域中间件
    CORSMiddleware,  # 中间件类型：专门处理跨域
    allow_origins=settings.cors_origins_list,  # 只放行白名单里的前端，不再用 *
    allow_methods=["*"],  # 允许哪些请求方法（GET、POST）：* = 全部
    allow_headers=["*"],  # 允许带哪些请求头：* = 全部
)

app.include_router(register)  # 挂上注册路由：注册接口才生效
app.include_router(login)  # 挂上登录路由
app.include_router(payment)  # 挂上付款路由


@app.get("/")  # 注册一个 GET 接口，路径是根路径 /
def start():  # 有人访问 / 时，执行这个函数
    # __file__ = 当前 main.py 的完整路径；.parent = 它所在的文件夹（D:\py_920）；再拼 index.html
    return FileResponse(Path(__file__).parent / "static" / "index.html") # 把 index.html 文件返回给浏览器


@app.get("/tb_16x16.ico")  # 注册 GET 接口，路径是网站小图标的地址
def favicon():  # 浏览器来要小图标时，执行这个函数
    return FileResponse(Path(__file__).parent / "static" / "tb_16x16.ico") # 把 ico 图标文件返回给浏览器
