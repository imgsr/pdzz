#!/system/bin/sh

# ==================== 派对制造工具箱 ====================
# 版本：4.6 可对指定玩家金矿打工

# ==================== 颜色定义 ====================
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m'

# ==================== 检查并安装 Python ====================
check_and_install_python() {
    if command -v python3 >/dev/null 2>&1; then
        echo -e "${GREEN}✅ Python3 已安装${NC}"
        termux-wake-lock
        sleep 1
        return 0
    elif command -v python >/dev/null 2>&1; then
        echo -e "${GREEN}✅ Python 已安装${NC}"
        sleep 1
        return 0
    fi
    
    echo -e "${YELLOW}⚠️ 未检测到 Python，正在尝试自动安装...${NC}"
    
    if [ -d "/data/data/com.termux" ] || command -v pkg >/dev/null 2>&1; then
        echo -e "${BLUE}检测到 Termux 环境，使用 pkg 安装 Python...${NC}"
        termux-wake-lock
        pkg update -y 2>/dev/null
        pkg install python -y
    elif command -v apt >/dev/null 2>&1; then
        echo -e "${BLUE}检测到 apt，使用 apt 安装 Python3...${NC}"
        apt update -y 2>/dev/null
        apt install python3 -y
    elif command -v yum >/dev/null 2>&1; then
        echo -e "${BLUE}检测到 yum，使用 yum 安装 Python3...${NC}"
        yum install python3 -y
    elif command -v pacman >/dev/null 2>&1; then
        echo -e "${BLUE}检测到 pacman，使用 pacman 安装 Python...${NC}"
        pacman -S python --noconfirm
    else
        echo -e "${RED}❌ 无法识别包管理器，请手动安装 Python${NC}"
        echo -e "${YELLOW}提示：安装后重新运行脚本${NC}"
        exit 1
    fi
    
    if command -v python3 >/dev/null 2>&1; then
        echo -e "${GREEN}✅ Python3 安装成功！${NC}"
        sleep 1
        return 0
    elif command -v python >/dev/null 2>&1; then
        echo -e "${GREEN}✅ Python 安装成功！${NC}"
        sleep 1
        return 0
    else
        echo -e "${RED}❌ Python 安装失败，请手动安装${NC}"
        exit 1
    fi
}

# ==================== 配置文件路径 ====================
CONFIG_FILE="/data/local/tmp/party_tool_config.txt"

# ==================== 默认配置 ====================
DEFAULT_JWT="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJkZXZJZCI6IjMzOWY3YWJhZTg2OGI3ZjBhODMzODc3YjBkNWQ0NjQ1XG5kYTNkYzlhOTk5Mjg5OGY5MDk2YWI5MjAyOTVkM2ZhZSIsImZsYWciOiJiZGY2IiwiZnJvbSI6InRhcHRhcCIsImx0IjoiZ3Vlc3QiLCJzc24iOiI1Mjk5IiwidXNlcmlkIjoiNjlmNTk5MDNlOGQ1YjU1YmI0ZWViYjAyIiwidiI6IjAifQ.RHQ1EK0pEwiXBTILUyLNgHCetsfO57fUmJtcMGPqG-A"
DEFAULT_DEVICE_ID="339f7abae868b7f0a833877b0d5d46454a3dc9a9992898f9096ab920295d3fae"
DEFAULT_SSN="3c05"
DEFAULT_VER="2.1.93"
DEFAULT_COOKIE="SERVERID=769e7e1294f37fd70e4a8fd5d4a4a403|1774672107|1774600237"

# 最新地图查询默认数量
MAP_COUNT=100

# ==================== 随机生成Device ID ====================
generate_random_device_id() {
    RANDOM_ID=$(openssl rand -hex 16 2>/dev/null)
    if [ -z "$RANDOM_ID" ]; then
        RANDOM_ID=$(cat /dev/urandom 2>/dev/null | head -c 16 | od -An -tx1 | tr -d ' \n')
    fi
    if [ -z "$RANDOM_ID" ]; then
        RANDOM_ID=$(printf "%032x" $((RANDOM % 1000000000000000000)))
    fi
    echo "$RANDOM_ID"
}

# ==================== 配置加载/保存 ====================
load_config() {
    if [ -f "$CONFIG_FILE" ]; then
        source "$CONFIG_FILE" 2>/dev/null
    fi
    
    JWT=${JWT:-$DEFAULT_JWT}
    if [ -z "$DEVICE_ID" ]; then
        DEVICE_ID=$(generate_random_device_id)
    fi
    SSN=${SSN:-$DEFAULT_SSN}
    VER=${VER:-$DEFAULT_VER}
    COOKIE=${COOKIE:-$DEFAULT_COOKIE}
    MAP_COUNT=${SAVED_MAP_COUNT:-100}
}

save_config() {
    cat > "$CONFIG_FILE" << EOF
JWT="$JWT"
DEVICE_ID="$DEVICE_ID"
SSN="$SSN"
VER="$VER"
COOKIE="$COOKIE"
SAVED_MAP_COUNT="$MAP_COUNT"
EOF
}

# ==================== 获取Session（通用） ====================
get_session() {
    local session=$(curl -s -X POST "https://battlecraft.tuimotuimo.com/battlecraft/account/loginsession" \
      -H "Content-Type: application/x-www-form-urlencoded" \
      -H "ssn: $SSN" \
      -H "ver: $VER" \
      -H "Cookie: $COOKIE" \
      --data-urlencode "timezone=8" \
      --data-urlencode "v2=true" \
      --data-urlencode "v3=true" \
      --data-urlencode "session=$JWT" \
      --data-urlencode "deviceId=$DEVICE_ID" \
      --data-urlencode "tutorialType=ugc" \
      --compressed 2>/dev/null | grep -o '"sessionid":"[^"]*"' | cut -d'"' -f4)
    echo "$session"
}

# ==================== 工具函数 ====================
clear_screen() {
    printf "\033[2J\033[H"
}

print_header() {
    clear_screen
    echo -e "${CYAN}╔════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║      派对制造 Shell 工具箱 v4.6       ║${NC}"
    echo -e "${CYAN}╚════════════════════════════════════════╝${NC}"
    echo ""
}

print_menu() {
    echo -e "${YELLOW}════════════════ 主菜单 ════════════════${NC}"
    echo -e "${GREEN}A. 查看当前IP地址${NC}"
    echo -e "${GREEN}B. 设备ID设置${NC}"
    echo -e "${GREEN}C. 查询游戏版本信息${NC}"
    echo -e "${GREEN}D. 查询游戏公告${NC}"
    echo -e "${GREEN}E. 查看工具箱公告${NC}"
    echo -e "${GREEN}F. 查看工具箱版本${NC}"
    echo -e "${GREEN}1. 派对制造房间列表${NC}"
    echo -e "${GREEN}2. 派对制造地图查询${NC}"
    echo -e "${GREEN}3. 派对制造排行榜查询${NC}"
    echo -e "${GREEN}4. 派对制造玩家信息查询${NC}"
    echo -e "${GREEN}5. 查询最新地图${NC}"
    echo -e "${GREEN}6. 金矿打工${NC}"
    echo -e "${RED}0. 退出工具${NC}"
    echo -e "${YELLOW}════════════════════════════════════════${NC}"
    echo ""
}

