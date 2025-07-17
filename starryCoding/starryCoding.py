import requests
import time
import os
# 在https://www.starrycoding.com/网站登陆后按“F12”在Application——>LocalStorage中找到starryCoding.com的Token
# 将其复制到下面的TOKEN变量中

# ⭐️ 配置
BASE_URL = "https://api.starrycoding.com"
TOKEN = os.getenv("starryCoding_token") # <- 替换为你的实际 Token
HEADERS = {
    "Content-Type": "application/json",
    "Token": TOKEN,
    "Origin": "https://www.starrycoding.com",
    "Referer": "https://www.starrycoding.com/user/panel",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36"
}


def sign_in():
    print("📡 正在尝试签到...")

    sign_url = f"{BASE_URL}/user/task/sign"
    response = requests.post(sign_url, headers=HEADERS)

    if response.status_code == 201:
        result = response.json()

        if "data" in result and "coin" in result["data"]:
            coin = result["data"]["coin"]
            print(f"✅ 签到成功，获得 {coin} 枚星币 🎉")
        else:
            print(f"⚠️ 无法获取coin，完整响应为: {result}")
    elif response.status_code == 400:
        print("⚠️ 已签到或请求异常：", response.json().get("msg", "未知错误"))
    else:
        print("❌ 签到失败，状态码：", response.status_code)
        send("星码签到", "❌ 签到失败")
        print(response.text)
    time.sleep(1)


def get_user_info():
    print("\n📥 正在获取用户信息...")
    user_url = f"{BASE_URL}/user/token"
    response = requests.get(user_url, headers=HEADERS)

    if response.status_code == 200:
        data = response.json()["data"]
        print(f"""
👤 用户名：{data['username']}（昵称：{data.get('nickname', '-') or '-' }）
🪙 当前星币：{data['coin']}
🏅 排名：{data['rank']}（占比：{data['rank_ratio']:.2%}）
📧 邮箱：{data.get('email', '-') or '-'}
📱 手机号：{data.get('phone', '-') or '-'}
🕰️ 创建时间：{data['createdAt']}
        """)
    else:
        print("❌ 获取用户信息失败！")
        print(response.text)

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
    print("🌟 StarryCoding 签到脚本开始 🌟\n")
    load_send()
    sign_in()
    get_user_info()
    print("✨ 脚本执行完成。")
