"""
一次性准备好 undetected_chromedriver 使用的固定 chromedriver。
完成后：下载 -> 解压 -> 用 uc 做伪装(patch)，放到 D:\\py_920\\drivers\\chromedriver.exe。
之后 browser_session.py 用 driver_executable_path 指向它，uc 不再每次下载、也不会删除。
"""
import os
import zipfile
import shutil
import time

import requests
import undetected_chromedriver as uc

PROXY = {
    "http": "http://127.0.0.1:7897",
    "https": "http://127.0.0.1:7897",
}
# 与本机 Chrome 主版本 154 匹配（小版本差一位不影响）
URL = ("https://storage.googleapis.com/chrome-for-testing-public/"
       "154.0.8037.57/win64/chromedriver-win64.zip")

DEST_DIR = r"D:\py_920\drivers"
EXE = os.path.join(DEST_DIR, "chromedriver.exe")
ZIP = os.path.join(DEST_DIR, "_chromedriver.zip")

os.makedirs(DEST_DIR, exist_ok=True)

# 1) 下载，带重试，并校验字节数是否完整
ok = False
for i in range(1, 6):
    try:
        with requests.get(URL, proxies=PROXY, stream=True, timeout=30) as r:
            r.raise_for_status()
            total = int(r.headers.get("content-length", 0))
            got = 0
            with open(ZIP, "wb") as f:
                for chunk in r.iter_content(1 << 16):
                    f.write(chunk)
                    got += len(chunk)
        if total == 0 or got == total:
            print(f"[1/3] 下载完整: {got}/{total} 字节")
            ok = True
            break
        print(f"第{i}次不完整 {got}/{total}，重试...")
    except Exception as e:
        print(f"第{i}次下载失败: {e}")
        time.sleep(2)

if not ok:
    raise SystemExit("驱动下载失败，请检查 Clash 代理后重跑本脚本")

# 2) 解压出 chromedriver.exe
with zipfile.ZipFile(ZIP) as z:
    src = [n for n in z.namelist() if n.endswith("chromedriver.exe")][0]
    with z.open(src) as s, open(EXE, "wb") as o:
        shutil.copyfileobj(s, o)
os.remove(ZIP)
print(f"[2/3] 解压完成: {EXE}（{os.path.getsize(EXE)} 字节）")

# 3) 用 uc 对驱动做伪装(patch)，原地修改
p = uc.Patcher(executable_path=EXE, version_main=154)
if not p.is_binary_patched():
    p.patch_exe()
print(f"[3/3] 伪装(patch)完成: {p.is_binary_patched()}")
print("搞定。browser_session.py 用 driver_executable_path 指向此文件即可。")
