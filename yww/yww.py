import os
import requests
import pickle
import re
from bs4 import BeautifulSoup

# === 配置区域 ===
USERNAME = "账号"
PASSWORD = "密码"
COOKIE_FILE = "./yww_cookie.pkl"
BASE_URL = "https://www.yunweiku.com"
LOGIN_PAGE = f"{BASE_URL}/member.php?mod=logging&action=login"


def load_cookies(file_path):
    if not os.path.exists(file_path):
        return None
    with open(file_path, "rb") as f:
        return pickle.load(f)


def save_cookies(session, file_path):
    with open(file_path, "wb") as f:
        pickle.dump(session.cookies, f)


def create_session():
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/130.0.6723.70 Safari/537.36"
    })
    return session


def login():
    """执行登录并返回已登录 session"""
    session = create_session()

    # 获取 loginhash 和 formhash
    def get_loginhash():
        resp = session.get(LOGIN_PAGE)
        match = re.search(
            r'member\.php\?mod=logging&amp;action=login&amp;loginsubmit=yes&amp;loginhash=(\w+)', resp.text)
        if match:
            return match.group(1)
        raise Exception("未能提取 loginhash")

    def get_formhash():
        resp = session.get(LOGIN_PAGE)
        soup = BeautifulSoup(resp.text, "html.parser")
        formhash_input = soup.find("input", {"name": "formhash"})
        if formhash_input:
            return formhash_input.get("value")
        raise Exception("未能提取 formhash")

    loginhash = get_loginhash()
    formhash = get_formhash()

    login_url = f"{BASE_URL}/member.php?mod=logging&action=login&loginsubmit=yes&loginhash={loginhash}&inajax=1"
    payload = {
        "formhash": formhash,
        "referer": BASE_URL + "/",
        "username": USERNAME,
        "password": PASSWORD,
        "questionid": "0",
        "answer": "",
        "cookietime": "2592000"
    }

    headers = {
        "Origin": BASE_URL,
        "Referer": LOGIN_PAGE,
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }

    response = session.post(login_url, data=payload, headers=headers)

    if "欢迎您回来" in response.text:
        save_cookies(session, COOKIE_FILE)
        print("✅ 登录成功，cookie 已保存。")
        return session
    else:
        raise Exception("❌ 登录失败，请检查用户名密码或页面结构")


def get_formhash(session):
    url = f"{BASE_URL}/plugin.php?id=k_misign:sign"
    resp = session.get(url)
    soup = BeautifulSoup(resp.text, "html.parser")
    input_tag = soup.find("input", {"name": "formhash"})
    return input_tag.get("value") if input_tag else None


def build_session():
    """尝试加载 Cookie，如失败自动登录"""
    session = create_session()

    cookies = load_cookies(COOKIE_FILE)
    if cookies:
        session.cookies.update(cookies)
        formhash = get_formhash(session)
        if formhash:
            return session, formhash
        print("⚠️ Cookie 已失效，尝试重新登录...")

    # 重新登录
    session = login()
    formhash = get_formhash(session)
    if not formhash:
        raise Exception("❌ 登录后依然无法获取 formhash")
    return session, formhash


def check_in():
    session, formhash = build_session()

    session.headers.update({
        "X-Requested-With": "XMLHttpRequest",
        "Referer": f"{BASE_URL}/plugin.php?id=k_misign:sign"
    })

    # 发起签到请求
    checkin_url = f"{BASE_URL}/plugin.php?id=k_misign:sign&operation=qiandao&formhash={formhash}&format=empty&inajax=1&ajaxtarget=JD_sign"
    resp = session.get(checkin_url)

    if resp.status_code == 200:
        print("✅ 签到请求已发送")
    else:
        raise Exception("❌ 签到请求失败")

    # 获取签到结果页
    result_url = f"{BASE_URL}/plugin.php?id=k_misign:sign"
    resp = session.get(result_url)
    soup = BeautifulSoup(resp.text, "html.parser")

    def get_val_by_id(tag_id):
        tag = soup.find("input", {"id": tag_id})
        return tag["value"] if tag and tag.has_attr("value") else "?"

    data = {
        "连续签到": get_val_by_id("lxdays"),
        "签到等级": get_val_by_id("lxlevel"),
        "积分奖励": get_val_by_id("lxreward"),
        "总签到天数": get_val_by_id("lxtdays"),
        "今日已签到人数": soup.select_one(".weather_p .con").text.strip().replace("\n", "")
    }

    print("\n🎉 签到成功！今日统计：")
    for k, v in data.items():
        print(f"  {k:<10}: {v}")


if __name__ == "__main__":
    check_in()
