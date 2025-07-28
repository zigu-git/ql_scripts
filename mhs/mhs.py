import os
import requests
import base64
import json
from Cryptodome.Cipher import AES
from Cryptodome.Hash import SHA256
#需要安装pycryptodomex
#第一次使用前先抓https://bxo30.xyz/api/user/qd请求中的encryptedData和iv参数将其填到68和69行对应位置

# 配置
UserName = os.getenv("mhs_username")
Password = os.getenv("mhs_password")
TOKEN_FILE = "./mhs.txt"

def save_token(token):
    with open(TOKEN_FILE, 'w', encoding='utf-8') as f:
        f.write(token)

def load_token():
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, 'r', encoding='utf-8') as f:
            token = f.read().strip()
            if token:
                return token
    return None

def login():
    headers = {
        "Host": "bxo30.xyz",
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/json;charset=UTF-8",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.6723.70 Safari/537.36",
        "Origin": "https://bxo30.xyz",
        "Referer": "https://bxo30.xyz/",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
    }

    data = {
        "userName": UserName,
        "password": Password
    }

    url = "https://bxo30.xyz/api/auth/login"
    response = requests.post(url, json=data, headers=headers)
    if response.status_code == 200:
        print(f'🤪登录结果：{response.json().get("msg")}')
    else:
        print(f'☹️登录失败，状态码：{response.status_code}')
        return None

    plaintext = decrypt_aes_cbc_base64(response.json().get("data"), response.json().get("iv"))
    token = plaintext.get('token')
    if token:
        save_token(token)
    print("🤖新token:", token)
    return token

def qd(token):
    url = "https://bxo30.xyz/api/user/qd"
    headers = {
        "Content-Type": "application/json;charset=UTF-8",
        "Token": token,
        "Accept": "application/json, text/plain, */*",
        "Origin": "https://bxo30.xyz",
        "Referer": "https://bxo30.xyz/"
    }
    json_data = {
        "encryptedData": os.getenv("mhs_encryptedData"),
        "iv": os.getenv("mhs_iv")
    }
    response = requests.post(url, headers=headers, json=json_data)
    if response.status_code == 200:
        data = response.json()
        #print(data)
        if data.get("code") == 1:
            print("🥳签到成功:", data.get("msg"))
            return True
        else:
            print("😖签到失败:",  data.get("msg"))
            return True
    else:
        print("😖请求失败，状态码:", response.status_code)
        return False

def decrypt_aes_cbc_base64(cipher_b64: str, iv_b64: str, mH: str = "mhs-1234-s981re-k071y2"):
    try:
        key = SHA256.new(mH.encode()).digest()
        iv = base64.b64decode(iv_b64)
        ciphertext = base64.b64decode(cipher_b64)

        cipher = AES.new(key, AES.MODE_CBC, iv)
        padded_plaintext = cipher.decrypt(ciphertext)

        pad_len = padded_plaintext[-1]
        plaintext = padded_plaintext[:-pad_len].decode('utf-8')

        try:
            return json.loads(plaintext)
        except json.JSONDecodeError:
            return plaintext
    except Exception as e:
        print(f"😖解密失败: {e}")
        return None

def get_user_info(token):
    url = "https://bxo30.xyz/api/user/info"
    headers = {
        "Content-Type": "application/json;charset=UTF-8",
        "Token": token,
        "Accept": "application/json, text/plain, */*",
        "Origin": "https://bxo30.xyz",
        "Referer": "https://bxo30.xyz/"
    }

    response = requests.post(url, headers=headers)
    if response.status_code == 200:
        res_json = response.json()
        if res_json.get("code") == 1:
            data = decrypt_aes_cbc_base64(res_json.get("data"), res_json.get("iv"))
            return data
        else:
            print("😖请求失败，消息：", res_json.get("msg"))
    else:
        print("😖HTTP请求失败，状态码：", response.status_code)
    return None

def lottery(token, data):
    jf = data.get("jf") if data else 0
    if jf < 10:
        print("💀积分不足，无法抽奖")
        return
    url = "https://bxo30.xyz/api/user/lottery"
    headers = {
        "Content-Type": "application/json;charset=UTF-8",
        "Token": token
    }
    resp = requests.post(url, headers=headers, json={})
    if resp.status_code == 200:
        result = resp.json()
        code = result.get("code")
        msg = result.get("msg")
        name = result.get("data", {}).get("name")
        if code == 1:
            if name:
                print(f"😋抽奖{msg}，奖品信息：{name}")
            else:
                print("🥱抽奖成功，但结果为空")
        else:
            print(msg)
    else:
        print("😖抽奖发生错误, 错误码：", resp.status_code)
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
    token = load_token()
    load_send()
    if not token:
        print("🤖没有找到有效token，准备登录获取新token")
        token = login()

    if token:
        success = qd(token)
        if not success:
            print("😖签到失败，尝试重新登录获取token")
            send("米哈社签到", "😖签到失败，尝试重新登录获取token")
            token = login()
            if token:
                qd(token)

        data = get_user_info(token)
        print(f"🤑当前的积分:{data.get('jf')}")
        lottery(token, data)
