from datetime import date, datetime
from typing import TYPE_CHECKING
import threading

import bullpen.api as api
from bullpen.logging import LOGGER

from api.disney_api import fetch_list_of_disney_world_parks
from updater.data_updater import live_data_updater
from display.startup import render_mickey_logo
from display.countdown.countdown import render_countdown_to_disney
from display.display import initialize_fonts
from display.attractions.attraction_info import render_attraction_info
from display.park.park_details import render_park_information_screen

if TYPE_CHECKING:
    from RGBMatrixEmulator.emulation.canvas import Canvas


def _active_trip_date(trip_dates: list[date]) -> datetime | None:
    today = date.today()
    latest_past = None
    nearest_future = None
    for d in trip_dates:
        if d < today:
            if latest_past is None or d > latest_past:
                latest_past = d
        else:
            if nearest_future is None or d < nearest_future:
                nearest_future = d
    if latest_past and (today - latest_past).days <= 7:
        return datetime.combine(latest_past, datetime.min.time())
    if nearest_future:
        return datetime.combine(nearest_future, datetime.min.time())
    return None


class Config(api.PluginConfig):
    def __init__(self, base: api.MLBConfig) -> None:
        cfg = base.plugin_config
        self.park_name = cfg.get("park_name", None)  # None = all WDW parks
        self.refresh_seconds = cfg.get("refresh_seconds", 300)
        self.trip_dates: list[date] = []
        for s in cfg.get("trip_dates", []):
            try:
                self.trip_dates.append(date.fromisoformat(str(s)))
            except ValueError:
                LOGGER.warning("LightningLane: ignoring invalid trip date: %s", s)


class Data(api.PluginData):
    def __init__(self, config: Config) -> None:
        self.config = config
        self._parks_data = []  # shared list updated in-place by background thread
        self._thread: threading.Thread | None = None

    def update(self, force: bool = False) -> api.UpdateStatus:  # noqa: ARG002
        if self._thread is not None:
            return api.UpdateStatus.SUCCESS if self._parks_data else api.UpdateStatus.DEFERRED
        try:
            park_list = fetch_list_of_disney_world_parks()
            if not park_list:
                LOGGER.error("LightningLane: no parks returned from API")
                return api.UpdateStatus.FAILURE
            self._thread = threading.Thread(
                target=live_data_updater,
                args=(park_list, self.config.refresh_seconds, self._parks_data),
                daemon=True,
            )
            self._thread.start()
        except Exception:
            LOGGER.exception("LightningLane: failed to start updater thread")
            return api.UpdateStatus.FAILURE
        return api.UpdateStatus.DEFERRED

    def parks(self):
        if self.config.park_name:
            return [p for p in self._parks_data if self.config.park_name.lower() in p["name"].lower()]
        return self._parks_data

    def displayable_rides(self):
        result = []
        for park in self.parks():
            for attraction in park.get("attractions", []):
                if (attraction.get("status") not in ("CLOSED", "REFURBISHMENT")
                        and attraction.get("waitTime") not in (None, "")):
                    result.append((park, attraction))
        return result

    def operating_parks(self):
        seen = set()
        parks = []
        for park, _ in self.displayable_rides():
            if park["id"] not in seen:
                seen.add(park["id"])
                parks.append(park)
        return parks


class Renderer(api.PluginRenderer):
    def __init__(self, config: Config, _layout: api.Layout, _colors: api.Color) -> None:
        self.config = config
        self._phase = "mickey"  # "mickey" | "countdown" | "parks"
        self._park_index = 0
        self._item_index = 0  # 0 = park header, 1+ = attractions
        self._active_trip: datetime | None = None
        self._fonts_ready = False

    def wait_time(self) -> float:
        return 8.0

    def render(self, data: Data, canvas: "Canvas", _graphics: api.renderer.graphics, _scrolling_text_pos: int) -> None:
        if not self._fonts_ready:
            initialize_fonts(canvas.height)
            self._fonts_ready = True

        parks = data.operating_parks()
        if not parks:
            return

        if self._phase == "mickey":
            canvas.Fill(0, 0, 0)
            render_mickey_logo(canvas)
            self._active_trip = _active_trip_date(self.config.trip_dates)
            self._phase = "countdown" if self._active_trip else "parks"

        elif self._phase == "countdown":
            canvas.Fill(0, 0, 0)
            render_countdown_to_disney(canvas, self._active_trip)
            self._phase = "parks"

        else:
            canvas.Fill(0, 0, 0)
            self._render_parks(canvas, parks)

    def _render_parks(self, canvas: "Canvas", parks: list) -> None:
        self._park_index = self._park_index % len(parks)
        park = parks[self._park_index]

        displayable = [
            a for a in park.get("attractions", [])
            if a.get("status") not in ("CLOSED", "REFURBISHMENT")
            and a.get("waitTime") not in (None, "")
        ]

        if self._item_index == 0:
            render_park_information_screen(canvas, park)
            self._item_index = 1
        elif self._item_index - 1 < len(displayable):
            render_attraction_info(canvas, displayable[self._item_index - 1])
            self._item_index += 1

        if self._item_index > len(displayable):
            self._park_index += 1
            self._item_index = 0
            if self._park_index >= len(parks):
                self._phase = "mickey"
                self._park_index = 0

    def can_render(self, data: Data) -> bool:
        return bool(data.operating_parks())

    def reset(self) -> None:
        pass


def load() -> api.PLUGIN_DEFINITION:
    return Config, Data, Renderer
