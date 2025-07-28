import time
import re
import base64
import random
from io import BytesIO

import requests
from bs4 import BeautifulSoup
from PIL import Image
import numpy as np

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

import os
#需要安装的依赖 requests beautifulsoup4 pillow numpy selenium


# --- 配置 ---
USERNAME = os.getenv("it_jcb_username")
PASSWORD = os.getenv("it_jcb_password")


LOGIN_PAGE_URL = "https://www.itjc8.com/member.php?mod=logging&action=login"
LOGIN_POST_URL = "https://www.itjc8.com/member.php?mod=logging&action=login&loginsubmit=yes&inajax=1"
SIGN_URL = "https://www.itjc8.com/plugin.php?id=dsu_paulsign:sign&operation=qiandao&infloat=1&sign_as=1&inajax=1"

OCR_SERVICE = os.getenv("ocr_service") #替换为自部署的OCR服务地址
COOKIE_FILE = "./itlt.txt"

qdxq_list=["kx","ng","ym","wl","nu","ch","fd","yl","shuai"]

MAX_RETRY = 3

session = requests.Session()


def get_page_source_with_selenium(url):
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    driver = webdriver.Chrome(options=options)

    driver.get(url)
    time.sleep(3)
    try:
        driver.find_element(By.CSS_SELECTOR, "span[id^='seccode_']")
    except Exception:
        print("验证码区域未找到，页面可能未完全加载")
        driver.quit()
        return None

    html = driver.page_source
    driver.quit()
    return html


def parse_login_params(html):
    soup = BeautifulSoup(html, 'html.parser')

    formhash_tag = soup.find('input', {'name': 'formhash'})
    formhash = formhash_tag['value'] if formhash_tag else None

    login_form = soup.find('form', id=re.compile(r'^loginform_'))
    loginhash = None
    if login_form:
        id_attr = login_form.get('id', '')
        match = re.search(r'loginform_(\w+)', id_attr)
        if match:
            loginhash = match.group(1)
        else:
            action = login_form.get('action', '')
            match = re.search(r'loginhash=(\w+)', action)
            if match:
                loginhash = match.group(1)

    seccodehash_tag = soup.find('input', {'name': 'seccodehash'})
    seccodehash = seccodehash_tag['value'] if seccodehash_tag else None

    seccodemodid_tag = soup.find('input', {'name': 'seccodemodid'})
    seccodemodid = seccodemodid_tag['value'] if seccodemodid_tag else None

    captcha_idhash = None
    for img in soup.find_all('img'):
        src = img.get('src', '')
        match = re.search(r'idhash=(\w+)', src)
        if match:
            captcha_idhash = match.group(1)
            break

    return formhash, loginhash, seccodehash, seccodemodid, captcha_idhash


def fetch_captcha_frames(captcha_idhash):
    import cv2
    url = f"https://www.itjc8.com/misc.php?mod=seccode&idhash={captcha_idhash}&update={random.randint(100000, 999999)}"
    try:
        resp = session.get(url, headers={"Referer": LOGIN_PAGE_URL}, timeout=10)
        resp.raise_for_status()
        gif = Image.open(BytesIO(resp.content))
        frames = []
        for i in range(gif.n_frames):
            gif.seek(i)
            frame = gif.convert("RGB")
            buf = BytesIO()
            frame.save(buf, format="PNG")
            b64 = base64.b64encode(buf.getvalue()).decode()
            frames.append({"frame_index": i, "base64_data": b64})
        return frames
    except Exception as e:
        print(f"获取验证码帧失败: {e}")
        return []


def get_image_sharpness(b64):
    try:
        import cv2
        img = Image.open(BytesIO(base64.b64decode(b64))).convert('L')
        arr = np.array(img)
        return cv2.Laplacian(arr, cv2.CV_64F).var()
    except ImportError:
        return 0
    except Exception:
        return 0


def recognize_captcha(frames):
    valid = []
    for f in frames:
        sharpness = get_image_sharpness(f["base64_data"])
        try:
            r = session.post(OCR_SERVICE, json={"image": f["base64_data"]}, timeout=10)
            r.raise_for_status()
            res_json = r.json()
            result = res_json.get("result", "").strip()
            confidence = res_json.get("confidence", 0)
            print(f"帧 {f['frame_index']} 识别: {result}, 置信度: {confidence}, 清晰度: {sharpness:.2f}")
            if len(result) == 4 and result.isalnum():
                valid.append({"result": result, "confidence": confidence, "sharpness": sharpness})
        except Exception as e:
            print(f"OCR失败: {e}")
    if not valid:
        return ""
    valid.sort(key=lambda x: (-x["confidence"], -x["sharpness"]))
    return valid[0]["result"]


def save_cookies(filepath):
    try:
        cookie_str = "; ".join(f"{c.name}={c.value}" for c in session.cookies)
        with open(filepath, "w") as f:
            f.write(cookie_str)
        print(f"✅ Cookie 已保存: {filepath}")
    except Exception as e:
        print(f"Cookie保存失败: {e}")


