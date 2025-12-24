import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from PIL import Image
from io import BytesIO
import base64
import time
import random
import os
#所需依赖 requests selenium pillow


# 配置
USERNAME = os.getenv("sjs_username")
PASSWORD = os.getenv("sjs_password")
OCR_SERVICE = os.getenv("ocr_service") #替换为自部署的OCR服务地址
main_url = "https://xsijishe.net"
TIMEOUT = 10

# 登录用到的参数
formhash = ""
seccodehash = ""
referer = ""
cookies = {}
sign_url = '/k_misign-sign.html'
checkIn_status = 2  # 签到状态：0-已签到，1-签到成功，2-失败

def getrandom(code_len=4):
    chars = 'qazwsxedcrfvtgbyhnujmikolpQAZWSXEDCRFVTGBYHNUJIKOLP'
    return ''.join(random.choices(chars, k=code_len))

def cookiejar_to_json(Rcookie):
    """将cookiejar转换为json"""
    global cookies
    for item in Rcookie:
        cookies[item.name] = item.value

def recognize_captcha(base64_img):
    if "," in base64_img:
        base64_img = base64_img.split(",", 1)[1]
    try:
        resp = requests.post(OCR_SERVICE, json={"image": base64_img}, timeout=TIMEOUT)
        return resp.json().get("result", "").strip() if resp.ok else ""
    except Exception as e:
        print(f"🤖 OCR识别错误: {e}")
        return ""

def check_captcha(session, seccodehash, seccodeverify):
    url = f"{main_url}/misc.php"
    params = {
        "mod": "seccode",
        "action": "check",
        "inajax": "1",
        "modid": "member::logging",
        "idhash": seccodehash,
        "secverify": seccodeverify
    }
    headers = {
        "Referer": referer,
        "User-Agent": session.headers.get("User-Agent", ""),
        "X-Requested-With": "XMLHttpRequest"
    }
    try:
        r = session.get(url, params=params, headers=headers, timeout=TIMEOUT)
        #print(f"🔍 验证码校验结果：{'✅ success' if r.ok and 'succeed' in r.text else '❌ failed'}")
        return r.ok and "succeed" in r.text
    except Exception as e:
        print(f"❌ 验证码校验异常: {e}")
        return False

def get_form_info():
    global formhash, seccodehash, referer, cookies

    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--no-sandbox')
    driver = webdriver.Chrome(options=chrome_options)

    try:
        driver.get(main_url + "/home.php?mod=space")
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "referer")))
        referer_input = driver.find_element(By.NAME, "referer")
        referer = referer_input.get_attribute("value")

        driver.get(referer)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "formhash")))
        formhash = driver.find_element(By.NAME, "formhash").get_attribute("value")

        seccode_el = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//span[starts-with(@id, "seccode_")]'))
        )
        seccodehash = seccode_el.get_attribute("id").replace("seccode_", "")
        cookies = {c['name']: c['value'] for c in driver.get_cookies()}

        print(f"📝 [信息] 获取成功: formhash={formhash}, seccodehash={seccodehash}")
        return True
    except Exception as e:
        print(f"⚠️ 获取登录参数失败：{e}")
        return False
    finally:
        driver.quit()

