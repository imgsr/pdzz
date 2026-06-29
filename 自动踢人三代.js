#!/usr/bin/env node

/**
 * 派对制造 - 自动房间守卫工具（随机SSN/设备ID版）
 * 功能：使用随机SSN和设备ID创建房间，自动踢出进入的玩家
 */

const https = require('https');
const readline = require('readline');
const { execSync } = require('child_process');
const crypto = require('crypto');

// ==================== 检测 Termux 环境 ====================
function isTermux() {
    try {
        const fs = require('fs');
        if (fs.existsSync('/data/data/com.termux')) {
            return true;
        }
        if (process.env.TERMUX_VERSION) {
            return true;
        }
        try {
            execSync('which termux-wake-lock', { stdio: 'ignore' });
            return true;
        } catch (e) {}
    } catch (e) {}
    return false;
}

// ==================== 随机生成函数（从单地图自动点赞脚本移植） ====================
function generateSSN() {
    // 4位数字+小写字母
    const chars = '0123456789abcdefghijklmnopqrstuvwxyz';
    let result = '';
    for (let i = 0; i < 4; i++) {
        result += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    return result;
}

function generateDeviceId() {
    // 32位十六进制
    return crypto.randomBytes(16).toString('hex');
}

// ==================== 硬编码配置 ====================
const HARDCODED_CONFIG = {
    JWT: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJkZXZJZCI6IjMzOWY3YWJhZTg2OGI3ZjBhODMzODc3YjBkNWQ0NjQ1XG5kYTNkYzlhOTk5Mjg5OGY5MDk2YWI5MjAyOTVkM2ZhZSIsImZsYWciOiJiZGY2IiwiZnJvbSI6InRhcHRhcCIsImx0IjoiZ3Vlc3QiLCJzc24iOiI1Mjk5IiwidXNlcmlkIjoiNjlmNTk5MDNlOGQ1YjU1YmI0ZWViYjAyIiwidiI6IjAifQ.RHQ1EK0pEwiXBTILUyLNgHCetsfO57fUmJtcMGPqG-A',
    VER: '2.1.93'
};

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

// ==================== Unicode 解码 ====================
function decodeUnicode(str) {
    if (!str) return '未命名';
    try {
        return str.replace(/\\u([0-9a-fA-F]{4})/g, (match, hex) => {
            return String.fromCharCode(parseInt(hex, 16));
        });
    } catch (e) {
        return str;
    }
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

// ==================== 登录（保持原有逻辑，使用固定JWT） ====================
async function login(config) {
    // 生成随机SSN和设备ID
    const ssn = generateSSN();
    const deviceId = generateDeviceId();
    
    console.log(`   🔑 SSN: ${ssn}`);
    console.log(`   🆔 Device ID: ${deviceId.substring(0, 20)}...`);
    
    const headers = {
        'ssn': ssn,
        'ver': config.VER || '2.1.93',
        'Cookie': ''
    };
    
    const data = {
        timezone: '8',
        v2: 'true',
        v3: 'true',
        session: config.JWT,
        deviceId: deviceId,
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
                nickName: decodeUnicode(json.data.user?.nickName || ''),
                dan: json.data.userrole?.dan || 0,
                characterID: json.data.userrole?.currentCharacter || '0003',
                title: json.data.userrole?.titles ? Object.keys(json.data.userrole.titles)[0] : '0001',
                avatarUrl: json.data.user?.avatarUrl || '2',
                deviceId: deviceId,
                ssn: ssn
            };
        }
        return null;
    } catch (e) {
        return null;
    }
}

// ==================== 36进制转10进制 ====================
function base36to10(base36) {
    try {
        return parseInt(base36.toLowerCase(), 36);
    } catch (e) {
        return NaN;
    }
}

