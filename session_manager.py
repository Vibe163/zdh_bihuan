# session_manager.py —— 内存里记住当前打开的浏览器实例，支持存取删除
import threading

class SessionManager:
    def __init__(self):
        # 字典：session_id -> 浏览器对象
        self._sessions = {}
        # 锁：防止多个请求同时读写字典出问题，照写就行
        self._lock = threading.Lock()
        self._session_locks = {}  # 每个会话一把专用锁，防同一会话并发/双击
        self._links = {}  # 已完成的订阅链接缓存（独立于浏览器，关了浏览器也能返回）

    def add(self, session_id, browser):
        # 存入浏览器
        with self._lock:
            self._sessions[session_id] = browser

    def get(self, session_id):
        # 取出浏览器，没有就返回 None
        with self._lock:
            return self._sessions.get(session_id)

    def session_lock(self, session_id):
        # 返回该会话专属的锁：同一会话的并发/双击请求，会被这把锁拦成一个一个进
        with self._lock:
            lk = self._session_locks.get(session_id)
            if lk is None:
                lk = threading.Lock()
                self._session_locks[session_id] = lk
            return lk

    def set_link(self, session_id, link_url):
        # 缓存已拿到的订阅链接
        with self._lock:
            self._links[session_id] = link_url

    def get_link(self, session_id):
        # 取出缓存的链接，没有返回 None
        with self._lock:
            return self._links.get(session_id)

    def remove(self, session_id):
        # 删除并返回浏览器，没有就返回 None
        with self._lock:
            return self._sessions.pop(session_id, None)

    def close_and_remove(self, session_id):
        # 先从字典摘出来，再关（关浏览器可能要几秒，别占着锁）
        with self._lock:
            b = self._sessions.pop(session_id, None)
        if b:
            try:
                b.close()
            except Exception:
                pass  # 浏览器可能已经崩了，关不掉也等于释放了
        return b

    def close_all(self):
        # 停服时一次性关掉所有还开着的浏览器
        with self._lock:
            browsers = list(self._sessions.values())  # 先把所有浏览器取出来
            self._sessions.clear()                     # 清空字典
        for b in browsers:
            try:
                b.close()
            except Exception:
                pass  # 浏览器可能已经崩了，关不掉也等于释放了


# 全局唯一实例，所有接口 import 这一个
manager = SessionManager()
