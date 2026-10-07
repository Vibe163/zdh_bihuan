from fastapi import Depends, HTTPException
from fastapi.security import APIKeyHeader

from .config import settings

# 密钥放在请求头 X-Token 里；auto_error=False，让我们自己返回中文提示
admin_token_scheme = APIKeyHeader(name="X-Token", auto_error=False)

def verify_admin_token(x_token: str | None = Depends(admin_token_scheme)):
    # 门卫：请求头的 X-Token 必须等于配置里的管理密钥，否则 401
    if x_token != settings.admin_token:
        raise HTTPException(status_code=401, detail="无权访问，管理令牌错误")