# ==================== 功能A：查看IP ====================
func_show_ip() {
    print_header
    echo -e "${YELLOW}>>> 查询本机IP地址${NC}\n"
    
    echo -e "${BLUE}公网IP地址：${NC}"
    PUBLIC_IP=$(curl -s --max-time 5 ifconfig.me 2>/dev/null)
    if [ -n "$PUBLIC_IP" ]; then
        echo -e "${GREEN}  → $PUBLIC_IP${NC}"
    else
        PUBLIC_IP=$(curl -s --max-time 5 ipinfo.io/ip 2>/dev/null)
        if [ -n "$PUBLIC_IP" ]; then
            echo -e "${GREEN}  → $PUBLIC_IP${NC}"
        else
            echo -e "${RED}  → 获取失败${NC}"
        fi
    fi
    
    echo -e "\n${BLUE}内网IP地址：${NC}"
    INNER_IP=$(ip addr show 2>/dev/null | grep -oP '(?<=inet\s)\d+(\.\d+){3}' | grep -v '127.0.0.1' | head -1)
    if [ -n "$INNER_IP" ]; then
        echo -e "${GREEN}  → $INNER_IP${NC}"
    else
        INNER_IP=$(ifconfig 2>/dev/null | grep 'inet ' | grep -v '127.0.0.1' | awk '{print $2}' | head -1)
        if [ -n "$INNER_IP" ]; then
            echo -e "${GREEN}  → $INNER_IP${NC}"
        fi
    fi
    
    echo -e "\n${CYAN}按回车键返回主菜单...${NC}"
    read input
}

# ==================== 功能B：设备ID设置 ====================
func_device_setup() {
    while true; do
        print_header
        echo -e "${YELLOW}>>> 设备ID和认证设置${NC}\n"
        
        echo -e "${BLUE}当前配置：${NC}"
        echo -e "  JWT: ${JWT:0:50}..."
        echo -e "  Device ID: $DEVICE_ID"
        echo -e "  SSN: $SSN"
        echo -e "  Cookie: ${COOKIE:0:50}..."
        echo ""
        
        echo -e "${GREEN}请选择操作：${NC}"
        echo "  1. 重置为默认配置"
        echo "  2. 手动设置JWT"
        echo "  3. 手动设置Device ID"
        echo "  4. 手动设置SSN"
        echo "  5. 保存当前配置"
        echo "  0. 返回主菜单"
        echo ""
        
        read -p "请输入选项: " sub_opt
        
        case $sub_opt in
            1)
                JWT="$DEFAULT_JWT"
                DEVICE_ID=$(generate_random_device_id)
                SSN="$DEFAULT_SSN"
                COOKIE="$DEFAULT_COOKIE"
                echo -e "${GREEN}✅ 已重置为默认配置（Device ID已随机生成）${NC}"
                sleep 1
                ;;
            2)
                echo -e "${YELLOW}请输入JWT（以eyJ开头）：${NC}"
                read -r new_jwt
                if [ -n "$new_jwt" ]; then
                    JWT="$new_jwt"
                    echo -e "${GREEN}✅ JWT已设置${NC}"
                fi
                sleep 1
                ;;
            3)
                echo -e "${YELLOW}请输入Device ID：${NC}"
                read -r new_device
                if [ -n "$new_device" ]; then
                    DEVICE_ID="$new_device"
                    echo -e "${GREEN}✅ Device ID已设置${NC}"
                fi
                sleep 1
                ;;
            4)
                echo -e "${YELLOW}请输入SSN：${NC}"
                read -r new_ssn
                if [ -n "$new_ssn" ]; then
                    SSN="$new_ssn"
                    echo -e "${GREEN}✅ SSN已设置${NC}"
                fi
                sleep 1
                ;;
            5)
                save_config
                echo -e "${GREEN}✅ 配置已保存到 $CONFIG_FILE${NC}"
                sleep 1
                ;;
            0)
                return
                ;;
            *)
                echo -e "${RED}无效选项${NC}"
                sleep 1
                ;;
        esac
    done
}

