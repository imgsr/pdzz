# 🎉 派对制造工具箱

<div align="center">

![Version](https://img.shields.io/badge/version-4.3-brightgreen)
![Shell](https://img.shields.io/badge/shell-bash-blue)
![License](https://img.shields.io/badge/license-MIT-yellow)

**一款功能强大的派对制造游戏辅助工具箱，支持地图查询、排行榜查看、玩家信息获取等功能**

</div>

---

## 📖 项目简介

派对制造工具箱是一款基于 Shell 脚本开发的游戏辅助工具，通过调用游戏 API 实现多种实用功能。无需复杂配置，开箱即用！

## ✨ 主要功能

| 功能 | 说明 |
|------|------|
| 🔍 **地图查询** | 支持地图代码查询，查看地图详情、评论、排行榜 |
| 🏆 **排行榜查看** | 创造榜、操作榜、联赛榜（周榜/总榜） |
| 👤 **玩家信息查询** | 通过地图代码获取作者详细信息、关系图谱 |
| 🎮 **房间列表** | 查看当前对局房间及玩家信息 |
| 📢 **游戏公告** | 实时获取游戏公告信息 |
| 📱 **版本信息** | 查询各平台游戏版本号 |
| 🌐 **IP查询** | 查看本机公网/内网IP |

## 🚀 快速开始

### 环境要求

- Android (Termux) / Linux / macOS
- Bash 环境
- curl、Python3

### 一键运行

```bash
curl -o party_tool.sh https://raw.githubusercontent.com/imgsr/pdzz/main/party_tool.sh && chmod +x party_tool.sh && bash party_tool.sh
