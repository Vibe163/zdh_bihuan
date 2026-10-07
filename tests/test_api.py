# client 夹具由同目录 conftest.py 提供（SQLite 内存库，不碰 MySQL）

# 注册 one：返回 session_id
def test_register_one(client):
    r = client.post("/register/one")
    assert r.status_code == 200
    body = r.json()
    assert body["code"] == 200
    assert body["data"]["session_id"]


# 登录 one：返回 session_id
def test_login_one(client):
    r = client.post("/login/one")
    assert r.status_code == 200
    assert r.json()["data"]["session_id"]


# 注册 two：邮箱后缀不合法，应被参数校验拦住、返回 422（不会开浏览器）
def test_register_two_bad_suffix(client):
    sid = client.post("/register/one").json()["data"]["session_id"]
    r = client.post("/register/two", json={
        "session_id": sid,
        "username": "abc",
        "email_suffix": "@bad.com",
        "password": "123456"
    })
    assert r.status_code == 422
    assert r.json()["code"] == 422


# 注册 two：密码太短，返回 422
def test_register_two_short_password(client):
    sid = client.post("/register/one").json()["data"]["session_id"]
    r = client.post("/register/two", json={
        "session_id": sid,
        "username": "abc",
        "email_suffix": "@qq.com",
        "password": "123"
    })
    assert r.status_code == 422


# 付款 confirm：不带管理令牌，门禁直接拦、返回 401（不碰浏览器）
def test_confirm_without_token(client):
    r = client.post("/payment/confirm", json={"session_id": "fake-id"})
    assert r.status_code == 401
    assert r.json()["code"] == 401
