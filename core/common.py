from pydantic import BaseModel


# 通用模型：只传 session_id 的接口用
class CreateSession(BaseModel):
    session_id: str


# 截取错误信息：去掉换行、限长，避免存一大串英文
def short_error(e: Exception, limit: int = 200) -> str:
    msg = getattr(e, "msg", None) or str(e)
    msg = " ".join(msg.split())
    return msg[:limit]
def translate_error(e: Exception) -> str:
    # 拿到原始错误信息、转小写方便匹配关键词
    raw = getattr(e, "msg", None) or str(e)
    text = raw.lower()

    # 按关键词匹配、返回人话（具体的放前面，顺序别乱）
    if "no such window" in text or "target window already closed" in text:
        return "浏览器窗口已被关闭，请重新开始"
    if "session deleted" in text or "not connected to devtools" in text or "browser has closed" in text:
        return "浏览器已关闭或连接断开，请重新开始"
    if "unable to locate element" in text or "no such element" in text:
        return "网页加载异常或页面结构变化，请重试"
    if "stale element reference" in text:
        return "页面已刷新，请重试"
    if "element not interactable" in text:
        return "页面元素暂时无法操作，请重试"
    if "err_proxy_connection_failed" in text or "err_tunnel_connection_failed" in text:
        return "代理连接失败，请检查网络或更换节点"
    if "err_connection_closed" in text or "err_connection_refused" in text or "err_connection_reset" in text:
        return "网络连接异常，请检查网络后重试"
    if "timed out" in text or "timeout" in text:
        return "操作超时，网页响应太慢，请重试"
    if "unexpectedly exited" in text:
        return "浏览器驱动异常退出，请重试"
    # 兜底：不认识的错误，返回截断的原文
    return "操作失败：" + short_error(e)
