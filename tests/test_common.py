from core.common import short_error, translate_error


# short_error：换行被压成空格
def test_short_error_basic():
    e = Exception("hello\nworld")
    assert short_error(e) == "hello world"


# short_error：超长被截到 limit 个字
def test_short_error_limit():
    e = Exception("a" * 500)
    assert len(short_error(e, limit=200)) == 200


# translate_error：认识的关键词，返回对应人话
def test_translate_closed():
    assert translate_error(Exception("no such window")) == "浏览器窗口已被关闭，请重新开始"


def test_translate_timeout():
    assert translate_error(Exception("operation timed out")) == "操作超时，网页响应太慢，请重试"


# 不认识的错误，走兜底、以"操作失败："开头
def test_translate_unknown():
    assert translate_error(Exception("some weird new error")).startswith("操作失败：")
