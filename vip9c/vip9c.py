import requests
import os

# 配置
USERNAME = "账号"
PASSWORD = "密码"

LOGIN_URL = "https://vipc9.com/wp-admin/admin-ajax.php"
SIGN_URL = LOGIN_URL
COOKIE_FILE = "./9vip.txt"
HEADERS_BASE = {
    "Origin": "https://vipc9.com",
    "Referer": "https://vipc9.com/",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.6723.70 Safari/537.36",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "X-Requested-With": "XMLHttpRequest",
    "Accept": "*/*",
    "Accept-Language": "zh-CN,zh;q=0.9"
}


def save_cookie(cookie_str):
    with open(COOKIE_FILE, 'w') as f:
        f.write(cookie_str)

def load_cookie():
    if os.path.exists(COOKIE_FILE):
        with open(COOKIE_FILE, 'r') as f:
            return f.read().strip()
    return ""

def cookie_str_to_dict(cookie_str):
    cookies = {}
    for item in cookie_str.split(';'):
        if '=' in item:
            k, v = item.strip().split('=', 1)
            cookies[k] = v
    return cookies

def login():
    print("🔐 尝试登录中...")
    data = {
        "action": "user_login",
        "username": USERNAME,
        "password": PASSWORD
    }

    session = requests.Session()
    resp = session.post(LOGIN_URL, headers=HEADERS_BASE, data=data)

    try:
        result = resp.json()
    except:
        print("❌ 登录响应格式错误")
        return None

    if result.get("status") == "1":
        print("✅ 登录成功，保存 Cookie")
        cookie_str = "; ".join([f"{c.name}={c.value}" for c in session.cookies])
        save_cookie(cookie_str)
        return session.cookies
    else:
        print(f"❌ 登录失败：{result.get('msg')}")
        return None

def sign_in(cookies_dict):
    print("📩 尝试签到中...")
    data = {"action": "user_qiandao"}
    resp = requests.post(SIGN_URL, headers=HEADERS_BASE, cookies=cookies_dict, data=data)

    try:
        result = resp.json()
    except:
        print("❌ 签到响应格式错误")
        return False

    if result.get("status") == "1":
        print(f"🎉 签到成功：{result.get('msg')}")
        return True
    elif "请登录" in result.get("msg", ""):
        print("⚠️ 当前 Cookie 已失效，需重新登录")
        return False
    else:
        print(f"⚠️ 签到失败：{result.get('msg')}")
        return True  # 不是因为未登录

def main():
    cookie_str = load_cookie()
    cookies_dict = cookie_str_to_dict(cookie_str)

    if not sign_in(cookies_dict):
        new_cookies = login()
        if new_cookies:
            cookies_dict = requests.utils.dict_from_cookiejar(new_cookies)
            sign_in(cookies_dict)
        else:
            print("🚫 无法完成登录，程序结束")

if __name__ == "__main__":
    main()
