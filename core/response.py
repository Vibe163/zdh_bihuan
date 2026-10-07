from typing import Any
from fastapi.responses import JSONResponse


def success_response(data: Any = None, message: str = "success", code: int = 200) -> JSONResponse:
    """统一成功返回"""
    return JSONResponse(
        status_code=code,
        content={"code": code, "message": message, "data": data},
    )


def fail_response(code: int, message: str, data: Any = None) -> JSONResponse:
    """统一失败返回"""
    return JSONResponse(
        status_code=code,
        content={"code": code, "message": message, "data": data},
    )
