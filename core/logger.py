import logging
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path


def setup_logging(log_dir: Path | str = "logs", level: int = logging.INFO):
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)   # 日志目录不存在就建

    # 每行日志的统一格式：时间 级别 模块名 内容
    formatter = logging.Formatter(
        "%(asctime)s %(levelname)s %(name)s: %(message)s"
    )

    # 1. 控制台输出：开发时直接在终端看
    console = logging.StreamHandler()
    console.setLevel(level)
    console.setFormatter(formatter)

    # 2. 全量文件：按天轮转（每天一个文件）、保留15天，记 INFO 及以上
    app_file = TimedRotatingFileHandler(
        log_path / "app.log", when="midnight", backupCount=15, encoding="utf-8"
    )
    app_file.setLevel(level)
    app_file.setFormatter(formatter)

    # 3. 错误文件：只记 ERROR 及以上、保留30天，方便专门排查问题
    error_file = TimedRotatingFileHandler(
        log_path / "error.log", when="midnight", backupCount=30, encoding="utf-8"
    )
    error_file.setLevel(logging.ERROR)
    error_file.setFormatter(formatter)

    # 挂到根 logger：清掉旧的 handler（覆盖 basicConfig），再挂上这三个
    root = logging.getLogger()
    root.setLevel(level)
    root.handlers.clear()
    root.addHandler(console)
    root.addHandler(app_file)
    root.addHandler(error_file)

    # uvicorn 给自己的 logger 单独配了控制台、且不往根日志传，导致它的日志不进文件。
    # 这里统一处理：去掉它自己的 handler、改成往根 logger 传，走我们这套控制台+文件
    for name in ["uvicorn", "uvicorn.access", "uvicorn.error"]:
        uv_logger = logging.getLogger(name)
        uv_logger.handlers.clear()   # 去掉 uvicorn 自己的输出
        uv_logger.propagate = True   # 让它往根 logger 传，控制台和文件就都有了
