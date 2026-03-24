# astrbot_plugin_steam_friend_monitor

Steam 好友在线监控插件（AstrBot）。

## 功能

- 轮询 Steam 玩家状态，支持在线、离线、忙碌、离开等状态识别
- 自动推送上线、下线、状态变化、游戏启动、关闭和切换事件
- 支持 `online_only` 模式，只在离线 -> 在线时推送
- 生成带头像和游戏封面的状态图片，并自动清理旧渲染缓存
- 支持手动查询状态图和推送链路测试
- 内置中文字体，容器环境缺少系统字体时也能正常显示

## 安装

1. 在 AstrBot 面板上传插件 zip。
2. 安装后进入插件配置，至少填写：
   - `steam_api_key`
   - `steam_ids`
3. 在目标会话发送 `/sfm_bind` 绑定推送目标。

## 配置项

- `steam_api_key`：Steam Web API Key
- `steam_ids`：监控的 SteamID64 列表，英文逗号分隔
- `push_targets`：推送目标会话 ID，可由 `/sfm_bind` 自动维护
- `poll_interval_sec`：基础轮询间隔，最小 10 秒
- `online_only`：仅推送离线 -> 在线事件；关闭后也会推送更多变化事件
- `image_proxy_prefix`：头像和游戏封面的图片代理前缀

## 命令

- `/sfm_bind`：绑定当前会话为推送目标
- `/sfm_unbind`：取消当前会话绑定
- `/sfm_targets`：查看推送目标
- `/sfm_add_id <steamid64>`：添加监控 ID
- `/sfm_del_id <steamid64>`：删除监控 ID
- `/sfm_set_ids <id1,id2,...>`：批量设置监控 ID
- `/sfm_status`：立即查询并发送当前状态图
- `/sfm_test [all|cfg|status|image|push]`：测试配置、状态拉取和推送链路

## 运行特点

- SteamID 会自动去重，并在批量请求时按 100 个一组调用官方接口
- 图片渲染放在线程中执行，避免阻塞插件主事件循环
- 状态图片使用唯一文件名保存，避免轮询和手动查询互相覆盖
- 长时间全员离线时会自动降低轮询频率

## 中文字体

插件默认优先加载内置字体：

- `fonts/NotoSansCJKsc-Regular.otf`

若内置字体不可用，会自动回退到 Windows、Linux 或 macOS 的常见 CJK 字体，最后再回退到 PIL 默认字体。

## 开发文档

开发说明见 [DEVELOPMENT.md](./DEVELOPMENT.md)。

## 依赖

- httpx>=0.27.0
- Pillow>=10.0.0

## 版本

当前版本：`0.2.0`
