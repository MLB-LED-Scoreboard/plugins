from typing import TYPE_CHECKING
import requests
import bullpen.api as api
from bullpen.logging import LOGGER
from bullpen.util import scrolling_text

if TYPE_CHECKING:
    from RGBMatrixEmulator.emulation.canvas import Canvas

THEMEPARKS_API = "https://api.themeparks.wiki/v1"


class Config(api.PluginConfig):
    def __init__(self, base: api.MLBConfig) -> None:
        cfg = base.plugin_config
        self.park_id = cfg.get("park_id", "wdw-magickingdom")
        self.refresh_seconds = cfg.get("refresh_seconds", 60)


class Data(api.PluginData):
    def __init__(self, config: Config) -> None:
        self.config = config
        self.park_name = ""
        self.rides = []  # list of {"name": str, "wait": int | None}
        self._ticks = 0

    def update(self, force: bool = False) -> api.UpdateStatus:
        self._ticks += 1
        if not force and self._ticks % (self.config.refresh_seconds * 2) != 0:
            return api.UpdateStatus.SUCCESS

        try:
            url = f"{THEMEPARKS_API}/entity/{self.config.park_id}/live"
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            data = resp.json()

            self.park_name = data.get("name", "Disney")
            self.rides = [
                {
                    "name": e["name"],
                    "wait": e.get("queue", {}).get("STANDBY", {}).get("waitTime"),
                }
                for e in data.get("liveData", [])
                if e.get("entityType") == "ATTRACTION"
            ]
            self.rides.sort(key=lambda r: r["wait"] or 999)
            return api.UpdateStatus.SUCCESS

        except Exception:
            LOGGER.exception("LightningLane: failed to fetch wait times")
            return api.UpdateStatus.FAILURE


class Renderer(api.PluginRenderer):
    def __init__(self, config: Config, layout: api.Layout, colors: api.Color) -> None:
        self.config = config
        self.font = layout.font("4x6.bdf")
        self.color_white = api.renderer.graphics.Color(255, 255, 255)
        self.color_yellow = api.renderer.graphics.Color(255, 215, 0)
        self.color_bg = (0, 0, 40)
        self._ride_index = 0

    def wait_time(self) -> float:
        return 3.0

    def render(self, data: Data, canvas: "Canvas", graphics: api.renderer.graphics, scrolling_text_pos: int) -> None:
        canvas.Fill(*self.color_bg)

        if not data.rides:
            graphics.DrawText(canvas, self.font["font"], 1, 10, self.color_white, "Loading...")
            return

        graphics.DrawText(canvas, self.font["font"], 1, 7, self.color_yellow, data.park_name[:12])

        self._ride_index = self._ride_index % len(data.rides)
        ride = data.rides[self._ride_index]
        self._ride_index += 1

        name = ride["name"][:14]
        wait = f"{ride['wait']} min" if ride["wait"] is not None else "Closed"

        graphics.DrawText(canvas, self.font["font"], 1, 18, self.color_white, name)
        graphics.DrawText(canvas, self.font["font"], 1, 26, self.color_yellow, wait)

    def can_render(self, data: Data) -> bool:
        return len(data.rides) > 0


def load() -> api.PLUGIN_DEFINITION:
    return Config, Data, Renderer
