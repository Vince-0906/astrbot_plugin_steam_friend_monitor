import asyncio
import json
from functools import lru_cache
from io import BytesIO
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List
from urllib.parse import quote
from urllib.request import urlopen

import httpx
from PIL import Image, ImageDraw, ImageFont

from astrbot.api import AstrBotConfig, logger
import astrbot.api.message_components as Comp
from astrbot.api.event import AstrMessageEvent, MessageChain, filter
from astrbot.api.star import Context, Star, register

STEAM_SUMMARY_API = "https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2/"


@lru_cache(maxsize=1)
def _pick_cjk_font() -> str | None:
    """Pick an available CJK font path for PIL on Windows/Linux/macOS."""
    candidates = [
        # Windows
        "C:/Windows/Fonts/msyh.ttc",
        "C:/Windows/Fonts/msyhbd.ttc",
        "C:/Windows/Fonts/simsun.ttc",
        # Linux common CJK fonts
        "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
        "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/noto/NotoSansSC-Regular.otf",
        "/usr/share/fonts/truetype/arphic/ukai.ttc",
        "/usr/share/fonts/truetype/arphic/uming.ttc",
        # macOS
        "/System/Library/Fonts/PingFang.ttc",
        "/System/Library/Fonts/Hiragino Sans GB.ttc",
        "/System/Library/Fonts/STHeiti Light.ttc",
    ]

    for fp in candidates:
        if Path(fp).exists():
            return fp
    return None


def _safe_font(size: int, plugin_dir: Path | None = None):
    # 1) Prefer bundled font shipped with plugin
    if plugin_dir is not None:
        bundled = plugin_dir / "fonts" / "NotoSansCJKsc-Regular.otf"
        if bundled.exists():
            try:
                return ImageFont.truetype(str(bundled), size)
            except Exception:
                pass

    # 2) Fallback to system CJK fonts
    font_path = _pick_cjk_font()
    if font_path:
        try:
            return ImageFont.truetype(font_path, size)
        except Exception:
            pass

    # 3) Last resort
    return ImageFont.load_default()


@lru_cache(maxsize=1024)
def _fetch_url_bytes(url: str) -> bytes | None:
    if not url:
        return None
    try:
        with urlopen(url, timeout=8) as resp:
            return resp.read()
    except Exception:
        return None


@lru_cache(maxsize=512)
def _get_game_icon_url(appid: str) -> str | None:
    if not appid:
        return None
    api = f"https://store.steampowered.com/api/appdetails?appids={appid}&l=schinese"
    raw = _fetch_url_bytes(api)
    if not raw:
        return None
    try:
        data = json.loads(raw.decode("utf-8", errors="ignore"))
        node = data.get(str(appid), {})
        if not node.get("success"):
            return None
        app = node.get("data", {})
        return app.get("header_image") or app.get("capsule_image")
    except Exception:
        return None


def _with_image_proxy(url: str, proxy_prefix: str) -> str:
    if not url:
        return url
    prefix = (proxy_prefix or "").strip()
    if not prefix:
        return url

    encoded = quote(url, safe="")
    if "{url}" in prefix:
        return prefix.replace("{url}", encoded)
    if "%s" in prefix:
        return prefix % encoded
    return prefix + encoded


def _load_remote_image(
    url: str, size: tuple[int, int], proxy_prefix: str = ""
) -> Image.Image | None:
    # try direct first, then proxy
    candidates = [url]
    if proxy_prefix:
        candidates.append(_with_image_proxy(url, proxy_prefix))

    for u in candidates:
        raw = _fetch_url_bytes(u)
        if not raw:
            continue
        try:
            img = Image.open(BytesIO(raw)).convert("RGBA")
            return img.resize(size, Image.Resampling.LANCZOS)
        except Exception:
            continue
    return None


def _circle_crop(img: Image.Image) -> Image.Image:
    mask = Image.new("L", img.size, 0)
    d = ImageDraw.Draw(mask)
    d.ellipse((0, 0, img.size[0], img.size[1]), fill=255)
    out = Image.new("RGBA", img.size)
    out.paste(img, (0, 0), mask)
    return out


def parse_ids(raw: str) -> List[str]:
    return [x.strip() for x in (raw or "").replace("\n", ",").split(",") if x.strip()]


def persona_text(state: int) -> str:
    mapping = {
        0: "离线",
        1: "在线",
        2: "忙碌",
        3: "离开",
        4: "打盹",
        5: "想交易",
        6: "想玩游戏",
    }
    return mapping.get(state, f"未知({state})")


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def parse_iso(ts: str) -> datetime | None:
    if not ts:
        return None
    try:
        return datetime.fromisoformat(ts)
    except Exception:
        return None


