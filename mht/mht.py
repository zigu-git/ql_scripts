import httpx
import json
import os
#需要安装httpx[http2]依赖

#在棉花糖vip站点https://vip.bdziyi.com/登录后按F12在Application——>Cookies中找到vip.bdziyi.com的PHPSESSID和wordpress_logged_in_替换为对应的key
#将其复制到下面的cookies变量中

# 🍪 设置 Cookie（注意：请确保此 Cookie 仍然有效）
cookies = {
    os.getenv("mht_key"): os.getenv("mht_value"),# wordpress_logged_in_替换为对应的key、替换为对应的值
    "PHPSESSID": os.getenv("mht_phpsessid_value")# 替换为对应的值
}
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
# 🔧 请求头
headers = {
    "Host": "vip.bdziyi.com",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "X-Requested-With": "XMLHttpRequest",
    "Origin": "https://vip.bdziyi.com",
    "Referer": "https://vip.bdziyi.com/",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "zh-CN,zh;q=0.9",
}

# 📦 表单数据
data = {
    "action": "user_checkin"
}

# 🔗 请求发送
url = "https://vip.bdziyi.com/wp-admin/admin-ajax.php"

# 📨 发起 POST 请求
with httpx.Client(http2=True, cookies=cookies, headers=headers) as client:
    response = client.post(url, data=data)

# 📊 处理响应
if response.status_code == 200:
    load_send()
    try:
        result = response.json()
        if not result.get("error"):
            print("✅ 签到成功！🎉")
            print(f"📅 连续签到：{result['continuous_day']} 天")
            print(f"⭐ 获得积分：+{result['data']['points']}")
            print(f"📚 获得经验：+{result['data']['integral']}")
            print(f"🕒 时间：{result['data']['time']}")
        else:
            print("❌ 签到失败：", result.get("msg", "未知错误"))
            send("棉花糖签到", "❌ 签到失败")
    except json.JSONDecodeError:
        print("❌ 无法解析返回结果：", response.text)
else:
    print(f"🚫 请求失败，状态码：{response.status_code}")
