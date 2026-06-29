#!/usr/bin/env node

/**
 * 派对制造 - 自动建房/开局/退出循环工具（改进版）
 * 功能：无限循环 创建房间 → 尝试公开 → 有玩家进入后开始游戏 → 立即退出 → 重新创建
 * 新增：随机SSN/设备ID（仅初始化时生成一次）、显示公开状态
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

// ==================== 随机生成函数 ====================
function generateSSN() {
    const chars = '0123456789abcdefghijklmnopqrstuvwxyz';
    let result = '';
    for (let i = 0; i < 4; i++) {
        result += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    return result;
}

function generateDeviceId() {
    return crypto.randomBytes(16).toString('hex');
}

// ==================== 硬编码配置 ====================
const HARDCODED_CONFIG = {
    JWT: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJkZXZJZCI6IjlkZTEwNzE4ZTI3NjU1YTU2MmJiNzcxNGNhZjQzZjdmIiwiZmxhZyI6IjA0MzYiLCJmcm9tIjoidGFwdGFwIiwibHQiOiJndWVzdCIsInNzbiI6IjUyOTkiLCJ1c2VyaWQiOiI2YTJjZDU2YWU4ZDViNTViYjRmNDA2ZDAiLCJ2IjoiMCJ9.v8ivNqzRvnPuvMeTmRbYxMJxhQweoU8-Wng-EQ31f_Y',
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

// ==================== 登录（使用传入的SSN和设备ID） ====================
async function login(config, ssn, deviceId) {
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

// ==================== 创建房间并等待玩家进入后开始游戏 ====================
async function createRoomAndStart(levelId, sessionid, userInfo, config) {
    const WebSocket = require('ws');
    
    const fullLevelId = `ugc_${levelId}`;
    const cycleStartTime = Date.now();
    let publicResult = null;
    let publicResponseReceived = false;
    
    console.log('\n' + '='.repeat(70));
    log(colors.cyan, `🔄 【循环 #${global.cycleCount || 0}】创建房间`);
    console.log('='.repeat(70));
    console.log(`🗺️  地图ID: ${levelId}`);
    console.log(`🗺️  完整地图: ${fullLevelId}`);
    console.log(`👤 房主ID: ${userInfo.userid}`);
    console.log(`🎮 房主: ${userInfo.nickName || '未命名'}`);
    console.log(`🆔 设备ID: ${userInfo.deviceId.substring(0, 20)}...`);
    console.log(`🔑 SSN: ${userInfo.ssn}`);
    console.log('='.repeat(70));
    
    const wsUrl = `wss://battlecraft.tuimotuimo.com/battlecraft/matchmaking-friends`;
    
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
        let hasPlayerJoined = false;
        let gameStarted = false;
        let resolved = false;
        let roomIdPrefix = '';
        let shouldAbort = false;
        
        function showUptime() {
            const elapsed = Math.floor((Date.now() - startTime) / 1000);
            const mins = Math.floor(elapsed / 60);
            const secs = elapsed % 60;
            return `${mins}分${secs}秒`;
        }
        
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
        
        function finalResolve(result) {
            if (!resolved) {
                resolved = true;
                resolve(result);
            }
        }
        
        ws.on('open', () => {
            log(colors.green, '✅ WebSocket 连接成功');
            
            const msg = JSON.stringify(createMsg);
            ws.send(msg);
            log(colors.blue, `📤 发送创建房间请求 (尝试公开)`);
            
            heartbeatInterval = setInterval(() => {
                if (ws.readyState === WebSocket.OPEN) {
                    ws.send(JSON.stringify({ Ping: {} }));
                    heartbeatCount++;
                    if (heartbeatCount % 10 === 0) {
                        const status = hasPlayerJoined ? '🟢 有玩家' : '⏳ 等待中';
                        let publicStatus = '❓';
                        if (publicResult === true) publicStatus = '🔓公开';
                        else if (publicResult === false) publicStatus = '🔒私有';
                        process.stdout.write(`\r💓 心跳 #${heartbeatCount} | ${status} | ${publicStatus} | 运行: ${showUptime()}  `);
                    }
                }
            }, 500);
            
            log(colors.cyan, '💓 心跳已启动 (等待玩家进入...)');
        });
        
        ws.on('message', (data) => {
            try {
                const text = data.toString('utf8');
                const json = JSON.parse(text);
                
                if (json.Pong) return;
                
                // 房间创建成功 / 状态更新
                if (json.S2C_FriendlyMatchState) {
                    const state = json.S2C_FriendlyMatchState;
                    
                    if (!created) {
                        created = true;
                        roomId = state.matchID;
                        roomIdPrefix = roomId.charAt(0);
                        
                        console.log('\n' + '='.repeat(70));
                        log(colors.green, `🎉 【房间创建成功！】`);
                        console.log('='.repeat(70));
                        console.log(`📋 房间ID: ${roomId}`);
                        console.log(`📋 房间ID开头: "${roomIdPrefix}"`);
                        console.log(`🗺️  地图: ${state.levelID}`);
                        console.log('='.repeat(70));
                        
                        // 检查房间ID是否以2开头
                        if (roomIdPrefix === '2') {
                            log(colors.yellow, `⚠️ 房间ID以 "2" 开头，将立即退出并重新创建`);
                            shouldAbort = true;
                            if (ws.readyState === WebSocket.OPEN) {
                                const quitMsg = { C2S_CancelMatchmaking: {} };
                                ws.send(JSON.stringify(quitMsg));
                                log(colors.blue, '📤 已发送退出请求 (房间ID以2开头)');
                                setTimeout(() => {
                                    cleanup();
                                    finalResolve({ 
                                        roomId, 
                                        success: false, 
                                        error: '房间ID以2开头，重新创建',
                                        shouldRetry: true 
                                    });
                                }, 500);
                            }
                            return;
                        }
                        
                        log(colors.yellow, '⏳ 等待玩家进入...');
                    }
                    
                    // 检查玩家列表
                    const players = state.players || [];
                    const ownerId = state.ownerID;
                    
                    let otherPlayer = null;
                    for (const player of players) {
                        if (player.userid === ownerId) continue;
                        if (player.isAI) continue;
                        otherPlayer = player;
                        break;
                    }
                    
                    if (otherPlayer && !hasPlayerJoined && !shouldAbort) {
                        hasPlayerJoined = true;
                        const nickName = decodeUnicode(otherPlayer.nickName || '未命名');
                        console.log('\n' + '='.repeat(70));
                        log(colors.magenta, '🚪 【玩家进入！】');
                        console.log('='.repeat(70));
                        console.log(`👤 昵称: ${nickName}`);
                        console.log(`🆔 ID: ${otherPlayer.userid}`);
                        console.log(`🏆 段位: ${otherPlayer.dan || 0}`);
                        console.log('='.repeat(70));
                        log(colors.blue, '🎮 准备开始游戏...');
                        
                        const startMsg = {
                            C2S_StartFriendlyMatch: {
                                matchID: roomId
                            }
                        };
                        ws.send(JSON.stringify(startMsg));
                        log(colors.blue, '📤 已发送开始游戏请求');
                    }
                    
                    return;
                }
                
                // 公开房间响应
                if (json.C2C_FriendlyBasicInfo) {
                    const info = json.C2C_FriendlyBasicInfo;
                    publicResult = (info.roomType === 0);
                    publicResponseReceived = true;
                    
                    console.log('\n' + '='.repeat(70));
                    log(colors.magenta, '🔓 【公开房间响应】');
                    console.log('='.repeat(70));
                    console.log(`📋 房间ID: ${info.matchID}`);
                    console.log(`📊 PvP模式: ${info.pvpMode}`);
                    console.log(`📊 房间类型: ${info.roomType === 0 ? '🟢 公开' : '🔴 私有'}`);
                    console.log('='.repeat(70));
                    
                    if (info.roomType === 0) {
                        log(colors.green, '✅ 房间已成功公开！');
                    } else {
                        log(colors.red, '❌ 服务器拒绝了公开请求，房间为私有');
                    }
                }
                
                // 匹配成功（游戏开始）
                if (json.S2C_MatchmakingSuccess) {
                    if (!gameStarted && !shouldAbort) {
                        gameStarted = true;
                        console.log('\n' + '='.repeat(70));
                        log(colors.green, '⚔️ 【游戏已开始！】');
                        console.log('='.repeat(70));
                        console.log(`📋 房间ID: ${json.S2C_MatchmakingSuccess.matchID}`);
                        console.log(`🎯 PvP服务器: ${json.S2C_MatchmakingSuccess.serverAddress || 'N/A'}`);
                        console.log('='.repeat(70));
                        
                        log(colors.yellow, '⏳ 1秒后退出房间...');
                        setTimeout(() => {
                            if (ws.readyState === WebSocket.OPEN) {
                                const quitMsg = {
                                    C2S_CancelMatchmaking: {}
                                };
                                ws.send(JSON.stringify(quitMsg));
                                log(colors.blue, '📤 已发送退出请求');
                                
                                setTimeout(() => {
                                    const elapsed = Math.floor((Date.now() - cycleStartTime) / 1000);
                                    log(colors.green, `✅ 本轮完成 (耗时 ${elapsed}s)`);
                                    cleanup();
                                    finalResolve({ 
                                        roomId, 
                                        success: true,
                                        publicSuccess: publicResult,
                                        publicResponseReceived: publicResponseReceived,
                                        elapsed 
                                    });
                                }, 500);
                            } else {
                                cleanup();
                                finalResolve({ 
                                    roomId, 
                                    success: true, 
                                    publicSuccess: publicResult,
                                    publicResponseReceived: publicResponseReceived
                                });
                            }
                        }, 1000);
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
                            finalResolve({ roomId: null, success: false, error: msg, shouldRetry: true });
                            return;
                        }
                    }
                }
                
                if (json.S2C_Error) {
                    log(colors.red, `\n❌ 服务器错误: ${json.S2C_Error.msg || '未知'}`);
                    cleanup();
                    finalResolve({ roomId: null, success: false, error: json.S2C_Error.msg, shouldRetry: true });
                    return;
                }
                
                if (json.C2S_CancelMatchmaking) {
                    if (!shouldAbort) {
                        log(colors.yellow, '\n📤 收到取消匹配指令');
                    }
                    cleanup();
                    if (!resolved) {
                        finalResolve({ 
                            roomId, 
                            success: true,
                            publicSuccess: publicResult,
                            publicResponseReceived: publicResponseReceived
                        });
                    }
                    return;
                }
                
            } catch (e) {}
        });
        
        ws.on('error', (err) => {
            if (isRunning) {
                log(colors.red, `❌ WebSocket 错误: ${err.message}`);
            }
            cleanup();
            finalResolve({ roomId: null, success: false, error: err.message, shouldRetry: true });
        });
        
        ws.on('close', (code, reason) => {
            if (isRunning) {
                const reasonStr = reason.toString('utf8') || '正常关闭';
                log(colors.yellow, `\n🔌 连接已关闭 (code: ${code})`);
            }
            cleanup();
            if (!resolved) {
                finalResolve({ roomId: null, success: false, error: '连接关闭', shouldRetry: true });
            }
        });
        
        // Ctrl+C 处理
        const sigintHandler = () => {
            if (!isRunning) return;
            console.log('');
            log(colors.yellow, '👋 用户中断，正在退出...');
            cleanup();
            finalResolve({ roomId: null, success: false, error: '用户中断', shouldRetry: false });
            process.exit(0);
        };
        
        process.once('SIGINT', sigintHandler);
    });
}

// ==================== 主循环 ====================
async function mainLoop(levelId, userInfo, sessionid, config) {
    global.cycleCount = 0;
    let totalSuccess = 0;
    let totalFail = 0;
    let totalPublicSuccess = 0;
    let totalPublicFail = 0;
    let totalNoPublicResponse = 0;
    let totalAborted = 0;
    const startTime = Date.now();
    
    console.log('\n' + '='.repeat(70));
    log(colors.cyan, '♾️  【无限循环模式】');
    console.log('='.repeat(70));
    console.log(`🗺️  地图ID: ${levelId}`);
    console.log(`👤 玩家: ${userInfo.nickName || '未命名'}`);
    console.log(`🆔 设备ID: ${userInfo.deviceId.substring(0, 20)}...`);
    console.log(`🔑 SSN: ${userInfo.ssn}`);
    console.log(`📋 逻辑: 创建房间 → 尝试公开 → 等待玩家进入 → 开始游戏 → 退出 → 重复`);
    console.log(`📋 特殊: 房间ID以2开头则自动重开`);
    console.log('='.repeat(70));
    log(colors.yellow, '💡 按 Ctrl+C 停止循环');
    console.log('='.repeat(70) + '\n');
    
    while (true) {
        global.cycleCount++;
        
        try {
            const result = await createRoomAndStart(levelId, sessionid, userInfo, config);
            
            if (result.success) {
                totalSuccess++;
                if (result.publicSuccess === true) {
                    totalPublicSuccess++;
                } else if (result.publicSuccess === false) {
                    totalPublicFail++;
                } else if (!result.publicResponseReceived) {
                    totalNoPublicResponse++;
                }
                const elapsed = Math.floor((Date.now() - startTime) / 1000);
                let publicStatus = '❓未知';
                if (result.publicSuccess === true) publicStatus = '🔓公开';
                else if (result.publicSuccess === false) publicStatus = '🔒私有';
                else if (!result.publicResponseReceived) publicStatus = '⏳无响应';
                log(colors.green, `\n✅ 循环 #${global.cycleCount} 完成 | ${publicStatus} | 成功: ${totalSuccess} | 失败: ${totalFail} | 总运行: ${elapsed}s`);
            } else if (result.error === '房间ID以2开头，重新创建') {
                totalAborted++;
                const elapsed = Math.floor((Date.now() - startTime) / 1000);
                log(colors.yellow, `\n🔄 循环 #${global.cycleCount} 已重开 (ID以2开头) | 成功: ${totalSuccess} | 失败: ${totalFail} | 重开: ${totalAborted} | 总运行: ${elapsed}s`);
                continue;
            } else {
                totalFail++;
                const elapsed = Math.floor((Date.now() - startTime) / 1000);
                log(colors.red, `\n❌ 循环 #${global.cycleCount} 失败: ${result.error || '未知'} | 成功: ${totalSuccess} | 失败: ${totalFail} | 总运行: ${elapsed}s`);
            }
            
            console.log(`📊 公开统计: 成功 ${totalPublicSuccess} | 失败 ${totalPublicFail} | 无响应 ${totalNoPublicResponse}`);
            
            if (result.success) {
                log(colors.yellow, `⏳ 3秒后进入下一轮...`);
                await new Promise(resolve => setTimeout(resolve, 3000));
            }
            
        } catch (err) {
            totalFail++;
            log(colors.red, `\n❌ 循环 #${global.cycleCount} 异常: ${err.message}`);
            await new Promise(resolve => setTimeout(resolve, 3000));
        }
    }
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
    console.log(`${colors.cyan}║  派对制造 - 自动建房/开局/退出循环  ║${colors.nc}`);
    console.log(`${colors.cyan}║     (改进版 - 公开+ID检测+随机SSN)   ║${colors.nc}`);
    console.log(`${colors.cyan}╚════════════════════════════════════════╝${colors.nc}`);
    console.log('');
}

// ==================== 主逻辑 ====================
async function main() {
    printHeader();
    
    // Termux 唤醒锁
    if (isTermux()) {
        try {
            execSync('termux-wake-lock', { stdio: 'ignore' });
            log(colors.green, '✅ Termux 唤醒锁已获取');
        } catch (e) {
            log(colors.yellow, '⚠️ 无法获取 Termux 唤醒锁');
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
    
    // 初始化时生成随机SSN和设备ID（只生成一次）
    const ssn = generateSSN();
    const deviceId = generateDeviceId();
    
    const config = HARDCODED_CONFIG;
    log(colors.green, '✅ 使用硬编码配置 + 随机SSN/设备ID');
    console.log(`   🔑 SSN: ${ssn}`);
    console.log(`   🆔 Device ID: ${deviceId}`);
    console.log(`   📦 VER: ${config.VER}`);
    
    // 登录（使用生成的SSN和设备ID）
    log(colors.blue, '\n🔑 登录游戏...');
    const userInfo = await login(config, ssn, deviceId);
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
    
    const levelId = base36to10(mapCode);
    if (isNaN(levelId) || levelId <= 0) {
        log(colors.red, `❌ 无效的地图代码: ${mapCode}`);
        await question('按回车键退出...');
        process.exit(1);
    }
    
    log(colors.green, `✅ 地图ID: ${levelId} (36进制: ${mapCode})`);
    
    // 启动主循环（复用同一个userInfo）
    await mainLoop(levelId, userInfo, userInfo.sessionid, config);
}

// ==================== 启动 ====================
main().catch((err) => {
    console.error('程序异常:', err);
    process.exit(1);
});