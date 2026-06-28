#!/usr/bin/env node

/**
 * 派对制造 - 自动进入房间工具
 * 使用工具箱配置文件
 */

const https = require('https');
const readline = require('readline');
const fs = require('fs');
const path = require('path');

// ==================== 配置文件路径 ====================
// 与工具箱保持一致
const TOOL_CONFIG_DIR = process.env.HOME 
    ? path.join(process.env.HOME, '.party_tool')
    : path.join(__dirname, '.party_tool');
const TOOL_CONFIG_FILE = path.join(TOOL_CONFIG_DIR, 'config.txt');

// 脚本自己的配置目录
const SCRIPT_CONFIG_DIR = path.join(__dirname, 'party_config');
const SCRIPT_CONFIG_FILE = path.join(SCRIPT_CONFIG_DIR, 'config.txt');

// ==================== 颜色 ====================
const colors = {
    green: '\x1b[0;32m',
    yellow: '\x1b[1;33m',
    blue: '\x1b[0;34m',
    red: '\x1b[0;31m',
    cyan: '\x1b[0;36m',
    magenta: '\x1b[0;35m',
    nc: '\x1b[0m'
};

function log(color, msg) {
    console.log(`${color}${msg}${colors.nc}`);
}

// ==================== 读取工具箱配置 ====================
function loadToolConfig() {
    try {
        if (fs.existsSync(TOOL_CONFIG_FILE)) {
            const content = fs.readFileSync(TOOL_CONFIG_FILE, 'utf8');
            const config = {};
            content.split('\n').forEach(line => {
                const [key, ...rest] = line.split('=');
                if (key && rest.length) {
                    config[key.trim()] = rest.join('=').trim();
                }
            });
            return config;
        }
    } catch (e) {}
    return null;
}

// ==================== 读取/保存脚本配置 ====================
function loadScriptConfig() {
    try {
        if (!fs.existsSync(SCRIPT_CONFIG_DIR)) {
            fs.mkdirSync(SCRIPT_CONFIG_DIR, { recursive: true });
        }
        if (fs.existsSync(SCRIPT_CONFIG_FILE)) {
            const content = fs.readFileSync(SCRIPT_CONFIG_FILE, 'utf8');
            const config = {};
            content.split('\n').forEach(line => {
                const [key, ...rest] = line.split('=');
                if (key && rest.length) {
                    config[key.trim()] = rest.join('=').trim();
                }
            });
            return config;
        }
    } catch (e) {}
    return {};
}

function saveScriptConfig(config) {
    try {
        if (!fs.existsSync(SCRIPT_CONFIG_DIR)) {
            fs.mkdirSync(SCRIPT_CONFIG_DIR, { recursive: true });
        }
        const content = Object.entries(config)
            .map(([k, v]) => `${k}=${v}`)
            .join('\n');
        fs.writeFileSync(SCRIPT_CONFIG_FILE, content);
    } catch (e) {}
}

// ==================== HTTP 请求 ====================
function post(url, data, headers = {}) {
    return new Promise((resolve, reject) => {
        const urlObj = new URL(url);
        const postData = new URLSearchParams(data).toString();
        
        const options = {
            hostname: urlObj.hostname,
            port: urlObj.port || 443,
            path: urlObj.pathname,
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Content-Length': Buffer.byteLength(postData),
                'Accept': '*/*',
                'Accept-Encoding': 'deflate, gzip',
                ...headers
            },
            rejectUnauthorized: false
        };
        
        const req = https.request(options, (res) => {
            let body = '';
            res.on('data', (chunk) => { body += chunk; });
            res.on('end', () => { resolve(body); });
        });
        
        req.on('error', reject);
        req.write(postData);
        req.end();
    });
}

// ==================== 核心 API ====================
async function login(config) {
    const headers = {
        'ssn': config.SSN || 'e5a2',
        'ver': config.VER || '2.1.93',
        'Cookie': config.COOKIE || ''
    };
    
    const data = {
        timezone: '8',
        v2: 'true',
        v3: 'true',
        session: config.JWT,
        deviceId: config.DEVICE_ID,
        tutorialType: 'ugc'
    };
    
    try {
        const resp = await post(
            'https://battlecraft.tuimotuimo.com/battlecraft/account/loginsession',
            data,
            headers
        );
        const json = JSON.parse(resp);
        if (json.code === 0 && json.data?.sessionid) {
            return {
                sessionid: json.data.sessionid,
                userid: json.data.user?.userid || '',
                nickName: json.data.user?.nickName || '',
                dan: json.data.userrole?.dan || 0,
                characterID: json.data.userrole?.currentCharacter || '0003',
                title: json.data.userrole?.titles ? Object.keys(json.data.userrole.titles)[0] : '0001',
                avatarUrl: json.data.user?.avatarUrl || '2'
            };
        }
        return null;
    } catch (e) {
        return null;
    }
}