@register("astrbot_plugin_steam_friend_monitor", "SZC", "Steam 好友在线监控", "0.1.0")
class SteamFriendMonitor(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.config = config
        self.plugin_dir = Path(__file__).parent
        self.data_dir = self.plugin_dir / "data"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.state_file = self.data_dir / "state.json"

        self.state: Dict[str, Any] = self._load_state()
        self._stop = False
        self._task: asyncio.Task | None = None

    async def initialize(self):
        logger.info("[steam-monitor] initialized")
        self._task = asyncio.create_task(self._poll_loop())

    async def terminate(self):
        self._stop = True
        if self._task:
            self._task.cancel()
        logger.info("[steam-monitor] terminated")

    def _load_state(self) -> Dict[str, Any]:
        if not self.state_file.exists():
            return {}
        try:
            return json.loads(self.state_file.read_text(encoding="utf-8"))
        except Exception:
            return {}

    def _save_state(self):
        self.state_file.write_text(
            json.dumps(self.state, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def _save_config_safe(self):
        try:
            self.config.save_config()
        except Exception:
            pass

    def _get_targets(self) -> List[str]:
        cfg_targets = parse_ids(self.config.get("push_targets", ""))
        legacy_targets = self.state.get("_push_targets", [])
        merged = []
        for t in cfg_targets + legacy_targets:
            if t and t not in merged:
                merged.append(t)
        return merged

    def _set_targets(self, targets: List[str]):
        uniq = []
        for t in targets:
            if t and t not in uniq:
                uniq.append(t)
        self.config["push_targets"] = ",".join(uniq)
        self._save_config_safe()

    async def _fetch_players(self, steam_ids: List[str]) -> List[Dict[str, Any]]:
        api_key = self.config.get("steam_api_key", "")
        if not api_key:
            raise RuntimeError("未配置 steam_api_key")

        params = {
            "key": api_key,
            "steamids": ",".join(steam_ids),
        }
        async with httpx.AsyncClient(timeout=20) as client:
            r = await client.get(STEAM_SUMMARY_API, params=params)
            r.raise_for_status()
            data = r.json()
            return data.get("response", {}).get("players", [])

    def _build_status_image(self, players: List[Dict[str, Any]]) -> str:
        w = 980
        row_h = 110
        top = 56
        h = top + row_h * max(1, len(players)) + 20

        img = Image.new("RGB", (w, h), (22, 26, 31))
        draw = ImageDraw.Draw(img)

        font_text = _safe_font(24, self.plugin_dir)
        font_small = _safe_font(18, self.plugin_dir)

        now_text = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        bbox = draw.textbbox((0, 0), now_text, font=font_small)
        text_w = bbox[2] - bbox[0]
        draw.text(
            (w - 24 - text_w, 18),
            now_text,
            fill=(160, 170, 180),
            font=font_small,
        )

        proxy_prefix = self.config.get(
            "image_proxy_prefix", "https://images.weserv.nl/?url="
        )

        y = top
        for p in players:
            name = p.get("personaname", "Unknown")
            state = int(p.get("personastate", 0))
            game = (p.get("gameextrainfo", "") or "").strip()
            gameid = str(p.get("gameid", "") or "").strip()

            draw.rounded_rectangle(
                (20, y, w - 20, y + 96), radius=14, fill=(35, 41, 48)
            )

            avatar = None
            avatar_url = p.get("avatarfull") or p.get("avatarmedium") or p.get("avatar")
            if avatar_url:
                avatar = _load_remote_image(avatar_url, (64, 64), proxy_prefix)
                if avatar is not None:
                    avatar = _circle_crop(avatar)

            if avatar is not None:
                img.paste(avatar, (34, y + 16), avatar)
            else:
                color = (67, 160, 71) if state != 0 else (120, 130, 140)
                draw.ellipse((34, y + 28, 54, y + 48), fill=color)

            draw.text((112, y + 18), name, fill=(240, 240, 240), font=font_text)
            line2 = f"状态: {persona_text(state)}" + (
                f" | 游戏: {game}" if game else ""
            )
            draw.text((112, y + 54), line2, fill=(170, 180, 190), font=font_small)

            if gameid:
                icon_url = _get_game_icon_url(gameid)
                if icon_url:
                    game_icon = _load_remote_image(icon_url, (180, 68), proxy_prefix)
                    if game_icon is not None:
                        img.paste(game_icon, (w - 220, y + 14), game_icon)

            y += row_h

        out = self.data_dir / "steam_status_latest.png"
        img.save(out)
        return str(out)

    async def _push_image(self, umo: str, text: str, image_path: str):
        chain = MessageChain()
        chain.chain = [
            Comp.Plain(text=text),
            Comp.Image.fromFileSystem(image_path),
        ]
        await self.context.send_message(umo, chain)

    def _compute_next_interval(
        self, players: List[Dict[str, Any]], default_sec: int
    ) -> int:
        any_online = any(int(p.get("personastate", 0)) != 0 for p in players)
        if any_online:
            return max(10, default_sec)

        offline_minutes_max = 0.0
        for p in players:
            sid = p.get("steamid", "")
            record = self.state.get(sid, {})
            off_since = parse_iso(record.get("offline_since", ""))
            if off_since:
                mins = (datetime.now() - off_since).total_seconds() / 60.0
                if mins > offline_minutes_max:
                    offline_minutes_max = mins

        if offline_minutes_max >= 30:
            return 600
        if offline_minutes_max >= 10:
            return 300
        return max(10, default_sec)

    async def _poll_loop(self):
        await asyncio.sleep(3)
        while not self._stop:
            try:
                steam_ids = parse_ids(self.config.get("steam_ids", ""))
                default_interval = int(self.config.get("poll_interval_sec", 60) or 60)
                if not steam_ids:
                    await asyncio.sleep(max(30, default_interval))
                    continue

                players = await self._fetch_players(steam_ids)

                events = []
                now = now_iso()
                for p in players:
                    sid = p.get("steamid")
                    st = int(p.get("personastate", 0))
                    game = (p.get("gameextrainfo", "") or "").strip()

                    prev_record = self.state.get(sid, {})
                    prev = prev_record.get("personastate")
                    prev_game = (prev_record.get("gameextrainfo", "") or "").strip()

                    offline_since = prev_record.get("offline_since", "")
                    if st == 0:
                        if not (prev == 0 and offline_since):
                            offline_since = now
                    else:
                        offline_since = ""

                    self.state[sid] = {
                        "personaname": p.get("personaname", ""),
                        "personastate": st,
                        "gameextrainfo": game,
                        "offline_since": offline_since,
                        "ts": now,
                    }

                    # 首轮仅建立基线，不推送
                    if prev is None:
                        continue

                    name = p.get("personaname", "?")

                    # 上线 / 下线
                    if prev == 0 and st != 0:
                        events.append(f"{name}: 上线 ({persona_text(st)})")
                    elif prev != 0 and st == 0:
                        events.append(f"{name}: 下线")

                    # 游戏启动 / 关闭 / 切换（仅当前在线时判定）
                    if st != 0:
                        if not prev_game and game:
                            events.append(f"{name}: 启动游戏《{game}》")
                        elif prev_game and not game:
                            events.append(f"{name}: 关闭游戏《{prev_game}》")
                        elif prev_game and game and prev_game != game:
                            events.append(
                                f"{name}: 切换游戏《{prev_game}》 -> 《{game}》"
                            )

                self._save_state()

                if events:
                    image_path = self._build_status_image(players)
                    targets = self._get_targets()
                    if targets:
                        text = "Steam 状态变化：\n" + "\n".join(events)
                        for umo in targets:
                            try:
                                await self._push_image(umo, text, image_path)
                            except Exception as e:
                                logger.error(f"[steam-monitor] push failed {umo}: {e}")

                next_sleep = self._compute_next_interval(players, default_interval)
                logger.info(f"[steam-monitor] next poll in {next_sleep}s")
                await asyncio.sleep(next_sleep)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[steam-monitor] poll error: {e}")
                await asyncio.sleep(30)

    @filter.command("sfm_bind")
    async def bind_group(self, event: AstrMessageEvent):
        """绑定当前会话为推送目标"""
        umo = event.unified_msg_origin
        targets = self._get_targets()
        if umo not in targets:
            targets.append(umo)
            self._set_targets(targets)
        yield event.plain_result(
            "已绑定当前会话为 Steam 监控推送目标（可在配置页 push_targets 查看）"
        )

    @filter.command("sfm_unbind")
    async def unbind_group(self, event: AstrMessageEvent):
        """取消当前会话推送绑定"""
        umo = event.unified_msg_origin
        targets = self._get_targets()
        if umo in targets:
            targets.remove(umo)
            self._set_targets(targets)
        yield event.plain_result("已取消当前会话绑定")

    @filter.command("sfm_targets")
    async def show_targets(self, event: AstrMessageEvent):
        """查看当前推送目标列表"""
        targets = self._get_targets()
        if not targets:
            yield event.plain_result("当前无推送目标，请先 /sfm_bind")
            return
        yield event.plain_result("当前推送目标：\n" + "\n".join(targets))

    @filter.command("sfm_add_id")
    async def bind_id(self, event: AstrMessageEvent, steam_id64: str):
        """绑定一个 SteamID64 到监控列表"""
        steam_id64 = (steam_id64 or "").strip()
        if not steam_id64.isdigit() or len(steam_id64) < 10:
            yield event.plain_result("SteamID64 格式不正确")
            return

        ids = parse_ids(self.config.get("steam_ids", ""))
        if steam_id64 not in ids:
            ids.append(steam_id64)
        self.config["steam_ids"] = ",".join(ids)
        self._save_config_safe()
        yield event.plain_result(
            f"已绑定 SteamID64: {steam_id64}，当前监控数量: {len(ids)}"
        )

    @filter.command("sfm_del_id")
    async def unbind_id(self, event: AstrMessageEvent, steam_id64: str):
        """从监控列表移除一个 SteamID64"""
        steam_id64 = (steam_id64 or "").strip()
        ids = parse_ids(self.config.get("steam_ids", ""))
        if steam_id64 in ids:
            ids.remove(steam_id64)
        self.config["steam_ids"] = ",".join(ids)
        self._save_config_safe()
        yield event.plain_result(
            f"已移除 SteamID64: {steam_id64}，当前监控数量: {len(ids)}"
        )

    @filter.command("sfm_status")
    async def status(self, event: AstrMessageEvent):
        """手动查询并发送当前状态图"""
        steam_ids = parse_ids(self.config.get("steam_ids", ""))
        if not steam_ids:
            yield event.plain_result("未配置 steam_ids")
            return

        players = await self._fetch_players(steam_ids)
        image_path = self._build_status_image(players)
        msg = "\n".join(
            [
                f"{p.get('personaname', '?')}: {persona_text(int(p.get('personastate', 0)))}"
                for p in players
            ]
        )

        yield event.plain_result(f"当前状态:\n{msg}")
        chain = MessageChain()
        chain.chain = [Comp.Image.fromFileSystem(image_path)]
        await self.context.send_message(event.unified_msg_origin, chain)

    @filter.command("sfm_set_ids")
    async def set_ids(self, event: AstrMessageEvent, ids: str):
        """设置监控 SteamID64（逗号分隔）"""
        parsed = parse_ids(ids)
        self.config["steam_ids"] = ",".join(parsed)
        self._save_config_safe()
        yield event.plain_result(f"已设置监控ID数量: {len(parsed)}")

    @filter.command("sfm_test")
    async def steam_monitor_test(self, event: AstrMessageEvent, action: str = "all"):
        """测试命令：检查配置/拉取状态/生成图片/推送到当前会话"""
        action = (action or "all").strip().lower()
        steam_ids = parse_ids(self.config.get("steam_ids", ""))
        targets = self._get_targets()

        if action in ("cfg", "config"):
            msg = [
                "[steam_monitor_test: config]",
                f"steam_ids_count={len(steam_ids)}",
                f"push_targets_count={len(targets)}",
                f"poll_interval_sec={self.config.get('poll_interval_sec', 60)}",
                f"online_only={self.config.get('online_only', True)}",
                f"steam_api_key_set={'yes' if bool(self.config.get('steam_api_key', '')) else 'no'}",
            ]
            yield event.plain_result("\n".join(msg))
            return

        if not steam_ids:
            yield event.plain_result("[steam_monitor_test] 未配置 steam_ids")
            return

        try:
            players = await self._fetch_players(steam_ids)
            image_path = self._build_status_image(players)
            status_text = "\n".join(
                [
                    f"{p.get('personaname', '?')} ({p.get('steamid', '')}): {persona_text(int(p.get('personastate', 0)))}"
                    + (
                        f" | {p.get('gameextrainfo', '')}"
                        if p.get("gameextrainfo")
                        else ""
                    )
                    for p in players
                ]
            )

            if action in ("status", "pull"):
                yield event.plain_result("[steam_monitor_test: status]\n" + status_text)
                return

            # all / image / push
            yield event.plain_result(
                "[steam_monitor_test] 状态拉取成功，发送测试图片中..."
            )
            chain = MessageChain()
            chain.chain = [
                Comp.Plain(text="[steam_monitor_test] 这是测试推送图"),
                Comp.Image.fromFileSystem(image_path),
            ]
            await self.context.send_message(event.unified_msg_origin, chain)

            if action in ("push", "all"):
                ok = 0
                for umo in targets:
                    try:
                        await self._push_image(
                            umo, "[steam_monitor_test] 目标会话测试推送", image_path
                        )
                        ok += 1
                    except Exception as e:
                        logger.error(f"[steam-monitor] test push failed {umo}: {e}")
                if targets:
                    yield event.plain_result(
                        f"[steam_monitor_test] 目标会话测试推送完成: {ok}/{len(targets)}"
                    )
        except Exception as e:
            yield event.plain_result(f"[steam_monitor_test] 执行失败: {e}")
