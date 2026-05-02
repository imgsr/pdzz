#!/system/bin/sh

# ==================== 派对制造工具箱 ====================
# 版本：3.1 - 新增版本查询和公告查询

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m'

# 配置文件路径
CONFIG_FILE="/data/local/tmp/party_tool_config.txt"

# ==================== 默认配置 ====================
DEFAULT_JWT="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJkZXZJZCI6IjMzOWY3YWJhZTg2OGI3ZjBhODMzODc3YjBkNWQ0NjQ1XG5kYTNkYzlhOTk5Mjg5OGY5MDk2YWI5MjAyOTVkM2ZhZSIsImZsYWciOiJiZGY2IiwiZnJvbSI6InRhcHRhcCIsImx0IjoiZ3Vlc3QiLCJzc24iOiI1Mjk5IiwidXNlcmlkIjoiNjlmNTk5MDNlOGQ1YjU1YmI0ZWViYjAyIiwidiI6IjAifQ.RHQ1EK0pEwiXBTILUyLNgHCetsfO57fUmJtcMGPqG-A"
DEFAULT_DEVICE_ID="339f7abae868b7f0a833877b0d5d46454a3dc9a9992898f9096ab920295d3fae"
DEFAULT_SSN="3c05"
DEFAULT_VER="2.1.92"
DEFAULT_COOKIE="SERVERID=769e7e1294f37fd70e4a8fd5d4a4a403|1774672107|1774600237"

# ==================== 随机生成Device ID ====================
generate_random_device_id() {
    # 生成32位十六进制随机数
    RANDOM_ID=$(openssl rand -hex 16 2>/dev/null)
    if [ -z "$RANDOM_ID" ]; then
        # 如果openssl不可用，使用系统随机数
        RANDOM_ID=$(cat /dev/urandom 2>/dev/null | head -c 16 | od -An -tx1 | tr -d ' \n')
    fi
    if [ -z "$RANDOM_ID" ]; then
        # 最后的备选方案
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
    # Device ID：如果配置文件中没有，则随机生成；如果有则使用现有的
    if [ -z "$DEVICE_ID" ]; then
        DEVICE_ID=$(generate_random_device_id)
    fi
    SSN=${SSN:-$DEFAULT_SSN}
    VER=${VER:-$DEFAULT_VER}
    COOKIE=${COOKIE:-$DEFAULT_COOKIE}
}

save_config() {
    cat > "$CONFIG_FILE" << EOF
JWT="$JWT"
DEVICE_ID="$DEVICE_ID"
SSN="$SSN"
VER="$VER"
COOKIE="$COOKIE"
EOF
}

# ==================== 工具函数 ====================
clear_screen() {
    printf "\033[2J\033[H"
}

print_header() {
    clear_screen
    echo -e "${CYAN}╔════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║      派对制造 Shell 工具箱 v3.1       ║${NC}"
    echo -e "${CYAN}╚════════════════════════════════════════╝${NC}"
    echo ""
}

print_menu() {
    echo -e "${YELLOW}════════════════ 主菜单 ════════════════${NC}"
    echo -e "${GREEN}A. 查看当前IP地址${NC}"
    echo -e "${GREEN}B. 设备ID设置${NC}"
    echo -e "${GREEN}C. 查询游戏版本信息${NC}"
    echo -e "${GREEN}D. 查询游戏公告${NC}"
    echo -e "${GREEN}1. 派对制造房间列表${NC}"
    echo -e "${GREEN}2. 派对制造地图查询${NC}"
    echo -e "${GREEN}3. 派对制造排行榜查询${NC}"
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
    
    # 按顺序显示主要平台
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
            # 标记当前版本
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
    
    # 当前公告
    notice = data.get('notice', {})
    notice_type = notice.get('type', 'normal')
    notice_title = notice.get('title', '')
    notice_text = notice.get('text', '')
    
    # 后续公告
    notice_after = data.get('noticeAfter', {})
    after_type = notice_after.get('type', 'normal')
    after_title = notice_after.get('title', '')
    after_text = notice_after.get('text', '')
    
    if notice_title or notice_text:
        print(f\"  {'='*50}\")
        print(f\"  📢 {'【重要公告】' if notice_type == 'stopServer' else '【当前公告】'}\")
        if notice_title:
            print(f\"  {notice_title}\")
        if notice_text:
            print(f\"\\n{notice_text}\\n\" if len(notice_text) > 50 else f\"\\n  {notice_text}\\n\")
    
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
    
    # 一行显示两个玩家
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

# ==================== 功能2：地图查询 ====================
func_map_query() {
    print_header
    echo -e "${YELLOW}>>> 派对制造地图查询${NC}\n"

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
    read -p "请输入地图Base36代码：" CODE
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

    echo -e "\n${GREEN}=== 地图信息 ===${NC}"
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
lev = data.get('data', {}).get('level', {})
owner = lev.get('owner', {})

print(f"地图名称：{lev.get('name', '无')}")
print(f"地图ID：{lev.get('id', '无')}")
print(f"作者：{owner.get('nickName', '无')}  | 短ID：{owner.get('userShortId', '无')}")

print("\n==== 单人排行榜 ====")
top = lev.get("top", [])
for i, item in enumerate(top[:3], 1):
    p = item.get("player", {})
    print(f"第{i}名：{p.get('nickName','无')} | 短ID：{p.get('userShortId','无')}")

sticky = lev.get('commentInfo', {}).get('stickyComment')
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
    echo "  输入 y → 下一页"
    echo "  输入 n → 退出"
    echo "  输入数字 → 直接跳转到指定页码（例：输入10 → 跳转到第10页）"
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

        python3 - << EOF
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
              -d "name=$rank_name&count=30&rankId=$rank_id" 2>/dev/null)
        else
            RANK_RESP=$(curl -s -X POST "https://battlecraft.tuimotuimo.com/battlecraft/ranklist/getleveltop" \
              -H "Auth: $SESSION" \
              -H "ssn: $SSN" \
              -H "ver: $VER" \
              -H "Cookie: $COOKIE" \
              -H "Content-Type: application/x-www-form-urlencoded" \
              -d "name=$rank_name&count=30&rankId=$rank_id" 2>/dev/null)
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
    
    for i, item in enumerate(ranklist[:30], 1):
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

# ==================== 主程序 ====================
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
        1)
            func_room_list
            ;;
        2)
            func_map_query
            ;;
        3)
            func_rank_query
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