// ==================== 创建房间并守卫 ====================
async function createAndGuardRoom(levelId, sessionid, userInfo, config) {
    const WebSocket = require('ws');
    
    const fullLevelId = `ugc_${levelId}`;
    
    console.log('\n' + '='.repeat(70));
    log(colors.cyan, '🔰 【自动房间守卫】');
    console.log('='.repeat(70));
    console.log(`🗺️  地图ID: ${levelId}`);
    console.log(`🗺️  完整地图: ${fullLevelId}`);
    console.log(`👤 房主ID: ${userInfo.userid}`);
    console.log(`🎮 房主: ${userInfo.nickName || '未命名'}`);
    console.log(`🏆 段位: ${userInfo.dan}`);
    console.log(`🆔 设备ID: ${userInfo.deviceId.substring(0, 20)}...`);
    console.log(`🔑 SSN: ${userInfo.ssn}`);
    console.log('='.repeat(70));
    log(colors.yellow, '⚔️ 模式: 自动踢人模式');
    log(colors.yellow, '💡 任何进入的玩家都会被立即踢出');
    console.log('='.repeat(70));
    
    const wsUrl = `wss://battlecraft.tuimotuimo.com/battlecraft/matchmaking-friends`;
    log(colors.blue, `\n🔗 连接: ${wsUrl}`);
    
    const createMsg = {
        C2S_StartFriendlyMatchmaking: {
            matchID: '',
            levelID: fullLevelId,
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
        let created = false;
        let roomId = null;
        let heartbeatCount = 0;
        let startTime = Date.now();
        let kickedCount = 0;
        
        function showUptime() {
            const elapsed = Math.floor((Date.now() - startTime) / 1000);
            const mins = Math.floor(elapsed / 60);
            const secs = elapsed % 60;
            return `${mins}分${secs}秒`;
        }
        
        ws.on('open', () => {
            log(colors.green, '✅ WebSocket 连接成功');
            
            const msg = JSON.stringify(createMsg);
            ws.send(msg);
            log(colors.blue, `📤 发送创建房间请求 (${msg.length} bytes)`);
            
            heartbeatInterval = setInterval(() => {
                if (ws.readyState === WebSocket.OPEN) {
                    ws.send(JSON.stringify({ Ping: {} }));
                    heartbeatCount++;
                    if (heartbeatCount % 10 === 0) {
                        process.stdout.write(`\r💓 心跳 #${heartbeatCount} | 运行: ${showUptime()} | 已踢: ${kickedCount}人  `);
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
                
                // 房间创建成功
                if (json.S2C_FriendlyMatchState) {
                    const state = json.S2C_FriendlyMatchState;
                    
                    // 首次创建成功
                    if (!created) {
                        created = true;
                        roomId = state.matchID;
                        
                        console.log('\n' + '='.repeat(70));
                        log(colors.green, '🎉 【房间创建成功！】');
                        console.log('='.repeat(70));
                        console.log(`📋 房间ID: ${state.matchID}`);
                        console.log(`🗺️  地图: ${state.levelID}`);
                        console.log(`👑 房主ID: ${state.ownerID}`);
                        console.log('='.repeat(70));
                        log(colors.yellow, '\n🔰 守卫模式已启动');
                        log(colors.yellow, '💡 任何进入的玩家将被立即踢出');
                        console.log(`💡 心跳频率: 1秒2次\n`);
                    }
                    
                    // 检查玩家列表，踢出新进入的玩家
                    const players = state.players || [];
                    const ownerId = state.ownerID;
                    
                    for (const player of players) {
                        // 如果是房主自己，跳过
                        if (player.userid === ownerId) continue;
                        if (player.isAI) continue;
                        
                        // 发现其他玩家，立即踢出
                        const nickName = decodeUnicode(player.nickName || '未命名');
                        console.log('\n' + '='.repeat(70));
                        log(colors.magenta, '🚨 【检测到玩家进入！】');
                        console.log('='.repeat(70));
                        console.log(`👤 昵称: ${nickName}`);
                        console.log(`🔢 短ID: ${player.userShortId || 'N/A'}`);
                        console.log(`🆔 长ID: ${player.userid}`);
                        console.log(`🏆 段位: ${player.dan || 0}`);
                        console.log(`🎭 角色: ${player.characterID || 'N/A'}`);
                        console.log('='.repeat(70));
                        
                        // 发送踢人请求
                        const kickMsg = {
                            C2S_KickPlayerFromFriendlyMatch: {
                                matchID: roomId,
                                session: sessionid,
                                target: player.userid
                            }
                        };
                        
                        ws.send(JSON.stringify(kickMsg));
                        kickedCount++;
                        log(colors.red, `💥 已发送踢人指令 (目标: ${player.userid})`);
                        log(colors.green, `📊 已踢出 ${kickedCount} 人`);
                        console.log('='.repeat(70) + '\n');
                    }
                    
                    return;
                }
                
                // 操作结果
                if (json.S2C_ActionResult) {
                    const code = json.S2C_ActionResult.code;
                    if (code !== 0 && code !== 102) {
                        const errorMsgs = {
                            2: '地图不存在或无法创建房间',
                            10: '被踢出',
                            102: '房间已失效',
                            103: '房间已满',
                            104: '已在房间中'
                        };
                        const msg = errorMsgs[code] || `未知错误 (${code})`;
                        log(colors.red, `\n❌ ${msg}`);
                        if (code === 102 || code === 2) {
                            cleanup();
                            resolve(null);
                            return;
                        }
                    }
                }
                
                if (json.S2C_Error) {
                    log(colors.red, `\n❌ 服务器错误: ${json.S2C_Error.msg || '未知'}`);
                    cleanup();
                    resolve(null);
                    return;
                }
                
                if (json.C2S_CancelMatchmaking) {
                    log(colors.yellow, '\n📤 收到取消匹配指令');
                    cleanup();
                    resolve(roomId);
                    return;
                }
                
            } catch (e) {}
        });
        
        ws.on('error', (err) => {
            if (isRunning) {
                log(colors.red, `❌ WebSocket 错误: ${err.message}`);
            }
            cleanup();
            resolve(null);
        });
        
        ws.on('close', (code, reason) => {
            if (isRunning) {
                const reasonStr = reason.toString('utf8') || '正常关闭';
                log(colors.yellow, `\n🔌 连接已关闭 (code: ${code})`);
                if (code !== 1000 && code !== 1001) {
                    log(colors.yellow, `   原因: ${reasonStr}`);
                }
            }
            cleanup();
            if (!created) resolve(null);
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
            log(colors.yellow, `👋 正在退出... (共踢出 ${kickedCount} 人)`);
            
            if (ws.readyState === WebSocket.OPEN) {
                ws.send(JSON.stringify({ C2S_CancelMatchmaking: {} }));
                log(colors.blue, '📤 已发送取消请求');
                setTimeout(() => {
                    cleanup();
                    resolve(roomId);
                    process.exit(0);
                }, 500);
            } else {
                cleanup();
                resolve(roomId);
                process.exit(0);
            }
        };
        
        process.once('SIGINT', sigintHandler);
        
        setTimeout(() => {
            if (!created && isRunning) {
                log(colors.yellow, '\n⏰ 创建超时，继续等待...');
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
    console.log(`${colors.cyan}║     派对制造 - 自动房间守卫工具      ║${colors.nc}`);
    console.log(`${colors.cyan}╚════════════════════════════════════════╝${colors.nc}`);
    console.log('');
}

// ==================== 主逻辑 ====================
async function main() {
    printHeader();
    
    // ===== Termux 唤醒锁 =====
    if (isTermux()) {
        try {
            execSync('termux-wake-lock', { stdio: 'ignore' });
            log(colors.green, '✅ Termux 唤醒锁已获取 (CPU保持唤醒)');
        } catch (e) {
            log(colors.yellow, '⚠️ 无法获取 Termux 唤醒锁，可能影响长时间运行');
        }
    }
    
    // 检查依赖
    try {
        require.resolve('ws');
        log(colors.green, '✅ ws 库已安装');
    } catch (e) {
        log(colors.red, '❌ ws 库未安装');
        log(colors.yellow, '请运行: npm install ws');
        process.exit(1);
    }
    
    // 使用硬编码配置
    const config = HARDCODED_CONFIG;
    log(colors.green, '✅ 使用内置配置 (随机SSN和设备ID)');
    console.log(`   📦 VER: ${config.VER}`);
    
    // 登录（使用随机SSN和设备ID）
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
    
    // 输入地图代码
    console.log('\n' + '='.repeat(70));
    log(colors.cyan, '📝 请输入地图代码 (36进制)');
    console.log('='.repeat(70));
    console.log('示例: 1v6sq, jskru, abc123');
    console.log('输入 q 退出');
    console.log('='.repeat(70));
    
    const mapCode = await question('\n地图代码: ');
    
    if (mapCode.toLowerCase() === 'q') {
        log(colors.green, '感谢使用！');
        process.exit(0);
    }
    
    // 转换地图代码
    const levelId = base36to10(mapCode);
    if (isNaN(levelId) || levelId <= 0) {
        log(colors.red, `❌ 无效的地图代码: ${mapCode}`);
        await question('按回车键退出...');
        process.exit(1);
    }
    
    log(colors.green, `✅ 地图ID: ${levelId} (36进制: ${mapCode})`);
    
    // 创建房间并开启守卫模式
    log(colors.blue, `\n🔰 启动自动房间守卫...`);
    const roomId = await createAndGuardRoom(levelId, userInfo.sessionid, userInfo, config);
    
    if (roomId) {
        log(colors.green, `\n✅ 房间守卫已启动: ${roomId}`);
        log(colors.yellow, '💡 按 Ctrl+C 停止守卫并退出');
    } else {
        log(colors.red, '\n❌ 房间创建失败');
    }
    
    await question('\n按回车键退出...');
    process.exit(0);
}

// ==================== 启动 ====================
main().catch((err) => {
    console.error('程序异常:', err);
    process.exit(1);
});