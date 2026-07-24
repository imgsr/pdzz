#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
派对制造工具箱 Web 版
功能：地图查询、玩家信息+关系图谱、金矿打工、地图评论、广播地图
"""

import os
import json
import time
import random
import secrets
import base64
from pathlib import Path
from urllib.parse import urlencode
from flask import Flask, request, jsonify, send_file, send_from_directory
from flask_cors import CORS
import requests

app = Flask(__name__)
CORS(app)

# ========== 配置 ==========
CONFIG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
os.makedirs(CONFIG_DIR, exist_ok=True)
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")
GRAPH_DIR = os.path.join(CONFIG_DIR, "graphs")
os.makedirs(GRAPH_DIR, exist_ok=True)

# ========== 默认配置 ==========
DEFAULT_CONFIG = {
    "jwt": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJkZXZJZCI6IjMzOWY3YWJhZTg2OGI3ZjBhODMzODc3YjBkNWQ0NjQ1XG5kYTNkYzlhOTk5Mjg5OGY5MDk2YWI5MjAyOTVkM2ZhZSIsImZsYWciOiJiZGY2IiwiZnJvbSI6InRhcHRhcCIsImx0IjoiZ3Vlc3QiLCJzc24iOiI1Mjk5IiwidXNlcmlkIjoiNjlmNTk5MDNlOGQ1YjU1YmI0ZWViYjAyIiwidiI6IjAifQ.RHQ1EK0pEwiXBTILUyLNgHCetsfO57fUmJtcMGPqG-A",
    "device_id": "339f7abae868b7f0a833877b0d5d46454a3dc9a9992898f9096ab920295d3fae",
    "ssn": "3c05",
    "ver": "2.1.93",
    "cookie": "SERVERID=769e7e1294f37fd70e4a8fd5d4a4a403|1774672107|1774600237"
}

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

# ========== 配置管理 ==========
def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return DEFAULT_CONFIG.copy()

def save_config(config):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)

# ========== 辅助函数 ==========
def dec_to_base36(num):
    if num == 0:
        return "0"
    digits = "0123456789abcdefghijklmnopqrstuvwxyz"
    res = ""
    n = num
    while n > 0:
        n, rem = divmod(n, 36)
        res = digits[rem] + res
    return res

def base36_to_dec(s):
    if not s:
        return None
    try:
        return int(s.lower(), 36)
    except ValueError:
        return None

def get_session(config):
    url = "https://battlecraft.tuimotuimo.com/battlecraft/account/loginsession"
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "*/*",
        "ssn": config.get("ssn", DEFAULT_CONFIG["ssn"]),
        "ver": config.get("ver", DEFAULT_CONFIG["ver"]),
        "Cookie": config.get("cookie", DEFAULT_CONFIG["cookie"]),
    }
    data = {
        "timezone": "8",
        "v2": "true",
        "v3": "true",
        "session": config.get("jwt", DEFAULT_CONFIG["jwt"]),
        "deviceId": config.get("device_id", DEFAULT_CONFIG["device_id"]),
        "tutorialType": "ugc"
    }
    try:
        resp = requests.post(url, headers=headers, data=data, timeout=10)
        resp.raise_for_status()
        result = resp.json()
        session = result.get("data", {}).get("sessionid")
        return session
    except Exception as e:
        return None

def get_headers(session, config):
    return {
        "Auth": session,
        "ssn": config.get("ssn", DEFAULT_CONFIG["ssn"]),
        "ver": config.get("ver", DEFAULT_CONFIG["ver"]),
        "Cookie": config.get("cookie", DEFAULT_CONFIG["cookie"]),
        "Content-Type": "application/x-www-form-urlencoded",
    }

# ========== API: 配置 ==========
@app.route('/api/config', methods=['GET', 'POST'])
def handle_config():
    if request.method == 'GET':
        config = load_config()
        # 隐藏敏感信息部分显示
        safe_config = {
            "jwt": config.get("jwt", "")[:20] + "...",
            "device_id": config.get("device_id", ""),
            "ssn": config.get("ssn", ""),
            "ver": config.get("ver", ""),
            "cookie": config.get("cookie", "")[:30] + "..."
        }
        return jsonify({"success": True, "data": safe_config})
    
    # POST - 更新配置
    data = request.json
    config = load_config()
    if "jwt" in data and data["jwt"]:
        config["jwt"] = data["jwt"]
    if "device_id" in data and data["device_id"]:
        config["device_id"] = data["device_id"]
    if "ssn" in data and data["ssn"]:
        config["ssn"] = data["ssn"]
    if "ver" in data and data["ver"]:
        config["ver"] = data["ver"]
    if "cookie" in data and data["cookie"]:
        config["cookie"] = data["cookie"]
    save_config(config)
    return jsonify({"success": True, "message": "配置已更新"})

# ========== API: 功能2 - 地图查询 ==========
@app.route('/api/map/query', methods=['POST'])
def map_query():
    data = request.json
    map_code = data.get('map_code', '').strip()
    page = data.get('page', 1)
    page_size = data.get('page_size', 5)
    
    if not map_code:
        return jsonify({"success": False, "error": "地图代码不能为空"})
    
    map_id = base36_to_dec(map_code)
    if map_id is None or map_id == 0:
        return jsonify({"success": False, "error": "地图代码无效"})
    
    config = load_config()
    session = get_session(config)
    if not session:
        return jsonify({"success": False, "error": "获取Session失败"})
    
    headers = get_headers(session, config)
    
    # 获取地图详情
    url = "https://battlecraft.tuimotuimo.com/battlecraft/ugclevel/get"
    try:
        resp = requests.post(url, headers=headers, data={"id": str(map_id), "needMarkList": "false"}, timeout=10)
        resp.raise_for_status()
        map_data = resp.json()
        if map_data.get("code") != 0:
            return jsonify({"success": False, "error": f"查询失败，错误码: {map_data.get('code')}"})
        
        level = map_data.get("data", {}).get("level", {})
        owner = level.get("owner", {})
        clan = owner.get("clan", {})
        
        # 获取评论
        start = (page - 1) * page_size
        url_comment = "https://battlecraft.tuimotuimo.com/battlecraft/ugclevel/getcomments"
        resp_comment = requests.post(url_comment, headers=headers, data={"id": str(map_id), "start": str(start), "count": str(page_size)}, timeout=10)
        resp_comment.raise_for_status()
        comments_data = resp_comment.json()
        comments = comments_data.get("data", {}).get("comments", [])
        
        # 构建返回数据
        result = {
            "map": {
                "id": level.get("id"),
                "code": dec_to_base36(level.get("id", 0)),
                "name": level.get("name", "无"),
                "timestamp": level.get("timestamp", 0),
                "status": level.get("status", 0),
                "inTrash": level.get("inTrash", False),
                "playCount": level.get("playCount", 0),
                "finishCount": level.get("finishCount", 0),
                "likes": level.get("likes", 0),
                "dislike": level.get("dislike", 0),
                "bestScore": level.get("bestScore", 0),
                "ratings": level.get("ratings", 0),
                "pvpOnly": level.get("pvpOnly", False),
                "needAllStar": level.get("needAllStar", False),
                "respawnType": level.get("respawnType", 0),
                "tags": level.get("tags", []),
                "owner": {
                    "userid": owner.get("userid"),
                    "nickName": owner.get("nickName", "未知"),
                    "userShortId": owner.get("userShortId"),
                    "dan": owner.get("dan", 0),
                    "level": owner.get("level", 0),
                    "gender": owner.get("gender", 0),
                    "title": owner.get("title", ""),
                    "province": owner.get("province", ""),
                    "city": owner.get("city", ""),
                    "clan": clan.get("name", "无战队")
                },
                "top": level.get("top", [])[:3]
            },
            "comments": [
                {
                    "id": c.get("id"),
                    "type": c.get("type"),
                    "content": c.get("content"),
                    "ts": c.get("ts", 0),
                    "player": {
                        "nickName": c.get("player", {}).get("nickName", "未知"),
                        "userShortId": c.get("player", {}).get("userShortId")
                    }
                }
                for c in comments
            ],
            "page": page,
            "page_size": page_size,
            "has_more": len(comments) == page_size
        }
        return jsonify({"success": True, "data": result})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

# ========== API: 功能4 - 玩家信息 + 关系图谱 ==========
@app.route('/api/player/info', methods=['POST'])
def player_info():
    data = request.json
    map_code = data.get('map_code', '').strip()
    
    if not map_code:
        return jsonify({"success": False, "error": "地图代码不能为空"})
    
    map_id = base36_to_dec(map_code)
    if map_id is None or map_id == 0:
        return jsonify({"success": False, "error": "地图代码无效"})
    
    config = load_config()
    session = get_session(config)
    if not session:
        return jsonify({"success": False, "error": "获取Session失败"})
    
    headers = get_headers(session, config)
    
    # 获取地图信息提取作者ID
    url_map = "https://battlecraft.tuimotuimo.com/battlecraft/ugclevel/get"
    try:
        resp = requests.post(url_map, headers=headers, data={"id": str(map_id), "needMarkList": "false"}, timeout=10)
        resp.raise_for_status()
        map_data = resp.json()
        author_id = map_data.get("data", {}).get("level", {}).get("owner", {}).get("userid")
        if not author_id:
            return jsonify({"success": False, "error": "无法获取作者信息"})
    except Exception as e:
        return jsonify({"success": False, "error": f"获取地图信息失败: {e}"})
    
    # 获取玩家详细信息
    url_user = "https://battlecraft.tuimotuimo.com/battlecraft/userrole/detailinfo"
    try:
        resp = requests.post(url_user, headers=headers, data={"userId": author_id}, timeout=10)
        resp.raise_for_status()
        user_data = resp.json()
    except Exception as e:
        return jsonify({"success": False, "error": f"获取玩家信息失败: {e}"})
    
    # 获取关系图谱
    url_relation = "https://battlecraft.tuimotuimo.com/battlecraft/relation/info"
    try:
        resp_rel = requests.post(url_relation, headers=headers, data={"frdId": author_id}, timeout=10)
        resp_rel.raise_for_status()
        relation_data = resp_rel.json()
    except Exception as e:
        relation_data = {}
    
    # 解析玩家信息
    user = user_data.get("data", {})
    basic = user.get("basic", {})
    ugc_info = user.get("ugcInfo", {})
    honesty = user.get("honesty", {})
    userlevel = user.get("userlevel", {})
    clan = basic.get("clan", {})
    
    gender_map = {1: '男', 2: '女', 0: '保密'}
    
    # 解析关系
    relations = relation_data.get("data", {}).get("relation", {}).get("relations", {})
    rel_type_map = {
        "0001": {"name": "CP", "icon": "💕", "color": "#ff9a9e"},
        "0002": {"name": "师父", "icon": "👨‍🏫", "color": "#6ecb63"},
        "0003": {"name": "徒弟", "icon": "👨‍🎓", "color": "#4da6ff"},
        "0004": {"name": "搭档", "icon": "🤝", "color": "#ffd166"},
        "0005": {"name": "闺蜜", "icon": "👭", "color": "#db4dff"},
        "0006": {"name": "基友", "icon": "👬", "color": "#5e60ce"}
    }
    
    friend_list = []
    for rel_key, rel_info in relations.items():
        rel_type = rel_type_map.get(rel_key, {}).get("name", rel_key)
        rel_color = rel_type_map.get(rel_key, {}).get("color", "#999")
        for f in rel_info.get("friends", []):
            avatar = f.get("avatarUrl", "")
            if not avatar or avatar.startswith("avatar://"):
                avatar = f"https://ui-avatars.com/api/?name={f.get('nickName', '玩家')}&background=random&size=80"
            friend_list.append({
                "id": f"f{f.get('userShortId', '')}",
                "nickName": f.get("nickName", "未知"),
                "avatarUrl": avatar,
                "level": f.get("level", 0),
                "gender": f.get("gender", 0),
                "intimacy": f.get("intimacy", 0),
                "clan": f.get("clan", {}).get("name", ""),
                "relationType": rel_type,
                "relationColor": rel_color,
                "relationKey": rel_key
            })
    
    result = {
        "player": {
            "userid": basic.get("userid"),
            "nickName": basic.get("nickName", "未知"),
            "userShortId": basic.get("userShortId"),
            "gender": gender_map.get(basic.get("gender", 0), "保密"),
            "level": basic.get("level", 0),
            "dan": basic.get("dan", 0),
            "province": basic.get("province", ""),
            "city": basic.get("city", ""),
            "clan": clan.get("name", "无战队"),
            "title": basic.get("title", ""),
            "avatarUrl": basic.get("avatarUrl", ""),
            "createdAt": basic.get("createdAt", 0),
            "honesty": honesty.get("honesty", 0),
            "rank": basic.get("rank", 0),
            "expCreative": userlevel.get("exp", {}).get("creative", 0),
            "expSkill": userlevel.get("exp", {}).get("skill", 0),
            "expPvp": userlevel.get("exp", {}).get("pvp", 0),
            "expActive": userlevel.get("exp", {}).get("active", 0),
            "creativeRank": basic.get("expRank", {}).get("creative", 0),
            "skillRank": basic.get("expRank", {}).get("skill", 0),
            "maps": [dec_to_base36(mid) for mid in ugc_info.get("ids", [])[:20]]
        },
        "relations": friend_list,
        "relationTypes": rel_type_map
    }
    
    return jsonify({"success": True, "data": result})

# ========== API: 功能4 - 生成并下载关系图谱 ==========
@app.route('/api/player/graph', methods=['POST'])
def generate_graph():
    data = request.json
    player = data.get('player', {})
    relations = data.get('relations', [])
    
    if not player:
        return jsonify({"success": False, "error": "玩家数据为空"})
    
    # 生成HTML
    html = generate_graph_html(player, relations)
    
    # 保存文件
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    filename = f"关系图谱_{player.get('nickName', 'unknown')}_{timestamp}.html"
    filepath = os.path.join(GRAPH_DIR, filename)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(html)
    
    return jsonify({
        "success": True,
        "filename": filename,
        "url": f"/api/graph/download/{filename}"
    })

@app.route('/api/graph/download/<filename>')
def download_graph(filename):
    return send_from_directory(GRAPH_DIR, filename, as_attachment=True)

def generate_graph_html(player, relations):
    """生成关系图谱HTML"""
    name = player.get("nickName", "未知")
    avatar = player.get("avatarUrl", "")
    if not avatar or avatar.startswith("avatar://"):
        avatar = f"https://ui-avatars.com/api/?name={name}&background=random&size=80"
    
    level = player.get("level", 0)
    title = player.get("title", "")
    clan = player.get("clan", "")
    gender = player.get("gender", "保密")
    
    # 构建关系类型映射
    rel_types = {
        "CP": {"color": "#ff9a9e"},
        "师父": {"color": "#6ecb63"},
        "徒弟": {"color": "#4da6ff"},
        "搭档": {"color": "#ffd166"},
        "闺蜜": {"color": "#db4dff"},
        "基友": {"color": "#5e60ce"}
    }
    
    import json
    rel_json = json.dumps(relations, ensure_ascii=False)
    player_json = json.dumps({
        "id": "center",
        "name": name,
        "avatar": avatar,
        "level": level,
        "gender": gender,
        "title": title,
        "clan": clan
    }, ensure_ascii=False)
    
    html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>{name}的关系图谱</title>
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
      <img class="user-avatar" src="{avatar}" onerror="this.src='https://ui-avatars.com/api/?name={name}&background=random&size=80'">
      <div class="user-info">
        <h2>{name}</h2>
        <div class="user-title">{title}</div>
        <div class="clan-info">{clan}</div>
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
const me = {player_json};
const relations = {rel_json};

const relMap = {{
  "CP": {{ color: "#ff9a9e" }},
  "师父": {{ color: "#6ecb63" }},
  "徒弟": {{ color: "#4da6ff" }},
  "搭档": {{ color: "#ffd166" }},
  "闺蜜": {{ color: "#db4dff" }},
  "基友": {{ color: "#5e60ce" }}
}};

const nodes = [me];
const links = [];

relations.forEach(f => {{
  const avatarReal = f.avatarUrl && !f.avatarUrl.startsWith("avatar://") && f.avatarUrl !== "" ? f.avatarUrl : `https://ui-avatars.com/api/?name=${{encodeURIComponent(f.nickName||"玩家")}}&background=random&size=80`;
  nodes.push({{
    ...f,
    nickName: f.nickName,
    avatarReal,
    intimacy: f.intimacy,
    relationType: f.relationType,
    gender: f.gender === 0 ? "保密" : f.gender === 1 ? "男" : "女",
    clan: f.clan || "无战队"
  }});
  links.push({{ source: me.id, target: f.id, relationType: f.relationType, color: f.relationColor, value: f.intimacy }});
}});

// 背景装饰
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
  .attr("stroke", d => d.relationType ? relMap[d.relationType].color : "#ff7979")
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
  .attr("fill", d => relMap[d.relationType].color)
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
      <div>关系: <b style="color:${{relMap[d.relationType].color}}">${{d.relationType || "自己"}}</b></div>
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
    return html

# ========== API: 功能6 - 金矿打工 ==========
@app.route('/api/goldmine/work', methods=['POST'])
def goldmine_work():
    data = request.json
    map_code = data.get('map_code', '').strip()
    use_extra = data.get('use_extra', False)
    
    if not map_code:
        return jsonify({"success": False, "error": "地图代码不能为空"})
    
    map_id = base36_to_dec(map_code)
    if map_id is None or map_id == 0:
        return jsonify({"success": False, "error": "地图代码无效"})
    
    config = load_config()
    session = get_session(config)
    if not session:
        return jsonify({"success": False, "error": "获取Session失败"})
    
    headers = get_headers(session, config)
    
    # 查询作者
    url_map = "https://battlecraft.tuimotuimo.com/battlecraft/ugclevel/get"
    try:
        resp = requests.post(url_map, headers=headers, data={"id": str(map_id), "needMarkList": "false"}, timeout=10)
        resp.raise_for_status()
        map_data = resp.json()
        friend_id = map_data.get("data", {}).get("level", {}).get("owner", {}).get("userid")
        if not friend_id:
            return jsonify({"success": False, "error": "无法获取作者信息"})
    except Exception as e:
        return jsonify({"success": False, "error": f"查询地图失败: {e}"})
    
    # 打工
    url_work = "https://battlecraft.tuimotuimo.com/battlecraft/bank/startwork"
    result = {"main": None, "extra": []}
    
    try:
        resp = requests.post(url_work, headers=headers, data={"friendId": friend_id}, timeout=10)
        resp.raise_for_status()
        work_resp = resp.json()
        if work_resp.get("code") == 0:
            nick = work_resp.get("data", {}).get("receiver", {}).get("nickName", "")
            result["main"] = {"success": True, "nick": nick}
        else:
            result["main"] = {"success": False, "error": work_resp.get("msg", "未知错误")}
    except Exception as e:
        result["main"] = {"success": False, "error": str(e)}
    
    # 额外账号
    if use_extra and result["main"].get("success"):
        for idx, acc in enumerate(EXTRA_ACCOUNTS, 1):
            extra_session = get_session(acc)
            if not extra_session:
                result["extra"].append({"index": idx, "success": False, "error": "获取Session失败"})
                continue
            extra_headers = {
                "Auth": extra_session,
                "ssn": config.get("ssn", DEFAULT_CONFIG["ssn"]),
                "ver": config.get("ver", DEFAULT_CONFIG["ver"]),
                "Cookie": config.get("cookie", DEFAULT_CONFIG["cookie"]),
                "Content-Type": "application/x-www-form-urlencoded",
            }
            try:
                resp2 = requests.post(url_work, headers=extra_headers, data={"friendId": friend_id}, timeout=10)
                resp2.raise_for_status()
                res2 = resp2.json()
                if res2.get("code") == 0:
                    extra_nick = res2.get("data", {}).get("receiver", {}).get("nickName", "")
                    result["extra"].append({"index": idx, "success": True, "nick": extra_nick})
                else:
                    result["extra"].append({"index": idx, "success": False, "error": res2.get("msg", "未知错误")})
            except Exception as e:
                result["extra"].append({"index": idx, "success": False, "error": str(e)})
            time.sleep(0.3)
    
    return jsonify({"success": True, "data": result})

# ========== API: 功能7 - 地图评论 ==========
@app.route('/api/map/comment', methods=['POST'])
def map_comment():
    data = request.json
    map_code = data.get('map_code', '').strip()
    comment_type = data.get('comment_type', 'text')  # text 或 stamp
    content = data.get('content', '').strip()
    like = data.get('like', True)
    
    if not map_code:
        return jsonify({"success": False, "error": "地图代码不能为空"})
    
    map_id = base36_to_dec(map_code)
    if map_id is None or map_id == 0:
        return jsonify({"success": False, "error": "地图代码无效"})
    
    if comment_type == 'text' and not content:
        return jsonify({"success": False, "error": "评论内容不能为空"})
    if comment_type == 'text' and len(content) > 20:
        return jsonify({"success": False, "error": "评论内容不能超过20字"})
    
    if comment_type == 'stamp':
        if not content:
            content = f"{random.randint(1, 4):04d}"
    
    config = load_config()
    session = get_session(config)
    if not session:
        return jsonify({"success": False, "error": "获取Session失败"})
    
    headers = get_headers(session, config)
    
    url_comment = "https://battlecraft.tuimotuimo.com/battlecraft/ugclevel/addcomment"
    data_comment = {
        "id": str(map_id),
        "type": comment_type,
        "content": content,
        "like": "true" if like else "false",
    }
    try:
        resp = requests.post(url_comment, headers=headers, data=data_comment, timeout=10)
        resp.raise_for_status()
        result = resp.json()
        code = result.get("code", -1)
        msg = result.get("msg", "未知错误")
        
        if code == 0:
            comment_id = result.get("data", {}).get("comment", {}).get("id")
            return jsonify({
                "success": True,
                "data": {
                    "code": code,
                    "message": "评论成功",
                    "comment_id": comment_id
                }
            })
        elif code == 1105:
            return jsonify({"success": False, "error": "您已评论过该地图", "code": code})
        elif code == 1103:
            return jsonify({"success": False, "error": "包含违规词", "code": code})
        elif code == 1001:
            return jsonify({"success": False, "error": "参数无效", "code": code})
        else:
            return jsonify({"success": False, "error": msg, "code": code})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

# ========== API: 功能8 - 广播地图 ==========
@app.route('/api/map/broadcast', methods=['POST'])
def map_broadcast():
    data = request.json
    map_code = data.get('map_code', '').strip()
    
    if not map_code:
        return jsonify({"success": False, "error": "地图代码不能为空"})
    
    map_id = base36_to_dec(map_code)
    if map_id is None or map_id == 0:
        return jsonify({"success": False, "error": "地图代码无效"})
    
    config = load_config()
    session = get_session(config)
    if not session:
        return jsonify({"success": False, "error": "获取Session失败"})
    
    headers = get_headers(session, config)
    
    # 领取免费喇叭
    url_claim = "https://battlecraft.tuimotuimo.com/battlecraft/horn/claimfree"
    try:
        resp = requests.post(url_claim, headers=headers, data={"claimsCount": "1", "all": "false"}, timeout=10)
        resp.raise_for_status()
        claim_resp = resp.json()
        if claim_resp.get("code") == 0:
            horn_count = claim_resp.get("data", {}).get("userrole", {}).get("horn", 0)
        # 失败也继续
    except:
        pass
    
    # 广播
    url_broadcast = "https://battlecraft.tuimotuimo.com/battlecraft/chatroom/sendugclevel"
    try:
        resp = requests.post(url_broadcast, headers=headers, data={"ugcLvId": str(map_id), "v2": "true"}, timeout=10)
        resp.raise_for_status()
        broadcast_resp = resp.json()
        code = broadcast_resp.get("code", -1)
        if code == 0:
            return jsonify({"success": True, "message": f"地图 {map_code} 广播成功"})
        elif code == 2014:
            return jsonify({"success": False, "error": "请求错误 c2014", "code": code})
        else:
            return jsonify({"success": False, "error": broadcast_resp.get("msg", "未知错误"), "code": code})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

# ========== 前端页面 ==========
@app.route('/')
def index():
    return send_file('static/index.html')

if __name__ == '__main__':
    os.makedirs('static', exist_ok=True)
    app.run(host='0.0.0.0', port=5000, debug=True)