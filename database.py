from sqlmodel import create_engine,Session,SQLModel # 拿到数据库的连接入口，后面所有数据库操作都要靠它
from model import Register

# ========== 数据库连接信息 ==========
USER = "root"        # mysql账号
PASSWORD = "123456"  # mysql密码
HOST = "127.0.0.1"   # 数据库实例IP
PORT = "3306"        # 实例端口
DB_NAME = "email"  # 数据库名（这个库要提前在mysql手动建好）

# 拼接连接URL
SQL_URL = f"mysql+pymysql://{USER}:{PASSWORD}@{HOST}:{PORT}/{DB_NAME}"

# 创建数据库引擎
engine = create_engine(
    SQL_URL,
    echo=False,         # echo=True 调试时打开，打印SQL语句；上线关闭
    pool_pre_ping=True  # 自动检测连接是否失效
)

# 新建表函数，服务启动时调用
def create_db_and_tables():
    # 把model里面所有继承SQLModel的表全部创建
    SQLModel.metadata.create_all(engine)

# 【获取数据库会话】依赖函数，FastAPI Depends 使用
def get_db():
    with Session(engine) as session:
        yield session