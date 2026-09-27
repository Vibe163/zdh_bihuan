# session_manager.py —— 内存里记住当前打开的浏览器实例，支持存取删除，含超时自动清理
import threading

class SessionManager:
    def __init__(self):
        # 字典：session_id -> 浏览器对象
        self._sessions = {}
        # 锁：防止多个请求同时读写字典出问题，照写就行
        self._lock = threading.Lock()

    def add(self, session_id, browser):
        # 存入浏览器
        with self._lock:
            self._sessions[session_id] = browser

    def get(self, session_id):
        # 取出浏览器，没有就返回 None
        with self._lock:
            return self._sessions.get(session_id)

    def remove(self, session_id):
        # 删除并返回浏览器，没有就返回 None
        with self._lock:
            return self._sessions.pop(session_id, None)

# 全局唯一实例，所有接口 import 这一个
manager = SessionManager()
