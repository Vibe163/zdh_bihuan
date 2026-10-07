import undetected_chromedriver as uc # 隐藏自动化
from selenium.webdriver.common.by import By # 自动化操作
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
import time
import os
from datetime import datetime


from selenium.webdriver.support.ui import WebDriverWait,Select
from selenium.webdriver.support import expected_conditions as EC

from selenium.common.exceptions import TimeoutException, WebDriverException
class VerifyCodeError(Exception):
    """验证码错误：浏览器保留，允许重填"""
    pass


class LoginFailError(Exception):
    """登录失败：账号或密码错误，浏览器保留、允许重试"""
    pass




class Browser:

    # 初始化自动打开浏览器——————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————
    def __init__(self):
        options = uc.ChromeOptions()
        # 【提速参数】
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-default-apps")
        options.add_argument("--disable-features=Translate") # 关闭翻译功能
        options.add_argument("--disable-plugins")
        # 使用固定的、已伪装驱动：uc 不会再每次联网下载，也不会用完删除
        # Chrome 以后大版本更新时，重跑 setup_driver.py，并同步改这里的版本号
        self.driver = uc.Chrome(
            options=options,
            version_main=154,
            driver_executable_path=r"D:\py_920\drivers\chromedriver.exe",
        )
        self.driver.maximize_window()  # 浏览器全屏
        self.actions = ActionChains(self.driver) # ActionChains 是一个 "键盘鼠标动作的遥控器"。这一行是给当前浏览器配一个遥控器
        self.driver.set_page_load_timeout(30)
        self.payment_started = False  # 是否已走到付款二维码页（防重复结账）



    # 打开页面（带重试）：代理链路偶发 net::ERR_CONNECTION_CLOSED，重试即可恢复
    def get_page(self, url, tries=3):
        for i in range(tries):
            try:
                self.driver.get(url)
                return
            except WebDriverException as e:
                if i == tries - 1:
                    raise
                print(f"打开页面失败，2秒后重试（第{i + 1}次）：{str(e)[:120]}", flush=True)
                time.sleep(2)



    # 注册模块————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————
    def open_register_page(self):
        time.sleep(1.2)
        target_url = "https://xn--4gq62f52gdss.com/#/register"
        self.get_page(target_url)

    # def fill_email_and_pwd(self, email, password):
    #     # 邮箱输入框（你原来的代码不动）
    #     time.sleep(5)
    #     email_xpath = '//*[@id="main-container"]/div[2]/div/div/div/div[1]/div/div/div[2]/div[1]/input'
    #     email_input = WebDriverWait(self.driver, 30).until(
    #         EC.presence_of_element_located((By.XPATH, email_xpath))
    #     )
    #     email_input.send_keys(email)
    #
    #     # 密码框
    #     time.sleep(1.2)
    #     pwd1_xpath = '//*[@id="main-container"]/div[2]/div/div/div/div[1]/div/div/div[2]/div[3]/input'
    #     pwd1_input = WebDriverWait(self.driver, 30).until(
    #         EC.presence_of_element_located((By.XPATH, pwd1_xpath))
    #     )
    #     pwd1_input.send_keys(password)
    #
    #     # 确认密码框
    #     time.sleep(1.2)
    #     pwd2 = self.driver.find_element(By.XPATH,'//*[@id="main-container"]/div[2]/div/div/div/div[1]/div/div/div[2]/div[4]/input')
    #     pwd2.send_keys(password)
    def fill_email_and_pwd(self, username, email_suffix, password):
        # 等邮箱用户名输入框出现（注册表单动态渲染，要10~20秒，必须等、不能直接找）
        username_input = WebDriverWait(self.driver, 30).until(
            EC.presence_of_element_located(
                (By.XPATH, '//input[@placeholder="邮箱"]')
            )
        )
        username_input.send_keys(username)

        # 等后缀下拉出现，再选（原生 select，按显示文字选，如 "@qq.com"）
        suffix_select = Select(
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located(
                    (By.XPATH, '//select[contains(@class,"form-control-alt")]')
                )
            )
        )
        suffix_select.select_by_visible_text(email_suffix)

        # 填密码、确认密码（沿用你原来测试通过的定位，不改动）
        self.driver.find_element(By.XPATH, '//*[@id="main-container"]/div[2]/div/div/div/div[1]/div/div/div[2]/div[3]/input').send_keys(password)
        self.driver.find_element(By.XPATH, '//*[@id="main-container"]/div[2]/div/div/div/div[1]/div/div/div[2]/div[4]/input').send_keys(password)



    def click_verify_button(self):
        # 点击发送按钮
        time.sleep(3)
        get_code_btn = self.driver.find_element(By.XPATH,
                                           '//*[@id="main-container"]/div[2]/div/div/div/div[1]/div/div/div[2]/div[2]/div[2]/button')
        get_code_btn.click()

        # ========== 新增：按Tab，等1.5秒，按空格 ==========
        time.sleep(12)
        self.actions.send_keys(Keys.TAB).perform()
        self.actions.send_keys(Keys.SPACE).perform()
        # ================================================


    # def enter_verify_and_click(self,num):
    #     # 输入验证码
    #     yzm_btn = self.driver.find_element(By.XPATH,
    #                                   '//*[@id="main-container"]/div[2]/div/div/div/div[1]/div/div/div[2]/div[2]/div[1]/input')
    #     yzm_btn.send_keys(num)
    #
    #     # 注册按钮
    #     time.sleep(2)
    #     register_btn = self.driver.find_element(By.XPATH,
    #                                        '//*[@id="main-container"]/div[2]/div/div/div/div[1]/div/div/div[2]/div[6]/button/span/i')
    #     register_btn.click()
    #
    #     # 利用键盘实现自动点击
    #     time.sleep(12)
    #     self.actions.send_keys(Keys.TAB).perform()
    #     time.sleep(1.5)
    #     self.actions.send_keys(Keys.SPACE).perform()


    def enter_verify_and_click(self, num):
        # 验证码框，重填前先清空
        yzm_input = self.driver.find_element(
            By.XPATH,
            '//*[@id="main-container"]/div[2]/div/div/div/div[1]/div/div/div[2]/div[2]/div[1]/input')
        yzm_input.clear()
        yzm_input.send_keys(num)

        # 注册按钮
        time.sleep(2)
        register_btn = self.driver.find_element(
            By.XPATH,
            '//*[@id="main-container"]/div[2]/div/div/div/div[1]/div/div/div[2]/div[6]/button/span/i')
        register_btn.click()

        # 键盘过 CF
        time.sleep(12)
        self.actions.send_keys(Keys.TAB).perform()
        time.sleep(1.5)
        self.actions.send_keys(Keys.SPACE).perform()

        # 等成功标志 sidebar：出现=成功，等不到=验证码错，贴红标签
        try:
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.XPATH, '//*[@id="sidebar"]'))
            )
        except TimeoutException:
            raise VerifyCodeError("验证码错误，请重新输入")





    #登录模块—————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————
    def is_alive(self):
        # 试着取当前网址，取不到说明浏览器已关闭或断开
        try:
            _ = self.driver.current_url
            return True
        except Exception:
            return False

    def is_logged_in(self):
        # 判断当前是否已进入仪表盘：sidebar 或 page-header 任一存在，就是已登录
        for xpath in ['//nav[@id="sidebar"]', '//header[@id="page-header"]']:
            try:
                if self.driver.find_element(By.XPATH, xpath):
                    return True
            except Exception:
                pass  # 这个没找到，看下一个
        return False

    def open_login_page(self):
        time.sleep(1.2)
        target_url = "https://xn--4gq62f52gdss.com/#/login"  # 登录页面
        self.get_page(target_url)

    def login_email_password(self, email, password):
        # 等邮箱输入框出现：登录表单是动态渲染的，不能写死 sleep 赌时机（实测要 10~20 秒，放宽到 30）
        login_email = WebDriverWait(self.driver, 30).until(
            EC.presence_of_element_located(
                (By.XPATH, '//*[@id="main-container"]/div[2]/div/div/div/div[1]/div/div/div[2]/input'))
        )
        login_email.clear()          # 重试时先清空旧内容，再填
        login_email.send_keys(email)
        # 密码框
        login_pass = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located(
                (By.XPATH, '//*[@id="main-container"]/div[2]/div/div/div/div[1]/div/div/div[3]/input'))
        )
        login_pass.clear()           # 重试时先清空旧密码，再填
        login_pass.send_keys(password)
        # 登录按钮，等它可以点击
        login_click = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable(
                (By.XPATH, '//*[@id="main-container"]/div[2]/div/div/div/div[1]/div/div/div[4]/button'))
        )
        login_click.click()

        # 判断登录是否成功：sidebar 或 page-header 任一出现即成功，最多等20秒
        def login_success(driver):
            # 逐个看两个核心元素，找到任意一个就返回 True
            for xpath in ['//nav[@id="sidebar"]', '//header[@id="page-header"]']:
                try:
                    if driver.find_element(By.XPATH, xpath):
                        return True
                except Exception:
                    pass  # 这个没找到，接着看下一个
            return False  # 两个都没找到，返回 False、继续等

        try:
            WebDriverWait(self.driver, 5).until(login_success)
        except TimeoutException:
            # 失败后立刻清空两个框，让浏览器停在空框状态、等用户重填
            login_email.clear()
            login_pass.clear()
            raise LoginFailError("登录未成功")

    #付款模块——————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————
    def payment_one(self):
        # 关闭登录后的公示弹窗
        time.sleep(1.5)
        # 等待弹窗完全渲染好，挡住按钮的元素消失
        self.driver.find_element(By.XPATH, '//button[@aria-label="Close"]').click()
    def payment_two(self):
        # 购买订阅
        time.sleep(2)
        self.driver.find_element(By.XPATH, '//*[@id="sidebar"]/div[2]/ul/li[5]/a/span').click()
        # 选择套餐
        time.sleep(2)
        self.driver.find_element(By.XPATH, '//*[@id="main-container"]/div/div[2]/div[2]/a/div[2]/div/p[1]').click()

    # def payment_three(self):
    #     # 点击下单
    #     time.sleep(2)
    #     self.driver.find_element(By.XPATH, '//*[@id="cashier"]/div[2]/div[2]/button').click()
    #     # 点击确定取消
    #     time.sleep(2)
    #     self.driver.find_element(By.XPATH, '/html/body/div[3]/div/div[2]/div/div[2]/div/div/div[2]/button[2]').click()

    def payment_three(self):
        # 点击下单
        time.sleep(2)
        self.driver.find_element(By.XPATH, '//*[@id="cashier"]/div[2]/div[2]/button').click()

    def payment_four(self):
        # 选择微信支付
        time.sleep(5)
        self.driver.find_element(By.XPATH, '/html/body/div/div/main/div/div/div[1]/div[3]/div[2]/div[2]').click()
        # 点击结账
        time.sleep(2)
        self.driver.find_element(By.XPATH, '/html/body/div/div/main/div/div/div[2]/div/button').click()

        time.sleep(3)

    def payment_five(self):
        # ========== 页面截图，自动生成文件名 ==========
        # 生成带时间戳的文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]  # 到毫秒
        img_name = f"{timestamp}.png"
        # 保存路径（这里我用D盘Desktop/screenshot文件夹）
        save_dir = r"D:\Desktop\screenshot"
        os.makedirs(save_dir, exist_ok=True)
        save_path = os.path.join(save_dir, img_name)

        # 浏览器截图保存
        self.driver.get_screenshot_as_file(save_path)
        print(f"✅截图已保存：{save_path}")
        time.sleep(1.5)

    def payment_six(self):
        # # 浏览器返回
        # self.driver.back()
        # time.sleep(1)

        # 点击仪表盘
        self.driver.find_element(By.XPATH, '//*[@id="sidebar"]/div[2]/ul/li[1]/a').click()
        time.sleep(3)

        # 关闭提示弹窗,等待弹窗完全渲染好，挡住按钮的元素消失
        self.driver.find_element(By.XPATH, '//button[@aria-label="Close"]').click()
        time.sleep(1)

        # 点击一键订阅
        self.driver.find_element(By.XPATH, '//*[@id="main-container"]/div/div[2]/div[2]/div/div[2]/div/div/div[2]/div[1]').click()
        time.sleep(1.5)

        hook_js = """
            window.captured_subscribe_link = null;

            // 劫持新版 clipboard.writeText
            if(navigator.clipboard && navigator.clipboard.writeText){
                const originalWrite = navigator.clipboard.writeText;
                navigator.clipboard.writeText = async function(text){
                    window.captured_subscribe_link = text;
                    return originalWrite.call(this, text);
                }
            }

            // 劫持老的 document.execCommand('copy')
            const originalExec = document.execCommand;
            document.execCommand = function(cmd, ...args){
                if(cmd === 'copy'){
                    // 获取当前选中的文本，execCommand copy是复制选中内容
                    const sel = window.getSelection();
                    if(sel.rangeCount > 0){
                        window.captured_subscribe_link = sel.toString();
                    }
                }
                return originalExec.call(document, cmd, ...args);
            }
            """
        # 注入钩子
        self.driver.execute_script(hook_js)

        # 点击复制按钮
        self.driver.find_element(By.XPATH, '//div[contains(text(),"复制订阅地址")]').click()
        time.sleep(0.8)

        # 读取捕获的链接
        subscribe_url = self.driver.execute_script("return window.captured_subscribe_link;")
        return subscribe_url

    def close(self):
        self.driver.quit()


# ===== 测试入口：直接运行这个文件时执行 =====
if __name__ == "__main__":
    b = Browser()
    b.open_register_page()
    b.fill_email_and_pwd("2995179799", "ooolll666")

    input("浏览器保持中，按回车才会关闭...")   # ← 程序卡在这，浏览器不会关
    b.close()