def login_by_requests():
    if not get_form_info():
        return False

    session = requests.Session()
    for k, v in cookies.items():
        session.cookies.set(k, v)
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/114.0 Safari/537.36",
        "Referer": referer
    })

    captcha_url = f"{main_url}/misc.php?mod=seccode&update={int(time.time())}&idhash={seccodehash}"
    for _ in range(5):
        resp = session.get(captcha_url)
        if "image" not in resp.headers.get("Content-Type", ""):
            print("❗ 验证码图片响应异常，重试...")
            continue

        img = Image.open(BytesIO(resp.content))
        buffer = BytesIO()
        img.save(buffer, format="JPEG")
        base64_img = "data:image/jpeg;base64," + base64.b64encode(buffer.getvalue()).decode()

        seccodeverify = recognize_captcha(base64_img)

        if len(seccodeverify) == 4 and check_captcha(session, seccodehash, seccodeverify):
            print(f"🤖 [OCR] 验证码识别结果: {seccodeverify} | ✅ [验证通过]")
            break
        else:
            print(f"🤖 [OCR] 验证码识别结果: {seccodeverify}  | ❌ [验证不通过]")
    else:
        print("❌ [失败] 验证码识别/验证失败")
        return False

    login_url = f"{main_url}/member.php?mod=logging&action=login&loginsubmit=yes&handlekey=login&loginhash=L{getrandom()}&inajax=1"
    payload = {
        "formhash": formhash,
        "referer": referer,
        "username": USERNAME,
        "password": PASSWORD,
        "questionid": "0",
        "answer": "",
        "seccodehash": seccodehash,
        "seccodemodid": "member::logging",
        "seccodeverify": seccodeverify,
    }

    r = session.post(login_url, data=payload, headers={
        "Content-Type": "application/x-www-form-urlencoded"
    })

    if "欢迎您回来" in r.text:
        print("🎉 [成功] 登录成功！")
        cookiejar_to_json(r.cookies)
        return True
    else:
        print(f"❌ [失败] 登录失败：{r.text[:100]}...")  # 截断打印防止过长
        send("司机社签到", "❌ [失败] 登录失败")
        return False

def do_sign_in(driver):
    """使用 Selenium 执行签到操作"""
    global checkIn_status
    try:
        print("⏳ 正在执行签到操作...")

        driver.get(main_url)
        time.sleep(1)

        driver.delete_all_cookies()
        for cookie_name, cookie_value in cookies.items():
            driver.add_cookie({'name': cookie_name, 'value': cookie_value, 'path': '/', 'domain': 'xsijishe.com'})

        sign_page_url = f"{main_url}{sign_url}"
        print(f"➡️ 访问签到页面: {sign_page_url}")
        driver.get(sign_page_url)

        wait = WebDriverWait(driver, 15)
        wait.until(EC.presence_of_element_located((By.ID, 'JD_sign')))

        page_source = driver.page_source
        if "今日已签" in page_source or "您今天已经签到过了" in page_source:
            print("✅ 今日已签到")
            checkIn_status = 0
            return True

        sign_button = driver.find_element(By.ID, 'JD_sign')
        print("👉 找到签到按钮，准备点击")

        driver.save_screenshot("before_sign.png")

        sign_button.click()
        print("✅ 已点击签到按钮")

        time.sleep(2)

        driver.save_screenshot("after_sign.png")

        new_page_source = driver.page_source
        if "今日已签" in new_page_source or "您今天已经签到过了" in new_page_source:
            print("✅ 签到成功，页面显示今日已签到")
            checkIn_status = 0
            return True
        elif "签到成功" in new_page_source:
            print("🎉 签到成功")
            checkIn_status = 1
            return True
        else:
            print("⚠️ 签到后页面未显示成功信息，尝试刷新页面再次确认")

            driver.refresh()
            time.sleep(2)

            refresh_page_source = driver.page_source
            if "今日已签" in refresh_page_source or "您今天已经签到过了" in refresh_page_source:
                print("✅ 刷新后确认签到成功")
                checkIn_status = 0
                return True

        checkIn_status = 2
        print("❌ 签到失败")
        send("司机社签到", "❌ 签到操作失败")
        return False

    except Exception as e:
        print(f"❌ 签到过程中出现异常")
        send("司机社签到", "❌ 签到过程中出现异常")
        checkIn_status = 2
        return False

