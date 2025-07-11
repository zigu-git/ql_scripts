import socket
import requests
import time
from prettytable import PrettyTable
from urllib.parse import urlparse

#需要安装requests prettytable

# 支持备注的服务地址格式：备注@ip:port 或 备注@https://域名
targets = [
    "备注1@ip:port",
    "备注2@https://demo.com",
]

# 海外网站可达性测试
overseas_sites = [
    ("Google", "https://www.google.com"),
    ("GitHub", "https://github.com"),
    ("YouTube", "https://www.youtube.com"),
]

def check_tcp(ip, port, timeout=3):
    try:
        start = time.time()
        with socket.create_connection((ip, port), timeout=timeout):
            return True, round((time.time() - start) * 1000)
    except Exception:
        return False, None

def check_http(url, timeout=5):
    try:
        start = time.time()
        r = requests.get(url, timeout=timeout)
        return r.status_code < 500, round((time.time() - start) * 1000)
    except Exception:
        return False, None

def parse_target(target):
    if "@" not in target:
        return "未知", target, "UNKNOWN", None
    remark, address = target.split("@", 1)
    if "://" in address:
        return remark, address, "HTTP", address
    elif ":" in address:
        ip, port = address.split(":")
        return remark, address, "TCP", (ip, int(port))
    else:
        return remark, address, "UNKNOWN", address

def color_text(text, color_code):
    return f"\033[{color_code}m{text}\033[0m"

def format_status(result, delay_ms):
    if result is True:
        return color_text(f"🟢 存活 ({delay_ms}ms)", "32")
    elif result is False:
        return color_text("🔴 无响应", "31")
    else:
        return color_text("⚠️ 未知", "33")

def main():
    print("\n🔍 正在检测服务与海外网站连通性...\n")

    table = PrettyTable()
    table.field_names = ["备注", "目标地址", "协议", "状态/延迟"]

    for target in targets:
        remark, addr, proto, data = parse_target(target)

        if proto == "TCP":
            result, delay = check_tcp(*data)
        elif proto == "HTTP":
            result, delay = check_http(data)
        else:
            result, delay = None, None

        table.add_row([remark, addr, proto, format_status(result, delay)])

    print("🧾 服务状态检测结果：\n")
    print(table)

    # 检查海外网站连通性
    overseas_table = PrettyTable()
    overseas_table.field_names = ["🌐 站点", "地址", "连通性/延迟"]

    for name, url in overseas_sites:
        result, delay = check_http(url)
        overseas_table.add_row([name, url, format_status(result, delay)])

    print("\n🌍 海外网站可达性检测结果：\n")
    print(overseas_table)
    print("\n✅ 检测完毕！\n")

if __name__ == "__main__":
    main()