async function getRoomIds(sessionid, config) {
    const headers = {
        'Auth': sessionid,
        'ssn': config.SSN || 'e5a2',
        'ver': config.VER || '2.1.93',
        'Cookie': config.COOKIE || ''
    };
    
    try {
        const resp = await post(
            'https://battlecraft.tuimotuimo.com/battlecraft/matchpvp/getroomids',
            { start: '0', count: '100' },
            headers
        );
        const json = JSON.parse(resp);
        if (json.code === 0) {
            return json.data?.matchRoomIds || [];
        }
        return [];
    } catch (e) {
        return [];
    }
}

async function getRoomList(roomIds, sessionid, config) {
    if (!roomIds || roomIds.length === 0) return [];
    
    const headers = {
        'Auth': sessionid,
        'ssn': config.SSN || 'e5a2',
        'ver': config.VER || '2.1.93',
        'Cookie': config.COOKIE || ''
    };
    
    try {
        const resp = await post(
            'https://battlecraft.tuimotuimo.com/battlecraft/matchpvp/getroomlist',
            { ids: roomIds.join(',') },
            headers
        );
        const json = JSON.parse(resp);
        if (json.code === 0) {
            return json.data?.matchRooms || [];
        }
        return [];
    } catch (e) {
        return [];
    }
}

