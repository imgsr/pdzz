# 🎮 派对制造 · 全能工具箱

> 一款真正「能用、好用、持续在更新」的游戏辅助工具  
> 支持 Termux / Linux / macOS / 浏览器（Web 版）  
> **已有真实用户持续使用中，已迭代 30+ 版本**

<p align="center">
  <img src="https://img.shields.io/badge/version-5.2.1-brightgreen" />
  <img src="https://img.shields.io/badge/platform-Termux%20%7C%20Linux%20%7C%20Web-blue" />
  <img src="https://img.shields.io/badge/language-Shell%20%7C%20Python%20%7C%20JavaScript-yellow" />
  <img src="https://img.shields.io/badge/status-active-success" />
</p>

---

## 📌 这是什么？

**派对制造工具箱** 是一个面向《派对制造》游戏玩家的多功能辅助工具，  
提供从 **地图查询**、**玩家档案**、**金矿打工** 到 **关系图谱生成** 等一系列实用功能。

无论你是在 **Termux 手机端**、**Linux 终端**，还是 **浏览器网页版**，都能流畅使用。

> ✅ 已有真实用户 Star 并持续使用  
> ✅ 项目保持高频迭代（30+ 版本，持续更新中）  
> ✅ 代码开源，功能自用级稳定

---

## 🚀 一键安装（Shell 版）

```bash
curl -o party_tool.sh https://ghproxy.net/https://raw.githubusercontent.com/imgsr/pdzz/main/party_tool.sh && chmod +x party_tool.sh && bash party_tool.sh
```

脚本会自动检测并安装 Python 依赖，开箱即用。

---

🔧 功能全景

功能 说明
🗺️ 地图查询 通过 36 进制地图码查询地图详情、作者、评论（支持翻页）
👤 玩家信息 查询玩家档案、段位、经验、地图作品
💕 关系图谱 自动生成玩家亲密关系的力导向图（HTML 交互版）
⛏️ 金矿打工 支持 4 个账号同时为指定玩家打工
💬 地图评论 支持文本 / stamp 两种评论方式，可顺便点赞
📢 广播地图 自动领取免费喇叭，将地图推送到游戏首页
🏆 排行榜查询 创造榜 / 操作榜 / 联赛榜（周榜 + 总榜）
📡 房间列表 查看当前在线房间及玩家信息
🎲 随机昵称 批量拉取游戏随机昵称，保存到本地

---

🌐 两种使用方式

1️⃣ Shell/Python版（Termux /Windows/ Linux）

适合手机端或终端爱好者，功能最全，响应快。

```bash
bash party_tool.sh
```
```bash
python party_tool.py
```

2️⃣ Web 网页版（浏览器）

适合桌面端，可视化操作，支持关系图谱下载。

```bash
python3 app.py
# 然后打开浏览器访问 http://127.0.0.1:5000
```

Web 版支持：地图查询 / 玩家档案 / 金矿打工 / 评论 / 广播 / 关系图谱生成

---

🧠 项目亮点

· 一个人维护，持续迭代：从 Shell 到 Python 再到 Web，全部独立完成
· 真实用户验证：已有陌生人 Star 并实际使用
· 跨平台兼容：手机（Termux）+ 电脑（Linux/macOS）+ 浏览器
· 功能驱动开发：每个功能都来自实际需求，不是玩具代码
· 关系图谱可视化：基于 D3.js 生成交互式力导向图，可下载分享

---

📁 项目结构

```
party_tool/
├── party_tool.sh          # Shell 主程序（Termux 推荐）
├── party_tool.py          # Python 版（跨平台）
├── app.py                 # Web 版服务端
├── static/
│   └── index.html         # Web 前端界面
├── data/
│   ├── config.json        # 配置文件
│   └── graphs/            # 生成的关系图谱 HTML
└── README.md              # 就是这个文件
```

---

⚙️ 配置说明

脚本首次运行会自动生成配置文件，路径：

· Termux：/storage/emulated/0/party_tool/config.txt
· Linux：~/.party_tool/config.txt

如需自定义 JWT / Device ID / SSN，可在功能菜单 B 中设置。

🤝 交流与反馈

· 📦 项目地址：https://github.com/imgsr/pdzz
· 💬 QQ 群：1031952094
· 🐛 问题反馈：欢迎提 Issue 或加群讨论

---

⚠️ 免责声明

本工具仅供学习与研究使用，请勿用于商业目的。
使用本工具产生的任何后果由使用者自行承担。

---

⭐ 如果这个工具帮到了你

请点一个 Star —— 这是对独立开发者最大的鼓励。
你的一个 Star，比任何赞美都更有力量。

<p align="center">
  <b>⭐ Star 这个项目，让更多人看到 ⭐</b>
</p>
```

---