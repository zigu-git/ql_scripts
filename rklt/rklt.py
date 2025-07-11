import os
import requests
import re
import pickle
from bs4 import BeautifulSoup
#需要安装requests beautifulsoup4 pickle


# 配置
UserName = "账号"
Password = "密码"
COOKIE_FILE = "./rklt_cookie.pkl"

def save_cookies(session, filename=COOKIE_FILE):
    with open(filename, 'wb') as f:
        pickle.dump(session.cookies, f)

def load_cookies(session, filename=COOKIE_FILE):
    if os.path.exists(filename):
        with open(filename, 'rb') as f:
            session.cookies.update(pickle.load(f))
        return True
    return False

def get_formhash(session):
    url = "https://www.ruike1.com/"
    try:
        resp = session.get(url)
        resp.encoding = "gbk"
        match = re.search(r'name="formhash" value="([a-f0-9]{8})"', resp.text)
        if match:
            return match.group(1)
        else:
            print("❌ 无法提取 formhash")
            return None
    except Exception as e:
        print(f"🔥 获取 formhash 出错: {e}")
        return None

def login():
    session = requests.Session()
    formhash = get_formhash(session)
    if not formhash:
        return None

    url = "https://www.ruike1.com/member.php?mod=logging&action=login&loginsubmit=yes&infloat=yes&lssubmit=yes&inajax=1"
    headers = {
        "Host": "www.ruike1.com",
        "Content-Type": "application/x-www-form-urlencoded",
        "Origin": "https://www.ruike1.com",
        "Referer": "https://www.ruike1.com/",
        "User-Agent": "Mozilla/5.0",
    }
    data = {
        "fastloginfield": "username",
        "username": UserName,
        "password": Password,
        "cookietime": "2592000",
        "formhash": formhash,
        "quickforward": "yes",
        "handlekey": "ls"
    }
    response = session.post(url, headers=headers, data=data)
    response.encoding = "gbk"

    if response.status_code == 200:
        if "window.location.href" in response.text:
            print("✅ 登录成功，已保存 Cookie")
            save_cookies(session)
            return session
        else:
            print("❌ 登录失败，可能用户名或密码错误")
            return None
    else:
        print(f"❌ 登录请求失败，状态码：{response.status_code}")
        return None

def sign_in(session):
    formhash = get_formhash(session)
    if not formhash:
        return False

    url = f"https://www.ruike1.com/k_misign-sign.html?operation=qiandao&format=global_usernav_extra&formhash={formhash}&inajax=1&ajaxtarget=k_misign_topb"
    headers = {
        "Host": "www.ruike1.com",
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://www.ruike1.com/",
        "X-Requested-With": "XMLHttpRequest",
        "Accept": "*/*",
        "Accept-Language": "zh-CN,zh;q=0.9",
    }

    try:
        response = session.get(url, headers=headers)
        response.encoding = "gbk"
        if response.status_code == 200:
            if "今日已签" in response.text:
                print("✅ 今日已签到，无需重复。")
                return True
            elif "签到成功" in response.text or "已成功签到" in response.text:
                print("🎉 签到成功！")
                return True
            else:
                print("⚠️ 无法确认签到状态，响应如下：")
                print(response.text)
                return False
        else:
            print(f"❌ 签到失败，HTTP 状态码: {response.status_code}")
            return False
    except Exception as e:
        print(f"🔥 签到请求异常：{e}")
        return False

def get_credit(session: requests.Session):
    url = "https://www.ruike1.com/"
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://www.ruike1.com/",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9",
    }

    try:
        response = session.get(url, headers=headers)
        response.encoding = "gbk"

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            credit_tag = soup.find("a", id="extcreditmenu")
            if credit_tag:
                credit_text = credit_tag.text.strip()
                match = re.search(r"积分[:：]\s*(\d+)", credit_text)
                if match:
                    credit = int(match.group(1))
                    print(f"💰 当前积分：{credit}")
                    return credit
                else:
                    print(f"⚠️ 未能从文本中提取积分数值：{credit_text}")
            else:
                print("❌ 页面中未找到积分链接 (id='extcreditmenu')，可能未登录或页面结构变化")
        else:
            print(f"❌ 请求失败，HTTP状态码: {response.status_code}")
    except Exception as e:
        print(f"🔥 获取积分出错：{e}")

if __name__ == "__main__":
    session = requests.Session()

    print("📦 尝试使用已保存 Cookie 进行签到...")
    if load_cookies(session):
        if sign_in(session):
            get_credit(session)
            exit(0)
        else:
            print("🔁 Cookie 失效或签到失败，尝试重新登录...")

    print("🔐 正在尝试登录...")
    session = login()
    if session:
        sign_in(session)
        get_credit(session)
    else:
        print("⛔ 无法完成登录，签到中止。")
