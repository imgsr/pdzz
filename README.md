派对制造 Shell工具箱

一个功能齐全的派对制造游戏 Shell 工具箱，支持房间列表、地图查询、排行榜、玩家信息、金矿打工、评论和广播等功能。

一键安装

```bash
curl -o party_tool.sh https://ghproxy.net/https://raw.githubusercontent.com/imgsr/pdzz/main/party_tool.sh && chmod +x party_tool.sh && bash party_tool.sh
```

功能列表

功能 说明
A 查看当前 IP 地址
B 设备 ID 设置（JWT/Device ID/SSN）
C 查询游戏版本信息
D 查询游戏公告
E 查看工具箱公告
F 查看工具箱版本
1 派对制造房间列表
2 派对制造地图查询（增强版）
3 派对制造排行榜查询
4 派对制造玩家信息查询
5 派对制造查询最新地图
6 派对制造金矿打工
7 派对制造评论地图
8 派对制造广播地图

环境要求

· Android + Termux 或任意 Linux/macOS 系统
· Python 3（脚本会自动检测并尝试安装）
· curl
· openssl（用于生成随机 Device ID）

配置文件

脚本会在 /data/local/tmp/party_tool_config.txt 保存配置，包含：

· JWT Token
· Device ID
· SSN
· VER（游戏版本）
· Cookie

更新日志

v4.8

· 增加对指定地图地图广播功能
· 增加对指定地图地图评论功能
· 排版优化

v4.6

· 支持对指定玩家金矿打工

v4.5

· 使运行更加稳定
· 关系图谱可看玩家 ID

注意事项

1. 第一次运行：脚本会自动检测并安装 Python 3
2. 权限问题：在 Termux 中运行需要存储权限
3. 网络要求：需要能够访问游戏 API 和 GitHub（用于获取公告）
4. 默认配置：脚本内置了默认 JWT 和 Device ID，建议自行更换

主要功能详解

地图查询（功能 2）

· 通过 36 进制地图代码查询地图详情
· 显示作者信息、游玩数据、评论列表
· 支持分页查看评论

金矿打工（功能 6）

· 输入作者的地图代码
· 自动为该作者的金矿打工

评论地图（功能 7）

· 支持 stamp（预设表情/短语）和自定义文本
· 自动检测是否已评论过

广播地图（功能 8）

· 自动领取免费喇叭
· 将地图广播到世界频道

常见问题

Q: 提示 Python 安装失败？
A: 手动安装 Python (pkg install python)后重新运行脚本

Q: 获取 Session 失败？
A: 检查网络或 JWT 和 Device ID 是否正确，在功能 B 中重新设置

Q: 地图代码无效？
A: 确保输入的是正确的 36 进制地图代码

免责声明

本工具仅供学习和研究使用，请勿用于商业目的。使用本工具产生的任何后果由使用者自行承担。

许可证

MIT License

---

Star ⭐ 这个项目，让更多人看到！
