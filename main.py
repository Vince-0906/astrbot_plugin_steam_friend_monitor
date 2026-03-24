<<<<<<< HEAD
from __future__ import annotations

import asyncio
import json
from datetime import datetime
from functools import lru_cache
from io import BytesIO
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import quote
from urllib.request import urlopen
from uuid import uuid4
=======
import asyncio
import contextlib
import ipaddress
import json
import time
from collections import OrderedDict
from datetime import datetime
from io import BytesIO
import uuid
from pathlib import Path
from typing import Any, Dict, List
from urllib.parse import quote, urlparse
>>>>>>> cc237a9798bbf38a9c18ff3e68180ff08d5da0a6

import httpx
from PIL import Image, ImageDraw, ImageFont

from astrbot.api import AstrBotConfig, logger
import astrbot.api.message_components as Comp
from astrbot.api.event import AstrMessageEvent, MessageChain, filter
<<<<<<< HEAD
from astrbot.api.star import Context, Star, register

STEAM_SUMMARY_API = "https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2/"
STEAM_APP_DETAILS_API = "https://store.steampowered.com/api/appdetails"
DEFAULT_IMAGE_PROXY_PREFIX = "https://images.weserv.nl/?url="
MAX_STEAM_IDS_PER_REQUEST = 100
MAX_RENDER_CACHE_FILES = 20
MIN_POLL_INTERVAL_SEC = 10

PERSONA_TEXT_MAP = {
    0: "离线",
    1: "在线",
    2: "忙碌",
    3: "离开",
    4: "打盹",
    5: "想交易",
    6: "想玩游戏",
}

PERSONA_COLOR_MAP = {
    0: (120, 130, 140),
    1: (67, 160, 71),
    2: (239, 108, 0),
    3: (255, 193, 7),
    4: (100, 181, 246),
    5: (171, 71, 188),
    6: (0, 172, 193),
}


@lru_cache(maxsize=1)
def _pick_cjk_font() -> str | None:
    """Pick an available CJK font path for PIL on Windows/Linux/macOS."""
    candidates = [
        "C:/Windows/Fonts/msyh.ttc",
        "C:/Windows/Fonts/msyhbd.ttc",
        "C:/Windows/Fonts/simsun.ttc",
        "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
        "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/noto/NotoSansSC-Regular.otf",
        "/usr/share/fonts/truetype/arphic/ukai.ttc",
        "/usr/share/fonts/truetype/arphic/uming.ttc",
        "/System/Library/Fonts/PingFang.ttc",
        "/System/Library/Fonts/Hiragino Sans GB.ttc",
        "/System/Library/Fonts/STHeiti Light.ttc",
    ]

    for font_path in candidates:
        if Path(font_path).exists():
            return font_path
    return None


def _safe_font(size: int, plugin_dir: Path | None = None):
    if plugin_dir is not None:
        bundled = plugin_dir / "fonts" / "NotoSansCJKsc-Regular.otf"
        if bundled.exists():
            try:
                return ImageFont.truetype(str(bundled), size)
            except Exception:
                pass

    font_path = _pick_cjk_font()
    if font_path:
        try:
            return ImageFont.truetype(font_path, size)
        except Exception:
            pass

    return ImageFont.load_default()


