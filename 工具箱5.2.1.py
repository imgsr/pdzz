#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
派对制造工具箱 Python 版
版本：5.2.1 (移植自 Shell 版)
功能：玩家信息查询、地图评论、金矿打工、批量昵称等
"""

import os
import sys
import json
import time
import random
import secrets
from pathlib import Path
from urllib.parse import urlencode

try:
    import requests
except ImportError:
    print("请先安装 requests 库: pip install requests")
    sys.exit(1)

# ========== 颜色定义 ==========
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
BLUE = '\033[0;34m'
RED = '\033[0;31m'
CYAN = '\033[0;36m'
NC = '\033[0m'

# ========== 配置路径 ==========
if os.path.exists("/storage/emulated/0") and os.access("/storage/emulated/0", os.W_OK):
    CONFIG_DIR = "/storage/emulated/0/party_tool"
elif os.environ.get("HOME") and os.access(os.environ["HOME"], os.W_OK):
    CONFIG_DIR = os.path.join(os.environ["HOME"], ".party_tool")
else:
    CONFIG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".party_tool")

CONFIG_FILE = os.path.join(CONFIG_DIR, "config.txt")

# ========== 默认配置 ==========
DEFAULT_JWT = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJkZXZJZCI6IjMzOWY3YWJhZTg2OGI3ZjBhODMzODc3YjBkNWQ0NjQ1XG5kYTNkYzlhOTk5Mjg5OGY5MDk2YWI5MjAyOTVkM2ZhZSIsImZsYWciOiJiZGY2IiwiZnJvbSI6InRhcHRhcCIsImx0IjoiZ3Vlc3QiLCJzc24iOiI1Mjk5IiwidXNlcmlkIjoiNjlmNTk5MDNlOGQ1YjU1YmI0ZWViYjAyIiwidiI6IjAifQ.RHQ1EK0pEwiXBTILUyLNgHCetsfO57fUmJtcMGPqG-A"
DEFAULT_DEVICE_ID = "339f7abae868b7f0a833877b0d5d46454a3dc9a9992898f9096ab920295d3fae"
DEFAULT_SSN = "3c05"
DEFAULT_VER = "2.1.93"
DEFAULT_COOKIE = "SERVERID=769e7e1294f37fd70e4a8fd5d4a4a403|1774672107|1774600237"
MAP_COUNT = 100

# 额外打工账号（硬编码）
EXTRA_ACCOUNTS = [
    {
        "jwt": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJkZXZJZCI6ImNiM2FmYjQ0ZjYzYzI1OWQ0OTQ0NWJmNTM0MzA1YjRkIiwiZmxhZyI6ImQ1YjQiLCJmcm9tIjoidGFwdGFwIiwibHQiOiJndWVzdCIsInNzbiI6IjUyOTkiLCJ1c2VyaWQiOiI2YTU2MmI4YmU4ZDViNTViYjRmOTFmMzUiLCJ2IjoiMCJ9.69uVhcJyQiVeZ-GwmV8Bfy_kC1pg4Dj0rVARpO7SlLc",
        "device_id": "cb3afb44f63c259d49445bf534305b4d"
    },
    {
        "jwt": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJkZXZJZCI6IjdlY2YxOTRhZGQ5NWVkMmQ1ZTZhMWU1MGFiYmIyMDEzIiwiZmxhZyI6ImE3NmUiLCJmcm9tIjoidGFwdGFwIiwibHQiOiJndWVzdCIsInNzbiI6IjUyOTkiLCJ1c2VyaWQiOiI2YTU2MmI4ZGU4ZDViNTViYjRmOTFmMzciLCJ2IjoiMCJ9.rS8JFlzPxw_jnYBO9_WhsKX6wnpUJi6U-dWKYLIWivY",
        "device_id": "7ecf194add95ed2d5e6a1e50abb2013"
    },
    {
        "jwt": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJkZXZJZCI6IjlmMWNhZTIxZmFiYzgxZjFmMzViN2ExYmMyMjNkMmU1IiwiZmxhZyI6ImVlZGQiLCJmcm9tIjoidGFwdGFwIiwibHQiOiJndWVzdCIsInNzbiI6IjUyOTkiLCJ1c2VyaWQiOiI2YTU2MmI4ZmU4ZDViNTViYjRmOTFmMzkiLCJ2IjoiMCJ9.RMXkY-BntXpPFiDPRNZ0JIybLYRrLPdYiRAGwxdXzRQ",
        "device_id": "9f1cae21fabc81f1f35b7a1bc223d2e5"
    }
]

# ========== 全局配置变量 ==========
JWT = DEFAULT_JWT
DEVICE_ID = DEFAULT_DEVICE_ID
SSN = DEFAULT_SSN
VER = DEFAULT_VER
COOKIE = DEFAULT_COOKIE

# ========== 辅助函数 ==========
def generate_random_device_id():
    """生成随机32位十六进制设备ID"""
    try:
        return secrets.token_hex(16)
    except:
        return ''.join(random.choices('0123456789abcdef', k=32))

def base36_to_dec(s):
    """36进制字符串转十进制整数"""
    if not s:
        return None
    try:
        return int(s.lower(), 36)
    except ValueError:
        return None

def dec_to_base36(num):
    """十进制转36进制字符串"""
    if num == 0:
        return "0"
    digits = "0123456789abcdefghijklmnopqrstuvwxyz"
    res = ""
    n = num
    while n > 0:
        n, rem = divmod(n, 36)
        res = digits[rem] + res
    return res

def print_header():
    """打印顶部标题"""
    os.system('cls' if os.name == 'nt' else 'clear')
    print(f"{CYAN}╔════════════════════════════════════════╗{NC}")
    print(f"{CYAN}║      派对制造 Python 工具箱 v5.2.1    ║{NC}")
    print(f"{CYAN}╚════════════════════════════════════════╝{NC}")
    print()

def print_menu():
    """打印主菜单"""
    print(f"{YELLOW}════════════════ 主菜单 ════════════════{NC}")
    print(f"{GREEN}A. 查看当前IP地址{NC}")
    print(f"{GREEN}B. 设备ID设置{NC}")
    print(f"{GREEN}C. 查询游戏版本信息{NC}")
    print(f"{GREEN}D. 查询游戏公告{NC}")
    print(f"{GREEN}E. 查看工具箱公告{NC}")
    print(f"{GREEN}F. 查看工具箱版本{NC}")
    print(f"{GREEN}1. 派对制造房间列表{NC}")
    print(f"{GREEN}2. 派对制造地图查询{NC}")
    print(f"{GREEN}3. 派对制造排行榜查询{NC}")
    print(f"{GREEN}4. 派对制造玩家信息查询 + 关系图谱生成{NC}")
    print(f"{GREEN}5. 派对制造查询最新地图{NC}")
    print(f"{GREEN}6. 派对制造金矿打工{NC}")
    print(f"{GREEN}7. 派对制造评论地图{NC}")
    print(f"{GREEN}8. 派对制造广播地图{NC}")
    print(f"{GREEN}9. 派对制造批量拉取昵称{NC}")
    print(f"{RED}0. 退出工具{NC}")
    print(f"{YELLOW}════════════════════════════════════════{NC}")
    print()

def load_config():
    """加载配置文件"""
    global JWT, DEVICE_ID, SSN, VER, COOKIE, MAP_COUNT
    if not os.path.exists(CONFIG_FILE):
        return
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or '=' not in line:
                    continue
                key, value = line.split('=', 1)
                value = value.strip().strip('"')
                if key == 'JWT':
                    JWT = value
                elif key == 'DEVICE_ID':
                    DEVICE_ID = value
                elif key == 'SSN':
                    SSN = value
                elif key == 'VER':
                    VER = value
                elif key == 'COOKIE':
                    COOKIE = value
                elif key == 'SAVED_MAP_COUNT':
                    MAP_COUNT = int(value)
    except Exception as e:
        print(f"{RED}读取配置失败: {e}{NC}")

def save_config():
    """保存配置到文件"""
    try:
        os.makedirs(CONFIG_DIR, exist_ok=True)
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            f.write(f"JWT={JWT}\n")
            f.write(f"DEVICE_ID={DEVICE_ID}\n")
            f.write(f"SSN={SSN}\n")
            f.write(f"VER={VER}\n")
            f.write(f"COOKIE={COOKIE}\n")
            f.write(f"SAVED_MAP_COUNT={MAP_COUNT}\n")
    except Exception as e:
        print(f"{RED}保存配置失败: {e}{NC}")

def get_session(jwt=None, device_id=None):
    if jwt is None:
        jwt = JWT
    if device_id is None:
        device_id = DEVICE_ID
    url = "https://battlecraft.tuimotuimo.com/battlecraft/account/loginsession"
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "*/*",
        "ssn": SSN,
        "ver": VER,
        "Cookie": COOKIE,
    }
    data = {
        "timezone": "8",
        "v2": "true",
        "v3": "true",
        "session": jwt,
        "deviceId": device_id,
        "tutorialType": "ugc"
    }
    try:
        resp = requests.post(url, headers=headers, data=data, timeout=10)
        resp.raise_for_status()
        result = resp.json()
        # 修复：sessionid 在 data 里面，不是在顶层
        session = result.get("data", {}).get("sessionid")
        if not session:
            print(f"{RED}响应中没有sessionid{NC}")
        return session
    except Exception as e:
        print(f"{RED}获取Session失败: {e}{NC}")
        return None

# ========== 功能函数 ==========
def func_show_ip():
    print_header()
    print(f"{YELLOW}>>> 查询本机IP地址{NC}\n")
    print(f"{BLUE}公网IP地址：{NC}")
    try:
        ip = requests.get("https://ifconfig.me", timeout=5).text.strip()
        if ip:
            print(f"{GREEN}  → {ip}{NC}")
        else:
            ip = requests.get("https://ipinfo.io/ip", timeout=5).text.strip()
            if ip:
                print(f"{GREEN}  → {ip}{NC}")
            else:
                print(f"{RED}  → 获取失败{NC}")
    except:
        print(f"{RED}  → 获取失败{NC}")

    print(f"\n{BLUE}内网IP地址：{NC}")
    try:
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        print(f"{GREEN}  → {local_ip}{NC}")
    except:
        print(f"{RED}  → 获取失败{NC}")

    input(f"\n{CYAN}按回车键返回主菜单...{NC}")

def func_device_setup():
    global JWT, DEVICE_ID, SSN, COOKIE
    while True:
        print_header()
        print(f"{YELLOW}>>> 设备ID和认证设置{NC}\n")
        print(f"{BLUE}当前配置：{NC}")
        print(f"  JWT: {JWT[:50]}...")
        print(f"  Device ID: {DEVICE_ID}")
        print(f"  SSN: {SSN}")
        print(f"  Cookie: {COOKIE[:50]}...\n")
        print(f"{GREEN}请选择操作：{NC}")
        print("  1. 重置为默认配置")
        print("  2. 手动设置JWT")
        print("  3. 手动设置Device ID")
        print("  4. 手动设置SSN")
        print("  5. 保存当前配置")
        print("  0. 返回主菜单")
        print()
        choice = input("请输入选项: ").strip()
        if choice == "1":
            JWT = DEFAULT_JWT
            DEVICE_ID = generate_random_device_id()
            SSN = DEFAULT_SSN
            COOKIE = DEFAULT_COOKIE
            print(f"{GREEN}✅ 已重置为默认配置（Device ID已随机生成）{NC}")
            time.sleep(0.3)
        elif choice == "2":
            val = input("请输入JWT（以eyJ开头）：").strip()
            if val:
                JWT = val
                print(f"{GREEN}✅ JWT已设置{NC}")
            time.sleep(0.3)
        elif choice == "3":
            val = input("请输入Device ID：").strip()
            if val:
                DEVICE_ID = val
                print(f"{GREEN}✅ Device ID已设置{NC}")
            time.sleep(0.3)
        elif choice == "4":
            val = input("请输入SSN：").strip()
            if val:
                SSN = val
                print(f"{GREEN}✅ SSN已设置{NC}")
            time.sleep(0.3)
        elif choice == "5":
            save_config()
            print(f"{GREEN}✅ 配置已保存到 {CONFIG_FILE}{NC}")
            time.sleep(0.3)
        elif choice == "0":
            return
        else:
            print(f"{RED}无效选项{NC}")
            time.sleep(0.3)

def func_game_version():
    print_header()
    print(f"{YELLOW}>>> 查询游戏版本信息{NC}\n")
    print(f"{BLUE}正在获取配置信息...{NC}")
    try:
        resp = requests.get("https://prod.tuimotuimo.com/config/info/battlecraft", timeout=10)
        resp.raise_for_status()
        data = resp.json()
        print(f"{GREEN}✅ 获取成功{NC}\n")
        print(f"{GREEN}════════════════ 版本信息 ════════════════{NC}\n")
        platforms = data.get("platforms", {})
        platform_names = {
            'taptap': 'TapTap', 'douyin_app': '抖音APP', 'douyin_live': '抖音直播',
            'ios': 'iOS', 'qq': 'QQ', 'wechat': '微信',
            'bilibili': 'Bilibili', 'kuaishou': '快手', 'momoyu': '摸摸鱼', 'toutiao': '头条'
        }
        for key in platform_names:
            if key in platforms:
                p = platforms[key]
                prod_ver = p.get('prod', '未知')
                current_mark = " ← (当前)" if prod_ver == VER else ""
                print(f"  {platform_names.get(key, key):<10}: {prod_ver}{current_mark}")
        print(f"\n  📦 应用版本: {data.get('version', '未知')}")
        print(f"  🔍 审核版本: {data.get('censorVersion', '未知')}")
        print(f"  🟢 服务状态: {'开启' if data.get('isOpen') else '关闭'}")
        print(f"  📹 OBS支持: {'开启' if data.get('obsEnabled') else '关闭'}")
    except Exception as e:
        print(f"{RED}获取失败: {e}{NC}")
    input(f"\n{CYAN}按回车键返回主菜单...{NC}")

def func_game_notice():
    print_header()
    print(f"{YELLOW}>>> 查询游戏公告{NC}\n")
    print(f"{BLUE}正在获取公告信息...{NC}")
    try:
        resp = requests.get("https://prod.tuimotuimo.com/config/info/battlecraft", timeout=10)
        resp.raise_for_status()
        data = resp.json()
        print(f"{GREEN}✅ 获取成功{NC}\n")
        notice = data.get('notice', {})
        notice_type = notice.get('type', 'normal')
        notice_title = notice.get('title', '')
        notice_text = notice.get('text', '')
        notice_after = data.get('noticeAfter', {})
        after_text = notice_after.get('text', '')
        if notice_title or notice_text:
            print(f"  {'='*50}")
            print(f"  📢 {'【重要公告】' if notice_type == 'stopServer' else '【当前公告】'}")
            if notice_title:
                print(f"  {notice_title}")
            if notice_text:
                print(f"\n{notice_text}\n")
        if after_text:
            print(f"  {'='*50}")
            print(f"  📰 【游戏公告】")
            print(f"\n{after_text}\n")
        if not notice_text and not after_text:
            print("  暂无公告")
    except Exception as e:
        print(f"{RED}获取失败: {e}{NC}")
    input(f"\n{CYAN}按回车键返回主菜单...{NC}")

def func_github_notice():
    print_header()
    print(f"{YELLOW}>>> 查看在线公告{NC}\n")
    print(f"{BLUE}正在获取公告内容...{NC}")
    try:
        resp = requests.get("https://ghproxy.net/https://raw.githubusercontent.com/imgsr/pdzz/main/context.txt", timeout=10)
        resp.raise_for_status()
        content = resp.text
        print(f"{GREEN}✅ 获取成功{NC}\n")
        print(f"{CYAN}════════════════ 公告内容 ════════════════{NC}")
        print(content)
        print(f"{CYAN}════════════════════════════════════════{NC}")
    except Exception as e:
        print(f"{RED}❌ 获取公告失败: {e}{NC}")
    input(f"\n{CYAN}按回车键返回主菜单...{NC}")

def func_toolbox_version():
    print_header()
    print(f"{YELLOW}>>> 查看工具箱版本{NC}\n")
    print(f"{BLUE}正在获取版本信息...{NC}")
    try:
        resp = requests.get("https://ghproxy.net/https://raw.githubusercontent.com/imgsr/pdzz/main/version.txt", timeout=10)
        resp.raise_for_status()
        content = resp.text
        print(f"{GREEN}✅ 获取成功{NC}\n")
        print(f"{CYAN}════════════════ 版本信息 ════════════════{NC}")
        print(content)
        print(f"{CYAN}════════════════════════════════════════{NC}")
    except Exception as e:
        print(f"{RED}❌ 获取版本信息失败: {e}{NC}")
    input(f"\n{CYAN}按回车键返回主菜单...{NC}")

def func_room_list():
    print_header()
    print(f"{YELLOW}>>> 派对制造房间列表{NC}\n")
    session = get_session()
    if not session:
        print(f"{RED}获取Session失败{NC}")
        input(f"{CYAN}按回车键返回主菜单...{NC}")
        return
    # 获取房间ID列表
    url = "https://battlecraft.tuimotuimo.com/battlecraft/matchpvp/getroomids"
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Auth": session,
        "ssn": SSN,
        "ver": VER,
        "Cookie": COOKIE,
    }
    data = {"start": "0", "count": "100"}
    try:
        resp = requests.post(url, headers=headers, data=data, timeout=10)
        resp.raise_for_status()
        room_data = resp.json()
        room_ids = room_data.get("data", {}).get("matchRoomIds", [])
        if not room_ids:
            print("未获取到房间ID")
            input(f"{CYAN}按回车键返回主菜单...{NC}")
            return
        ids_str = ",".join(room_ids)
        # 获取房间详情
        url2 = "https://battlecraft.tuimotuimo.com/battlecraft/matchpvp/getroomlist"
        data2 = {"ids": ids_str}
        resp2 = requests.post(url2, headers=headers, data=data2, timeout=10)
        resp2.raise_for_status()
        room_detail = resp2.json()
        rooms = room_detail.get("data", {}).get("matchRooms", [])
        print("\n========== 玩家列表 ==========")
        players = []
        for room in rooms:
            owner = room.get("owner", {})
            nick = owner.get("nickName", "未知")
            room_id = room.get("id", "N/A")
            short_id = owner.get("userShortId", "N/A")
            players.append((nick, room_id, short_id))
        for i in range(0, len(players), 2):
            p1_nick, p1_room, p1_short = players[i]
            line = f"{p1_nick} [房间:{p1_room}] [短ID:{p1_short}]"
            if i + 1 < len(players):
                p2_nick, p2_room, p2_short = players[i+1]
                line += f"  |  {p2_nick} [房间:{p2_room}] [短ID:{p2_short}]"
            print(line)
        print(f"\n总计: {len(players)} 人")
        print("============")
    except Exception as e:
        print(f"{RED}请求失败: {e}{NC}")
    input(f"\n{CYAN}按回车键返回主菜单...{NC}")

def func_map_query():
    print_header()
    print(f"{YELLOW}>>> 派对制造地图查询{NC}\n")
    code = input(f"{BLUE}请输入地图代码：{NC}").strip()
    if not code:
        print(f"{RED}地图代码不能为空{NC}")
        input(f"{CYAN}按回车键返回主菜单...{NC}")
        return
    map_id = base36_to_dec(code)
    if map_id is None or map_id == 0:
        print(f"{RED}地图码无效{NC}")
        input(f"{CYAN}按回车键返回主菜单...{NC}")
        return
    print(f"地图ID: {map_id}")
    session = get_session()
    if not session:
        print(f"{RED}登录失败{NC}")
        input(f"{CYAN}按回车键返回主菜单...{NC}")
        return
    print(f"{GREEN}✅ 登录成功{NC}")

    # 获取地图详情
    url = "https://battlecraft.tuimotuimo.com/battlecraft/ugclevel/get"
    headers = {
        "Auth": session,
        "ssn": SSN,
        "ver": VER,
        "Cookie": COOKIE,
        "Content-Type": "application/x-www-form-urlencoded",
    }
    data = {"id": str(map_id), "needMarkList": "false"}
    try:
        resp = requests.post(url, headers=headers, data=data, timeout=10)
        resp.raise_for_status()
        map_data = resp.json()
        if map_data.get("code") != 0:
            print(f"{RED}查询失败，错误码: {map_data.get('code')}{NC}")
            input(f"{CYAN}按回车键返回主菜单...{NC}")
            return
        level = map_data.get("data", {}).get("level", {})
        owner = level.get("owner", {})
        # 显示详细信息
        print(f"\n{GREEN}=== 地图详细信息 ==={NC}")
        print(f"  📌 地图名称：{level.get('name', '无')}")
        print(f"  🆔 地图ID：{level.get('id', '无')}")
        print(f"  🔢 地图码：{dec_to_base36(level.get('id', 0))}")
        print(f"  📅 发布时间：{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(level.get('timestamp', 0)/1000)) if level.get('timestamp') else '未知'}")
        # 状态
        status = level.get('status', 0)
        in_trash = level.get('inTrash', False)
        status_desc = "✅ 正常"
        if status == 1:
            status_desc = "🔴 官方亲自下线地图"
        elif status == 2:
            status_desc = "⚠️ 巡检屏蔽告示牌"
        elif 11 <= status <= 20:
            status_desc = "🟡 可能审核中"
        elif status >= 21:
            status_desc = "⏳ 审核中"
        print(f"  📋 地图状态：{status_desc} (status={status})")
        print(f"  🗑️ 回收站状态：{'已删除' if in_trash else '✅ 未删除'}")
        # 数据
        play_count = level.get('playCount', 0)
        finish_count = level.get('finishCount', 0)
        pass_rate = (finish_count / play_count * 100) if play_count > 0 else 0
        print(f"  🎮 游玩次数：{play_count}")
        print(f"  🎯 通关次数：{finish_count}")
        print(f"  📊 通关率：{pass_rate:.2f}%")
        print(f"  👍 点赞数：{level.get('likes', 0)}")
        print(f"  👎 点踩数：{level.get('dislike', 0)}")
        print(f"  🏆 最佳单人分数：{level.get('bestScore', 0)}")
        # 作者
        clan = owner.get('clan', {})
        print(f"\n  👤 作者信息：")
        print(f"    昵称：{owner.get('nickName', '未知')}")
        print(f"    短ID：{owner.get('userShortId', '无')}")
        print(f"    用户ID：{owner.get('userid', '无')}")
        print(f"    段位：{owner.get('dan', 0)}")
        print(f"    等级：{owner.get('level', 0)}")
        print(f"    性别：{('男' if owner.get('gender')==1 else '女' if owner.get('gender')==2 else '保密')}")
        print(f"    称号：{owner.get('title', '无')}")
        print(f"    城市：{owner.get('city', '未知')}")
        print(f"    省份：{owner.get('province', '未知')}")
        print(f"    战队：{clan.get('name', '无战队')}")
        # 标签
        tags = level.get('tags', [])
        print(f"\n  🏷️ 标签：{', '.join(tags) if tags else '无'}")
        # 排行榜
        top = level.get('top', [])
        if top:
            print(f"\n  🏆 单人排行榜 Top 3:")
            for i, item in enumerate(top[:3], 1):
                p = item.get('player', {})
                print(f"    {i}. {p.get('nickName','未知')} | 短ID:{p.get('userShortId','无')} | 分数:{item.get('record',0)}")
    except Exception as e:
        print(f"{RED}查询失败: {e}{NC}")
        input(f"{CYAN}按回车键返回主菜单...{NC}")
        return

    # 是否查看评论
    view = input("\n是否查看全部评论？(y/n) ").strip().lower()
    if view != 'y':
        input(f"{CYAN}按回车键返回主菜单...{NC}")
        return

    # 评论翻页
    PAGE_SIZE = 5
    current_page = 1
    start = 0
    while True:
        print(f"\n---- 第 {current_page} 页 ----")
        url_comment = "https://battlecraft.tuimotuimo.com/battlecraft/ugclevel/getcomments"
        data_comment = {"id": str(map_id), "start": str(start), "count": str(PAGE_SIZE)}
        try:
            resp = requests.post(url_comment, headers=headers, data=data_comment, timeout=10)
            resp.raise_for_status()
            comments = resp.json().get("data", {}).get("comments", [])
            if not comments:
                print("无更多评论")
                break
            for c in comments:
                p = c.get('player', {})
                ts = c.get('ts', 0) / 1000
                dt = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(ts))
                typ = c.get('type')
                content = c.get('content')
                show = content if typ == 'text' else f'stamp:{content}'
                print(f"时间：{dt}")
                print(f"用户：{p.get('nickName', '未知')} | 短ID：{p.get('userShortId', '无')}")
                print(f"评论ID：{c.get('id')}")
                print(f"内容：{show}")
                print("---")
        except Exception as e:
            print(f"{RED}获取评论失败: {e}{NC}")
            break

        op = input("请选择操作(y/n/页码): ").strip()
        if op == 'n':
            break
        elif op.isdigit():
            target = int(op)
            if target < 1:
                print(f"{RED}页码不能小于1{NC}")
                continue
            current_page = target
            start = (target - 1) * PAGE_SIZE
        elif op == 'y':
            current_page += 1
            start += PAGE_SIZE
        else:
            print(f"{RED}无效输入，继续下一页{NC}")
            current_page += 1
            start += PAGE_SIZE
    print(f"{GREEN}✅ 查询完成！{NC}")
    input(f"{CYAN}按回车键返回主菜单...{NC}")

def func_rank_query():
    while True:
        print_header()
        print(f"{YELLOW}>>> 派对制造排行榜查询{NC}\n")
        print(f"{GREEN}请选择排行榜类型：{NC}")
        print("  1. 创造榜（本周周榜）")
        print("  2. 操作榜（本周周榜）")
        print("  3. 联赛榜")
        print("  4. 创造榜（总榜）")
        print("  5. 操作榜（总榜）")
        print("  0. 返回主菜单")
        choice = input("请选择 [0-5]: ").strip()
        rank_map = {
            "1": ("creative", "week", "创造榜（本周周榜）"),
            "2": ("skill", "week", "操作榜（本周周榜）"),
            "3": ("leaguescore", "0060", "联赛榜"),
            "4": ("creative", "all", "创造榜（总榜）"),
            "5": ("skill", "all", "操作榜（总榜）"),
        }
        if choice == "0":
            return
        if choice not in rank_map:
            print(f"{RED}无效选项{NC}")
            time.sleep(0.3)
            continue
        rank_name, rank_id, title = rank_map[choice]
        session = get_session()
        if not session:
            print(f"{RED}获取Session失败{NC}")
            time.sleep(2)
            continue
        print(f"{BLUE}正在获取{title}...{NC}\n")
        url = "https://battlecraft.tuimotuimo.com/battlecraft/ranklist/gettop" if rank_name == "leaguescore" else "https://battlecraft.tuimotuimo.com/battlecraft/ranklist/getleveltop"
        headers = {
            "Auth": session,
            "ssn": SSN,
            "ver": VER,
            "Cookie": COOKIE,
            "Content-Type": "application/x-www-form-urlencoded",
        }
        data = {"name": rank_name, "count": "100", "rankId": rank_id}
        try:
            resp = requests.post(url, headers=headers, data=data, timeout=10)
            resp.raise_for_status()
            rank_data = resp.json()
            ranklist = rank_data.get("data", {}).get("ranklist", [])
            print(f"{GREEN}══════════ {title} ══════════{NC}\n")
            if not ranklist:
                print("  暂无数据")
            else:
                print(f"  {'排名':<4} {'段位':<6} {'玩家昵称':<20} {'短ID':<12} {'分数':<10}")
                print(f"  {'-'*60}")
                for i, item in enumerate(ranklist[:100], 1):
                    name = item.get('name', '未知')[:18]
                    score = item.get('score', 0)
                    dan = item.get('dan', 0)
                    short_id = item.get('userShortId', '')
                    clan = item.get('clan', {}).get('name', '')
                    display_name = f"[{clan}]{name}" if clan else name
                    print(f"  {i:<4} {dan:<6} {display_name:<20} {str(short_id):<12} {score:<10}")
                print(f"\n  📊 共 {len(ranklist)} 条记录")
        except Exception as e:
            print(f"{RED}请求失败: {e}{NC}")
        input(f"\n{CYAN}按回车键继续...{NC}")

def func_player_info():
    print_header()
    print(f"{YELLOW}>>> 派对制造玩家信息查询 + 关系图谱生成{NC}\n")
    map_code = input(f"{BLUE}请输入该玩家任意地图代码：{NC}").strip()
    if not map_code:
        print(f"{YELLOW}已取消{NC}")
        input(f"{CYAN}按回车键返回主菜单...{NC}")
        return
    map_id = base36_to_dec(map_code)
    if map_id is None:
        print(f"{RED}地图码无效{NC}")
        input(f"{CYAN}按回车键返回主菜单...{NC}")
        return
    print(f"{GREEN}地图ID: {map_id}{NC}")
    session = get_session()
    if not session:
        print(f"{RED}获取Session失败{NC}")
        input(f"{CYAN}按回车键返回主菜单...{NC}")
        return

    # 获取地图信息提取作者
    url_map = "https://battlecraft.tuimotuimo.com/battlecraft/ugclevel/get"
    headers = {
        "Auth": session,
        "ssn": SSN,
        "ver": VER,
        "Cookie": COOKIE,
        "Content-Type": "application/x-www-form-urlencoded",
    }
    data_map = {"id": str(map_id), "needMarkList": "false"}
    try:
        resp = requests.post(url_map, headers=headers, data=data_map, timeout=10)
        resp.raise_for_status()
        map_data = resp.json()
        author_id = map_data.get("data", {}).get("level", {}).get("owner", {}).get("userid")
        if not author_id:
            print(f"{RED}无法获取作者信息{NC}")
            input(f"{CYAN}按回车键返回主菜单...{NC}")
            return
        print(f"{GREEN}✅ 作者ID: {author_id}{NC}\n")
    except Exception as e:
        print(f"{RED}获取地图信息失败: {e}{NC}")
        input(f"{CYAN}按回车键返回主菜单...{NC}")
        return

    # 获取玩家详细信息
    url_user = "https://battlecraft.tuimotuimo.com/battlecraft/userrole/detailinfo"
    data_user = {"userId": author_id}
    try:
        resp = requests.post(url_user, headers=headers, data=data_user, timeout=10)
        resp.raise_for_status()
        user_data = resp.json()
    except Exception as e:
        print(f"{RED}获取玩家信息失败: {e}{NC}")
        input(f"{CYAN}按回车键返回主菜单...{NC}")
        return

    # 获取关系图谱
    url_relation = "https://battlecraft.tuimotuimo.com/battlecraft/relation/info"
    data_relation = {"frdId": author_id}
    try:
        resp_rel = requests.post(url_relation, headers=headers, data=data_relation, timeout=10)
        resp_rel.raise_for_status()
        relation_data = resp_rel.json()
    except Exception as e:
        print(f"{RED}获取关系图谱失败: {e}{NC}")
        relation_data = {}

    # 解析显示玩家信息
    print(f"\n{GREEN}════════════════════ 玩家档案 ════════════════════{NC}\n")
    user = user_data.get("data", {})
    basic = user.get("basic", {})
    ugc_info = user.get("ugcInfo", {})
    honesty = user.get("honesty", {})
    userlevel = user.get("userlevel", {})
    clan = basic.get("clan", {})
    nick = basic.get("nickName", "未知")
    gender_map = {1: '男', 2: '女', 0: '保密'}
    gender = gender_map.get(basic.get('gender', 0), '保密')
    level = basic.get('level', 0)
    short_id = basic.get('userShortId', '无')
    dan = basic.get('dan', 0)
    province = basic.get('province', '')
    city = basic.get('city', '')
    location = f"{province}{city}" if province and city else province or city or "未设置"
    clan_name = clan.get('name', '无战队')
    created_at = basic.get('createdAt', 0)
    reg_time = time.strftime('%Y-%m-%d', time.localtime(created_at/1000)) if created_at else '未知'
    honesty_score = honesty.get('honesty', 0)
    exp = userlevel.get('exp', {})
    exp_creative = exp.get('creative', 0)
    exp_skill = exp.get('skill', 0)
    exp_pvp = exp.get('pvp', 0)
    exp_active = exp.get('active', 0)
    exp_vip = exp.get('vip', 0)
    rank = basic.get('rank', 0)
    exp_rank = basic.get('expRank', {})
    creative_rank = exp_rank.get('creative', 0)
    skill_rank = exp_rank.get('skill', 0)

    print(f"  👤 昵称: {nick}")
    print(f"  🚻 性别: {gender}")
    print(f"  🎚️ 等级: {level}")
    print(f"  🎖️ 段位: {dan}")
    print(f"  🔢 短ID: {short_id}")
    print(f"  📍 位置: {location}")
    print(f"  🏠 战队: {clan_name}")
    print(f"  📅 注册日期: {reg_time}")
    print(f"  ⚖️ 人品值: {honesty_score}")
    print(f"  📊 联赛排名: #{rank}")
    print(f"  ✨ 创造榜排名: #{creative_rank}  | 创造经验: {exp_creative}")
    print(f"  🎯 操作榜排名: #{skill_rank}  | 操作经验: {exp_skill}")
    print(f"  ⚔️ 对战经验: {exp_pvp}")
    print(f"  🔥 活跃经验: {exp_active}")
    print(f"  💎 贵族经验: {exp_vip}")

    # 地图列表
    map_ids = ugc_info.get('ids', [])
    if map_ids:
        map_codes = [dec_to_base36(mid) for mid in map_ids]
        print(f"\n  🗺️ 玩家发布的地图 ({len(map_ids)}个):")
        for i in range(0, len(map_codes), 3):
            chunk = map_codes[i:i+3]
            print("     " + "  ".join(chunk))

    # 关系图谱解析
    print(f"\n  ━━━━━━━━━━━━━━━━━━━━ 亲密关系 ━━━━━━━━━━━━━━━━━━━━")
    relations = relation_data.get("data", {}).get("relation", {}).get("relations", {})
    rel_type_map = {
        "0001": {"name": "CP", "icon": "💕"},
        "0002": {"name": "师父", "icon": "👨‍🏫"},
        "0003": {"name": "徒弟", "icon": "👨‍🎓"},
        "0004": {"name": "搭档", "icon": "🤝"},
        "0005": {"name": "闺蜜", "icon": "👭"},
        "0006": {"name": "基友", "icon": "👬"}
    }
    for key in ["0001","0002","0003","0004","0005","0006"]:
        rel_info = relations.get(key, {})
        friends = rel_info.get('friends', [])
        rel = rel_type_map.get(key, {})
        rel_name = rel.get("name", key)
        icon = rel.get("icon", "•")
        if friends:
            show_list = []
            for f in friends[:3]:
                f_nick = f.get('nickName', '未知')
                f_short = f.get('userShortId', '无')
                f_intimacy = f.get('intimacy', 0)
                show_list.append(f"{f_nick}[{f_short}]({f_intimacy})")
            friends_text = ", ".join(show_list)
            if len(friends) > 3:
                friends_text += f" 等{len(friends)}人"
            print(f"  {icon} {rel_name}: {friends_text}")
        else:
            print(f"  {icon} {rel_name}: 无")

    print(f"\n{CYAN}════════════════════════════════════════════════════{NC}")

    # 生成关系图谱HTML
    gen = input(f"\n{YELLOW}是否生成该玩家的力导向图关系图谱？ [y/n] (默认 n):{NC} ").strip().lower()
    if gen == 'y':
        print(f"\n{BLUE}正在生成关系图谱...{NC}")
        # 提取所需信息
        author_name = nick
        author_avatar = basic.get('avatarUrl', '')
        author_title = basic.get('title', '')
        author_clan = clan_name
        author_gender = gender
        author_level = level

        # 构建friends列表
        friends_list = []
        for rel_key, rel_info in relations.items():
            rel_type = rel_type_map.get(rel_key, {}).get("name", rel_key)
            rel_color = {
                "0001": "#ff9a9e", "0002": "#6ecb63", "0003": "#4da6ff",
                "0004": "#ffd166", "0005": "#db4dff", "0006": "#5e60ce"
            }.get(rel_key, "#999")
            for f in rel_info.get('friends', []):
                intimacy = f.get('intimacy', 0)
                avatar = f.get('avatarUrl', '')
                if not avatar or avatar.startswith('avatar://'):
                    avatar = f"https://ui-avatars.com/api/?name={f.get('nickName', '玩家')}&background=random&size=80"
                friends_list.append({
                    "id": f"f{f.get('userShortId', '')}",
                    "nickName": f.get('nickName', '未知'),
                    "avatarUrl": avatar,
                    "level": f.get('level', 0),
                    "gender": f.get('gender', 0),
                    "intimacy": intimacy,
                    "clan": f.get('clan', {}).get('name', ''),
                    "relationType": rel_type,
                    "relationColor": rel_color,
                    "relationKey": rel_key
                })

        # 生成HTML
        output_dir = "/storage/emulated/0/partyd3js" if os.path.exists("/storage/emulated/0") else os.path.join(CONFIG_DIR, "partyd3js")
        os.makedirs(output_dir, exist_ok=True)
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join(output_dir, f"关系图谱_{author_name}_{timestamp}.html")

        # 构建JSON数据用于JavaScript
        me_json = {
            "id": "center",
            "name": author_name,
            "avatar": author_avatar,
            "level": author_level,
            "gender": author_gender,
            "title": author_title,
            "clan": author_clan
        }
        # 构建关系
        rel_json = {}
        for rel_key in ["0001","0002","0003","0004","0005","0006"]:
            rel_json[rel_key] = [f for f in friends_list if f.get("relationKey") == rel_key]

        html_content = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>{author_name}的关系图谱</title>
<script src="https://d3js.org/d3.v7.min.js"></script>
<style>
body{{margin:0;padding:0;background:linear-gradient(135deg,#e0f0ff,#c5e3ff);font-family:"Microsoft YaHei",sans-serif;overflow:hidden;}}
.container{{position:relative;width:100vw;height:100vh;}}
#graph{{width:100%;height:100%;}}
.header{{position:absolute;top:20px;left:50%;transform:translateX(-50%);background:rgba(255,255,255,.85);border-radius:20px;padding:15px 30px;box-shadow:0 5px 15px rgba(0,0,0,.1);z-index:100;display:flex;align-items:center;justify-content:center;flex-direction:column;max-width:400px;border:2px solid #4a90e2;}}
.header-main{{display:flex;align-items:center;margin-bottom:8px;}}
.user-avatar{{width:60px;height:60px;border-radius:50%;margin-right:15px;border:3px solid #ff7979;background:#f0f8ff;display:flex;align-items:center;justify-content:center;color:#ff7979;font-weight:bold;}}
.user-info h2{{margin:0;color:#333;font-size:20px;font-weight:bold;}}
.user-title{{color:#ff6b6b;font-size:14px;margin-top:5px;font-weight:bold;}}
.clan-info{{color:#4a90e2;font-size:14px;margin-top:2px;}}
.intimacy-display{{background:linear-gradient(to right,#ff9a9e,#fad0c4);border-radius:15px;padding:5px 15px;margin-top:10px;color:white;font-weight:bold;font-size:14px;box-shadow:0 3px 6px rgba(0,0,0,.1);}}
.legend{{position:absolute;bottom:20px;left:20px;background:rgba(255,255,255,.85);border-radius:15px;padding:15px;box-shadow:0 5px 15px rgba(0,0,0,.1);z-index:100;max-width:250px;}}
.legend h3{{margin:0 0 10px 0;color:#333;font-size:16px;}}
.legend-item{{display:flex;align-items:center;margin-bottom:8px;font-size:14px;}}
.legend-color{{width:20px;height:20px;border-radius:50%;margin-right:10px;border:2px solid white;}}
.node{{cursor:pointer;filter:drop-shadow(0 3px 5px rgba(0,0,0,.2));}}
.tooltip{{position:absolute;background:rgba(255,255,255,.95);border-radius:12px;padding:15px;box-shadow:0 8px 20px rgba(0,0,0,.15);max-width:250px;z-index:100;opacity:0;transition:opacity .3s;border:1px solid #ddd;pointer-events:none;}}
.tooltip-header{{display:flex;align-items:center;margin-bottom:10px;border-bottom:1px solid #eee;padding-bottom:10px;}}
.tooltip-avatar{{width:50px;height:50px;border-radius:50%;margin-right:10px;border:2px solid #4a90e2;}}
.tooltip-name{{font-weight:bold;font-size:18px;color:#333;}}
.tooltip-title{{color:#ff7979;font-size:14px;margin-top:3px;}}
.tooltip-info{{padding-top:8px;color:#666;font-size:14px;line-height:1.5;}}
.bg-element{{position:absolute;opacity:.08;z-index:1;pointer-events:none;}}
.avatar-container{{width:100%;height:100%;display:flex;align-items:center;justify-content:center;border-radius:50%;overflow:hidden;background:#f0f8ff;}}
.avatar-image{{width:100%;height:100%;object-fit:cover;}}
</style>
</head>
<body>
<div class="container">
  <div id="bg-elements"></div>
  <div class="header">
    <div class="header-main">
      <img class="user-avatar" src="{author_avatar}" onerror="this.src='https://ui-avatars.com/api/?name={author_name}&background=random&size=80'">
      <div class="user-info">
        <h2>{author_name}</h2>
        <div class="user-title">{author_title}</div>
        <div class="clan-info">{author_clan}</div>
      </div>
    </div>
    <div class="intimacy-display">亲密度≥100的好友显示在关系图谱中</div>
  </div>
  <div class="legend">
    <h3>关系图例</h3>
    <div class="legend-item"><div class="legend-color" style="background:#ff9a9e"></div><span>CP</span></div>
    <div class="legend-item"><div class="legend-color" style="background:#6ecb63"></div><span>师父</span></div>
    <div class="legend-item"><div class="legend-color" style="background:#4da6ff"></div><span>徒弟</span></div>
    <div class="legend-item"><div class="legend-color" style="background:#ffd166"></div><span>搭档</span></div>
    <div class="legend-item"><div class="legend-color" style="background:#db4dff"></div><span>闺蜜</span></div>
    <div class="legend-item"><div class="legend-color" style="background:#5e60ce"></div><span>基友</span></div>
  </div>
  <svg id="graph"></svg>
  <div class="tooltip"></div>
</div>

<script>
const me = {json.dumps(me_json)};
const relMap = {{
  "0001": {{ type: "CP", color: "#ff9a9e" }},
  "0002": {{ type: "师父", color: "#6ecb63" }},
  "0003": {{ type: "徒弟", color: "#4da6ff" }},
  "0004": {{ type: "搭档", color: "#ffd166" }},
  "0005": {{ type: "闺蜜", color: "#db4dff" }},
  "0006": {{ type: "基友", color: "#5e60ce" }}
}};
const relations = {json.dumps(rel_json)};

const nodes = [me];
const links = [];
Object.entries(relations).forEach(([k, arr]) => {{
  const {{ type, color }} = relMap[k];
  arr.forEach(f => {{
    const avatarReal = f.avatarUrl && !f.avatarUrl.startsWith("avatar://") && f.avatarUrl !== "" ? f.avatarUrl : `https://ui-avatars.com/api/?name=${{encodeURIComponent(f.nickName||"玩家")}}&background=random&size=80`;
    nodes.push({{
      ...f,
      nickName: f.nickName,
      avatarReal,
      intimacy: f.intimacy,
      relationType: type,
      gender: f.gender === 0 ? "保密" : f.gender === 1 ? "男" : "女",
      clan: f.clan || "无战队"
    }});
    links.push({{ source: me.id, target: f.id, relationType: type, color, value: f.intimacy }});
  }});
}});

const bg = d3.select("#bg-elements");
const emojis = ["🔨", "🥚", "🎮", "⭐", "🎖️"];
for (let i = 0; i < 25; i++) {{
  bg.append("div").classed("bg-element", true)
    .style("font-size", `${{Math.random() * 40 + 20}}px`)
    .style("left", `${{Math.random() * 100}}%`)
    .style("top", `${{Math.random() * 100}}%`)
    .text(emojis[Math.floor(Math.random() * emojis.length)]);
}}

const width = window.innerWidth, height = window.innerHeight;
const svg = d3.select("#graph").attr("width", width).attr("height", height);
const container = svg.append("g");

const simulation = d3.forceSimulation(nodes)
  .force("link", d3.forceLink(links).id(d => d.id).distance(d => {{
    const distMap = {{ CP: 100, 师父: 180, 徒弟: 220, 搭档: 160, 闺蜜: 150, 基友: 170 }};
    return distMap[d.relationType] || 180;
  }}))
  .force("charge", d3.forceManyBody().strength(-300))
  .force("center", d3.forceCenter(width / 2, height / 2))
  .force("collision", d3.forceCollide().radius(d => d.id === "center" ? 80 : 50));

const link = container.append("g").selectAll("line")
  .data(links).enter().append("line")
  .attr("stroke", d => d.color).attr("stroke-width", 2)
  .attr("stroke-dasharray", "5,2").attr("stroke-opacity", 0.6);

const linkText = container.append("g").selectAll("text")
  .data(links).enter().append("text")
  .text(d => d.value).attr("font-size", 12).attr("font-weight", "bold")
  .attr("fill", "#2c3e50").attr("pointer-events", "none");

const node = container.append("g").selectAll("g")
  .data(nodes).enter().append("g")
  .attr("class", "node")
  .call(d3.drag()
    .on("start", dragstarted)
    .on("drag", dragged)
    .on("end", dragended))
  .on("mouseover", showTooltip)
  .on("mouseout", hideTooltip);

node.append("circle")
  .attr("r", d => d.id === "center" ? 40 : 32)
  .attr("fill", "#fff")
  .attr("stroke", d => d.relationType ? relMap[Object.keys(relMap).find(k => relMap[k].type === d.relationType)].color : "#ff7979")
  .attr("stroke-width", 4);

const avatar = node.append("foreignObject")
  .attr("width", d => d.id === "center" ? 80 : 64)
  .attr("height", d => d.id === "center" ? 80 : 64)
  .attr("x", d => d.id === "center" ? -40 : -32)
  .attr("y", d => d.id === "center" ? -40 : -32);
avatar.append("xhtml:div").attr("class", "avatar-container")
  .html(d => {{
    const url = d.avatarReal || d.avatar || `https://ui-avatars.com/api/?name=${{encodeURIComponent(d.nickName || d.name || "玩家")}}&background=random&size=80`;
    return `<img src="${{url}}" class="avatar-image" onerror="this.src='https://via.placeholder.com/60?text=${{(d.nickName || d.name).slice(-2)}}'">`;
  }});

node.filter(d => d.id !== "center")
  .append("text").attr("dy", -12).attr("text-anchor", "middle")
  .attr("fill", d => relMap[Object.keys(relMap).find(k => relMap[k].type === d.relationType)].color)
  .attr("font-weight", "bold").text(d => d.relationType);
node.filter(d => d.id !== "center")
  .append("text").attr("dy", 45).attr("text-anchor", "middle")
  .attr("fill", "#ff6b6b").attr("font-size", 14).attr("font-weight", "bold")
  .text(d => d.intimacy);

function dragstarted(e, d) {{ if (!e.active) simulation.alphaTarget(.3); d.fx = d.x; d.fy = d.y; }}
function dragged(e, d) {{ d.fx = e.x; d.fy = e.y; }}
function dragended(e, d) {{ if (!e.active) simulation.alphaTarget(0); d.fx = null; d.fy = null; }}

simulation.on("tick", () => {{
  link.attr("x1", d => d.source.x).attr("y1", d => d.source.y)
      .attr("x2", d => d.target.x).attr("y2", d => d.target.y);
  linkText.attr("x", d => (d.source.x + d.target.x) / 2).attr("y", d => (d.source.y + d.target.y) / 2 + 3);
  node.attr("transform", d => `translate(${{d.x}},${{d.y}})`);
}});

svg.call(d3.zoom().scaleExtent([.5, 3]).on("zoom", e => container.attr("transform", e.transform)));

function showTooltip(e, d) {{
  const t = d3.select(".tooltip");
  t.html(`
    <div class="tooltip-header">
      <img src="${{d.avatarReal || d.avatar}}" class="tooltip-avatar" onerror="this.src='https://ui-avatars.com/api/?name=${{(d.nickName || d.name).slice(-2)}}&background=random&size=50'"/>
      <div>
        <div class="tooltip-name">${{d.nickName || d.name}}</div>
        <div class="tooltip-title">${{d.title || "无称号"}}</div>
      </div>
    </div>
    <div class="tooltip-info">
      <div>关系: <b style="color:${{relMap[Object.keys(relMap).find(k => relMap[k].type === d.relationType)].color}}">${{d.relationType || "自己"}}</b></div>
      <div>等级: ${{d.level}}</div>
      <div>战队: ${{d.clan || "无战队"}}</div>
      <div>亲密度: <b>${{d.intimacy || "无"}}</b></div>
      <div>性别: ${{d.gender || "保密"}}</div>
    </div>
  `).style("left", (e.pageX + 15) + "px").style("top", (e.pageY - 15) + "px").style("opacity", 1);
}}
function hideTooltip() {{ d3.select(".tooltip").style("opacity", 0); }}
</script>
</body>
</html>'''

        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            friend_count = len(friends_list)
            print(f"\n{GREEN}════════════════════════════════════════{NC}")
            print(f"{GREEN}✅ 关系图谱生成成功！{NC}")
            print(f"{CYAN}📁 输出文件: {output_file}{NC}")
            print(f"{CYAN}📊 好友数量: {friend_count} 人{NC}")
            print(f"{GREEN}════════════════════════════════════════{NC}")
            print(f"\n{YELLOW}💡 在浏览器中打开此HTML文件即可查看力导向图{NC}")
        except Exception as e:
            print(f"{RED}❌ 关系图谱生成失败: {e}{NC}")
    else:
        print(f"\n{YELLOW}已跳过关系图谱生成{NC}")

    input(f"\n{CYAN}按回车键返回主菜单...{NC}")

def query_latest_maps(rank_type, rank_name):
    print_header()
    print(f"{YELLOW}>>> 查询最新地图 ({rank_name}){NC}\n")
    session = get_session()
    if not session:
        print(f"{RED}❌ 获取Session失败{NC}")
        input(f"{CYAN}按回车键返回...{NC}")
        return

    rank_param = "all" if rank_type == "all" else rank_type
    url = "https://battlecraft.tuimotuimo.com/battlecraft/ugclevel/range2"
    headers = {
        "Cookie": COOKIE,
        "Auth": session,
        "Content-Type": "application/x-www-form-urlencoded",
        "ssn": SSN,
        "ver": VER,
    }
    data = {
        "start": "0",
        "count": str(MAP_COUNT),
        "idonly": "true",
        "filter": "latest",
        "rank": rank_param
    }
    try:
        resp = requests.post(url, headers=headers, data=data, timeout=10)
        resp.raise_for_status()
        range_data = resp.json()
        level_ids = range_data.get("data", {}).get("levelIds", [])
        if not level_ids:
            print(f"{RED}❌ 获取地图ID列表失败{NC}")
            input(f"{CYAN}按回车键返回...{NC}")
            return
        ids_str = ",".join(str(i) for i in level_ids)
        # 获取详情
        url2 = "https://battlecraft.tuimotuimo.com/battlecraft/ugclevel/getlist"
        data2 = {
            "ids": ids_str,
            "needBestPlayer": "false",
            "needMarkList": "false",
            "needAlbum": "false"
        }
        resp2 = requests.post(url2, headers=headers, data=data2, timeout=10)
        resp2.raise_for_status()
        levels = resp2.json().get("data", {}).get("levels", [])
        print(f"\n{GREEN}════════════════ 最新地图列表 ({rank_name}) ════════════════{NC}\n")
        if not levels:
            print("  ⚠️ 暂无数据")
        else:
            print(f"  {'序号':<4} {'地图名称':<20} {'地图码':<10} {'作者':<12} {'游玩':<8} {'点赞':<6} {'评论':<6}")
            print(f"  {'─'*85}")
            total_play = 0
            total_likes = 0
            total_comments = 0
            for idx, lev in enumerate(levels, 1):
                map_id = lev.get('id', 0)
                map_code = dec_to_base36(map_id)
                map_name = lev.get('name', '无名称')[:18]
                play_count = lev.get('playCount', 0)
                likes = lev.get('likes', 0)
                coments = lev.get('coments', 0)
                owner = lev.get('owner', {})
                author_name = owner.get('nickName', '未知')[:10]
                play_str = f"{play_count:,}" if play_count >= 1000 else str(play_count)
                print(f"  {idx:<4} {map_name:<20} {map_code:<10} {author_name:<12} {play_str:<8} {likes:<6} {coments:<6}")
                total_play += play_count
                total_likes += likes
                total_comments += coments
            print(f"\n   统计汇总")
            print(f"     共 {len(levels)} 个地图")
            print(f"     总游玩次数: {total_play:,}")
            print(f"     总点赞数: {total_likes}")
            print(f"     总评论数: {total_comments}")
        print(f"\n{CYAN}════════════════════════════════════════════════════════{NC}")
    except Exception as e:
        print(f"{RED}请求失败: {e}{NC}")
    input(f"\n{CYAN}按回车键返回菜单...{NC}")

def func_latest_maps():
    global MAP_COUNT
    while True:
        print_header()
        print(f"{YELLOW}>>> 最新地图查询{NC}\n")
        print(f"{GREEN}请选择难度类型：{NC}")
        print("  1. 所有难度")
        print("  2. 简单")
        print("  3. 中等")
        print("  4. 困难")
        print("  5. 超难")
        print("  6. 自定义查询数量（当前: {}）".format(MAP_COUNT))
        print("  0. 返回主菜单")
        choice = input("请选择 [0-6]: ").strip()
        if choice == "0":
            return
        elif choice == "1":
            query_latest_maps("all", "所有")
        elif choice == "2":
            query_latest_maps("easy", "简单")
        elif choice == "3":
            query_latest_maps("medium", "中等")
        elif choice == "4":
            query_latest_maps("hard", "困难")
        elif choice == "5":
            query_latest_maps("insane", "超难")
        elif choice == "6":
            new_count = input(f"{YELLOW}请输入新的查询数量 [1-100]: {NC}").strip()
            if new_count.isdigit() and 1 <= int(new_count) <= 100:
                MAP_COUNT = int(new_count)
                save_config()
                print(f"{GREEN}✅ 查询数量已设置为 {MAP_COUNT}{NC}")
            else:
                print(f"{RED}❌ 输入无效，请输入1-100之间的数字{NC}")
            time.sleep(0.3)
        else:
            print(f"{RED}无效选项{NC}")
            time.sleep(0.3)

def func_gold_mine():
    print_header()
    print(f"{YELLOW}>>> 金矿打工{NC}\n")
    map_code = input(f"{BLUE}请输入目标玩家的地图代码（例如：jskru）: {NC}").strip()
    if not map_code:
        print(f"{RED}❌ 未输入地图代码{NC}")
        input(f"{CYAN}按回车键返回主菜单...{NC}")
        return
    map_id = base36_to_dec(map_code)
    if map_id is None:
        print(f"{RED}❌ 无效的地图代码{NC}")
        input(f"{CYAN}按回车键返回主菜单...{NC}")
        return
    print(f"{GREEN}✓ 地图ID: {map_id}{NC}")

    session = get_session()
    if not session:
        print(f"{RED}❌ 获取 Session 失败{NC}")
        input(f"{CYAN}按回车键返回主菜单...{NC}")
        return
    print(f"{GREEN}✓ Session 获取成功{NC}")

    # 查询作者
    url_map = "https://battlecraft.tuimotuimo.com/battlecraft/ugclevel/get"
    headers = {
        "Auth": session,
        "ssn": SSN,
        "ver": VER,
        "Cookie": COOKIE,
        "Content-Type": "application/x-www-form-urlencoded",
    }
    data_map = {"id": str(map_id), "needMarkList": "false"}
    try:
        resp = requests.post(url_map, headers=headers, data=data_map, timeout=10)
        resp.raise_for_status()
        map_data = resp.json()
        friend_id = map_data.get("data", {}).get("level", {}).get("owner", {}).get("userid")
        if not friend_id:
            print(f"{RED}❌ 无法获取作者信息{NC}")
            input(f"{CYAN}按回车键返回主菜单...{NC}")
            return
        print(f"{GREEN}✓ 作者ID: {friend_id}{NC}")
    except Exception as e:
        print(f"{RED}❌ 查询地图失败: {e}{NC}")
        input(f"{CYAN}按回车键返回主菜单...{NC}")
        return

    # 打工
    url_work = "https://battlecraft.tuimotuimo.com/battlecraft/bank/startwork"
    data_work = {"friendId": friend_id}
    try:
        resp = requests.post(url_work, headers=headers, data=data_work, timeout=10)
        resp.raise_for_status()
        work_resp = resp.json()
        code = work_resp.get("code", -1)
        if code == 0:
            nick = work_resp.get("data", {}).get("receiver", {}).get("nickName", "")
            print(f"{GREEN}════════════════════════════════════════{NC}")
            print(f"{GREEN}✅ 打工成功！{NC}")
            print(f"   你正在为 {CYAN}{nick}{NC} 的金矿工作")
            print(f"{GREEN}════════════════════════════════════════{NC}")

            # 是否使用额外账号
            extra = input(f"\n{YELLOW}是否使用其他3个账号也为此玩家打工？ [y/n] (默认 n): {NC}").strip().lower()
            if extra == 'y':
                print(f"\n{BLUE}使用额外3个账号为 {nick} 打工...{NC}")
                success = 0
                fail = 0
                for idx, acc in enumerate(EXTRA_ACCOUNTS, 1):
                    print(f"\n{BLUE}[账号 {idx}] 获取会话...{NC}")
                    extra_session = get_session(jwt=acc["jwt"], device_id=acc["device_id"])
                    if not extra_session:
                        print(f"{RED}  ❌ 账号 {idx} 获取Session失败{NC}")
                        fail += 1
                        continue
                    print(f"{GREEN}  ✓ 账号 {idx} Session获取成功{NC}")
                    try:
                        resp2 = requests.post(url_work, headers={"Auth": extra_session, "ssn": SSN, "ver": VER, "Cookie": COOKIE, "Content-Type": "application/x-www-form-urlencoded"}, data={"friendId": friend_id}, timeout=10)
                        resp2.raise_for_status()
                        res2 = resp2.json()
                        if res2.get("code") == 0:
                            extra_nick = res2.get("data", {}).get("receiver", {}).get("nickName", "")
                            print(f"{GREEN}  ✅ 账号 {idx} 打工成功！为 {extra_nick} 打工{NC}")
                            success += 1
                        else:
                            print(f"{RED}  ❌ 账号 {idx} 打工失败: {res2.get('msg', '未知错误')}{NC}")
                            fail += 1
                    except Exception as e:
                        print(f"{RED}  ❌ 账号 {idx} 请求异常: {e}{NC}")
                        fail += 1
                    time.sleep(0.5)
                print(f"\n{GREEN}════════════════════════════════════════{NC}")
                print(f"{GREEN}📊 额外打工统计：{NC}")
                print(f"   ✅ 成功: {GREEN}{success}{NC} 个账号")
                print(f"   ❌ 失败: {RED}{fail}{NC} 个账号")
                print(f"{GREEN}════════════════════════════════════════{NC}")
        else:
            print(f"{RED}❌ 打工失败：{work_resp.get('msg', '未知错误')}{NC}")
    except Exception as e:
        print(f"{RED}❌ 打工请求失败: {e}{NC}")

    input(f"\n{CYAN}按回车键返回主菜单...{NC}")

def func_map_comment():
    print_header()
    print(f"{YELLOW}>>> 地图评论工具（支持stamp）{NC}\n")
    map_code = input(f"{BLUE}请输入地图代码（例如：jskru），输入 q 退出: {NC}").strip()
    if map_code.lower() == 'q':
        print(f"{CYAN}已取消{NC}")
        input(f"{CYAN}按回车键返回主菜单...{NC}")
        return
    if not map_code:
        print(f"{RED}❌ 地图代码不能为空{NC}")
        input(f"{CYAN}按回车键返回主菜单...{NC}")
        return
    map_id = base36_to_dec(map_code)
    if map_id is None:
        print(f"{RED}❌ 无效的地图代码{NC}")
        input(f"{CYAN}按回车键返回主菜单...{NC}")
        return
    print(f"{GREEN}✓ 地图ID: {map_id}{NC}")

    session = get_session()
    if not session:
        print(f"{RED}❌ 获取Session失败{NC}")
        input(f"{CYAN}按回车键返回主菜单...{NC}")
        return
    print(f"{GREEN}✓ Session获取成功{NC}")

    # 评论类型
    print(f"\n{YELLOW}请选择评论类型:{NC}")
    print("  1. 使用预设表情/短语 (stamp)")
    print("  2. 自定义文本 (text)")
    type_choice = input("请输入 [1/2]: ").strip()
    comment_type = ""
    stamp_content = ""
    if type_choice == "1":
        comment_type = "stamp"
        print(f"\n{YELLOW}请选择stamp内容:{NC}")
        print("  1. 随机选择 (0001-0004)")
        print("  2. 0001")
        print("  3. 0002")
        print("  4. 0003")
        print("  5. 0004")
        stamp_choice = input("请输入 [1-5]: ").strip()
        if stamp_choice == "1":
            stamp_content = f"{random.randint(1,4):04d}"
        elif stamp_choice in ["2","3","4","5"]:
            stamp_content = f"{int(stamp_choice)-1:04d}"
        else:
            print(f"{RED}无效，使用随机{NC}")
            stamp_content = f"{random.randint(1,4):04d}"
        print(f"{GREEN}✓ 将发送 stamp: {stamp_content}{NC}")
    elif type_choice == "2":
        comment_type = "text"
    else:
        print(f"{RED}❌ 无效选择{NC}")
        input(f"{CYAN}按回车键返回主菜单...{NC}")
        return

    # 是否点赞
    like_choice = input(f"\n{YELLOW}是否顺便点赞该地图？ [y/n] (默认 y): {NC}").strip().lower()
    like_flag = "true" if like_choice != 'n' else "false"
    if like_flag == "true":
        print(f"{BLUE}将同时点赞{NC}")
    else:
        print(f"{BLUE}将不点赞{NC}")

    # 评论循环
    while True:
        if comment_type == "stamp":
            final_content = stamp_content
        else:
            text_content = input(f"\n{YELLOW}请输入评论内容（不超过20字）: {NC}").strip()
            if not text_content:
                print(f"{RED}❌ 评论内容不能为空{NC}")
                continue
            if len(text_content) > 20:
                print(f"{RED}❌ 评论内容超过20字（当前{len(text_content)}字）{NC}")
                continue
            final_content = text_content
            print(f"{GREEN}✓ 评论内容长度: {len(text_content)}/20{NC}")

        # 发送评论
        url_comment = "https://battlecraft.tuimotuimo.com/battlecraft/ugclevel/addcomment"
        headers = {
            "Auth": session,
            "ssn": SSN,
            "ver": VER,
            "Cookie": COOKIE,
            "Content-Type": "application/x-www-form-urlencoded",
        }
        data_comment = {
            "id": str(map_id),
            "type": comment_type,
            "content": final_content,
            "like": like_flag,
        }
        try:
            resp = requests.post(url_comment, headers=headers, data=data_comment, timeout=10)
            resp.raise_for_status()
            result = resp.json()
            code = result.get("code", -1)
            msg = result.get("msg", "未知错误")
            print(f"\n{GREEN}═══════════════════════════════════════{NC}")
            if code == 0:
                print(f"{GREEN}✅ 评论成功！{NC}")
                comment_id = result.get("data", {}).get("comment", {}).get("id", "")
                if comment_id:
                    print(f"{CYAN}评论ID: {comment_id}{NC}")
                print(f"{CYAN}地图 {map_code} 的评论已发布{NC}")
                print(f"{GREEN}═══════════════════════════════════════{NC}")
                break
            elif code == 1105:
                print(f"{RED}❌ 评论失败：您已评论过该地图{NC}")
                print(f"{YELLOW}每张地图只能评论一次，无法继续{NC}")
                print(f"{GREEN}═══════════════════════════════════════{NC}")
                break
            elif code == 1103:
                print(f"{RED}❌ 评论失败：包含违规词{NC}")
                print(f"{YELLOW}请修改评论内容后重试{NC}")
                continue
            elif code == 1001:
                print(f"{RED}❌ 评论失败：参数无效{NC}")
                print(f"{YELLOW}可能原因：评论内容超长或包含非法字符{NC}")
                continue
            else:
                print(f"{RED}❌ 评论失败 (code: {code}){NC}")
                print(f"{YELLOW}错误信息: {msg}{NC}")
                retry = input(f"{YELLOW}是否重试？[y/n] (默认 n): {NC}").strip().lower()
                if retry != 'y':
                    break
        except Exception as e:
            print(f"{RED}❌ 请求失败: {e}{NC}")
            break

    input(f"\n{CYAN}按回车键返回主菜单...{NC}")

def func_broadcast_map():
    print_header()
    print(f"{YELLOW}>>> 广播地图工具{NC}\n")
    map_code = input(f"{BLUE}请输入地图代码（例如：jskru）: {NC}").strip()
    if not map_code:
        print(f"{RED}❌ 未输入地图代码{NC}")
        input(f"{CYAN}按回车键返回主菜单...{NC}")
        return
    map_id = base36_to_dec(map_code)
    if map_id is None:
        print(f"{RED}❌ 无效的地图代码{NC}")
        input(f"{CYAN}按回车键返回主菜单...{NC}")
        return
    print(f"{GREEN}✓ 地图ID: {map_id}{NC}")

    session = get_session()
    if not session:
        print(f"{RED}❌ 获取Session失败{NC}")
        input(f"{CYAN}按回车键返回主菜单...{NC}")
        return
    print(f"{GREEN}✓ Session获取成功{NC}")

    # 领取免费喇叭
    url_claim = "https://battlecraft.tuimotuimo.com/battlecraft/horn/claimfree"
    headers = {
        "Auth": session,
        "ssn": SSN,
        "ver": VER,
        "Cookie": COOKIE,
        "Content-Type": "application/x-www-form-urlencoded",
    }
    data_claim = {"claimsCount": "1", "all": "false"}
    try:
        resp = requests.post(url_claim, headers=headers, data=data_claim, timeout=10)
        resp.raise_for_status()
        claim_resp = resp.json()
        if claim_resp.get("code") == 0:
            horn_count = claim_resp.get("data", {}).get("userrole", {}).get("horn", 0)
            print(f"{GREEN}✓ 领取成功，当前喇叭数量: {horn_count}{NC}")
        else:
            print(f"{YELLOW}⚠️ 领取失败: {claim_resp.get('msg', '未知错误')} (可能今日已领取过){NC}")
    except Exception as e:
        print(f"{YELLOW}⚠️ 领取喇叭请求异常: {e}{NC}")

    # 广播
    url_broadcast = "https://battlecraft.tuimotuimo.com/battlecraft/chatroom/sendugclevel"
    data_broadcast = {"ugcLvId": str(map_id), "v2": "true"}
    try:
        resp = requests.post(url_broadcast, headers=headers, data=data_broadcast, timeout=10)
        resp.raise_for_status()
        broadcast_resp = resp.json()
        code = broadcast_resp.get("code", -1)
        if code == 0:
            print(f"{GREEN}═══════════════════════════════════════{NC}")
            print(f"{GREEN}✅ 广播成功！{NC}")
            print(f"{CYAN}地图 {map_code} 已发送到首页{NC}")
            print(f"{GREEN}═══════════════════════════════════════{NC}")
        elif code == 2014:
            print(f"{RED}❌ 广播失败，请求错误c2014{NC}")
        else:
            print(f"{RED}❌ 广播失败: {broadcast_resp.get('msg', '未知错误')}{NC}")
    except Exception as e:
        print(f"{RED}❌ 广播请求异常: {e}{NC}")

    input(f"\n{CYAN}按回车键返回主菜单...{NC}")

def func_fetch_nicknames():
    print_header()
    print(f"{YELLOW}>>> 派对制造批量拉取昵称{NC}\n")
    session = get_session()
    if not session:
        print(f"{RED}❌ 获取Session失败{NC}")
        input(f"{CYAN}按回车键返回主菜单...{NC}")
        return
    print(f"{GREEN}✅ Session获取成功{NC}\n")

    url = "https://battlecraft.tuimotuimo.com/battlecraft/account/autoname"
    headers = {
        "Cookie": COOKIE,
        "Auth": session,
        "Content-Type": "application/x-www-form-urlencoded",
        "ssn": SSN,
        "ver": VER,
    }
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if data.get("code") != 0:
            print(f"{RED}❌ API返回错误: {data.get('msg', '未知错误')}{NC}")
        else:
            nicknames = data.get("data", {}).get("nickNames", [])
            if nicknames:
                print(f"{GREEN}════════════════ 随机昵称列表 ════════════════{NC}\n")
                for idx, name in enumerate(nicknames, 1):
                    print(f"  {idx:>2}. {name}")
                # 保存到文件
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                output_file = os.path.join(CONFIG_DIR, f"nicknames_{timestamp}.txt")
                with open(output_file, 'w', encoding='utf-8') as f:
                    for name in nicknames:
                        f.write(name + '\n')
                print(f"\n  💾 已保存到: {output_file}")
            else:
                print("⚠️ 未获取到昵称")
    except Exception as e:
        print(f"{RED}❌ 请求失败: {e}{NC}")

    input(f"\n{CYAN}按回车键返回主菜单...{NC}")

# ========== 主程序 ==========
def main():
    load_config()
    while True:
        print_header()
        print_menu()
        choice = input("请选择功能: ").strip()
        if choice in ['A', 'a']:
            func_show_ip()
        elif choice in ['B', 'b']:
            func_device_setup()
        elif choice in ['C', 'c']:
            func_game_version()
        elif choice in ['D', 'd']:
            func_game_notice()
        elif choice in ['E', 'e']:
            func_github_notice()
        elif choice in ['F', 'f']:
            func_toolbox_version()
        elif choice == '1':
            func_room_list()
        elif choice == '2':
            func_map_query()
        elif choice == '3':
            func_rank_query()
        elif choice == '4':
            func_player_info()
        elif choice == '5':
            func_latest_maps()
        elif choice == '6':
            func_gold_mine()
        elif choice == '7':
            func_map_comment()
        elif choice == '8':
            func_broadcast_map()
        elif choice == '9':
            func_fetch_nicknames()
        elif choice == '0':
            print(f"\n{GREEN}感谢使用派对制造工具箱！{NC}")
            save_config()
            sys.exit(0)
        else:
            print(f"{RED}无效选项，请重新选择{NC}")
            time.sleep(0.3)

if __name__ == "__main__":
    main()