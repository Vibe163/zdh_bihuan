import logging

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from core.response import fail_response

logger = logging.getLogger(__name__)


async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    # 接住你自己主动 raise 的错，比如 400、404
    return fail_response(code=exc.status_code, message=str(exc.detail))


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    # 接住 422：前端传的参数格式不对，把出错字段拼成一句话
    detail = "; ".join(
        f"{'.'.join(str(x) for x in e['loc'])}: {e['msg']}"
        for e in exc.errors()
    )
    return fail_response(code=422, message=f"参数校验失败：{detail}")


async def global_exception_handler(request: Request, exc: Exception):
    # 兜底：接住所有没料到的崩溃，完整堆栈记日志，只给用户一句客气话
    logger.exception("服务器未处理异常")
    return fail_response(code=500, message="服务器内部错误，请稍后重试")
