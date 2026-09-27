from sqlmodel import SQLModel,Field # `SQLModel` 是基类，用来定义数据库模型（表结构），自带 Pydantic 校验
from datetime import datetime

class Register(SQLModel, table=True): # table=True 写这个在数据库建真表
    id: int | None = Field(default=None, primary_key=True)
    email: str | None = Field(default=None)
    password: str | None = Field(default=None)
    status: str = Field(default="init")
    session_id: str | None = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.now)
    error_msg: str | None = Field(default=None)


