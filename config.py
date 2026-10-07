from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # 等号后面的是 "默认值"。程序会先读 .env，.env 里写了就用 .env 的；.env 没写，才用默认值。
    db_user: str = "root"
    db_password: str = ""
    db_host: str = "127.0.0.1"
    db_port: int = 3306
    db_name: str = "email"
    # 允许哪些前端地址跨域调接口，多个用逗号分隔；.env 可覆盖
    cors_origins: str = "http://127.0.0.1:8080,http://localhost:8080"
    admin_token: str = "change-me"  # 管理接口密钥，真值放 .env
    encrypt_key: str = ""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @property
    def database_url(self) -> str:
        return f"mysql+pymysql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"
    @property
    def cors_origins_list(self) -> list[str]:
        # 把逗号分隔的字符串切成列表、去掉空格
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
