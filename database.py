from sqlmodel import create_engine,Session,SQLModel,select # 拿到数据库的连接入口，后面所有数据库操作都要靠它
from model import Register
from config import settings

# # ========== 数据库连接信息 ==========
# USER = "root"        # mysql账号
# PASSWORD = "123456"  # mysql密码
# HOST = "127.0.0.1"   # 数据库实例IP
# PORT = "3306"        # 实例端口
# DB_NAME = "email"  # 数据库名（这个库要提前在mysql手动建好）
#
# # 拼接连接URL
# SQL_URL = f"mysql+pymysql://{USER}:{PASSWORD}@{HOST}:{PORT}/{DB_NAME}"



# 创建数据库引擎
engine = create_engine(
    settings.database_url,
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

def reset_stuck_tasks():
    # 服务重启后，浏览器都已不在（manager 是内存），
    # 把所有没走完（init/filling/waiting_code/finished）的会话统一判失败，避免永远卡在中间
    with Session(engine) as session:
        stmt = select(Register).where(
            Register.status.in_(["init", "filling", "waiting_code", "finished"])
        )
        stuck = session.exec(stmt).all()
        for task in stuck:
            task.status = "register_fail"
            task.error_msg = "服务重启，任务中断，请重新开始"
        session.commit()
