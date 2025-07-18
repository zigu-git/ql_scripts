import requests
import json
import hashlib
from bs4 import BeautifulSoup

# 配置
USERNAME = "账号"
PASSWORD = "密码"
BASE_URL = "https://hifiti.com"

def md5_encrypt(text):
    m = hashlib.md5()
    m.update(text.encode("utf-8"))
    return m.hexdigest()

def login(username, password):
    login_url = f"{BASE_URL}/user-login.htm"
    session = requests.Session()

    # 访问登录页，获取初始Cookie（bbs_sid等）
    resp = session.get(login_url)
    print("登录页Cookie:", session.cookies.get_dict())

    # 准备登录请求头
    headers = {
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Origin": BASE_URL,
        "Referer": login_url,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.6723.70 Safari/537.36",
        "X-Requested-With": "XMLHttpRequest",
        "Accept": "text/plain, */*; q=0.01",
    }

    # 密码 MD5 加密
    pwd_md5 = md5_encrypt(password)

    # 表单数据
    data = {
        "email": username,
        "password": pwd_md5
    }

    # 发送登录 POST 请求
    response = session.post(login_url, headers=headers, data=data)

    print("🤖尝试登录....")

    try:
        result = response.json()
        if result.get("code") == "0":
            print("✅ 登录成功")
            return session
        else:
            print(f"❌ 登录失败：{result.get('message')}")
            return None
    except json.JSONDecodeError:
        print("⚠️ 返回内容不是有效 JSON，可能登录失败或者返回了登录页面HTML")
        return None

def sign(session):
    url = f"{BASE_URL}/sg_sign.htm"
    headers = {
        "X-Requested-With": "XMLHttpRequest",
        "Origin": BASE_URL,
        "Referer": f"{BASE_URL}/",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.6723.70 Safari/537.36",
        "Accept": "text/plain, */*; q=0.01",
    }

    response = session.post(url, headers=headers, data={})

    try:
        result = response.json()
        if result.get("code") == "0":
            print("✅ 签到成功:", result.get("message"))
        else:
            print("❌ 签到失败:", result.get("message"))
    except Exception as e:
        print("⚠️ 签到响应解析异常:", e)
        print(response.text)

def get_gold_count(session):
    url = "https://hifiti.com/my.htm"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.6723.70 Safari/537.36",
        "Referer": "https://hifiti.com/sg_sign.htm",
    }

    response = session.get(url, headers=headers)
    if response.status_code != 200:
        print(f"请求失败，状态码: {response.status_code}")
        return None

    soup = BeautifulSoup(response.text, "html.parser")

    span = soup.find("span", string="金币：")
    if span:
        em = span.find_next_sibling("em")
        if em:
            return em.text.strip()

    print("未能找到金币数量")
    return None

if __name__ == "__main__":
    session = login(USERNAME, PASSWORD)
    if session:
        sign(session)
        gold = get_gold_count(session)
        if gold is not None:
            print(f"当前金币数量：{gold}")
        else:
            print("获取金币失败")