def _unique_items(values: Iterable[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        item = str(value or "").strip()
        if not item or item in seen:
            continue
        seen.add(item)
        result.append(item)
    return result


def _chunked(values: list[str], size: int) -> Iterable[list[str]]:
    for start in range(0, len(values), size):
        yield values[start : start + size]


def _to_bool(value: Any, default: bool) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"1", "true", "yes", "y", "on"}:
            return True
        if normalized in {"0", "false", "no", "n", "off"}:
            return False
    return default


def _to_int(value: Any, default: int, minimum: int = 0) -> int:
    try:
        return max(minimum, int(value))
    except (TypeError, ValueError):
        return max(minimum, default)


def _persona_state(value: Any) -> int:
    return _to_int(value, 0, minimum=0)


def parse_ids(raw: str) -> list[str]:
    return _unique_items((raw or "").replace("\n", ",").split(","))


def is_valid_steam_id(steam_id64: str) -> bool:
    return steam_id64.isdigit() and len(steam_id64) >= 10


def persona_text(state: int) -> str:
    return PERSONA_TEXT_MAP.get(state, f"未知({state})")


def persona_color(state: int) -> tuple[int, int, int]:
    return PERSONA_COLOR_MAP.get(state, (120, 130, 140))
=======
from astrbot.api.star import Context, Star, StarTools

STEAM_SUMMARY_API = "https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2/"


def parse_ids(raw: str) -> List[str]:
    text = (raw or "").replace(chr(10), ",")
    return [x.strip() for x in text.split(",") if x.strip()]


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
>>>>>>> cc237a9798bbf38a9c18ff3e68180ff08d5da0a6


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def parse_iso(ts: str) -> datetime | None:
    if not ts:
        return None
    try:
        return datetime.fromisoformat(ts)
    except Exception:
        return None


<<<<<<< HEAD
@lru_cache(maxsize=1024)
def _fetch_url_bytes(url: str) -> bytes | None:
    if not url:
        return None
    try:
        with urlopen(url, timeout=8) as response:
            return response.read()
    except Exception:
        return None


@lru_cache(maxsize=512)
def _get_game_icon_url(appid: str) -> str | None:
    if not appid:
        return None

    api_url = f"{STEAM_APP_DETAILS_API}?appids={appid}&l=schinese"
    raw = _fetch_url_bytes(api_url)
    if not raw:
        return None

    try:
        payload = json.loads(raw.decode("utf-8", errors="ignore"))
    except json.JSONDecodeError:
        return None

    app_node = payload.get(str(appid), {})
    if not app_node.get("success"):
        return None

    app_info = app_node.get("data", {})
    return app_info.get("header_image") or app_info.get("capsule_image")


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
    if not url:
        return None

    candidates: list[str] = []
    if proxy_prefix:
        candidates.append(_with_image_proxy(url, proxy_prefix))
    candidates.append(url)

    for candidate in _unique_items(candidates):
        raw = _fetch_url_bytes(candidate)
        if not raw:
            continue
        try:
            image = Image.open(BytesIO(raw)).convert("RGBA")
            return image.resize(size, Image.Resampling.LANCZOS)
        except Exception:
            continue
    return None


def _circle_crop(image: Image.Image) -> Image.Image:
    mask = Image.new("L", image.size, 0)
    drawer = ImageDraw.Draw(mask)
    drawer.ellipse((0, 0, image.size[0], image.size[1]), fill=255)
    output = Image.new("RGBA", image.size)
    output.paste(image, (0, 0), mask)
    return output


def _player_sort_key(player: dict[str, Any]) -> tuple[bool, bool, str]:
    online = _persona_state(player.get("personastate")) != 0
    in_game = bool((player.get("gameextrainfo", "") or "").strip())
    name = str(player.get("personaname", "") or "").casefold()
    return (not online, not in_game, name)


def _text_size(drawer: ImageDraw.ImageDraw, text: str, font) -> tuple[int, int]:
    bbox = drawer.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


def _draw_badge(
    drawer: ImageDraw.ImageDraw,
    x: int,
    y: int,
    text: str,
    font,
    fill: tuple[int, int, int],
    text_fill: tuple[int, int, int] = (255, 255, 255),
) -> None:
    text_w, text_h = _text_size(drawer, text, font)
    pad_x = 12
    pad_y = 6
    drawer.rounded_rectangle(
        (x, y, x + text_w + pad_x * 2, y + text_h + pad_y * 2),
        radius=12,
        fill=fill,
    )
    drawer.text((x + pad_x, y + pad_y - 1), text, fill=text_fill, font=font)


@register(
    "astrbot_plugin_steam_friend_monitor",
    "SZC",
    "Steam 好友在线监控",
    "0.2.0",
)
=======
def pick_cjk_font() -> str | None:
    candidates = [
        "C:/Windows/Fonts/msyh.ttc",
        "C:/Windows/Fonts/msyhbd.ttc",
        "C:/Windows/Fonts/simsun.ttc",
        "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
        "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/noto/NotoSansSC-Regular.otf",
        "/System/Library/Fonts/PingFang.ttc",
    ]
    for fp in candidates:
        if Path(fp).exists():
            return fp
    return None


def safe_font(size: int, plugin_dir: Path | None = None):
    if plugin_dir is not None:
        bundled = plugin_dir / "fonts" / "NotoSansCJKsc-Regular.otf"
        if bundled.exists():
            try:
                return ImageFont.truetype(str(bundled), size)
            except Exception as e:
                logger.warning(f"[steam-monitor] load bundled font failed: {e}")

    sys_font = pick_cjk_font()
    if sys_font:
        try:
            return ImageFont.truetype(sys_font, size)
        except Exception as e:
            logger.warning(f"[steam-monitor] load system font failed: {e}")

    logger.warning(
        "[steam-monitor] no CJK font found; fallback font may render Chinese as squares"
    )
    return ImageFont.load_default()


def _dedup_keep_order(items):
    return list(dict.fromkeys(x for x in items if x))


def circle_crop(img: Image.Image) -> Image.Image:
    mask = Image.new("L", img.size, 0)
    d = ImageDraw.Draw(mask)
    d.ellipse((0, 0, img.size[0], img.size[1]), fill=255)
    out = Image.new("RGBA", img.size)
    out.paste(img, (0, 0), mask)
    return out


>>>>>>> cc237a9798bbf38a9c18ff3e68180ff08d5da0a6
class SteamFriendMonitor(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.config = config
        self.plugin_dir = Path(__file__).parent
<<<<<<< HEAD
        self.data_dir = self.plugin_dir / "data"
        self.render_dir = self.data_dir / "renders"
        self.state_file = self.data_dir / "state.json"

        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.render_dir.mkdir(parents=True, exist_ok=True)

        self.state: dict[str, Any] = self._load_state()
        self._stop = False
        self._task: asyncio.Task | None = None
        self._http_client: httpx.AsyncClient | None = None
        self._render_lock = asyncio.Lock()

        self._migrate_legacy_state()

    async def initialize(self):
        logger.info("[steam-monitor] initialized")
        await self._ensure_http_client()
        self._task = asyncio.create_task(self._poll_loop())
=======

        self.data_dir = StarTools.get_data_dir("astrbot_plugin_steam_friend_monitor")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.state_file = self.data_dir / "state.json"

        self.state: Dict[str, Any] = self._load_state()
        self._stop = False
        self._task: asyncio.Task | None = None

        self.http: httpx.AsyncClient | None = None
        self.bytes_cache: OrderedDict[str, tuple[float, bytes]] = OrderedDict()
        self.icon_url_cache: OrderedDict[str, tuple[float, str]] = OrderedDict()
        self._config_lock = asyncio.Lock()
        self._bg_tasks: set[asyncio.Task] = set()

    async def initialize(self):
        self.http = httpx.AsyncClient(timeout=15, follow_redirects=True)
        self._task = asyncio.create_task(self._poll_loop())
        logger.info("[steam-monitor] initialized")
>>>>>>> cc237a9798bbf38a9c18ff3e68180ff08d5da0a6

    async def terminate(self):
        self._stop = True
        if self._task:
            self._task.cancel()
<<<<<<< HEAD
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        if self._http_client is not None:
            await self._http_client.aclose()
            self._http_client = None
        logger.info("[steam-monitor] terminated")

    def _load_state(self) -> dict[str, Any]:
        if not self.state_file.exists():
            return {}

        try:
            payload = json.loads(self.state_file.read_text(encoding="utf-8"))
        except Exception:
            return {}

        return payload if isinstance(payload, dict) else {}

    def _save_state(self):
        temp_file = self.state_file.with_suffix(".tmp")
        temp_file.write_text(
            json.dumps(self.state, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        temp_file.replace(self.state_file)
=======
            with contextlib.suppress(asyncio.CancelledError):
                await self._task
            self._task = None
        for t in list(self._bg_tasks):
            t.cancel()
        self._bg_tasks.clear()
        if self.http:
            await self.http.aclose()
            self.http = None
        logger.info("[steam-monitor] terminated")

    def _load_state(self) -> Dict[str, Any]:
        if not self.state_file.exists():
            return {}
        try:
            return json.loads(self.state_file.read_text(encoding="utf-8"))
        except Exception as e:
            logger.warning(f"[steam-monitor] load state failed: {e}")
            return {}

    def _save_state(self):
        tmp = self.state_file.with_suffix(".json.tmp")
        tmp.write_text(
            json.dumps(self.state, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        tmp.replace(self.state_file)
>>>>>>> cc237a9798bbf38a9c18ff3e68180ff08d5da0a6

    def _save_config_safe(self):
        try:
            self.config.save_config()
<<<<<<< HEAD
        except Exception as exc:
            logger.warning(f"[steam-monitor] save_config failed: {exc}")

    def _migrate_legacy_state(self):
        legacy_targets = self.state.get("_push_targets")
        if not legacy_targets:
            return

        if isinstance(legacy_targets, list):
            migrated_targets = _unique_items(str(item) for item in legacy_targets)
        else:
            migrated_targets = parse_ids(str(legacy_targets))

        if migrated_targets and not parse_ids(self.config.get("push_targets", "")):
            self.config["push_targets"] = ",".join(migrated_targets)
            self._save_config_safe()

        self.state.pop("_push_targets", None)
        self._save_state()

    async def _ensure_http_client(self) -> httpx.AsyncClient:
        if self._http_client is None or self._http_client.is_closed:
            self._http_client = httpx.AsyncClient(
                timeout=httpx.Timeout(20.0, connect=10.0),
                headers={"User-Agent": "AstrBot-Steam-Friend-Monitor/0.2.0"},
            )
        return self._http_client

    def _get_poll_interval(self) -> int:
        return _to_int(
            self.config.get("poll_interval_sec", 60),
            60,
            minimum=MIN_POLL_INTERVAL_SEC,
        )

    def _is_online_only(self) -> bool:
        return _to_bool(self.config.get("online_only", True), True)

    def _get_steam_ids(self) -> list[str]:
        return [
            steam_id
            for steam_id in parse_ids(self.config.get("steam_ids", ""))
            if is_valid_steam_id(steam_id)
        ]

    def _get_targets(self) -> list[str]:
        config_targets = parse_ids(self.config.get("push_targets", ""))
        legacy_targets = self.state.get("_push_targets", [])
        if isinstance(legacy_targets, list):
            legacy_list = _unique_items(str(item) for item in legacy_targets)
        else:
            legacy_list = parse_ids(str(legacy_targets))
        return _unique_items(config_targets + legacy_list)

    def _set_targets(self, targets: list[str]):
        unique_targets = _unique_items(targets)
        self.config["push_targets"] = ",".join(unique_targets)
        if "_push_targets" in self.state:
            self.state.pop("_push_targets", None)
            self._save_state()
        self._save_config_safe()

    def _cleanup_removed_players(self, configured_ids: list[str]):
        valid_keys = set(configured_ids)
        stale_keys = [
            key
            for key in self.state.keys()
            if not key.startswith("_") and key not in valid_keys
        ]
        for key in stale_keys:
            self.state.pop(key, None)

    async def _fetch_players(self, steam_ids: list[str]) -> list[dict[str, Any]]:
        api_key = str(self.config.get("steam_api_key", "") or "").strip()
        if not api_key:
            raise RuntimeError("未配置 steam_api_key")

        if not steam_ids:
            return []

        client = await self._ensure_http_client()
        players: list[dict[str, Any]] = []

        for batch in _chunked(steam_ids, MAX_STEAM_IDS_PER_REQUEST):
            response = await client.get(
                STEAM_SUMMARY_API,
                params={"key": api_key, "steamids": ",".join(batch)},
            )
            response.raise_for_status()
            payload = response.json()
            players.extend(payload.get("response", {}).get("players", []))

        player_map = {
            str(player.get("steamid", "")).strip(): player
            for player in players
            if str(player.get("steamid", "")).strip()
        }
        missing_ids = [steam_id for steam_id in steam_ids if steam_id not in player_map]
        if missing_ids:
            logger.warning(
                f"[steam-monitor] player summary missing for steam ids: {','.join(missing_ids)}"
            )

        return [player_map[steam_id] for steam_id in steam_ids if steam_id in player_map]

    def _build_transition_events(
        self,
        name: str,
        previous_state: int | None,
        current_state: int,
        previous_game: str,
        current_game: str,
        online_only: bool,
    ) -> list[str]:
        if previous_state is None:
            return []

        events: list[str] = []

        if previous_state == 0 and current_state != 0:
            events.append(f"{name}: 上线（{persona_text(current_state)}）")
            if online_only:
                return events

        if online_only:
            return events

        if previous_state != 0 and current_state == 0:
            events.append(f"{name}: 下线")
        elif (
            previous_state not in (None, current_state)
            and previous_state != 0
            and current_state != 0
        ):
            events.append(
                f"{name}: 状态变更（{persona_text(previous_state)} -> {persona_text(current_state)}）"
            )

        if current_state != 0:
            if not previous_game and current_game:
                events.append(f"{name}: 启动游戏《{current_game}》")
            elif previous_game and not current_game:
                events.append(f"{name}: 关闭游戏《{previous_game}》")
            elif previous_game and current_game and previous_game != current_game:
                events.append(f"{name}: 切换游戏《{previous_game}》 -> 《{current_game}》")

        return events

    def _update_state_and_collect_events(
        self,
        players: list[dict[str, Any]],
        configured_ids: list[str],
    ) -> list[str]:
        events: list[str] = []
        online_only = self._is_online_only()
        current_time = now_iso()

        for player in players:
            steam_id = str(player.get("steamid", "")).strip()
            if not steam_id:
                continue

            current_state = _persona_state(player.get("personastate"))
            current_game = str(player.get("gameextrainfo", "") or "").strip()
            previous_record = self.state.get(steam_id, {})
            previous_raw_state = previous_record.get("personastate")
            previous_state = (
                _persona_state(previous_raw_state)
                if previous_raw_state is not None
                else None
            )
            previous_game = str(previous_record.get("gameextrainfo", "") or "").strip()

            events.extend(
                self._build_transition_events(
                    name=str(player.get("personaname", "?") or "?"),
                    previous_state=previous_state,
                    current_state=current_state,
                    previous_game=previous_game,
                    current_game=current_game,
                    online_only=online_only,
                )
            )

            offline_since = str(previous_record.get("offline_since", "") or "").strip()
            if current_state == 0:
                if not (previous_state == 0 and offline_since):
                    offline_since = current_time
            else:
                offline_since = ""

            self.state[steam_id] = {
                "personaname": str(player.get("personaname", "") or ""),
                "personastate": current_state,
                "gameextrainfo": current_game,
                "offline_since": offline_since,
                "ts": current_time,
            }

        self._cleanup_removed_players(configured_ids)
        self.state["_last_sync"] = current_time
        return events

    def _build_status_image_sync(self, players: list[dict[str, Any]]) -> str:
        ordered_players = sorted(players, key=_player_sort_key)

        width = 1040
        header_height = 96
        row_height = 112
        height = header_height + row_height * max(1, len(ordered_players)) + 24

        image = Image.new("RGB", (width, height), (18, 22, 28))
        drawer = ImageDraw.Draw(image)

        font_title = _safe_font(30, self.plugin_dir)
        font_name = _safe_font(24, self.plugin_dir)
        font_text = _safe_font(18, self.plugin_dir)
        font_small = _safe_font(16, self.plugin_dir)
        font_avatar = _safe_font(28, self.plugin_dir)

        online_count = sum(
            1 for player in ordered_players if _persona_state(player.get("personastate")) != 0
        )
        in_game_count = sum(
            1 for player in ordered_players if (player.get("gameextrainfo", "") or "").strip()
        )
        generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        summary_text = f"共 {len(ordered_players)} 人，在线 {online_count} 人，游戏中 {in_game_count} 人"

        drawer.text((28, 22), "Steam 好友状态", fill=(243, 244, 246), font=font_title)
        drawer.text((28, 60), summary_text, fill=(160, 170, 180), font=font_text)

        generated_width, _ = _text_size(drawer, generated_at, font_small)
        drawer.text(
            (width - 28 - generated_width, 30),
            generated_at,
            fill=(160, 170, 180),
            font=font_small,
        )

        proxy_prefix = str(
            self.config.get("image_proxy_prefix", DEFAULT_IMAGE_PROXY_PREFIX)
            or DEFAULT_IMAGE_PROXY_PREFIX
        ).strip()

        if not ordered_players:
            drawer.rounded_rectangle(
                (24, header_height, width - 24, header_height + 96),
                radius=18,
                fill=(32, 39, 48),
            )
            drawer.text(
                (48, header_height + 34),
                "未获取到玩家数据，请检查 SteamID64 与 API Key 配置。",
                fill=(220, 220, 220),
                font=font_text,
            )
        else:
            y = header_height
            for player in ordered_players:
                state = _persona_state(player.get("personastate"))
                status_color = persona_color(state)
                game_name = str(player.get("gameextrainfo", "") or "").strip()
                game_id = str(player.get("gameid", "") or "").strip()
                name = str(player.get("personaname", "Unknown") or "Unknown")

                drawer.rounded_rectangle(
                    (24, y, width - 24, y + 96),
                    radius=18,
                    fill=(32, 39, 48),
                )
                drawer.rounded_rectangle(
                    (24, y, 34, y + 96),
                    radius=5,
                    fill=status_color,
                )

                avatar = None
                avatar_url = (
                    player.get("avatarfull")
                    or player.get("avatarmedium")
                    or player.get("avatar")
                )
                if avatar_url:
                    avatar = _load_remote_image(str(avatar_url), (68, 68), proxy_prefix)
                    if avatar is not None:
                        avatar = _circle_crop(avatar)

                avatar_left = 52
                avatar_top = y + 14
                if avatar is not None:
                    image.paste(avatar, (avatar_left, avatar_top), avatar)
                else:
                    drawer.ellipse(
                        (avatar_left, avatar_top, avatar_left + 68, avatar_top + 68),
                        fill=(58, 69, 82),
                    )
                    fallback_text = (name[:1] or "?").upper()
                    fallback_width, fallback_height = _text_size(
                        drawer, fallback_text, font_avatar
                    )
                    drawer.text(
                        (
                            avatar_left + (68 - fallback_width) / 2,
                            avatar_top + (68 - fallback_height) / 2 - 2,
                        ),
                        fallback_text,
                        fill=(235, 235, 235),
                        font=font_avatar,
                    )

                drawer.text((140, y + 18), name, fill=(243, 244, 246), font=font_name)
                _draw_badge(
                    drawer,
                    140,
                    y + 54,
                    f"状态 {persona_text(state)}",
                    font_small,
                    fill=status_color,
                )

                game_text = f"正在玩：{game_name}" if game_name else "未在运行游戏"
                drawer.text(
                    (300, y + 57),
                    game_text,
                    fill=(190, 198, 205),
                    font=font_text,
                )

                if game_id:
                    icon_url = _get_game_icon_url(game_id)
                    if icon_url:
                        game_icon = _load_remote_image(icon_url, (180, 68), proxy_prefix)
                        if game_icon is not None:
                            image.paste(game_icon, (width - 224, y + 14), game_icon)

                y += row_height

        output_path = self.render_dir / (
            f"steam_status_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid4().hex[:8]}.png"
        )
        image.save(output_path, format="PNG")
        self._cleanup_render_cache_sync()
        return str(output_path)

    def _cleanup_render_cache_sync(self):
        render_files = sorted(
            self.render_dir.glob("steam_status_*.png"),
            key=lambda path: path.stat().st_mtime,
            reverse=True,
        )
        for stale_file in render_files[MAX_RENDER_CACHE_FILES:]:
            try:
                stale_file.unlink()
            except Exception:
                continue

    async def _render_status_image(self, players: list[dict[str, Any]]) -> str:
        async with self._render_lock:
            return await asyncio.to_thread(self._build_status_image_sync, players)

    async def _push_image(self, target: str, text: str, image_path: str):
        chain = MessageChain()
        chain.chain = [
            Comp.Plain(text=text),
            Comp.Image.fromFileSystem(image_path),
        ]
        await self.context.send_message(target, chain)

    def _compute_next_interval(
        self,
        players: list[dict[str, Any]],
        default_sec: int,
        configured_ids: list[str],
    ) -> int:
        default_sec = max(MIN_POLL_INTERVAL_SEC, default_sec)
        if any(_persona_state(player.get("personastate")) != 0 for player in players):
            return default_sec

        offline_minutes_max = 0.0
        for steam_id in configured_ids:
            record = self.state.get(steam_id, {})
            offline_since = parse_iso(str(record.get("offline_since", "") or ""))
            if offline_since is None:
                continue
            offline_minutes = (datetime.now() - offline_since).total_seconds() / 60.0
            offline_minutes_max = max(offline_minutes_max, offline_minutes)

        if offline_minutes_max >= 30:
            return max(default_sec, 600)
        if offline_minutes_max >= 10:
            return max(default_sec, 300)
        return default_sec

    def _format_player_summary(
        self, player: dict[str, Any], include_steam_id: bool = False
    ) -> str:
        name = str(player.get("personaname", "?") or "?")
        steam_id = str(player.get("steamid", "") or "").strip()
        state_text = persona_text(_persona_state(player.get("personastate")))
        game_name = str(player.get("gameextrainfo", "") or "").strip()
        prefix = f"{name} ({steam_id})" if include_steam_id and steam_id else name
        if game_name:
            return f"{prefix}: {state_text} | 游戏中：{game_name}"
        return f"{prefix}: {state_text}"

    def _build_config_snapshot(self) -> str:
        steam_ids = self._get_steam_ids()
        targets = self._get_targets()
        return "\n".join(
            [
                "[steam_monitor_test: config]",
                f"steam_ids_count={len(steam_ids)}",
                f"push_targets_count={len(targets)}",
                f"poll_interval_sec={self._get_poll_interval()}",
                f"online_only={self._is_online_only()}",
                f"steam_api_key_set={'yes' if bool(self.config.get('steam_api_key', '')) else 'no'}",
                f"image_proxy_prefix={self.config.get('image_proxy_prefix', DEFAULT_IMAGE_PROXY_PREFIX) or ''}",
            ]
        )
=======
        except Exception as e:
            logger.warning(f"[steam-monitor] save config failed: {e}")

    async def _update_config_atomic(self, key: str, value: str):
        async with self._config_lock:
            self.config[key] = value
            self._save_config_safe()

    async def _update_targets_atomic(self, targets: List[str]):
        async with self._config_lock:
            self._set_targets(targets)

    async def _is_host_resolved_private(self, host: str) -> bool:
        host = (host or "").strip()
        if not host:
            return True
        with contextlib.suppress(Exception):
            loop = asyncio.get_running_loop()
            infos = await loop.getaddrinfo(host, None)
            for info in infos:
                ip_str = info[4][0]
                with contextlib.suppress(Exception):
                    ip = ipaddress.ip_address(ip_str)
                    if (
                        ip.is_loopback
                        or ip.is_private
                        or ip.is_link_local
                        or ip.is_reserved
                        or ip.is_multicast
                        or ip.is_unspecified
                    ):
                        return True
        return False

    async def _delayed_unlink(self, image_path: str, delay_sec: int = 30):
        await asyncio.sleep(max(1, delay_sec))
        with contextlib.suppress(Exception):
            Path(image_path).unlink(missing_ok=True)

    def _schedule_delayed_unlink(self, image_path: str, delay_sec: int = 30):
        task = asyncio.create_task(self._delayed_unlink(image_path, delay_sec))
        self._bg_tasks.add(task)
        task.add_done_callback(lambda t: self._bg_tasks.discard(t))

    def _cache_ttl(self) -> int:
        return max(60, int(self.config.get("cache_ttl_sec", 3600) or 3600))

    def _cache_limit(self, kind: str) -> int:
        if kind == "bytes":
            return max(100, int(self.config.get("cache_max_bytes_items", 512) or 512))
        return max(100, int(self.config.get("cache_max_icon_items", 1024) or 1024))

    def _cache_get(self, cache: OrderedDict, key: str):
        if key not in cache:
            return None
        ts, val = cache[key]
        if time.time() - ts > self._cache_ttl():
            cache.pop(key, None)
            return None
        cache.move_to_end(key)
        return val

    def _cache_set(self, cache: OrderedDict, key: str, val: Any, kind: str):
        cache[key] = (time.time(), val)
        cache.move_to_end(key)
        while len(cache) > self._cache_limit(kind):
            cache.popitem(last=False)

    def _is_authorized(self, event: AstrMessageEvent) -> bool:
        allow = parse_ids(self.config.get("admin_origins", ""))
        if not allow:
            return True
        return event.unified_msg_origin in allow

    def _get_targets(self) -> List[str]:
        cfg_targets = parse_ids(self.config.get("push_targets", ""))
        legacy_targets = self.state.get("_push_targets", [])
        if not isinstance(legacy_targets, list):
            logger.warning("[steam-monitor] invalid legacy _push_targets type; ignored")
            legacy_targets = []
        legacy_targets = [x for x in legacy_targets if isinstance(x, str)]
        return _dedup_keep_order(cfg_targets + legacy_targets)

    def _set_targets(self, targets: List[str]):
        uniq = _dedup_keep_order(targets)
        self.config["push_targets"] = ",".join(uniq)
        self._save_config_safe()

    async def _fetch_players(self, steam_ids: List[str]) -> List[Dict[str, Any]]:
        api_key = self.config.get("steam_api_key", "")
        if not api_key:
            raise RuntimeError("未配置 steam_api_key")

        if not self.http:
            self.http = httpx.AsyncClient(timeout=15, follow_redirects=True)

        uniq_ids = _dedup_keep_order(steam_ids)

        batch_size = min(
            100, max(1, int(self.config.get("steam_batch_size", 100) or 100))
        )
        players: List[Dict[str, Any]] = []
        for i in range(0, len(uniq_ids), batch_size):
            chunk = uniq_ids[i : i + batch_size]
            params = {"key": api_key, "steamids": ",".join(chunk)}
            r = await self.http.get(STEAM_SUMMARY_API, params=params)
            r.raise_for_status()
            data = r.json()
            players.extend(data.get("response", {}).get("players", []))

        return players

    def _is_private_host(self, host: str) -> bool:
        host = (host or "").strip().lower()
        if not host:
            return True
        if host in {"localhost", "localhost.localdomain"}:
            return True
        try:
            ip = ipaddress.ip_address(host)
            return (
                ip.is_loopback
                or ip.is_private
                or ip.is_link_local
                or ip.is_reserved
                or ip.is_multicast
                or ip.is_unspecified
            )
        except Exception:
            # 域名层面的基础阻断（可按需扩展白名单）
            bad_suffixes = (
                ".local",
                ".lan",
                ".home",
                ".internal",
                ".corp",
                ".localhost",
            )
            return host.endswith(bad_suffixes)

    def _with_image_proxy(self, url: str, proxy_prefix: str) -> str:
        prefix = (proxy_prefix or "").strip()
        if not prefix:
            return url

        # 仅允许 http/https 且禁止本地回环/文件协议，避免恶意中转配置
        try:
            parsed = urlparse(prefix)
            scheme = (parsed.scheme or "").lower()
            host = (parsed.hostname or "").lower()
            if scheme and scheme not in ("http", "https"):
                logger.warning(f"[steam-monitor] invalid proxy scheme: {scheme}")
                return url
            if self._is_private_host(host):
                logger.warning("[steam-monitor] blocked private/local proxy host")
                return url
        except Exception as e:
            logger.warning(f"[steam-monitor] invalid proxy prefix: {e}")
            return url

        encoded = quote(url, safe="")
        if "{url}" in prefix:
            return prefix.replace("{url}", encoded)
        if "%s" in prefix:
            try:
                return prefix % encoded
            except Exception as e:
                logger.warning(f"[steam-monitor] invalid proxy format: {e}")
                return url
        return prefix + encoded

    async def _is_allowed_remote_url(self, url: str) -> bool:
        try:
            parsed = urlparse(url)
            scheme = (parsed.scheme or "").lower()
            host = (parsed.hostname or "").lower()
            if scheme not in ("http", "https"):
                return False
            if self._is_private_host(host):
                return False
            if await self._is_host_resolved_private(host):
                return False

            strict = bool(self.config.get("strict_remote_host", False))
            if not strict:
                return True

            custom = parse_ids(self.config.get("remote_host_allowlist", ""))
            allow = [
                "steamcommunity.com",
                "steamstatic.com",
                "steampowered.com",
                "akamaihd.net",
                "images.weserv.nl",
            ] + custom
            return any(host == d or host.endswith("." + d) for d in allow)
        except Exception:
            return False

    async def _fetch_url_bytes(
        self,
        url: str,
        proxy_prefix: str = "",
        allowed_types: tuple[str, ...] = ("image/", "application/json"),
        max_bytes: int = 3 * 1024 * 1024,
    ) -> bytes | None:
        if not url:
            return None

        cached = self._cache_get(self.bytes_cache, url)
        if cached is not None:
            return cached

        if not self.http:
            self.http = httpx.AsyncClient(timeout=15, follow_redirects=True)

        candidates = [url]
        if proxy_prefix:
            candidates.append(self._with_image_proxy(url, proxy_prefix))

        max_redirects = max(0, int(self.config.get("max_redirects", 3) or 3))

        for origin in candidates:
            current = origin
            if not await self._is_allowed_remote_url(current):
                logger.debug(f"[steam-monitor] blocked remote url: {current}")
                continue

            try:
                for _ in range(max_redirects + 1):
                    async with self.http.stream(
                        "GET", current, follow_redirects=False
                    ) as resp:
                        # redirect handling with per-hop validation
                        if resp.status_code in (301, 302, 303, 307, 308):
                            location = resp.headers.get("location")
                            if not location:
                                break
                            next_url = str(httpx.URL(location, base=resp.request.url))
                            if not await self._is_allowed_remote_url(next_url):
                                logger.warning(
                                    f"[steam-monitor] blocked redirect target: {next_url}"
                                )
                                break
                            current = next_url
                            continue

                        if resp.status_code != 200:
                            break

                        ctype = (resp.headers.get("content-type") or "").lower()
                        if allowed_types and not any(
                            ctype.startswith(x) for x in allowed_types
                        ):
                            break

                        clen = resp.headers.get("content-length")
                        if clen:
                            with contextlib.suppress(Exception):
                                if int(clen) > max_bytes:
                                    break

                        buf = bytearray()
                        async for chunk in resp.aiter_bytes(65536):
                            buf.extend(chunk)
                            if len(buf) > max_bytes:
                                buf = bytearray()
                                break

                        if not buf:
                            break

                        raw = bytes(buf)
                        self._cache_set(self.bytes_cache, url, raw, "bytes")
                        return raw
                    break
            except Exception as e:
                logger.debug(
                    f"[steam-monitor] fetch image bytes failed: {origin} err={e}"
                )

        return None

    async def _get_game_icon_url(self, appid: str) -> str | None:
        if not appid:
            return None
        cached = self._cache_get(self.icon_url_cache, appid)
        if cached is not None:
            return cached

        api = f"https://store.steampowered.com/api/appdetails?appids={appid}&l=schinese"
        raw = await self._fetch_url_bytes(
            api,
            allowed_types=("application/json", "text/json", "text/plain"),
            max_bytes=512 * 1024,
        )
        if not raw:
            return None

        try:
            data = json.loads(raw.decode("utf-8", errors="ignore"))
            node = data.get(str(appid), {})
            if not node.get("success"):
                return None
            app = node.get("data", {})
            icon_url = app.get("header_image") or app.get("capsule_image")
            if icon_url:
                self._cache_set(self.icon_url_cache, appid, icon_url, "icon")
            return icon_url
        except Exception as e:
            logger.warning(f"[steam-monitor] parse game icon failed appid={appid}: {e}")
            return None

    def _process_image_bytes(
        self, raw: bytes, size: tuple[int, int], circle: bool = False
    ) -> Image.Image | None:
        try:
            with Image.open(BytesIO(raw)) as opened:
                max_pixels = max(
                    512 * 512,
                    int(self.config.get("max_image_pixels", 4_000_000) or 4_000_000),
                )
                if opened.width * opened.height > max_pixels:
                    logger.warning(
                        f"[steam-monitor] image too large: {opened.width}x{opened.height}"
                    )
                    return None
                img = opened.convert("RGBA")
            img = img.resize(size, Image.Resampling.LANCZOS)
            if circle:
                img = circle_crop(img)
            return img
        except Exception as e:
            logger.warning(f"[steam-monitor] decode image failed: {e}")
            return None

    async def _load_remote_image(
        self,
        url: str,
        size: tuple[int, int],
        proxy_prefix: str = "",
        circle: bool = False,
    ) -> Image.Image | None:
        raw = await self._fetch_url_bytes(
            url,
            proxy_prefix=proxy_prefix,
            allowed_types=("image/",),
            max_bytes=max(
                256 * 1024,
                int(
                    self.config.get("max_image_bytes", 3 * 1024 * 1024)
                    or 3 * 1024 * 1024
                ),
            ),
        )
        if not raw:
            return None
        return await asyncio.to_thread(self._process_image_bytes, raw, size, circle)

    async def _prepare_assets(
        self, players: List[Dict[str, Any]]
    ) -> Dict[str, Dict[str, Any]]:
        proxy_prefix = self.config.get(
            "image_proxy_prefix", "https://images.weserv.nl/?url="
        )
        concurrency = max(1, int(self.config.get("asset_concurrency", 6) or 6))
        sem = asyncio.Semaphore(concurrency)

        async def one_player(p: Dict[str, Any]):
            sid = str(p.get("steamid", ""))
            avatar_url = p.get("avatarfull") or p.get("avatarmedium") or p.get("avatar")
            gameid = str(p.get("gameid", "") or "").strip()

            async with sem:
                avatar = await self._load_remote_image(
                    avatar_url or "", (64, 64), proxy_prefix, circle=True
                )

            game_icon = None
            if gameid:
                async with sem:
                    icon_url = await self._get_game_icon_url(gameid)
                if icon_url:
                    async with sem:
                        game_icon = await self._load_remote_image(
                            icon_url, (180, 68), proxy_prefix
                        )

            return sid, {"avatar": avatar, "game_icon": game_icon}

        pairs = await asyncio.gather(
            *(one_player(p) for p in players), return_exceptions=False
        )
        return dict(pairs)

    def _build_status_image(
        self, players: List[Dict[str, Any]], assets: Dict[str, Dict[str, Any]]
    ) -> str:
        w = 980
        row_h = 110
        top = 56
        h = top + row_h * max(1, len(players)) + 20

        img = Image.new("RGB", (w, h), (22, 26, 31))
        draw = ImageDraw.Draw(img)

        font_text = safe_font(24, self.plugin_dir)
        font_small = safe_font(18, self.plugin_dir)

        now_text = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        box = draw.textbbox((0, 0), now_text, font=font_small)
        text_w = box[2] - box[0]
        draw.text(
            (w - 24 - text_w, 18), now_text, fill=(160, 170, 180), font=font_small
        )

        y = top
        for p in players:
            sid = str(p.get("steamid", ""))
            aset = assets.get(sid, {})

            name = p.get("personaname", "Unknown")
            state = int(p.get("personastate", 0))
            game = (p.get("gameextrainfo", "") or "").strip()

            draw.rounded_rectangle(
                (20, y, w - 20, y + 96), radius=14, fill=(35, 41, 48)
            )

            avatar = aset.get("avatar")
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

            game_icon = aset.get("game_icon")
            if game_icon is not None:
                img.paste(game_icon, (w - 220, y + 14), game_icon)

            y += row_h

        out = (
            self.data_dir
            / f"steam_status_{int(time.time())}_{uuid.uuid4().hex[:8]}.png"
        )
        try:
            img.save(out)
            return str(out)
        finally:
            img.close()

    async def _render_status_image(self, players: List[Dict[str, Any]]) -> str:
        assets = await self._prepare_assets(players)
        return await asyncio.to_thread(self._build_status_image, players, assets)

    async def _push_image(self, umo: str, text: str, image_path: str):
        chain = MessageChain()
        chain.chain = [Comp.Plain(text=text), Comp.Image.fromFileSystem(image_path)]
        await self.context.send_message(umo, chain)

    def _compute_next_interval(self, steam_ids: List[str], default_sec: int) -> int:
        # 基于完整监控集合（配置 ID + state）计算，而不是仅 API 返回列表
        all_ids = _dedup_keep_order(
            sid
            for sid in (steam_ids + list(self.state.keys()))
            if not (isinstance(sid, str) and sid.startswith("_"))
        )

        any_online = False
        offline_minutes_max = 0.0
        for sid in all_ids:
            record = self.state.get(sid, {})
            if not isinstance(record, dict):
                continue
            st = int(record.get("personastate", 0) or 0)
            if st != 0:
                any_online = True
                break
            off_since = parse_iso(record.get("offline_since", ""))
            if off_since:
                mins = (datetime.now() - off_since).total_seconds() / 60.0
                if mins > offline_minutes_max:
                    offline_minutes_max = mins

        if any_online:
            return max(10, default_sec)
        if offline_minutes_max >= 30:
            return 600
        if offline_minutes_max >= 10:
            return 300
        return max(10, default_sec)
>>>>>>> cc237a9798bbf38a9c18ff3e68180ff08d5da0a6

    async def _poll_loop(self):
        await asyncio.sleep(3)
        while not self._stop:
<<<<<<< HEAD
            configured_ids = self._get_steam_ids()
            default_interval = self._get_poll_interval()

            if not configured_ids:
                await asyncio.sleep(max(30, default_interval))
                continue

            next_sleep = default_interval
            try:
                players = await self._fetch_players(configured_ids)
                events = self._update_state_and_collect_events(players, configured_ids)
                self._save_state()

                if events:
                    targets = self._get_targets()
                    if targets:
                        image_path = await self._render_status_image(players)
                        text = "Steam 状态变化：\n" + "\n".join(events)
                        for target in targets:
                            try:
                                await self._push_image(target, text, image_path)
                            except Exception as exc:
                                logger.error(
                                    f"[steam-monitor] push failed for {target}: {exc}"
                                )
                    else:
                        logger.info("[steam-monitor] events detected but no push targets bound")

                next_sleep = self._compute_next_interval(
                    players=players,
                    default_sec=default_interval,
                    configured_ids=configured_ids,
                )
                logger.info(f"[steam-monitor] next poll in {next_sleep}s")
            except asyncio.CancelledError:
                break
            except Exception as exc:
                logger.error(f"[steam-monitor] poll error: {exc}")
                next_sleep = max(30, default_interval)

            await asyncio.sleep(next_sleep)

    @filter.command("sfm_bind")
    async def bind_group(self, event: AstrMessageEvent):
        """绑定当前会话为推送目标。"""
        current_target = event.unified_msg_origin
        targets = self._get_targets()
        if current_target not in targets:
            targets.append(current_target)
            self._set_targets(targets)
        yield event.plain_result(
            "已绑定当前会话为 Steam 监控推送目标，可在配置项 push_targets 中查看。"
=======
            image_path = None
            try:
                steam_ids = parse_ids(self.config.get("steam_ids", ""))
                default_interval = int(self.config.get("poll_interval_sec", 60) or 60)

                if not steam_ids:
                    await asyncio.sleep(max(30, default_interval))
                    continue

                players = await self._fetch_players(steam_ids)
                player_map = {str(p.get("steamid", "")): p for p in players}

                events = []
                now = now_iso()
                for sid in steam_ids:
                    p = player_map.get(sid)
                    if p is None:
                        prev_record = self.state.get(sid, {})
                        prev = prev_record.get("personastate")
                        prev_game = (prev_record.get("gameextrainfo", "") or "").strip()
                        self.state[sid] = {
                            "personaname": prev_record.get("personaname", sid),
                            "personastate": 0,
                            "gameextrainfo": "",
                            "offline_since": prev_record.get("offline_since", now),
                            "ts": now,
                            "missing": True,
                        }
                        if prev is not None and prev != 0:
                            events.append(
                                f"{prev_record.get('personaname', sid)}: 下线（接口未返回）"
                            )
                        elif prev is not None and prev_game:
                            events.append(
                                f"{prev_record.get('personaname', sid)}: 关闭游戏《{prev_game}》（接口未返回）"
                            )
                        continue

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
                        "missing": False,
                    }

                    if prev is None:
                        continue

                    name = p.get("personaname", "?")
                    if prev == 0 and st != 0:
                        events.append(f"{name}: 上线 ({persona_text(st)})")
                    elif prev != 0 and st == 0:
                        events.append(f"{name}: 下线")

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
                    image_path = await self._render_status_image(players)
                    targets = self._get_targets()
                    if targets:
                        text = "Steam 状态变化：" + chr(10) + chr(10).join(events)
                        for umo in targets:
                            try:
                                await self._push_image(umo, text, image_path)
                            except Exception as e:
                                logger.error(f"[steam-monitor] push failed {umo}: {e}")

                next_sleep = self._compute_next_interval(steam_ids, default_interval)
                logger.info(f"[steam-monitor] next poll in {next_sleep}s")
                await asyncio.sleep(next_sleep)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[steam-monitor] poll error: {e}")
                if "steam_api_key" in str(e):
                    await asyncio.sleep(
                        max(
                            300,
                            int(self.config.get("missing_key_sleep_sec", 600) or 600),
                        )
                    )
                else:
                    await asyncio.sleep(30)
            finally:
                if image_path:
                    with contextlib.suppress(Exception):
                        Path(image_path).unlink(missing_ok=True)

    def _validate_steam_id64(self, sid: str) -> bool:
        sid = (sid or "").strip()
        return sid.isdigit() and len(sid) >= 10

    @filter.command("sfm_bind")
    async def bind_group(self, event: AstrMessageEvent):

        if not self._is_authorized(event):
            yield event.plain_result("无权限执行该命令")
            return
        umo = event.unified_msg_origin
        targets = self._get_targets()
        if umo not in targets:
            targets.append(umo)
            await self._update_targets_atomic(targets)
        yield event.plain_result(
            "已绑定当前会话为 Steam 监控推送目标（可在配置页 push_targets 查看）"
>>>>>>> cc237a9798bbf38a9c18ff3e68180ff08d5da0a6
        )

    @filter.command("sfm_unbind")
    async def unbind_group(self, event: AstrMessageEvent):
<<<<<<< HEAD
        """取消当前会话的推送绑定。"""
        current_target = event.unified_msg_origin
        targets = self._get_targets()
        if current_target in targets:
            targets.remove(current_target)
            self._set_targets(targets)
        yield event.plain_result("已取消当前会话的 Steam 监控推送绑定。")

    @filter.command("sfm_targets")
    async def show_targets(self, event: AstrMessageEvent):
        """查看当前推送目标列表。"""
        targets = self._get_targets()
        if not targets:
            yield event.plain_result("当前没有推送目标，请先执行 /sfm_bind。")
            return
        yield event.plain_result("当前推送目标：\n" + "\n".join(targets))

    @filter.command("sfm_add_id")
    async def bind_id(self, event: AstrMessageEvent, steam_id64: str):
        """添加一个 SteamID64 到监控列表。"""
        steam_id64 = str(steam_id64 or "").strip()
        if not is_valid_steam_id(steam_id64):
            yield event.plain_result("SteamID64 格式不正确。")
            return

        ids = self._get_steam_ids()
        if steam_id64 not in ids:
            ids.append(steam_id64)

        self.config["steam_ids"] = ",".join(ids)
        self._save_config_safe()
        yield event.plain_result(
            f"已添加 SteamID64: {steam_id64}，当前监控数量：{len(ids)}"
=======

        if not self._is_authorized(event):
            yield event.plain_result("无权限执行该命令")
            return
        umo = event.unified_msg_origin
        targets = self._get_targets()
        if umo in targets:
            targets.remove(umo)
            self._set_targets(targets)
        yield event.plain_result("已取消当前会话绑定")

    @filter.command("sfm_targets")
    async def show_targets(self, event: AstrMessageEvent):

        if not self._is_authorized(event):
            yield event.plain_result("无权限执行该命令")
            return
        targets = self._get_targets()
        if not targets:
            yield event.plain_result("当前无推送目标，请先 /sfm_bind")
            return
        yield event.plain_result("当前推送目标：" + chr(10) + chr(10).join(targets))

    @filter.command("sfm_add_id")
    async def bind_id(self, event: AstrMessageEvent, steam_id64: str):

        if not self._is_authorized(event):
            yield event.plain_result("无权限执行该命令")
            return
        steam_id64 = (steam_id64 or "").strip()
        if not self._validate_steam_id64(steam_id64):
            yield event.plain_result("SteamID64 格式不正确")
            return

        ids = parse_ids(self.config.get("steam_ids", ""))
        if steam_id64 not in ids:
            ids.append(steam_id64)
        await self._update_config_atomic("steam_ids", ",".join(ids))
        yield event.plain_result(
            f"已绑定 SteamID64: {steam_id64}，当前监控数量: {len(ids)}"
>>>>>>> cc237a9798bbf38a9c18ff3e68180ff08d5da0a6
        )

    @filter.command("sfm_del_id")
    async def unbind_id(self, event: AstrMessageEvent, steam_id64: str):
<<<<<<< HEAD
        """从监控列表移除一个 SteamID64。"""
        steam_id64 = str(steam_id64 or "").strip()
        ids = self._get_steam_ids()
        if steam_id64 in ids:
            ids.remove(steam_id64)
            self.state.pop(steam_id64, None)
            self._save_state()

        self.config["steam_ids"] = ",".join(ids)
        self._save_config_safe()
        yield event.plain_result(
            f"已移除 SteamID64: {steam_id64}，当前监控数量：{len(ids)}"
        )

    @filter.command("sfm_status")
    async def status(self, event: AstrMessageEvent):
        """手动查询并发送当前状态图。"""
        steam_ids = self._get_steam_ids()
        if not steam_ids:
            yield event.plain_result("未配置有效的 steam_ids。")
            return

        players = await self._fetch_players(steam_ids)
        image_path = await self._render_status_image(players)
        summary_lines = (
            [self._format_player_summary(player) for player in players]
            if players
            else ["未获取到玩家数据。"]
        )

        yield event.plain_result("当前状态：\n" + "\n".join(summary_lines))
        chain = MessageChain()
        chain.chain = [Comp.Image.fromFileSystem(image_path)]
        await self.context.send_message(event.unified_msg_origin, chain)

    @filter.command("sfm_set_ids")
    async def set_ids(self, event: AstrMessageEvent, ids: str):
        """批量设置监控的 SteamID64。"""
        parsed_ids = parse_ids(ids)
        valid_ids = [steam_id for steam_id in parsed_ids if is_valid_steam_id(steam_id)]
        invalid_ids = [steam_id for steam_id in parsed_ids if not is_valid_steam_id(steam_id)]

        self.config["steam_ids"] = ",".join(valid_ids)
        self._save_config_safe()
        self._cleanup_removed_players(valid_ids)
        self._save_state()

        if invalid_ids:
            yield event.plain_result(
                f"已设置监控 ID 数量：{len(valid_ids)}；忽略无效 ID：{', '.join(invalid_ids)}"
            )
            return

        yield event.plain_result(f"已设置监控 ID 数量：{len(valid_ids)}")

    @filter.command("sfm_test")
    async def steam_monitor_test(self, event: AstrMessageEvent, action: str = "all"):
        """测试配置、拉取状态、渲染图片和推送链路。"""
        action = str(action or "all").strip().lower()
        valid_actions = {"all", "cfg", "config", "status", "pull", "image", "push"}
        if action not in valid_actions:
            yield event.plain_result("用法：/sfm_test [all|cfg|status|image|push]")
            return

        if action in {"cfg", "config"}:
            yield event.plain_result(self._build_config_snapshot())
            return

        steam_ids = self._get_steam_ids()
        targets = self._get_targets()
        if not steam_ids:
            yield event.plain_result("[steam_monitor_test] 未配置有效的 steam_ids。")
            return

        try:
            players = await self._fetch_players(steam_ids)
            image_path = await self._render_status_image(players)
            status_text = (
                "\n".join(
                    self._format_player_summary(player, include_steam_id=True)
                    for player in players
                )
                if players
                else "未获取到玩家数据。"
            )

            if action in {"status", "pull"}:
                yield event.plain_result("[steam_monitor_test: status]\n" + status_text)
                return

            yield event.plain_result(
                "[steam_monitor_test] 状态拉取成功，正在向当前会话发送测试图片。"
            )
            chain = MessageChain()
            chain.chain = [
                Comp.Plain(text="[steam_monitor_test] 这是当前会话的测试推送图。"),
                Comp.Image.fromFileSystem(image_path),
            ]
            await self.context.send_message(event.unified_msg_origin, chain)

            if action in {"push", "all"}:
                if not targets:
                    yield event.plain_result("[steam_monitor_test] 当前没有绑定的推送目标。")
                    return

                success_count = 0
                for target in targets:
                    try:
                        await self._push_image(
                            target,
                            "[steam_monitor_test] 目标会话推送链路测试。",
                            image_path,
                        )
                        success_count += 1
                    except Exception as exc:
                        logger.error(
                            f"[steam-monitor] test push failed for {target}: {exc}"
                        )

                yield event.plain_result(
                    f"[steam_monitor_test] 目标会话测试推送完成：{success_count}/{len(targets)}"
                )
        except Exception as exc:
            yield event.plain_result(f"[steam_monitor_test] 执行失败: {exc}")
=======

        if not self._is_authorized(event):
            yield event.plain_result("无权限执行该命令")
            return
        steam_id64 = (steam_id64 or "").strip()
        ids = parse_ids(self.config.get("steam_ids", ""))
        if steam_id64 in ids:
            ids.remove(steam_id64)
        self.state.pop(steam_id64, None)
        self._save_state()
        await self._update_config_atomic("steam_ids", ",".join(ids))
        yield event.plain_result(
            f"已移除 SteamID64: {steam_id64}，当前监控数量: {len(ids)}"
        )

    @filter.command("sfm_set_ids")
    async def set_ids(self, event: AstrMessageEvent, ids: str):

        if not self._is_authorized(event):
            yield event.plain_result("无权限执行该命令")
            return
        parsed = parse_ids(ids)
        valid = [sid for sid in parsed if self._validate_steam_id64(sid)]
        invalid = [sid for sid in parsed if not self._validate_steam_id64(sid)]
        await self._update_config_atomic("steam_ids", ",".join(valid))
        if invalid:
            yield event.plain_result(
                f"已设置监控ID数量: {len(valid)}；忽略非法ID {len(invalid)} 个："
                + ", ".join(invalid[:10])
            )
        else:
            yield event.plain_result(f"已设置监控ID数量: {len(valid)}")

    @filter.command("sfm_status")
    async def status(self, event: AstrMessageEvent):

        if not self._is_authorized(event):
            yield event.plain_result("无权限执行该命令")
            return
        steam_ids = parse_ids(self.config.get("steam_ids", ""))
        if not steam_ids:
            yield event.plain_result("未配置 steam_ids")
            return

        image_path = None
        try:
            players = await self._fetch_players(steam_ids)
            image_path = await self._render_status_image(players)
            msg = chr(10).join(
                [
                    f"{p.get('personaname', '?')}: {persona_text(int(p.get('personastate', 0)))}"
                    for p in players
                ]
            )

            chain = MessageChain()
            chain.chain = [
                Comp.Plain(text="当前状态：" + chr(10) + msg),
                Comp.Image.fromFileSystem(image_path),
            ]
            yield event.chain_result(chain)
        finally:
            if image_path:
                self._schedule_delayed_unlink(image_path, 30)

    @filter.command("sfm_test")
    async def steam_monitor_test(self, event: AstrMessageEvent, action: str = "all"):

        if not self._is_authorized(event):
            yield event.plain_result("无权限执行该命令")
            return

        action = (action or "all").strip().lower()
        steam_ids = parse_ids(self.config.get("steam_ids", ""))
        targets = self._get_targets()

        if action in ("cfg", "config"):
            msg = [
                "[steam_monitor_test: config]",
                f"steam_ids_count={len(steam_ids)}",
                f"push_targets_count={len(targets)}",
                f"poll_interval_sec={self.config.get('poll_interval_sec', 60)}",
                f"steam_api_key_set={'yes' if bool(self.config.get('steam_api_key', '')) else 'no'}",
            ]
            yield event.plain_result(chr(10).join(msg))
            return

        if not steam_ids:
            yield event.plain_result("[steam_monitor_test] 未配置 steam_ids")
            return

        image_path = None
        try:
            players = await self._fetch_players(steam_ids)
            status_text = chr(10).join(
                [
                    f"{p.get('personaname', '?')}: {persona_text(int(p.get('personastate', 0)))}"
                    + (
                        f" | {p.get('gameextrainfo', '')}"
                        if p.get("gameextrainfo")
                        else ""
                    )
                    for p in players
                ]
            )

            if action in ("status", "pull"):
                yield event.plain_result(
                    "[steam_monitor_test: status]" + chr(10) + status_text
                )
                return

            image_path = await self._render_status_image(players)

            chain = MessageChain()
            chain.chain = [
                Comp.Plain(text="[steam_monitor_test] 状态拉取成功，测试图如下"),
                Comp.Image.fromFileSystem(image_path),
            ]
            yield event.chain_result(chain)

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
        finally:
            if image_path:
                self._schedule_delayed_unlink(image_path, 30)
>>>>>>> cc237a9798bbf38a9c18ff3e68180ff08d5da0a6