# ==================== 功能C：查询游戏版本信息 ====================
func_game_version() {
    print_header
    echo -e "${YELLOW}>>> 查询游戏版本信息${NC}\n"
    
    echo -e "${BLUE}正在获取配置信息...${NC}"
    
    CONFIG_RESP=$(curl -s --max-time 10 "https://prod.tuimotuimo.com/config/info/battlecraft" \
      -H "Host: prod.tuimotuimo.com" \
      -H "Accept: */*" \
      -H "Accept-Encoding: deflate, gzip" 2>/dev/null)
    
    if [ -z "$CONFIG_RESP" ]; then
        echo -e "${RED}获取配置信息失败，请检查网络${NC}"
        echo -e "${CYAN}按回车键返回主菜单...${NC}"
        read input
        return
    fi
    
    echo -e "${GREEN}✅ 获取成功${NC}\n"
    echo -e "${GREEN}════════════════ 版本信息 ════════════════${NC}\n"
    
    echo "$CONFIG_RESP" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    
    print(f\"  📱 各平台版本号：\")
    print(f\"  {'─'*40}\")
    
    platforms = data.get('platforms', {})
    
    platform_list = ['taptap', 'douyin_app', 'douyin_live', 'ios', 'qq', 'wechat', 'bilibili', 'kuaishou', 'momoyu', 'toutiao']
    platform_names = {
        'taptap': 'TapTap',
        'douyin_app': '抖音APP',
        'douyin_live': '抖音直播',
        'ios': 'iOS',
        'qq': 'QQ',
        'wechat': '微信',
        'bilibili': 'Bilibili',
        'kuaishou': '快手',
        'momoyu': '摸摸鱼',
        'toutiao': '头条'
    }
    
    for key in platform_list:
        if key in platforms:
            p = platforms[key]
            prod_ver = p.get('prod', '未知')
            name = platform_names.get(key, key)
            current_mark = \" ← (当前)\" if prod_ver == \"$VER\" else \"\"
            print(f\"  {name:<10}: {prod_ver}{current_mark}\")
    
    print(f\"\n  📦 应用版本: {data.get('version', '未知')}\")
    print(f\"  🔍 审核版本: {data.get('censorVersion', '未知')}\")
    print(f\"  🟢 服务状态: {'开启' if data.get('isOpen') else '关闭'}\")
    print(f\"  📹 OBS支持: {'开启' if data.get('obsEnabled') else '关闭'}\")
    
except Exception as e:
    print(f\"  解析失败: {e}\")
"
    
    echo -e "\n${CYAN}按回车键返回主菜单...${NC}"
    read input
}

# ==================== 功能D：查询游戏公告 ====================
func_game_notice() {
    print_header
    echo -e "${YELLOW}>>> 查询游戏公告${NC}\n"
    
    echo -e "${BLUE}正在获取公告信息...${NC}"
    
    CONFIG_RESP=$(curl -s --max-time 10 "https://prod.tuimotuimo.com/config/info/battlecraft" \
      -H "Host: prod.tuimotuimo.com" \
      -H "Accept: */*" \
      -H "Accept-Encoding: deflate, gzip" 2>/dev/null)
    
    if [ -z "$CONFIG_RESP" ]; then
        echo -e "${RED}获取公告失败，请检查网络${NC}"
        echo -e "${CYAN}按回车键返回主菜单...${NC}"
        read input
        return
    fi
    
    echo -e "${GREEN}✅ 获取成功${NC}\n"
    
    echo "$CONFIG_RESP" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    
    notice = data.get('notice', {})
    notice_type = notice.get('type', 'normal')
    notice_title = notice.get('title', '')
    notice_text = notice.get('text', '')
    
    notice_after = data.get('noticeAfter', {})
    after_text = notice_after.get('text', '')
    
    if notice_title or notice_text:
        print(f\"  {'='*50}\")
        print(f\"  📢 {'【重要公告】' if notice_type == 'stopServer' else '【当前公告】'}\")
        if notice_title:
            print(f\"  {notice_title}\")
        if notice_text:
            print(f\"\\n{notice_text}\\n\")
    
    if after_text:
        print(f\"  {'='*50}\")
        print(f\"  📰 【游戏公告】\")
        print(f\"\\n{after_text}\\n\")
    
    if not notice_text and not after_text:
        print(\"  暂无公告\")
    
except Exception as e:
    print(f\"  解析失败: {e}\")
"
    
    echo -e "\n${CYAN}按回车键返回主菜单...${NC}"
    read input
}

# ==================== 功能E：查看G在线公告 ====================
func_github_notice() {
    print_header
    echo -e "${YELLOW}>>> 查看在线公告${NC}\n"
    
    echo -e "${BLUE}正在获取公告内容...${NC}"
    NOTICE_CONTENT=$(curl -s --max-time 10 "https://ghproxy.net/https://raw.githubusercontent.com/imgsr/pdzz/main/context.txt" 2>/dev/null)
    
    if [ -z "$NOTICE_CONTENT" ]; then
        echo -e "${RED}❌ 获取公告失败，请检查网络连接${NC}"
    else
        echo -e "${GREEN}✅ 获取成功${NC}\n"
        echo -e "${CYAN}════════════════ 公告内容 ════════════════${NC}"
        echo "$NOTICE_CONTENT"
        echo -e "${CYAN}════════════════════════════════════════${NC}"
    fi
    
    echo -e "\n${CYAN}按回车键返回主菜单...${NC}"
    read input
}

# ==================== 功能F：查看工具箱版本信息 ====================
func_toolbox_version() {
    print_header
    echo -e "${YELLOW}>>> 查看工具箱版本${NC}\n"
    
    echo -e "${BLUE}正在获取版本信息...${NC}"
    VERSION_CONTENT=$(curl -s --max-time 10 "https://ghproxy.net/https://raw.githubusercontent.com/imgsr/pdzz/main/version.txt" 2>/dev/null)
    
    if [ -z "$VERSION_CONTENT" ]; then
        echo -e "${RED}❌ 获取版本信息失败，请检查网络连接${NC}"
    else
        echo -e "${GREEN}✅ 获取成功${NC}\n"
        echo -e "${CYAN}════════════════ 版本信息 ════════════════${NC}"
        echo "$VERSION_CONTENT"
        echo -e "${CYAN}════════════════════════════════════════${NC}"
    fi
    
    echo -e "\n${CYAN}按回车键返回主菜单...${NC}"
    read input
}

# ==================== 功能1：房间列表 ====================
func_room_list() {
    print_header
    echo -e "${YELLOW}>>> 派对制造房间列表${NC}\n"

    echo "===================="
    echo "开始执行房间信息获取"
    echo "===================="

    echo "使用JWT: ${JWT:0:50}..."

    SESSION=$(curl -s -X POST "https://battlecraft.tuimotuimo.com/battlecraft/account/loginsession" \
      -H "Host: battlecraft.tuimotuimo.com" \
      -H "Accept: */*" \
      -H "Accept-Encoding: deflate, gzip" \
      -H "Cookie: $COOKIE" \
      -H "Content-Type: application/x-www-form-urlencoded" \
      -H "ssn: $SSN" \
      -H "ver: $VER" \
      --data "timezone=8&v2=true&v3=true&session=$JWT&deviceId=$DEVICE_ID&tutorialType=ugc" \
      --compressed \
      | grep -o '"sessionid":"[^"]*"' | cut -d'"' -f4)

    if [ -z "$SESSION" ]; then
        echo "获取Session失败，退出"
        echo -e "${CYAN}按回车键返回主菜单...${NC}"
        read input
        return
    fi

    echo "获取Session成功: ${SESSION:0:50}..."

    ROOM_RESPONSE=$(curl -s -X POST "https://battlecraft.tuimotuimo.com/battlecraft/matchpvp/getroomids" \
      -H "Content-Type: application/x-www-form-urlencoded" \
      -H "Auth: $SESSION" \
      -H "ssn: $SSN" \
      -H "ver: $VER" \
      -H "Cookie: $COOKIE" \
      -d "start=0&count=100")

    ROOM_IDS=$(echo "$ROOM_RESPONSE" | grep -o '"matchRoomIds":\[[^]]*\]' | grep -o '"[a-z0-9]*"' | tr -d '"' | tr '\n' ',' | sed 's/,$//')

    if [ -z "$ROOM_IDS" ]; then
        echo "未获取到房间ID"
        echo -e "${CYAN}按回车键返回主菜单...${NC}"
        read input
        return
    fi

    echo "获取到房间ID: $ROOM_IDS"

    ROOM_DETAIL_RESPONSE=$(curl -s -X POST "https://battlecraft.tuimotuimo.com/battlecraft/matchpvp/getroomlist" \
      -H "Content-Type: application/x-www-form-urlencoded" \
      -H "Auth: $SESSION" \
      -H "ssn: $SSN" \
      -H "ver: $VER" \
      -H "Cookie: $COOKIE" \
      -d "ids=$ROOM_IDS")

    echo ""
    echo "========== 玩家列表 =========="

    python3 << EOF 2>/dev/null
import json
import sys

try:
    data = json.loads("""$ROOM_DETAIL_RESPONSE""")
    rooms = data.get("data", {}).get("matchRooms", [])
    
    if not rooms:
        print("暂无玩家")
        sys.exit(0)
    
    players = []
    for room in rooms:
        owner = room.get("owner", {})
        room_id = room.get("id", "N/A")
        nick = owner.get("nickName", "未知")
        short_id = owner.get("userShortId", "N/A")
        players.append((nick, room_id, short_id))
    
    for i in range(0, len(players), 2):
        p1_nick, p1_room, p1_short = players[i]
        line = f"{p1_nick} [房间:{p1_room}] [短ID:{p1_short}]"
        
        if i + 1 < len(players):
            p2_nick, p2_room, p2_short = players[i + 1]
            line += f"  |  {p2_nick} [房间:{p2_room}] [短ID:{p2_short}]"
        
        print(line)
    
    print(f"\n总计: {len(players)} 人")
    
except Exception as e:
    print("[解析失败，显示原始数据]")
    print(json.dumps(json.loads("""$ROOM_DETAIL_RESPONSE"""), indent=2, ensure_ascii=False))
EOF

    if [ $? -ne 0 ]; then
        echo "$ROOM_DETAIL_RESPONSE"
    fi

    echo "=============================="
    echo -e "\n${CYAN}按回车键返回主菜单...${NC}"
    read input
}

# ==================== 功能2：地图查询（增强版） ====================
func_map_query() {
    print_header
    echo -e "${YELLOW}>>> 派对制造地图查询（增强版）${NC}\n"

    JWT="$JWT"
    DEVICE_ID="$DEVICE_ID"
    SSN="$SSN"
    VER="$VER"
    COOKIE="$COOKIE"
    PAGE_SIZE=5

    base36_to_decimal() {
        local base36_str="$1"
        local decimal=0
        local base=36
        local len=${#base36_str}
        for ((i=0; i<len; i++)); do
            char="${base36_str:$i:1}"
            if [[ "$char" =~ [0-9] ]]; then
                val=$((char))
            elif [[ "$char" =~ [a-z] ]]; then
                val=$(( $(printf "%d" "'$char") - $(printf "%d" "'a") + 10 ))
            elif [[ "$char" =~ [A-Z] ]]; then
                val=$(( $(printf "%d" "'$char") - $(printf "%d" "'A") + 10 ))
            else
                echo "-1"
                return 1
            fi
            decimal=$((decimal * base + val))
        done
        echo "$decimal"
    }

    echo -e "${BLUE}=== 派对制造 地图+评论查询 ===${NC}"
    read -p "请输入地图代码：" CODE
    MAP_ID=$(base36_to_decimal "$CODE")
    if [ "$MAP_ID" = "-1" ]; then
        echo -e "${RED}地图码错误${NC}"
        echo -e "${CYAN}按回车键返回主菜单...${NC}"
        read input
        return
    fi
    echo "地图ID: $MAP_ID"

    echo -e "\n→ 登录获取会话..."
    LOGIN_RESP=$(curl -s -X POST "https://battlecraft.tuimotuimo.com/battlecraft/account/loginsession" \
      -H "Content-Type: application/x-www-form-urlencoded" \
      -H "ssn: $SSN" \
      -H "ver: $VER" \
      -H "Cookie: $COOKIE" \
      --data-urlencode "timezone=8" \
      --data-urlencode "v2=true" \
      --data-urlencode "v3=true" \
      --data-urlencode "session=$JWT" \
      --data-urlencode "deviceId=$DEVICE_ID" \
      --data-urlencode "tutorialType=ugc" \
      --compressed)

    SESSION=$(echo "$LOGIN_RESP" | grep -o '"sessionid":"[^"]*"' | cut -d'"' -f4)
    if [ -z "$SESSION" ]; then
        echo -e "${RED}登录失败${NC}"
        echo -e "${CYAN}按回车键返回主菜单...${NC}"
        read input
        return
    fi
    echo -e "${GREEN}✅ 登录成功${NC}"

    echo -e "\n${GREEN}=== 地图详细信息 ===${NC}"
    MAP_RESP=$(curl -s -X POST "https://battlecraft.tuimotuimo.com/battlecraft/ugclevel/get" \
      -H "Auth: $SESSION" \
      -H "ssn: $SSN" \
      -H "ver: $VER" \
      -H "Cookie: $COOKIE" \
      -H "Content-Type: application/x-www-form-urlencoded" \
      -d "id=$MAP_ID&needMarkList=false")

    python3 - << EOF
import sys, json, time

data = json.loads("""$MAP_RESP""")
code = data.get('code', -1)
if code != 0:
    print(f"❌ 查询失败，错误码: {code}")
    sys.exit(0)

lev = data.get('data', {}).get('level', {})
owner = lev.get('owner', {})
owner_clan = owner.get('clan', {})

# 辅助函数：十进制转36进制
def to_base36(num):
    if num == 0:
        return "0"
    digits = "0123456789abcdefghijklmnopqrstuvwxyz"
    res = ""
    n = num
    while n > 0:
        n, rem = divmod(n, 36)
        res = digits[rem] + res
    return res

map_code = to_base36(lev.get('id', 0))

# ==================== 基础信息 ====================
print(f"\n📌 【基础信息】")
print(f"  地图名称：{lev.get('name', '无')}")
print(f"  地图ID：{lev.get('id', '无')}")
print(f"  地图码：{map_code}")
print(f"  模板ID：{lev.get('templateID', '无')}")
print(f"  版本：{lev.get('version', '无')}")
print(f"  发布时间：{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(lev.get('timestamp', 0) / 1000)) if lev.get('timestamp') else '未知'}")

# ==================== 状态信息 ====================
status = lev.get('status', 0)
in_trash = lev.get('inTrash', False)

status_desc = ""
if status == 1:
    status_desc = "🔴 官方亲自下线地图"
elif status == 2:
    status_desc = "⚠️ 巡检屏蔽告示牌"
elif 11 <= status <= 20:
    status_desc = "🟡 可能审核中"
elif status >= 21:
    status_desc = "⏳ 审核中"
else:
    status_desc = "✅ 正常"

trash_desc = "🗑️ 已删除" if in_trash else "✅ 未删除"

print(f"\n📋 【状态信息】")
print(f"  地图状态：{status_desc} (status={status})")
print(f"  回收站状态：{trash_desc}")
print(f"  上传状态：{'已上传' if lev.get('uploaded') else '未上传'}")

# ==================== 游玩数据 ====================
play_count = lev.get('playCount', 0)
finish_count = lev.get('finishCount', 0)
if play_count > 0:
    pass_rate = (finish_count / play_count) * 100
    pass_rate_str = f"{pass_rate:.2f}%"
else:
    pass_rate_str = "0%"

ratings = lev.get('ratings', 0)
rating_desc = ""
if 1 <= ratings <= 2:
    rating_desc = "精选 ⭐⭐"
elif 3 <= ratings <= 4:
    rating_desc = "推荐 ⭐⭐⭐"
elif ratings >= 5:
    rating_desc = "强烈推荐 ⭐⭐⭐⭐⭐"
else:
    rating_desc = "无评级"

star_tag = lev.get('starTag', 0)

print(f"\n🎮 【游玩数据】")
print(f"  游玩次数：{play_count}")
print(f"  通关次数：{finish_count}")
print(f"  通关率：{pass_rate_str}")
print(f"  点赞数：{lev.get('likes', 0)}")
print(f"  点踩数：{lev.get('dislike', 0)}")
print(f"  举报数：{lev.get('reports', 0)}")
print(f"  评分：{rating_desc} (ratings={ratings})")
print(f"  需领取星星数：{star_tag}")
print(f"  最佳单人分数：{lev.get('bestScore', 0)}")

# ==================== 模式属性 ====================
print(f"\n🎯 【模式属性】")
print(f"  是否双人地图：{'是' if lev.get('pvpOnly') else '否'}")
print(f"  是否仅PVP模式：{'是' if lev.get('pvpOnly') else '否'}")
print(f"  通关是否需要星星：{'是' if lev.get('needAllStar') else '否'}")
print(f"  重生类型：{lev.get('respawnType', 0)} (0:默认 1:气泡 )")

# ==================== 全景图 ====================
has_panorama = lev.get('havePanorama', False)
print(f"\n🌄 【全景图】")
print(f"  作者是否解锁全景图：{'是 ✅' if has_panorama else '否 ❌'}")

# ==================== 评论统计 ====================
comments_baned = lev.get('comentsBaned', 0)
comment_info = lev.get('commentInfo', {})
baned_count = comment_info.get('banedCount', 0)
total_comments = lev.get('coments', 0)

print(f"\n💬 【评论信息】")
print(f"  评论总数：{total_comments}")
print(f"  被屏蔽评论数：{comments_baned}")
print(f"  被屏蔽评论数：{baned_count}")
# 其实这两个数值上一样
# 置顶评论信息
sticky = comment_info.get('stickyComment')
if sticky:
    print("\n==== 🌟 置顶评论 ====")
    p = sticky.get('player', {})
    ts = sticky.get('ts', 0) / 1000
    dt = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(ts))
    typ = sticky.get('type')
    content = sticky.get('content')
    show = content if typ == 'text' else f'stamp:{content}'
    print(f"时间：{dt}")
    print(f"用户：{p.get('nickName', '无')} | 短ID：{p.get('userShortId', '无')}")
    print(f"评论ID：{sticky.get('id')}")
    print(f"内容：{show}")

# ==================== 作者信息 ====================
print(f"\n👤 【作者信息】")
print(f"  昵称：{owner.get('nickName', '未知')}")
print(f"  短ID：{owner.get('userShortId', '无')}")
print(f"  用户ID：{owner.get('userid', '无')}")
print(f"  段位：{owner.get('dan', 0)}")
print(f"  等级：{owner.get('level', 0)}")
print(f"  性别：{('男' if owner.get('gender') == 1 else '女' if owner.get('gender') == 2 else '保密')}")
print(f"  称号：{owner.get('title', '无')}")
print(f"  头像边框：{owner.get('border', '无')}")
print(f"  城市：{owner.get('city', '未知')}")
print(f"  省份：{owner.get('province', '未知')}")
print(f"  战队：{owner_clan.get('name', '无战队')}")
print(f"  战队徽章：{owner_clan.get('badge', '无')}")

# ==================== 标签（关闭映射，显示原始值） ====================
tags = lev.get('tags', [])
print(f"\n🏷️ 【标签】")
if tags:
    print(f"  {', '.join(tags)}")
else:
    print("  无")

# ==================== 排行榜预览 ====================
top = lev.get("top", [])
if top:
    print(f"\n🏆 【单人排行榜 Top 3】")
    for i, item in enumerate(top[:3], 1):
        p = item.get("player", {})
        print(f"  {i}. {p.get('nickName','未知')} | 短ID:{p.get('userShortId','无')} | 分数:{item.get('record',0)}")

EOF

    echo -e "\n"
    read -p "是否查看全部评论？(y/n) " view_comment
    if [ "$view_comment" != "y" ]; then
        echo -e "${GREEN}查询完成！${NC}"
        echo -e "${CYAN}按回车键返回主菜单...${NC}"
        read input
        return
    fi

    echo -e "\n${YELLOW}=== 评论列表（步长$PAGE_SIZE，支持跳页） ===${NC}"
    echo "操作说明："
    echo "  输入 y或回车 → 下一页"
    echo "  输入 n → 退出"
    echo "  输入数字 → 直接跳转到指定页码，超过103页的评论部分无法获取"
    echo "----------------------------------------"

    current_page=1
    start=0

    while true; do
        echo -e "\n---- 第 $current_page 页 ----"

        COMMENT_RESP=$(curl -s -X POST "https://battlecraft.tuimotuimo.com/battlecraft/ugclevel/getcomments" \
          -H "Auth: $SESSION" \
          -H "ssn: $SSN" \
          -H "ver: $VER" \
          -H "Cookie: $COOKIE" \
          -H "Content-Type: application/x-www-form-urlencoded" \
          -d "id=$MAP_ID&start=$start&count=$PAGE_SIZE")

        python3 << EOF
import sys, json, time
data = json.loads("""$COMMENT_RESP""")
coms = data.get('data', {}).get('comments', [])
if not coms:
    print("无更多评论")
    sys.exit()

for c in coms:
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
EOF

        read -p "请选择操作(y/n/页码): " op
        if [ "$op" = "n" ]; then
            break
        elif [[ "$op" =~ ^[0-9]+$ ]]; then
            target_page=$op
            if [ "$target_page" -lt 1 ]; then
                echo -e "${RED}页码不能小于1，自动跳转到第1页${NC}"
                target_page=1
            fi
            current_page=$target_page
            start=$(( (target_page - 1) * PAGE_SIZE ))
            echo -e "${YELLOW}已跳转到第$current_page页${NC}"
        elif [ "$op" = "y" ]; then
            current_page=$((current_page + 1))
            start=$((start + PAGE_SIZE))
        else
            echo -e "${RED}无效输入，继续下一页${NC}"
            current_page=$((current_page + 1))
            start=$((start + PAGE_SIZE))
        fi
    done

    echo -e "\n${GREEN}✅ 查询完成！${NC}"
    echo -e "${CYAN}按回车键返回主菜单...${NC}"
    read input
}

# ==================== 功能3：排行榜查询 ====================
func_rank_query() {
    while true; do
        print_header
        echo -e "${YELLOW}>>> 派对制造排行榜查询${NC}\n"
        
        echo -e "${GREEN}请选择排行榜类型：${NC}"
        echo "  1. 创造榜（本周周榜）"
        echo "  2. 操作榜（本周周榜）"
        echo "  3. 联赛榜"
        echo "  4. 创造榜（总榜）"
        echo "  5. 操作榜（总榜）"
        echo "  0. 返回主菜单"
        echo ""
        
        read -p "请选择 [0-5]: " rank_type
        
        case $rank_type in
            1)
                rank_name="creative"
                rank_id="week"
                title="创造榜（本周周榜）"
                ;;
            2)
                rank_name="skill"
                rank_id="week"
                title="操作榜（本周周榜）"
                ;;
            3)
                rank_name="leaguescore"
                rank_id="0060"
                title="联赛榜"
                ;;
            4)
                rank_name="creative"
                rank_id="all"
                title="创造榜（总榜）"
                ;;
            5)
                rank_name="skill"
                rank_id="all"
                title="操作榜（总榜）"
                ;;
            0)
                return
                ;;
            *)
                echo -e "${RED}无效选项${NC}"
                sleep 1
                continue
                ;;
        esac
        
        echo -e "${BLUE}正在获取会话...${NC}"
        SESSION=$(curl -s -X POST "https://battlecraft.tuimotuimo.com/battlecraft/account/loginsession" \
          -H "Content-Type: application/x-www-form-urlencoded" \
          -H "ssn: $SSN" \
          -H "ver: $VER" \
          -H "Cookie: $COOKIE" \
          --data-urlencode "timezone=8" \
          --data-urlencode "v2=true" \
          --data-urlencode "v3=true" \
          --data-urlencode "session=$JWT" \
          --data-urlencode "deviceId=$DEVICE_ID" \
          --data-urlencode "tutorialType=ugc" \
          --compressed 2>/dev/null | grep -o '"sessionid":"[^"]*"' | cut -d'"' -f4)
        
        if [ -z "$SESSION" ]; then
            echo -e "${RED}获取Session失败${NC}"
            sleep 2
            continue
        fi
        
        echo -e "${GREEN}✅ 会话获取成功${NC}\n"
        echo -e "${BLUE}正在获取$title...${NC}\n"
        
        if [ "$rank_name" = "leaguescore" ]; then
            RANK_RESP=$(curl -s -X POST "https://battlecraft.tuimotuimo.com/battlecraft/ranklist/gettop" \
              -H "Auth: $SESSION" \
              -H "ssn: $SSN" \
              -H "ver: $VER" \
              -H "Cookie: $COOKIE" \
              -H "Content-Type: application/x-www-form-urlencoded" \
              -d "name=$rank_name&count=100&rankId=$rank_id" 2>/dev/null)
        else
            RANK_RESP=$(curl -s -X POST "https://battlecraft.tuimotuimo.com/battlecraft/ranklist/getleveltop" \
              -H "Auth: $SESSION" \
              -H "ssn: $SSN" \
              -H "ver: $VER" \
              -H "Cookie: $COOKIE" \
              -H "Content-Type: application/x-www-form-urlencoded" \
              -d "name=$rank_name&count=100&rankId=$rank_id" 2>/dev/null)
        fi
        
        echo -e "${GREEN}══════════ $title ══════════${NC}\n"
        
        echo "$RANK_RESP" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    ranklist = data.get('data', {}).get('ranklist', [])
    if not ranklist:
        print('  暂无数据')
        sys.exit(0)
    
    print(f\"  {'排名':<4} {'段位':<6} {'玩家昵称':<20} {'短ID':<12} {'分数':<10}\")
    print(f\"  {'-'*60}\")
    
    for i, item in enumerate(ranklist[:100], 1):
        name = item.get('name', '未知')[:18]
        score = item.get('score', 0)
        dan = item.get('dan', 0)
        user_short_id = item.get('userShortId', '')
        clan = item.get('clan', {})
        clan_name = clan.get('name', '')
        
        dan_display = str(dan)
        name_display = name
        if clan_name:
            name_display = f\"[{clan_name}]{name}\"
        
        print(f\"  {i:<4} {dan_display:<6} {name_display:<20} {str(user_short_id):<12} {score:<10}\")
    
    print(f\"\n  📊 共 {len(ranklist)} 条记录\")
except Exception as e:
    print(f'  解析失败: {e}')
"
        
        echo -e "\n${CYAN}按回车键继续...${NC}"
        read input
    done
}

# ==================== 功能4：玩家信息查询（通过地图代码） ====================
func_player_info() {
    print_header
    echo -e "${YELLOW}>>> 派对制造玩家信息查询${NC}\n"
    
    echo -e "${BLUE}请输入该玩家任意地图代码：${NC}"
    read -r map_code
    
    if [ -z "$map_code" ]; then
        echo -e "${YELLOW}已取消${NC}"
        echo -e "${CYAN}按回车键返回主菜单...${NC}"
        read input
        return
    fi
    
    # Base36转十进制
    MAP_ID=$(echo "$map_code" | tr '[:upper:]' '[:lower:]' | python3 -c "
import sys
code = sys.stdin.read().strip()
try:
    print(int(code, 36))
except:
    print('-1')
" 2>/dev/null)
    
    if [ "$MAP_ID" = "-1" ] || [ -z "$MAP_ID" ]; then
        echo -e "${RED}地图码无效${NC}"
        echo -e "${CYAN}按回车键返回主菜单...${NC}"
        read input
        return
    fi
    
    echo -e "${GREEN}地图ID: $MAP_ID${NC}"
    
    # 获取session
    echo -e "\n${BLUE}正在获取会话...${NC}"
    SESSION=$(get_session)
    
    if [ -z "$SESSION" ]; then
        echo -e "${RED}获取Session失败，请检查配置${NC}"
        echo -e "${CYAN}按回车键返回主菜单...${NC}"
        read input
        return
    fi
    
    # 获取地图详情，提取作者userid
    echo -e "${BLUE}正在获取地图信息...${NC}"
    MAP_RESP=$(curl -s --max-time 10 -X POST "https://battlecraft.tuimotuimo.com/battlecraft/ugclevel/get" \
      -H "Auth: $SESSION" \
      -H "ssn: $SSN" \
      -H "ver: $VER" \
      -H "Cookie: $COOKIE" \
      -H "Content-Type: application/x-www-form-urlencoded" \
      -d "id=$MAP_ID&needMarkList=false" 2>/dev/null)
    
    AUTHOR_USERID=$(echo "$MAP_RESP" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    userid = data.get('data', {}).get('level', {}).get('owner', {}).get('userid', '')
    print(userid)
except:
    print('')
" 2>/dev/null)
    
    if [ -z "$AUTHOR_USERID" ]; then
        echo -e "${RED}无法获取作者信息，请确认地图码正确${NC}"
        echo -e "${CYAN}按回车键返回主菜单...${NC}"
        read input
        return
    fi
    
    echo -e "${GREEN}✅ 作者ID: $AUTHOR_USERID${NC}\n"
    
    # 1. 获取玩家基本信息
    echo -e "${BLUE}正在获取玩家信息...${NC}"
    USER_RESP=$(curl -s --max-time 10 -X POST "https://battlecraft.tuimotuimo.com/battlecraft/userrole/detailinfo" \
      -H "Auth: $SESSION" \
      -H "ssn: $SSN" \
      -H "ver: $VER" \
      -H "Cookie: $COOKIE" \
      -H "Content-Type: application/x-www-form-urlencoded" \
      -d "userId=$AUTHOR_USERID" 2>/dev/null)
    
    # 2. 获取关系图谱
    echo -e "${BLUE}正在获取关系图谱...${NC}"
    RELATION_RESP=$(curl -s --max-time 10 -X POST "https://battlecraft.tuimotuimo.com/battlecraft/relation/info" \
      -H "Auth: $SESSION" \
      -H "ssn: $SSN" \
      -H "ver: $VER" \
      -H "Cookie: $COOKIE" \
      -H "Content-Type: application/x-www-form-urlencoded" \
      -d "frdId=$AUTHOR_USERID" 2>/dev/null)
    
    echo -e "\n${GREEN}════════════════════ 玩家档案 ════════════════════${NC}\n"
    
    python3 - << EOF
import sys, json, time

# 解析玩家信息
try:
    user_data = json.loads("""$USER_RESP""")
    user = user_data.get('data', {})
    basic = user.get('basic', {})
    ugc_info = user.get('ugcInfo', {})
    honesty = user.get('honesty', {})
    userlevel = user.get('userlevel', {})
    
    # 基本资料
    nick = basic.get('nickName', '未知')
    gender_map = {1: '男', 2: '女', 0: '保密'}
    gender = gender_map.get(basic.get('gender', 0), '保密')
    level = basic.get('level', 0)
    short_id = basic.get('userShortId', '无')
    dan = basic.get('dan', 0)
    
    # 战队
    clan = basic.get('clan', {})
    clan_name = clan.get('name', '无战队')
    
    # 注册时间
    created_at = basic.get('createdAt', 0)
    if created_at:
        reg_time = time.strftime('%Y-%m-%d', time.localtime(created_at / 1000))
    else:
        reg_time = '未知'
    
    # 人品分
    honesty_score = honesty.get('honesty', 0)
    
    # 各项经验分
    exp = userlevel.get('exp', {})
    exp_creative = exp.get('creative', 0)
    exp_skill = exp.get('skill', 0)
    exp_pvp = exp.get('pvp', 0)
    exp_active = exp.get('active', 0)
    exp_vip = exp.get('vip', 0)
    
    # 排名
    rank = basic.get('rank', 0)
    exp_rank = basic.get('expRank', {})
    creative_rank = exp_rank.get('creative', 0)
    skill_rank = exp_rank.get('skill', 0)
    
    print(f"  👤 昵称: {nick}")
    print(f"  🚻 性别: {gender}")
    print(f"  🎚️ 等级: {level}")
    print(f"  🎖️ 段位: {dan}")
    print(f"  🔢 短ID: {short_id}")
    print(f"  🏠 战队: {clan_name}")
    print(f"  📅 注册日期: {reg_time}")
    print(f"  ⚖️ 人品值: {honesty_score}")
    print(f"  📊 联赛排名: #{rank}")
    print(f"  ✨ 创造榜排名: #{creative_rank}  | 创造经验: {exp_creative}")
    print(f"  🎯 操作榜排名: #{skill_rank}  | 操作经验: {exp_skill}")
    print(f"  ⚔️ 对战经验: {exp_pvp}")
    print(f"  🔥 活跃经验: {exp_active}")
    print(f"  💎 贵族经验: {exp_vip}")
    
    # 地图作品（ID转36进制）
    map_ids = ugc_info.get('ids', [])
    if map_ids:
        def to_base36(num):
            if num == 0:
                return "0"
            digits = "0123456789abcdefghijklmnopqrstuvwxyz"
            res = ""
            while num > 0:
                num, rem = divmod(num, 36)
                res = digits[rem] + res
            return res
        map_codes = [to_base36(mid) for mid in map_ids]
        print(f"\n  🗺️ 玩家发布的地图 ({len(map_ids)}个):")
        for i in range(0, len(map_codes), 3):
            chunk = map_codes[i:i+3]
            print("     " + "  ".join(chunk))
    
except Exception as e:
    print(f"  解析玩家信息失败: {e}")

# 解析关系图谱
print(f"\n  ━━━━━━━━━━━━━━━━━━━━ 亲密关系 ━━━━━━━━━━━━━━━━━━━━")
try:
    rel_data = json.loads("""$RELATION_RESP""")
    relations = rel_data.get('data', {}).get('relation', {}).get('relations', {})
    
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
                f_userShortId = f.get('userShortId', '无')
                f_intimacy = f.get('intimacy', 0)
                show_list.append(f"{f_nick}[{f_userShortId}]({f_intimacy})")
            friends_text = ", ".join(show_list)
            if len(friends) > 3:
                friends_text += f" 等{len(friends)}人"
            print(f"  {icon} {rel_name}: {friends_text}")
        else:
            print(f"  {icon} {rel_name}: 无")
except Exception as e:
    print(f"  解析关系图谱失败: {e}")
EOF
    
    echo -e "\n${CYAN}按回车键返回主菜单...${NC}"
    read input
}

# ==================== 功能5：最新地图查询（新增） ====================
func_latest_maps() {
    while true; do
        print_header
        echo -e "${YELLOW}>>> 最新地图查询${NC}\n"
        
        echo -e "${GREEN}请选择难度类型：${NC}"
        echo "  1. 所有难度"
        echo "  2. 简单"
        echo "  3. 中等"
        echo "  4. 困难"
        echo "  5. 超难"
        echo "  6. 自定义查询数量（当前: $MAP_COUNT）"
        echo "  0. 返回主菜单"
        echo ""
        
        read -p "请选择 [0-6]: " diff_choice
        
        case $diff_choice in
            1)
                query_latest_maps "all" "所有"
                ;;
            2)
                query_latest_maps "easy" "简单"
                ;;
            3)
                query_latest_maps "medium" "中等"
                ;;
            4)
                query_latest_maps "hard" "困难"
                ;;
            5)
                query_latest_maps "insane" "超难"
                ;;
            6)
                echo -e "\n${BLUE}当前查询数量: $MAP_COUNT (最大100)${NC}"
                echo -e "${YELLOW}请输入新的查询数量 [1-100]:${NC}"
                read -r new_count
                if [[ "$new_count" =~ ^[0-9]+$ ]] && [ "$new_count" -ge 1 ] && [ "$new_count" -le 100 ]; then
                    MAP_COUNT=$new_count
                    save_config
                    echo -e "${GREEN}✅ 查询数量已设置为 $MAP_COUNT${NC}"
                else
                    echo -e "${RED}❌ 输入无效，请输入1-100之间的数字${NC}"
                fi
                sleep 1
                ;;
            0)
                return
                ;;
            *)
                echo -e "${RED}无效选项${NC}"
                sleep 1
                ;;
        esac
    done
}

query_latest_maps() {
    local rank_type=$1
    local rank_name=$2
    
    print_header
    echo -e "${YELLOW}>>> 查询最新地图 (${rank_name})${NC}\n"
    
    echo -e "${BLUE}[1/3] 获取Session...${NC}"
    SESSION=$(get_session)
    
    if [ -z "$SESSION" ]; then
        echo -e "${RED}❌ 获取Session失败${NC}"
        echo -e "${CYAN}按回车键返回...${NC}"
        read input
        return 1
    fi
    echo -e "${GREEN}✅ Session获取成功${NC}\n"
    
    # 构建rank参数
    if [ "$rank_type" = "all" ]; then
        RANK_PARAM="all"
    else
        RANK_PARAM="$rank_type"
    fi
    
    echo -e "${BLUE}[2/3] 获取地图ID列表 (数量: $MAP_COUNT)...${NC}"
    
    RANGE_RESP=$(curl -s -X POST "https://battlecraft.tuimotuimo.com/battlecraft/ugclevel/range2" \
      -H "Cookie: $COOKIE" \
      -H "Auth: $SESSION" \
      -H "Content-Type: application/x-www-form-urlencoded" \
      -H "ssn: $SSN" \
      -H "ver: $VER" \
      -d "start=0&count=$MAP_COUNT&idonly=true&filter=latest&rank=$RANK_PARAM" 2>/dev/null)
    
    # 提取ID列表
    MAP_IDS=$(echo "$RANGE_RESP" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    ids = data.get('data', {}).get('levelIds', [])
    print(','.join(str(i) for i in ids))
except:
    print('')
" 2>/dev/null)
    
    if [ -z "$MAP_IDS" ]; then
        echo -e "${RED}❌ 获取地图ID列表失败${NC}"
        echo -e "${CYAN}按回车键返回...${NC}"
        read input
        return 1
    fi
    
    ID_COUNT=$(echo "$MAP_IDS" | tr ',' '\n' | grep -c .)
    echo -e "${GREEN}✅ 获取到 $ID_COUNT 个地图ID${NC}\n"
    
    echo -e "${BLUE}[3/3] 获取地图详情...${NC}"
    
    # 使用/storage/emulated/0/目录，确保可访问
    TEMP_DIR="/storage/emulated/0/party_tool_temp"
    mkdir -p "$TEMP_DIR" 2>/dev/null
    TEMP_FILE="$TEMP_DIR/latest_maps_temp.json"
    
    curl -s -X POST "https://battlecraft.tuimotuimo.com/battlecraft/ugclevel/getlist" \
      -H "Cookie: $COOKIE" \
      -H "Auth: $SESSION" \
      -H "Content-Type: application/x-www-form-urlencoded" \
      -H "ssn: $SSN" \
      -H "ver: $VER" \
      --data-urlencode "ids=$MAP_IDS" \
      --data-urlencode "needBestPlayer=false" \
      --data-urlencode "needMarkList=false" \
      --data-urlencode "needAlbum=false" 2>/dev/null > "$TEMP_FILE"
    
    echo -e "\n${GREEN}════════════════ 最新地图列表 (${rank_name}) ════════════════${NC}\n"
    
    # 使用Python解析并显示
    python3 << EOF
import json

def to_base36(num):
    if num == 0:
        return "0"
    digits = "0123456789abcdefghijklmnopqrstuvwxyz"
    res = ""
    n = num
    while n > 0:
        n, rem = divmod(n, 36)
        res = digits[rem] + res
    return res

try:
    with open("$TEMP_FILE", "r", encoding="utf-8") as f:
        data = json.load(f)
    
    if data.get('code') != 0:
        print(f"  接口返回错误码: {data.get('code')}")
        print(f"  错误信息: {data.get('msg', '未知')}")
        sys.exit(0)
    
    levels = data.get('data', {}).get('levels', [])
    
    if not levels:
        print("  ⚠️ 暂无数据")
        sys.exit(0)
    
    # 难度类型映射
    rank_names = {
        'easy': '简单',
        'medium': '中等',
        'hard': '困难',
        'insane': '超难'
    }
    
    # 表头
    print(f"  {'序号':<4} {'地图名称':<20} {'地图码':<10} {'难度':<6} {'作者':<12} {'游玩':<8} {'点赞':<6} {'评论':<6}")
    print(f"  {'─'*85}")
    
    for idx, lev in enumerate(levels, 1):
        map_id = lev.get('id', 0)
        map_code = to_base36(map_id)
        map_name = lev.get('name', '无名称')
        if len(map_name) > 18:
            map_name = map_name[:16] + ".."
        
        rank = lev.get('rank', 'unknown')
        rank_display = rank_names.get(rank, rank)
        
        play_count = lev.get('playCount', 0)
        likes = lev.get('likes', 0)
        coments = lev.get('coments', 0)
        
        owner = lev.get('owner', {})
        author_name = owner.get('nickName', '未知')
        if len(author_name) > 10:
            author_name = author_name[:8] + ".."
        
        # 格式化数字（千分位）
        if play_count >= 1000:
            play_str = f"{play_count:,}"
        else:
            play_str = str(play_count)
        
        print(f"  {idx:<4} {map_name:<20} {map_code:<10} {rank_display:<6} {author_name:<12} {play_str:<8} {likes:<6} {coments:<6}")
    
    # 统计汇总
    total_play = sum(l.get('playCount', 0) for l in levels)
    total_likes = sum(l.get('likes', 0) for l in levels)
    total_comments = sum(l.get('coments', 0) for l in levels)
    
    print(f"\n  📊 统计汇总")
    print(f"     共 {len(levels)} 个地图")
    print(f"     总游玩次数: {total_play:,}")
    print(f"     总点赞数: {total_likes}")
    print(f"     总评论数: {total_comments}")

except Exception as e:
    print(f"  ❌ 解析失败: {e}")
EOF
    
    # 清理临时文件
    rm -f "$TEMP_FILE"
    rmdir "$TEMP_DIR" 2>/dev/null
    
    echo -e "\n${CYAN}════════════════════════════════════════════════════════${NC}"
    echo -e "\n${CYAN}按回车键返回菜单...${NC}"
    read input
}

# ==================== 功能6：金矿打工 ====================
func_gold_mine() {
    print_header
    echo -e "${YELLOW}>>> 金矿打工${NC}\n"
    
    echo -e "${BLUE}请输入作者的地图代码（例如：jskru）${NC}"
    echo -n "地图代码: "
    read map_code
    if [ -z "$map_code" ]; then
        echo -e "${RED}❌ 未输入地图代码${NC}"
        echo -e "${CYAN}按回车键返回主菜单...${NC}"
        read input
        return
    fi

    # 1. 转换地图代码 -> 十进制ID
    echo -e "\n${BLUE}[1/4] 转换地图代码...${NC}"
    map_id=$(echo "$map_code" | python3 -c "import sys; print(int(sys.stdin.read().strip().lower(), 36))" 2>/dev/null)
    if [ -z "$map_id" ] || [ "$map_id" = "0" ]; then
        echo -e "${RED}❌ 无效的地图代码${NC}"
        echo -e "${CYAN}按回车键返回主菜单...${NC}"
        read input
        return
    fi
    echo -e "${GREEN}✓ 地图ID: $map_id${NC}"

    # 2. 获取 Session
    echo -e "\n${BLUE}[2/4] 获取会话...${NC}"
    session=$(get_session)
    if [ -z "$session" ]; then
        echo -e "${RED}❌ 获取 Session 失败，请检查网络或配置${NC}"
        echo -e "${CYAN}按回车键返回主菜单...${NC}"
        read input
        return
    fi
    echo -e "${GREEN}✓ Session 获取成功${NC}"

    # 3. 查询地图详情，提取作者 userid
    echo -e "\n${BLUE}[3/4] 查询地图作者...${NC}"
    map_resp=$(curl -s -X POST "https://battlecraft.tuimotuimo.com/battlecraft/ugclevel/get" \
      -H "Auth: $session" \
      -H "ssn: $SSN" \
      -H "ver: $VER" \
      -H "Cookie: $COOKIE" \
      -H "Content-Type: application/x-www-form-urlencoded" \
      -d "id=$map_id&needMarkList=false")

    # 用 Python 提取 userid
    friend_id=$(echo "$map_resp" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    userid = data.get('data', {}).get('level', {}).get('owner', {}).get('userid', '')
    if userid:
        print(userid)
    else:
        print('')
except:
    print('')
" 2>/dev/null)

    if [ -z "$friend_id" ]; then
        echo -e "${RED}❌ 无法获取作者信息，请确认地图代码正确${NC}"
        echo -e "${CYAN}按回车键返回主菜单...${NC}"
        read input
        return
    fi
    echo -e "${GREEN}✓ 作者ID: $friend_id${NC}"

    # 4. 发起打工请求
    echo -e "\n${BLUE}[4/4] 发送打工请求...${NC}"
    work_resp=$(curl -s -X POST "https://battlecraft.tuimotuimo.com/battlecraft/bank/startwork" \
      -H "Auth: $session" \
      -H "ssn: $SSN" \
      -H "ver: $VER" \
      -H "Cookie: $COOKIE" \
      -H "Content-Type: application/x-www-form-urlencoded" \
      -d "friendId=$friend_id")

    # 打印原始响应
    echo -e "${CYAN}原始响应：${NC}"
    echo "$work_resp"
    echo ""

    # 解析结果
    code=$(echo "$work_resp" | python3 -c "import sys, json; print(json.load(sys.stdin).get('code', -1))" 2>/dev/null)
    if [ "$code" = "0" ]; then
        nick=$(echo "$work_resp" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('data',{}).get('receiver',{}).get('nickName',''))" 2>/dev/null)
        echo -e "${GREEN}════════════════════════════════════════${NC}"
        echo -e "${GREEN}✅ 打工成功！${NC}"
        echo -e "   你正在为 ${CYAN}$nick${NC} 的金矿工作"
        echo -e "${GREEN}════════════════════════════════════════${NC}"
    else
        msg=$(echo "$work_resp" | python3 -c "import sys, json; print(json.load(sys.stdin).get('msg', '未知错误'))" 2>/dev/null)
        echo -e "${RED}❌ 打工失败：$msg${NC}"
    fi

    echo -e "\n${CYAN}按回车键返回主菜单...${NC}"
    read input
}

# ==================== 主程序 ====================
check_and_install_python
load_config

while true; do
    print_header
    print_menu
    read -p "请选择功能: " choice
    
    case $choice in
        A|a)
            func_show_ip
            ;;
        B|b)
            func_device_setup
            ;;
        C|c)
            func_game_version
            ;;
        D|d)
            func_game_notice
            ;;
        E|e)
            func_github_notice
            ;;
        F|f)
            func_toolbox_version
            ;;
        1)
            func_room_list
            ;;
        2)
            func_map_query
            ;;
        3)
            func_rank_query
            ;;
        4)
            func_player_info
            ;;
        5)
            func_latest_maps
            ;;
        6)
            func_gold_mine
            ;;
        0)
            echo -e "\n${GREEN}感谢使用派对制造工具箱！${NC}"
            save_config
            exit 0
            ;;
        *)
            echo -e "${RED}无效选项，请重新选择${NC}"
            sleep 1
            ;;
    esac
done