def printUserInfo(driver):
    """获取用户信息"""
    global checkIn_status

    try:
        print("🔎 准备获取用户信息...")

        sign_page_url = f"{main_url}{sign_url}"
        print(f"➡️ 访问签到页面: {sign_page_url}")
        driver.get(sign_page_url)

        wait = WebDriverWait(driver, 20)
        wait.until(EC.presence_of_element_located((By.ID, 'qiandaobtnnum')))

        qiandao_num = driver.find_element(By.ID, 'qiandaobtnnum').get_attribute('value')
        lxdays = driver.find_element(By.ID, 'lxdays').get_attribute('value')
        lxtdays = driver.find_element(By.ID, 'lxtdays').get_attribute('value')
        lxlevel = driver.find_element(By.ID, 'lxlevel').get_attribute('value')
        lxreward = driver.find_element(By.ID, 'lxreward').get_attribute('value')

        page_content = driver.page_source
        if "今日已签" in page_content or "您今天已经签到过了" in page_content:
            print("✅ 页面显示今日已签到")
            checkIn_status = 0
        elif "签到成功" in page_content:
            print("🎉 页面显示签到成功")
            checkIn_status = 1

        lxqiandao_content = (
            f'签到排名：{qiandao_num}\n'
            f'签到等级：Lv.{lxlevel}\n'
            f'连续签到：{lxdays} 天\n'
            f'签到总数：{lxtdays} 天\n'
            f'签到奖励：{lxreward}\n'
        )

        profile_url = f'{main_url}/home.php?mod=space'
        print(f"➡️ 访问个人主页: {profile_url}")
        driver.get(profile_url)

        wait.until(EC.presence_of_element_located((By.ID, 'ct')))
        driver.save_screenshot("profile_page.png")

        xm = None
        xpaths = [
            '//*[@id="ct"]/div/div[2]/div/div[1]/div[1]/h2',
            '//div[contains(@class, "h")]/h2',
            '//h2[contains(@class, "mt")]',
            '//div[contains(@id, "profile")]//h2'
        ]

        for xpath in xpaths:
            elements = driver.find_elements(By.XPATH, xpath)
            if elements:
                xm = elements[0].text.strip()
                print(f"👤 找到用户名: {xm}")
                break
        if not xm:
            print("⚠️ 警告: 无法获取用户名，将使用默认值")
            xm = "未知用户"

        jf = ww = cp = gx = "未知"
        try:
            stats_container = driver.find_element(By.ID, "psts")
            stats = stats_container.find_elements(By.TAG_NAME, "li")
            for stat in stats:
                text = stat.text.lower()
                if "积分" in text:
                    jf = stat.text
                elif "威望" in text:
                    ww = stat.text
                elif "车票" in text:
                    cp = stat.text
                elif "贡献" in text:
                    gx = stat.text
        except:
            try:
                all_elements = driver.find_elements(By.XPATH,
                                                    "//*[contains(text(), '积分') or contains(text(), '威望') or contains(text(), '车票') or contains(text(), '贡献')]")
                for element in all_elements:
                    text = element.text.lower()
                    if "积分" in text:
                        jf = element.text
                    elif "威望" in text:
                        ww = element.text
                    elif "车票" in text:
                        cp = element.text
                    elif "贡献" in text:
                        gx = element.text
            except Exception as e:
                print(f"❌ 无法获取详细统计信息: {e}")

        xm = f"账户【{xm}】".center(24, '=')

        checkIn_content = ["已签到", "签到成功", "签到失败"]
        info_text = (
            f'{xm}\n'
            f'签到状态: {checkIn_content[checkIn_status]} \n'
            f'{lxqiandao_content} \n'
            f'当前积分: {jf}\n'
            f'当前威望: {ww}\n'
            f'当前车票: {cp}\n'
            f'当前贡献: {gx}\n\n'
        )
        print(info_text)
        return True

    except Exception as e:
        print(f'❌ 获取用户信息失败: {e}')
        try:
            driver.save_screenshot("error_screenshot.png")
            print("保存错误截图到 error_screenshot.png")
        except:
            pass
        return False
def load_send():
    global send
    cur_path = os.path.abspath(os.path.dirname(__file__))
    notify_file_path = os.path.join(cur_path, "..", "notify.py")
    if os.path.exists(notify_file_path):
        try:
            from notify import send
        except:
            send = False
            print("加载通知服务失败~")
    else:
        send = False
        print("加载通知服务失败~")
if __name__ == "__main__":
    load_send()
    if login_by_requests():
        print("✔️ 登录成功，准备启动浏览器执行签到和信息获取")
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--no-sandbox')
        driver = webdriver.Chrome(options=chrome_options)

        try:
            success = do_sign_in(driver)
            if success:
                print("✔️ 签到操作完成")
            else:
                print("❌ 签到操作失败")
            printUserInfo(driver)
        finally:
            driver.quit()
    else:
        print("❌ 登录失败，脚本结束")
        send("司机社签到", "❌ 登录失败，脚本结束")
