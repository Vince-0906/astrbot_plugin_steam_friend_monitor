# astrbot_plugin_steam_friend_monitor

Steam 好友在线监控插件（AstrBot）。

## 功能

- 轮询 Steam 玩家状态（在线/离线/忙碌/离开等）
- 玩家上线、下线、启动游戏、关闭游戏、切换游戏时自动推送图片到已绑定会话
- 支持手动查询当前状态图
- 内置中文字体，容器里不装系统字体也能正常显示中文

## 安装

1. 在 AstrBot 面板上传插件 zip。
2. 安装后进入插件配置，填写：
   - `steam_api_key`
   - `steam_ids`（英文逗号分隔的 SteamID64）
3. 在目标会话发送 `/sfm_bind` 绑定推送目标。

## 配置项

- `steam_api_key`：Steam Web API Key
- `steam_ids`：监控 SteamID64 列表（逗号分隔）
- `push_targets`：推送目标会话 ID（可由 `/sfm_bind` 自动写入）
- `poll_interval_sec`：基础轮询间隔（秒）
- `online_only`：仅在离线 -> 在线时推送
- `image_proxy_prefix`：图片中转前缀（头像/游戏图标），默认 `https://images.weserv.nl/?url=`

## 命令

- `/sfm_bind`：绑定当前会话为推送目标
- `/sfm_unbind`：取消当前会话绑定
- `/sfm_targets`：查看推送目标
- `/sfm_add_id <steamid64>`：添加监控 ID
- `/sfm_del_id <steamid64>`：删除监控 ID
- `/sfm_set_ids <id1,id2,...>`：批量设置监控 ID
- `/sfm_status`：立即查询并发送当前状态图
- `/sfm_test [all|cfg|status|push]`：测试命令

## 中文字体说明

插件默认优先加载内置字体：

- `fonts/NotoSansCJKsc-Regular.otf`

若内置字体不可用，会自动回退系统字体（Windows/Linux/macOS 常见 CJK 字体），最后再回退 PIL 默认字体。

## 依赖

- httpx>=0.27.0
- Pillow>=10.0.0

## 版本

当前版本：`0.1.0`



## 界面

- 状态图展示玩家头像（Steam avatar）
- 游戏中展示游戏封面图标（Steam Store header image）
- 不显示 64 位 SteamID
- 顶部不再显示“Steam 好友状态监控”标题


## 0.1.9 变更

- 修复右上角时间显示被裁切问题（自动按文字宽度右对齐）
- 头像和游戏图标支持“直连失败自动走中转”
- 新增配置 `image_proxy_prefix`，适配中国大陆网络环境