def load_cookies(filepath):
    try:
        with open(filepath, "r") as f:
            cookie_str = f.read().strip()
        cookies = cookie_str.split("; ")
        for c in cookies:
            if "=" in c:
                k, v = c.split("=", 1)
                session.cookies.set(k, v)
        print(f"✅ Cookie 已加载: {filepath}")
        return True
    except Exception as e:
        print(f"加载Cookie失败: {e}")
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

def login(username, password):
    load_send()
    for attempt in range(1, MAX_RETRY + 1):
        print(f"\n🔐 第{attempt}次尝试登录...")
        html = get_page_source_with_selenium(LOGIN_PAGE_URL)
        if not html:
            print("无法获取登录页面源码")
            continue

        formhash, loginhash, seccodehash, seccodemodid, captcha_idhash = parse_login_params(html)
        print(f"获取参数: formhash={formhash}, loginhash={loginhash}, seccodehash={seccodehash}, seccodemodid={seccodemodid}, captcha_idhash={captcha_idhash}")

        if not all([formhash, loginhash, seccodehash, seccodemodid, captcha_idhash]):
            print("动态参数不完整，重新尝试...")
            continue

        frames = fetch_captcha_frames(captcha_idhash)
        if not frames:
            print("无法获取验证码图片，重新尝试...")
            continue

        captcha = recognize_captcha(frames)
        if not captcha:
            print("验证码识别失败，重新尝试...")
            continue

        print(f"识别验证码: {captcha}")

        post_data = {
            "formhash": formhash,
            "referer": "https://www.itjc8.com/",
            "username": username,
            "password": password,
            "questionid": "0",
            "answer": "",
            "seccodehash": seccodehash,
            "seccodemodid": seccodemodid,
            "seccodeverify": captcha,
        }

        try:
            full_url = f"{LOGIN_POST_URL}&loginhash={loginhash}"
            r = session.post(full_url, data=post_data, timeout=15)
            r.raise_for_status()
            if any(s in r.text for s in ["欢迎您回来", "您已经登录"]):
                print("🎉 登录成功")
                save_cookies(COOKIE_FILE)
                return True
            else:
                print(f"登录失败，响应片段：{r.text[:300]}")
        except Exception as e:
            print(f"登录请求异常: {e}")

        print("3秒后重试...")
        time.sleep(3)

    print("❌ 登录失败，达到最大重试次数")
    return False


def sign_in():
    # 先尝试从cookie签到
    print("🔄 尝试签到...")
    html = get_page_source_with_selenium(LOGIN_PAGE_URL)  # 为了保证cookie生效，刷新一下页面（可选）

    # 先从文件加载cookie
    if not load_cookies(COOKIE_FILE):
        print("Cookie文件不存在或加载失败，需登录")
        return False

    # 使用文件中cookie尝试签到
    # 需要先获取签到时需要的 formhash
    try:
        r = session.get(LOGIN_PAGE_URL, timeout=10)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        formhash_tag = soup.find("input", {"name": "formhash"})
        formhash = formhash_tag['value'] if formhash_tag else None
        if not formhash:
            print("无法获取签到formhash，可能cookie失效")
            return False

        day_xq = random.choice(qdxq_list)

        post_data = {
            "formhash": formhash,
            "qdxq" : day_xq,
            "qdmode": "3",
            "todaysay": "",
            "fastreply": "0",
        }
        headers = {
            "Referer": "https://www.itjc8.com/",
            "Content-Type": "application/x-www-form-urlencoded",
        }
        sign_resp = session.post(SIGN_URL, data=post_data, headers=headers, timeout=10)
        sign_resp.raise_for_status()

        text = sign_resp.text
        # 简单提取 <div class="c"> 内文字
        m = re.search(r'<div class="c">\s*(.*?)\s*</div>', text, re.S)
        msg = m.group(1).strip() if m else "未知签到返回"

        # 简单emoji美化
        if "成功" in msg or "已签到" in msg:
            print(f"✅ 签到成功: {msg} 🎉")
            return True
        elif "心情不正确" in msg:
            print(f"⚠️ 签到失败: {msg}")
            send("ITJC8签到", f"❌ 签到失败: {msg}")
            return False
        elif "未登录" in msg or "登录" in msg:
            print("❌ Cookie 失效或未登录，需要重新登录")
            return False
        else:
            print(f"ℹ️ 签到响应: {msg}")
            return True

    except Exception as e:
        print(f"签到异常: {e}")
        return False


if __name__ == "__main__":
    USER = USERNAME
    PASS = PASSWORD

    if not sign_in():
        print("需要登录后签到")
        if login(USER, PASS):
            print("登录成功，开始签到...")
            if sign_in():
                print("🎉 签到完成")
            else:
                print("❌ 签到失败")
        else:
            print("❌ 登录失败，无法签到")
    else:
        print("🎉 使用Cookie签到成功")