// ==================== 进入房间 ====================
async function enterRoom(roomId, sessionid, userInfo, config) {
    const WebSocket = require('ws');
    
    console.log('\n' + '='.repeat(70));
    log(colors.cyan, '🔍 【进入房间】');
    console.log('='.repeat(70));
    console.log(`📋 房间ID: ${roomId}`);
    console.log(`👤 UserID: ${userInfo.userid}`);
    console.log(`🎮 玩家: ${userInfo.nickName || '未命名'}`);
    console.log(`🏆 段位: ${userInfo.dan}`);
    console.log('='.repeat(70));
    
    const wsUrl = `wss://battlecraft.tuimotuimo.com/battlecraft/matchmaking-friends?roomId=${roomId}`;
    log(colors.blue, `\n🔗 连接: ${wsUrl}`);
    
    // 构建进入消息
    const enterMsg = {
        C2S_StartFriendlyMatchmaking: {
            matchID: roomId,
            pvpMode: 0,
            roomType: 0,
            douyinTaskRoomID: '',
            userid: userInfo.userid,
            session: sessionid,
            nickName: userInfo.nickName || '',
            avatarUrl: userInfo.avatarUrl || '2',
            characterID: userInfo.characterID || '0003',
            characterSkinID: '',
            dan: userInfo.dan || 0,
            title: userInfo.title || '0001',
            clanBadge: '',
            channel: 'taptap',
            gender: 0,
            isVip: null
        }
    };
    
    return new Promise((resolve) => {
        const ws = new WebSocket(wsUrl, {
            headers: {
                'User-Agent': 'Mozilla/5.0',
                'Connection': 'Upgrade',
                'Upgrade': 'websocket'
            },
            rejectUnauthorized: false
        });
        
        let heartbeatInterval = null;
        let isRunning = true;
        let entered = false;
        let heartbeatCount = 0;
        let startTime = Date.now();
        
        function showUptime() {
            const elapsed = Math.floor((Date.now() - startTime) / 1000);
            const mins = Math.floor(elapsed / 60);
            const secs = elapsed % 60;
            return `${mins}分${secs}秒`;
        }
        
        ws.on('open', () => {
            log(colors.green, '✅ WebSocket 连接成功');
            
            const msg = JSON.stringify(enterMsg);
            ws.send(msg);
            log(colors.blue, `📤 发送进入请求 (${msg.length} bytes)`);
            
            // 心跳 1秒2次
            heartbeatInterval = setInterval(() => {
                if (ws.readyState === WebSocket.OPEN) {
                    ws.send(JSON.stringify({ Ping: {} }));
                    heartbeatCount++;
                    if (heartbeatCount % 10 === 0) {
                        process.stdout.write(`\r💓 心跳 #${heartbeatCount} | 运行: ${showUptime()}  `);
                    }
                }
            }, 500);
            
            log(colors.cyan, '💓 心跳已启动 (1秒2次)');
        });
        
        ws.on('message', (data) => {
            try {
                const text = data.toString('utf8');
                const json = JSON.parse(text);
                
                if (json.Pong) return;
                
                // 进入成功
                if (json.S2C_FriendlyMatchState) {
                    const state = json.S2C_FriendlyMatchState;
                    entered = true;
                    console.log('\n' + '='.repeat(70));
                    log(colors.green, '🎉 【成功进入房间！】');
                    console.log('='.repeat(70));
                    console.log(`📋 房间ID: ${state.matchID || roomId}`);
                    console.log(`🗺️  地图: ${state.levelID || 'N/A'}`);
                    console.log(`👑 房主ID: ${state.ownerID || 'N/A'}`);
                    
                    const players = state.players || [];
                    if (players.length > 0) {
                        console.log(`\n👥 房间内玩家 (${players.length}人):`);
                        for (const p of players) {
                            const ownerMark = p.isOwner ? ' 👑' : '';
                            const isMe = p.userid === userInfo.userid ? ' ⭐(你)' : '';
                            const isAI = p.isAI ? ' 🤖' : '';
                            console.log(`  - ${p.nickName || '未命名'}${ownerMark}${isMe}${isAI}`);
                            console.log(`    段位: ${p.dan || 0}, 角色: ${p.characterID || 'N/A'}`);
                        }
                    }
                    console.log('='.repeat(70));
                    log(colors.yellow, '\n💡 按 Ctrl+C 退出房间');
                    console.log(`💡 心跳频率: 1秒2次\n`);
                    return;
                }
                
                // 操作结果
                if (json.S2C_ActionResult) {
                    const code = json.S2C_ActionResult.code;
                    const errorMsgs = {
                        2: '房间不存在',
                        10: '被房主踢出 🚫',
                        102: '房间已失效或已开始',
                        103: '房间已满',
                        104: '已在房间中'
                    };
                    const msg = errorMsgs[code] || `未知错误 (${code})`;
                    
                    if (code === 0) {
                        if (!entered) log(colors.green, '✅ 操作成功');
                    } else if (code === 2) {
                        log(colors.red, `\n❌ ${msg}`);
                        cleanup();
                        resolve(false);
                        return;
                    } else if (code === 10) {
                        log(colors.magenta, `\n🚫 ${msg}`);
                        cleanup();
                        resolve(false);
                        return;
                    } else if (code === 102 || code === 103 || code === 104) {
                        log(colors.yellow, `\n⚠️ ${msg}`);
                        cleanup();
                        resolve(false);
                        return;
                    } else {
                        log(colors.yellow, `\n⚠️ ${msg}`);
                    }
                }
                
                if (json.S2C_Error) {
                    log(colors.red, `\n❌ 服务器错误: ${json.S2C_Error.msg || '未知'}`);
                    cleanup();
                    resolve(false);
                    return;
                }
                
                if (json.C2S_CancelMatchmaking) {
                    log(colors.yellow, '\n📤 收到取消匹配指令');
                    cleanup();
                    resolve(true);
                    return;
                }
                
            } catch (e) {}
        });
        
        ws.on('error', (err) => {
            if (isRunning) {
                log(colors.red, `❌ WebSocket 错误: ${err.message}`);
            }
            cleanup();
            resolve(false);
        });
        
        ws.on('close', (code, reason) => {
            if (isRunning) {
                const reasonStr = reason.toString('utf8') || '正常关闭';
                log(colors.yellow, `\n🔌 连接已关闭 (code: ${code})`);
            }
            cleanup();
            if (!entered) resolve(false);
        });
        
        function cleanup() {
            isRunning = false;
            if (heartbeatInterval) {
                clearInterval(heartbeatInterval);
                heartbeatInterval = null;
                console.log('');
            }
            if (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING) {
                try { ws.close(); } catch (e) {}
            }
        }
        
        // Ctrl+C 处理
        const sigintHandler = () => {
            if (!isRunning) return;
            console.log('');
            log(colors.yellow, '👋 正在退出房间...');
            
            if (ws.readyState === WebSocket.OPEN) {
                ws.send(JSON.stringify({ C2S_CancelMatchmaking: {} }));
                log(colors.blue, '📤 已发送取消请求');
                setTimeout(() => {
                    cleanup();
                    resolve(entered);
                    process.exit(0);
                }, 500);
            } else {
                cleanup();
                resolve(entered);
                process.exit(0);
            }
        };
        
        process.once('SIGINT', sigintHandler);
        
        // 超时
        setTimeout(() => {
            if (!entered && isRunning) {
                log(colors.yellow, '\n⏰ 进入超时，继续等待...');
            }
        }, 15000);
    });
}

