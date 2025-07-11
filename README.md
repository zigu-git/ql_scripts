<p align="center">
  <a href="https://github.com/clearligh/ql_scripts/stargazers">
    <img src="https://img.shields.io/github/stars/clearligh/ql_scripts?color=yellow&style=flat-square" alt="Stars" />
  </a>
  <a href="https://github.com/clearligh/ql_scripts/network/members">
    <img src="https://img.shields.io/github/forks/clearligh/ql_scripts?color=blue&style=flat-square" alt="Forks" />
  </a>
  <a href="https://github.com/clearligh/ql_scripts/issues">
    <img src="https://img.shields.io/github/issues/clearligh/ql_scripts?color=critical&style=flat-square" alt="Issues" />
  </a>
  <a href="https://github.com/clearligh/ql_scripts/blob/main/LICENSE">
    <img src="https://img.shields.io/github/license/clearligh/ql_scripts?style=flat-square" alt="License" />
  </a>
</p>


# 🐉 ql_scripts - 自写自用脚本集

<div style="text-align: center;">
  <img src="./static/ql.png" alt="QingLong" width="150" />
</div>


> 🧰 自用 Python 脚本合集，配合 [青龙面板 (QingLong)](https://github.com/whyour/qinglong) 使用。

---

## 📦 可用性
| 名称      | 描述                                 | 可用性           |
|:---------:|:----------------------------------:|:--------------:|
| sjs  | 司机社签到 | ✅️    |
| mhs    | 米哈社签到+抽奖 | ✅️    |
| vip9c   | vip9c资源站签到 | ✅️   |
| it_jcb   | IT教程吧签到 | ✅️   |
| rklt   | 瑞客论坛签到 | ✅️   |
| starryCoding   | starryCoding签到 | ✅️   |
| mht   | 棉花糖VIP站签到 | ✅️   |
| fwjc   | 服务检测 | ✅️   |


---
## 使用教程  
青龙——>订阅管理——>填入随意名称-填入下面链接-定时 2 21 7 * * ?

```
https://github.com/clearligh/ql_scripts.git
```
脚本中的OCR服务使用的是[雪佬的ddddocr](https://github.com/xzxxn777/ddddocr)  
docker部署
```
docker run -d -p 7777:7777 --restart=always --name ddddocr xzxxn777/ddddocr:latest
```

部署完成后替换脚本中的**OCR_SERVICE**即可
例如你部署在本地127.0.0.1的7777端口，那么你需要替换为
`http://127.0.0.1:7777/classification`


---
## 🐶[狗东上车](https://jd.clearligh.top/)
上车网址：[jd.clearligh.top](https://jd.clearligh.top/)  
上车Vx机器人：Czb112378121  
上车TG机器人：[@zigu_jd](https://t.me/zigu_jd)