#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
派对制造 - 战队聊天 Web 版 (带IP监控 + 自动刷新Session)
版本: 5.0
功能:
  1. 双账号切换聊天
  2. 自动轮询新消息
  3. Session过期自动刷新 (401/1001)
  4. 真实IP识别 (Serveo/X-Forwarded-For)
  5. 访客统计
  6. IP封禁
"""

from flask import Flask, render_template_string, request, jsonify
import requests
import json
import time
import threading

app = Flask(__name__)
app.secret_key = "party_chat_secret_key_2024"

# ==================== 配置 ====================
BASE_URL = "https://battlecraft.tuimotuimo.com"
CLAN_ID = "6358fb013520c312257bec24"

# 账号1配置 (e20e - 玩家51616112)
ACCOUNT1 = {
    "key": "1",
    "name": "玩家51616112",
    "short_id": "51616112",
    "jwt": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJkZXZJZCI6IjMwNjIxMDVhYjhjMTRkZjU3OWIwM2RlN2MzM2JkNGZjMyIsImZsYWciOiJmZjY1IiwiZnJvbSI6InRhcHRhcCIsImx0Ijoic2Vzc2lvbiIsInNzbiI6ImUyMGUiLCJ1c2VyaWQiOiI2YTVjNTRlNjM1MjBjMzE2MzUxZGUyMGUiLCJ2IjoiMCJ9.QlFDewCmm1QJeQPQPusiLuUFKAJ7CSSJz9hgWgHMwbY",
    "device_id": "3062105ab8c14df579b03de7c33bd4fc3",
    "ssn": "e20e",
    "cookie": "SERVERID=769e7e1294f37fd70e4a8fd5d4a4a403|1784437635|1784435942",
    "session_id": None
}

# 账号2配置 (6817 - 雨晴1)
ACCOUNT2 = {
    "key": "2",
    "name": "雨晴1",
    "short_id": "51611447",
    "jwt": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJkZXZJZCI6IjQ1OGFmMGNmMTE1NTkyMjJiZDQ0YjVkZjAwNTM5ZThlMiIsImZsYWciOiJjMjRiIiwiZnJvbSI6InRhcHRhcCIsImx0Ijoic2Vzc2lvbiIsInNzbiI6IjY4MTciLCJ1c2VyaWQiOiI2YTU4ODQzZDM1MjBjMzE2MzUxZDY4MTciLCJ2IjoiMCJ9.bbMvFfbKDHwDNe7aPMYSy_gvV72lcP26WIKYcRY1bXU",
    "device_id": "458af0cf11559222bd44b5df00539e8e2",
    "ssn": "6817",
    "cookie": "SERVERID=29e952f23be3377cd3e2b06495536a39|1784437722|1784361827",
    "session_id": None
}

# 当前使用的账号key
current_account_key = "1"

# 消息缓存
message_cache = []
last_ids_cache = {"1": set(), "2": set()}

# ==================== IP记录 ====================
visitor_ips = {}
banned_ips = set()

# ==================== 获取真实IP ====================
def get_real_ip():
    """获取客户端真实IP (支持Serveo/ngrok/Cloudflare)"""
    serveo_ip = request.headers.get('X-Serveo-Client-IP')
    if serveo_ip:
        return serveo_ip
    
    forwarded = request.headers.get('X-Forwarded-For')
    if forwarded:
        return forwarded.split(',')[0].strip()
    
    real_ip = request.headers.get('X-Real-IP')
    if real_ip:
        return real_ip
    
    cf_ip = request.headers.get('CF-Connecting-IP')
    if cf_ip:
        return cf_ip
    
    true_ip = request.headers.get('True-Client-IP')
    if true_ip:
        return true_ip
    
    return request.remote_addr

def get_all_headers():
    headers = {}
    for key, value in request.headers.items():
        headers[key] = value
    return headers

def log_visitor():
    ip = get_real_ip()
    now = time.time()
    
    if ip in visitor_ips:
        visitor_ips[ip]["last_visit"] = now
        visitor_ips[ip]["count"] += 1
    else:
        visitor_ips[ip] = {
            "first_visit": now,
            "last_visit": now,
            "count": 1,
            "user_agent": request.headers.get('User-Agent', '')[:100]
        }
    
    print(f"[访问] {ip} - {request.method} {request.path}")

# ==================== 登录 ====================
def login(account):
    """使用JWT换取Session"""
    url = f"{BASE_URL}/battlecraft/account/loginsession"
    headers = {
        "Host": "battlecraft.tuimotuimo.com",
        "Accept": "*/*",
        "Accept-Encoding": "deflate, gzip",
        "Cookie": account["cookie"],
        "Content-Type": "application/x-www-form-urlencoded",
        "ssn": account["ssn"],
        "ver": "2.1.93"
    }
    data = {
        "timezone": "8",
        "v2": "true",
        "v3": "true",
        "session": account["jwt"],
        "deviceId": account["device_id"],
        "tutorialType": "ugc"
    }
    
    try:
        resp = requests.post(url, headers=headers, data=data, timeout=10)
        result = resp.json()
        if result.get("code") == 0:
            sessionid = result.get("data", {}).get("sessionid")
            if sessionid:
                account["session_id"] = sessionid
                print(f"[登录] ✅ {account['name']} 登录成功")
                return sessionid
        print(f"[登录] ❌ {account['name']} 登录失败: {result}")
        return None
    except Exception as e:
        print(f"[登录] ❌ {account['name']} 异常: {e}")
        return None

def ensure_logged_in(account):
    """确保账号已登录，返回session_id"""
    if account["session_id"]:
        return account["session_id"]
    return login(account)

# ==================== Session刷新检测 ====================
def refresh_session_if_needed(account, resp):
    """
    检查响应是否需要刷新Session
    支持 requests.Response 对象 或 dict
    返回: (是否需要刷新, 新session或None)
    """
    # 检查HTTP状态码 401
    if hasattr(resp, 'status_code'):
        if resp.status_code == 401:
            print(f"[Session] ⚠️ {account['name']} 收到HTTP 401，刷新Session...")
            account["session_id"] = None
            new_session = login(account)
            return True, new_session
    
    # 检查JSON中的code
    try:
        if hasattr(resp, 'json'):
            data = resp.json()
        else:
            data = resp
        
        code = data.get("code")
        # 401 或 1001 都表示认证失败
        if code in (401, 1001):
            print(f"[Session] ⚠️ {account['name']} 收到code={code}，刷新Session...")
            account["session_id"] = None
            new_session = login(account)
            return True, new_session
    except:
        pass
    
    return False, None

# ==================== 获取消息ID (带自动刷新) ====================
def get_message_ids(account):
    session_id = ensure_logged_in(account)
    if not session_id:
        return None
    
    url = f"{BASE_URL}/battlecraft/clan/getmessageids"
    headers = {
        "Host": "battlecraft.tuimotuimo.com",
        "Accept": "*/*",
        "Accept-Encoding": "deflate, gzip",
        "Cookie": account["cookie"],
        "Auth": session_id,
        "Content-Type": "application/x-www-form-urlencoded",
        "ssn": account["ssn"],
        "ver": "2.1.93"
    }
    data = {"clanId": CLAN_ID}
    
    try:
        resp = requests.post(url, headers=headers, data=data, timeout=10)
        
        # 检查是否需要刷新Session
        need_refresh, new_session = refresh_session_if_needed(account, resp)
        if need_refresh and new_session:
            headers["Auth"] = new_session
            resp = requests.post(url, headers=headers, data=data, timeout=10)
        elif need_refresh and not new_session:
            return None
        
        result = resp.json()
        if result.get("code") == 0:
            data = result.get("data", {})
            return {
                "chatmsgIds": data.get("chatmsgIds", []),
                "blockedIds": data.get("blockedIds", [])
            }
        return None
    except Exception as e:
        print(f"[获取ID异常] {e}")
        return None

# ==================== 获取消息详情 (带自动刷新) ====================
def get_messages(account, ids):
    if not ids:
        return []
    
    session_id = ensure_logged_in(account)
    if not session_id:
        return []
    
    url = f"{BASE_URL}/battlecraft/clan/getmessages"
    headers = {
        "Host": "battlecraft.tuimotuimo.com",
        "Accept": "*/*",
        "Accept-Encoding": "deflate, gzip",
        "Cookie": account["cookie"],
        "Auth": session_id,
        "Content-Type": "application/x-www-form-urlencoded",
        "ssn": account["ssn"],
        "ver": "2.1.93"
    }
    ids_str = ",".join(ids)
    data = {"ids": ids_str}
    
    try:
        resp = requests.post(url, headers=headers, data=data, timeout=10)
        
        # 检查是否需要刷新Session
        need_refresh, new_session = refresh_session_if_needed(account, resp)
        if need_refresh and new_session:
            headers["Auth"] = new_session
            resp = requests.post(url, headers=headers, data=data, timeout=10)
        elif need_refresh and not new_session:
            return []
        
        result = resp.json()
        if result.get("code") == 0:
            return result.get("data", {}).get("chatmsgList", [])
        return []
    except Exception as e:
        print(f"[获取消息异常] {e}")
        return []

# ==================== 发送消息 (带自动刷新) ====================
def send_message(account, content):
    session_id = ensure_logged_in(account)
    if not session_id:
        return {"success": False, "msg": "登录失败"}
    
    url = f"{BASE_URL}/battlecraft/clan/sendmessage"
    headers = {
        "Host": "battlecraft.tuimotuimo.com",
        "Accept": "*/*",
        "Accept-Encoding": "deflate, gzip",
        "Cookie": account["cookie"],
        "Auth": session_id,
        "Content-Type": "application/x-www-form-urlencoded",
        "ssn": account["ssn"],
        "ver": "2.1.93"
    }
    data = {
        "clanId": CLAN_ID,
        "type": "1",
        "content": content,
        "reqId": str(int(time.time() * 1000))
    }
    
    try:
        resp = requests.post(url, headers=headers, data=data, timeout=10)
        
        # 检查是否需要刷新Session
        need_refresh, new_session = refresh_session_if_needed(account, resp)
        if need_refresh and new_session:
            headers["Auth"] = new_session
            resp = requests.post(url, headers=headers, data=data, timeout=10)
        elif need_refresh and not new_session:
            return {"success": False, "msg": "重新登录失败"}
        
        result = resp.json()
        code = result.get("code")
        
        if code == 0:
            return {"success": True, "code": 0}
        elif code == 1000:
            return {"success": False, "code": 1000, "msg": "内容包含违规词"}
        else:
            return {"success": False, "code": code, "msg": result.get("msg", "未知错误")}
    except Exception as e:
        return {"success": False, "msg": str(e)}

# ==================== 轮询新消息 ====================
def poll_new_messages(account_key):
    account = get_account(account_key)
    
    result = get_message_ids(account)
    if not result:
        return []
    
    current_ids = set(result.get("chatmsgIds", []))
    blocked_ids = set(result.get("blockedIds", []))
    
    last_ids = last_ids_cache.get(account_key, set())
    
    new_ids = current_ids - last_ids
    new_ids = new_ids - blocked_ids
    
    last_ids_cache[account_key] = current_ids
    
    if new_ids:
        messages = get_messages(account, list(new_ids))
        for msg in messages:
            msg["_account"] = account_key
            msg["_account_name"] = account["name"]
            msg["_account_short_id"] = account["short_id"]
        return messages
    
    return []

# ==================== 后台轮询线程 ====================
def background_poller():
    global message_cache
    while True:
        try:
            for key in ["1", "2"]:
                new_msgs = poll_new_messages(key)
                if new_msgs:
                    message_cache.extend(new_msgs)
                    if len(message_cache) > 200:
                        message_cache = message_cache[-200:]
        except Exception as e:
            print(f"[轮询异常] {e}")
        time.sleep(3)

# 启动后台轮询
poller_thread = threading.Thread(target=background_poller, daemon=True)
poller_thread.start()

# ==================== 获取账号 ====================
def get_account(key):
    return ACCOUNT1 if key == "1" else ACCOUNT2

def get_current_account():
    return get_account(current_account_key)

# ==================== Flask 路由 ====================

@app.before_request
def before_request():
    log_visitor()
    ip = get_real_ip()
    if ip in banned_ips:
        return jsonify({"error": "您的IP已被封禁"}), 403

@app.route('/')
def index():
    account = get_current_account()
    return render_template_string(HTML_TEMPLATE,
        current_name=account["name"],
        current_short_id=account["short_id"]
    )

@app.route('/api/switch_account', methods=['POST'])
def switch_account():
    global current_account_key
    
    data = request.get_json()
    new_key = data.get('account', '1')
    
    print(f"[切换账号] 从 {current_account_key} 切换到 {new_key}")
    
    current_account_key = new_key
    account = get_current_account()
    session_id = ensure_logged_in(account)
    
    if session_id:
        print(f"[切换账号] ✅ {account['name']} 已就绪")
        return jsonify({
            "success": True,
            "name": account["name"],
            "short_id": account["short_id"]
        })
    else:
        return jsonify({
            "success": False,
            "msg": "登录失败"
        })

@app.route('/api/messages')
def get_cached_messages():
    return jsonify({
        "success": True,
        "messages": message_cache[-100:],
        "visitor_count": len(visitor_ips)
    })

@app.route('/api/send', methods=['POST'])
def send():
    global message_cache
    
    data = request.get_json()
    content = data.get('content', '').strip()
    
    if not content:
        return jsonify({"success": False, "msg": "消息内容不能为空"})
    
    account = get_current_account()
    account_key = current_account_key
    
    result = send_message(account, content)
    
    if result["success"]:
        # 立即触发一次轮询，快速显示自己发的消息
        new_msgs = poll_new_messages(account_key)
        if new_msgs:
            message_cache.extend(new_msgs)
            if len(message_cache) > 200:
                message_cache = message_cache[-200:]
        return jsonify({"success": True})
    else:
        return jsonify({"success": False, "msg": result.get("msg", "发送失败")})

@app.route('/api/myip')
def my_ip():
    ip = get_real_ip()
    headers = get_all_headers()
    return jsonify({
        "ip": ip,
        "headers": headers
    })

@app.route('/api/visitors')
def get_visitors():
    return jsonify({
        "total": len(visitor_ips),
        "ips": list(visitor_ips.keys())[-20:]
    })

@app.route('/api/status')
def status():
    account = get_current_account()
    return jsonify({
        "online": True,
        "account": account["name"],
        "short_id": account["short_id"],
        "message_count": len(message_cache),
        "visitor_count": len(visitor_ips),
        "banned_count": len(banned_ips)
    })

@app.route('/api/headers')
def show_headers():
    headers = {}
    for key, value in request.headers.items():
        headers[key] = value
    return jsonify({
        "remote_addr": request.remote_addr,
        "headers": headers
    })

@app.route('/api/refresh_session', methods=['POST'])
def refresh_session():
    """手动刷新当前账号Session"""
    account = get_current_account()
    account["session_id"] = None
    new_session = login(account)
    if new_session:
        return jsonify({"success": True, "msg": f"{account['name']} Session已刷新"})
    else:
        return jsonify({"success": False, "msg": "刷新失败"})

# ==================== HTML模板 ====================
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>派对制造 - 战队聊天</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, "Microsoft YaHei", sans-serif;
            background: #1a1a2e;
            color: #fff;
            height: 100vh;
            display: flex;
            flex-direction: column;
        }
        .header {
            background: linear-gradient(135deg, #16213e, #0f3460);
            padding: 15px 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 2px solid #e94560;
            flex-shrink: 0;
            flex-wrap: wrap;
            gap: 8px;
        }
        .header h1 { font-size: 18px; color: #e94560; }
        .header .account-info { font-size: 12px; color: #aaa; }
        .header .account-info .name { color: #4fc3f7; font-weight: bold; }
        .chat-container {
            flex: 1;
            overflow-y: auto;
            padding: 15px 20px;
            background: #16213e;
        }
        .chat-container::-webkit-scrollbar { width: 4px; }
        .chat-container::-webkit-scrollbar-thumb { background: #e94560; border-radius: 2px; }
        .message {
            margin-bottom: 12px;
            display: flex;
            flex-direction: column;
        }
        .message .meta {
            font-size: 11px;
            color: #888;
            margin-bottom: 2px;
        }
        .message .meta .nick { color: #4fc3f7; font-weight: bold; }
        .message .meta .self { color: #ffd54f; }
        .message .meta .other { color: #ff8a65; }
        .message .bubble {
            display: inline-block;
            padding: 8px 14px;
            border-radius: 12px;
            max-width: 80%;
            word-break: break-all;
            font-size: 14px;
            background: #2a2a4a;
            align-self: flex-start;
        }
        .message.self .bubble {
            background: #e94560;
            align-self: flex-end;
        }
        .message.self { align-items: flex-end; }
        .message.self .meta { text-align: right; }
        .input-area {
            padding: 12px 20px;
            background: #1a1a2e;
            border-top: 1px solid #333;
            display: flex;
            gap: 10px;
            flex-shrink: 0;
        }
        .input-area input {
            flex: 1;
            padding: 10px 16px;
            border: 1px solid #333;
            border-radius: 20px;
            background: #2a2a4a;
            color: #fff;
            font-size: 14px;
            outline: none;
        }
        .input-area input:focus { border-color: #e94560; }
        .input-area input::placeholder { color: #666; }
        .input-area button {
            padding: 10px 24px;
            border: none;
            border-radius: 20px;
            background: #e94560;
            color: #fff;
            font-size: 14px;
            cursor: pointer;
            transition: background 0.2s;
            flex-shrink: 0;
        }
        .input-area button:hover { background: #ff6b81; }
        .input-area button:disabled { opacity: 0.5; cursor: not-allowed; }
        .switch-area {
            display: flex;
            gap: 8px;
            align-items: center;
        }
        .switch-area button {
            padding: 4px 12px;
            border: 1px solid #555;
            border-radius: 12px;
            background: transparent;
            color: #aaa;
            font-size: 11px;
            cursor: pointer;
            transition: all 0.2s;
        }
        .switch-area button.active {
            border-color: #e94560;
            color: #e94560;
            background: rgba(233, 69, 96, 0.1);
        }
        .switch-area button:hover { color: #fff; }
        .status {
            font-size: 11px;
            color: #666;
            padding: 4px 0;
            text-align: center;
            flex-shrink: 0;
        }
        .badge {
            font-size: 10px;
            background: #e94560;
            color: #fff;
            padding: 1px 8px;
            border-radius: 10px;
            margin-left: 6px;
        }
        .ip-badge {
            font-size: 10px;
            background: #2a2a4a;
            color: #888;
            padding: 1px 8px;
            border-radius: 10px;
            margin-left: 6px;
            border: 1px solid #444;
        }
        .serveo-url {
            font-size: 10px;
            color: #4fc3f7;
            background: rgba(79, 195, 247, 0.1);
            padding: 2px 10px;
            border-radius: 12px;
            border: 1px solid #4fc3f7;
        }
        .refresh-btn {
            font-size: 10px;
            color: #ffd54f;
            background: rgba(255, 213, 79, 0.1);
            padding: 2px 10px;
            border-radius: 12px;
            border: 1px solid #ffd54f;
            cursor: pointer;
            transition: all 0.2s;
        }
        .refresh-btn:hover {
            background: rgba(255, 213, 79, 0.2);
        }
        @media (max-width: 480px) {
            .header h1 { font-size: 15px; }
            .input-area input { font-size: 13px; }
            .message .bubble { font-size: 13px; max-width: 90%; }
            .header { flex-direction: column; align-items: stretch; }
            .switch-area { justify-content: center; }
        }
    </style>
</head>
<body>
    <div class="header">
        <div>
            <h1>🎮 战队聊天</h1>
            <div class="account-info">
                当前: <span class="name" id="currentAccountName">{{ current_name }}</span>
                <span class="badge" id="currentAccountBadge">短ID: {{ current_short_id }}</span>
                <span class="ip-badge" id="myIp">IP: 加载中...</span>
                <span class="serveo-url">🌐 Serveo</span>
                <span class="refresh-btn" onclick="refreshSession()">🔄 刷新Session</span>
            </div>
        </div>
        <div class="switch-area">
            <button class="active" data-account="1" onclick="switchAccount('1')">账号1</button>
            <button data-account="2" onclick="switchAccount('2')">账号2</button>
        </div>
    </div>
    
    <div class="chat-container" id="chatContainer"></div>
    
    <div class="status">
        <span id="statusText">🟢 在线</span> | 
        轮询: 3s | 
        <span id="msgCount">0</span> 条消息 |
        <span id="visitorCount">访客: 0</span>
    </div>
    
    <div class="input-area">
        <input type="text" id="msgInput" placeholder="输入消息... (Enter发送)" />
        <button id="sendBtn" onclick="sendMessage()">发送</button>
    </div>

    <script>
        let currentAccount = '1';
        let pollInterval = null;
        let lastMsgId = null;
        
        fetch('/api/myip')
            .then(res => res.json())
            .then(data => {
                document.getElementById('myIp').textContent = 'IP: ' + data.ip;
                console.log('当前IP:', data.ip);
                console.log('请求头:', data.headers);
            });
        
        function refreshSession() {
            fetch('/api/refresh_session', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    alert('✅ ' + data.msg);
                } else {
                    alert('❌ ' + data.msg);
                }
            });
        }
        
        function switchAccount(account) {
            currentAccount = account;
            document.querySelectorAll('.switch-area button').forEach(btn => {
                btn.classList.toggle('active', btn.dataset.account === account);
            });
            
            document.getElementById('chatContainer').innerHTML = '';
            
            fetch('/api/switch_account', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ account: account })
            }).then(res => res.json()).then(data => {
                if (data.success) {
                    document.getElementById('currentAccountName').textContent = data.name;
                    document.getElementById('currentAccountBadge').textContent = '短ID: ' + data.short_id;
                    document.getElementById('statusText').textContent = '🟢 已切换';
                    loadMessages();
                } else {
                    alert('切换账号失败: ' + data.msg);
                }
            });
        }
        
        function loadMessages() {
            fetch('/api/messages')
                .then(res => res.json())
                .then(data => {
                    if (data.success) {
                        renderMessages(data.messages);
                        document.getElementById('msgCount').textContent = data.messages.length;
                        document.getElementById('visitorCount').textContent = '访客: ' + (data.visitor_count || 0);
                    }
                });
        }
        
        function renderMessages(messages) {
            const container = document.getElementById('chatContainer');
            if (messages.length === 0) return;
            
            const lastMsg = messages[messages.length - 1];
            if (lastMsg.id === lastMsgId && container.children.length > 0) return;
            lastMsgId = lastMsg.id;
            
            const start = Math.max(0, messages.length - 50);
            const showMsgs = messages.slice(start);
            
            container.innerHTML = '';
            showMsgs.forEach(msg => {
                const div = document.createElement('div');
                div.className = 'message';
                
                const isSelf = msg._account === currentAccount;
                if (isSelf) div.classList.add('self');
                
                const meta = document.createElement('div');
                meta.className = 'meta';
                const nick = msg.sender?.nickName || '未知';
                const shortId = msg.sender?.userShortId || '';
                const ts = msg.ts ? new Date(msg.ts).toLocaleTimeString() : '未知';
                
                meta.innerHTML = `
                    <span class="nick ${isSelf ? 'self' : 'other'}">${nick}</span>
                    <span style="color:#555"> | </span>
                    <span>${ts}</span>
                    ${shortId ? `<span style="color:#555;font-size:10px"> (${shortId})</span>` : ''}
                    ${!isSelf ? '<span class="badge" style="background:#ff8a65">对方</span>' : ''}
                `;
                
                const bubble = document.createElement('div');
                bubble.className = 'bubble';
                bubble.textContent = msg.content || '(空消息)';
                
                div.appendChild(meta);
                div.appendChild(bubble);
                container.appendChild(div);
            });
            
            container.scrollTop = container.scrollHeight;
        }
        
        function sendMessage() {
            const input = document.getElementById('msgInput');
            const content = input.value.trim();
            if (!content) return;
            
            const btn = document.getElementById('sendBtn');
            btn.disabled = true;
            btn.textContent = '发送中...';
            
            fetch('/api/send', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ content: content })
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    input.value = '';
                    loadMessages();
                } else {
                    alert('发送失败: ' + (data.msg || '未知错误'));
                }
            })
            .catch(err => {
                alert('发送异常: ' + err);
            })
            .finally(() => {
                btn.disabled = false;
                btn.textContent = '发送';
            });
        }
        
        function startPoll() {
            loadMessages();
            pollInterval = setInterval(loadMessages, 3000);
        }
        
        document.getElementById('msgInput').addEventListener('keydown', function(e) {
            if (e.key === 'Enter') sendMessage();
        });
        
        startPoll();
        
        document.addEventListener('visibilitychange', function() {
            if (document.hidden) {
                clearInterval(pollInterval);
            } else {
                clearInterval(pollInterval);
                startPoll();
            }
        });
    </script>
</body>
</html>
'''

# ==================== 启动 ====================
if __name__ == '__main__':
    print("=" * 70)
    print("  🎮 派对制造 - 战队聊天 Web 版 v5.0")
    print("=" * 70)
    print(f"  账号1: {ACCOUNT1['name']} (短ID: {ACCOUNT1['short_id']})")
    print(f"  账号2: {ACCOUNT2['name']} (短ID: {ACCOUNT2['short_id']})")
    print("=" * 70)
    print("  🌐 本地访问: http://127.0.0.1:5000")
    print("=" * 70)
    print("  💡 功能:")
    print("     - 双账号切换聊天")
    print("     - Session 自动刷新 (401/1001)")
    print("     - 真实IP识别 (Serveo/X-Forwarded-For)")
    print("     - 访客统计 & IP封禁")
    print("=" * 70)
    print()
    
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)