// ==================== CLI ====================
const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout
});

function question(prompt) {
    return new Promise((resolve) => {
        rl.question(prompt, resolve);
    });
}

function printHeader() {
    console.clear();
    console.log(`${colors.cyan}╔════════════════════════════════════════╗${colors.nc}`);
    console.log(`${colors.cyan}║     派对制造 - 自动进入房间工具      ║${colors.nc}`);
    console.log(`${colors.cyan}╚════════════════════════════════════════╝${colors.nc}`);
    console.log('');
}

// ==================== 主逻辑 ====================
async function main() {
    printHeader();
    
    // 检查依赖
    try {
        require.resolve('ws');
        log(colors.green, '✅ ws 库已安装');
    } catch (e) {
        log(colors.red, '❌ ws 库未安装');
        log(colors.yellow, '请运行: npm install ws');
        process.exit(1);
    }
    
    // 1. 读取配置 - 优先从工具箱读取
    log(colors.blue, '\n📂 读取配置...');
    let config = loadToolConfig();
    let configSource = '工具箱';
    
    if (!config || !config.JWT) {
        // 尝试从脚本配置读取
        const scriptConfig = loadScriptConfig();
        if (scriptConfig && scriptConfig.JWT) {
            config = scriptConfig;
            configSource = '脚本本地';
        }
    }
    
    if (!config || !config.JWT) {
        log(colors.yellow, '⚠️ 未找到配置文件');
        log(colors.blue, '请选择操作:');
        console.log('  1. 手动输入 JWT');
        console.log('  2. 使用内置默认配置');
        console.log('  0. 退出');
        const choice = await question('\n请输入: ');
        
        if (choice === '0') {
            log(colors.green, '感谢使用！');
            process.exit(0);
        } else if (choice === '1') {
            const jwt = await question('请输入 JWT: ');
            if (!jwt.trim()) {
                log(colors.red, '❌ JWT 不能为空');
                process.exit(1);
            }
            config = { JWT: jwt.trim() };
            const ssn = await question('请输入 SSN (默认 e5a2): ');
            config.SSN = ssn.trim() || 'e5a2';
            const deviceId = await question('请输入 Device ID: ');
            config.DEVICE_ID = deviceId.trim() || '';
            config.VER = '2.1.93';
            config.COOKIE = '';
            saveScriptConfig(config);
            configSource = '手动输入';
        } else {
            // 使用抓包成功的默认配置
            config = {
                JWT: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJkZXZJZCI6IjQ1OGFmMGNmMTE1NTkyMjJiZDQ0YjVkZjAwNTM5ZThlMiIsImZsYWciOiJiYzg1IiwiZnJvbSI6InRhcHRhcCIsImx0Ijoic2Vzc2lvbiIsInNzbiI6ImU1YTIiLCJ1c2VyaWQiOiI2YTMzYWFlNjM1MjBjMzE2MzUxOGU1YTIiLCJ2IjoiMCJ9.r5_-ZeaZ0-KG43CUkDaFtmVfhdNf8KiZ22SPndEqXEs',
                SSN: 'e5a2',
                DEVICE_ID: '458af0cf11559222bd44b5df00539e8e2',
                VER: '2.1.93',
                COOKIE: ''
            };
            configSource = '内置默认';
        }
    }
    
    log(colors.green, `✅ 配置加载成功 (来源: ${configSource})`);
    
    // 2. 登录
    log(colors.blue, '\n🔑 登录游戏...');
    const userInfo = await login(config);
    if (!userInfo) {
        log(colors.red, '❌ 登录失败，请检查 JWT 是否有效');
        await question('按回车键退出...');
        process.exit(1);
    }
    log(colors.green, `✅ 登录成功`);
    console.log(`   👤 玩家: ${userInfo.nickName || '未命名'} (ID: ${userInfo.userid})`);
    console.log(`   🏆 段位: ${userInfo.dan}`);
    console.log(`   🔑 SessionID: ${userInfo.sessionid.substring(0, 50)}...`);
    
    // 3. 获取房间列表
    log(colors.blue, '\n📡 获取房间列表...');
    const roomIds = await getRoomIds(userInfo.sessionid, config);
    if (!roomIds || roomIds.length === 0) {
        log(colors.yellow, '⚠️ 当前没有可用的房间');
        const manualRoom = await question('请输入房间ID (或按回车退出): ');
        if (!manualRoom.trim()) {
            log(colors.green, '感谢使用！');
            process.exit(0);
        }
        // 直接进入
        log(colors.blue, `\n🚪 进入房间 ${manualRoom.trim()} ...`);
        await enterRoom(manualRoom.trim(), userInfo.sessionid, userInfo, config);
        await question('\n按回车键退出...');
        process.exit(0);
    }
    
    // 获取房间详情
    const rooms = await getRoomList(roomIds, userInfo.sessionid, config);
    
    // 显示房间列表
    console.log('\n' + '='.repeat(70));
    log(colors.cyan, '📋 可用房间列表');
    console.log('='.repeat(70));
    
    if (rooms.length === 0) {
        log(colors.yellow, '⚠️ 获取房间详情失败');
        const manualRoom = await question('请输入房间ID: ');
        if (!manualRoom.trim()) {
            log(colors.green, '感谢使用！');
            process.exit(0);
        }
        await enterRoom(manualRoom.trim(), userInfo.sessionid, userInfo, config);
        await question('\n按回车键退出...');
        process.exit(0);
    }
    
    rooms.forEach((room, i) => {
        const owner = room.owner || {};
        const statusMap = {
            0: '🟢 等待中',
            1: '🟡 游戏中',
            2: '🔴 已结束'
        };
        const status = statusMap[room.state] || `状态${room.state}`;
        const modeMap = { 0: '经典', 1: '对抗', 2: '竞速', 3: '合作' };
        const mode = modeMap[room.pvpMode] || `模式${room.pvpMode}`;
        
        console.log(`\n${i + 1}. 房间: ${room.id}`);
        console.log(`   👑 房主: ${owner.nickName || '未知'} (段位${owner.dan || 0})`);
        console.log(`   👥 人数: ${room.memberCount || 0}`);
        console.log(`   📊 模式: ${mode} | 状态: ${status}`);
        console.log(`   🗺️  地图: ${room.levelId || 'N/A'}`);
        if (owner.clan) {
            console.log(`   🏠 战队: ${owner.clan.name || ''}`);
        }
        console.log('-'.repeat(50));
    });
    
    console.log(`\n📊 共 ${rooms.length} 个房间`);
    
    // 4. 选择房间
    console.log('');
    const choice = await question('请输入房间编号或房间ID (回车直接选第1个): ');
    
    let selectedRoomId = '';
    if (!choice.trim()) {
        selectedRoomId = rooms[0]?.id || '';
    } else if (/^\d+$/.test(choice.trim())) {
        const idx = parseInt(choice) - 1;
        if (idx >= 0 && idx < rooms.length) {
            selectedRoomId = rooms[idx].id;
        } else {
            log(colors.red, '❌ 无效的编号');
            process.exit(1);
        }
    } else {
        selectedRoomId = choice.trim();
    }
    
    if (!selectedRoomId) {
        log(colors.red, '❌ 未选择房间');
        process.exit(1);
    }
    
    log(colors.green, `✅ 选择房间: ${selectedRoomId}`);
    
    // 5. 进入房间
    log(colors.blue, `\n🚪 进入房间 ${selectedRoomId} ...`);
    await enterRoom(selectedRoomId, userInfo.sessionid, userInfo, config);
    
    await question('\n按回车键退出...');
    process.exit(0);
}

// ==================== 启动 ====================
main().catch((err) => {
    console.error('程序异常:', err);
    process.exit(1);
});