# Based on https://github.com/tronbyt/apps/tree/main/apps/formula1

import base64
import io
import json
import time
import datetime
import requests
from typing import TYPE_CHECKING
from importlib.resources import files

from PIL import Image

import bullpen
from bullpen.api.update import UpdateStatus
from bullpen.logging import LOGGER
from bullpen.util import scrolling_text
from bullpen.time_formats import TIME_FORMAT_12H, os_datetime_format

if TYPE_CHECKING:
    from RGBMatrixEmulator.emulation.canvas import Canvas

RACES_URL = "https://api.jolpi.ca/ergast/f1/{}/races/?format=json"

UPDATE_RATE = 4 * 60 * 60  # 4 hours between feed updates


class Config(bullpen.api.PluginConfig):
    def __init__(self, config: bullpen.api.config.MLBConfig) -> None:
        self.today = config.parse_today()
        self.scrolling_speed = config.scrolling_speed
        time_format = config.time_format
        self.time_fmt_str = "{}:%M".format(time_format)
        if time_format == TIME_FORMAT_12H:
            self.time_fmt_str += "%p"


class Data(bullpen.api.PluginData):
    def __init__(self, config: Config) -> None:
        self.today = config.today
        self.year = self.today.year

        self.starttime = time.time()
        self.next_race = None

        self.update(True)

    def update(self, force=False) -> UpdateStatus:
        if force or self.__should_update():
            try:
                races = requests.get(RACES_URL.format(self.year), timeout=10).json()["MRData"]["RaceTable"]["Races"]
                for race in races:
                    date = datetime.datetime.strptime(race["date"], "%Y-%m-%d").date()
                    if date >= self.today:
                        self.next_race = race
                        break

            except Exception as e:
                LOGGER.exception("Failed to fetch F1 data: %s", e)
                return UpdateStatus.FAIL
            return UpdateStatus.SUCCESS
        return UpdateStatus.DEFERRED

    def __should_update(self):
        endtime = time.time()
        time_delta = endtime - self.starttime
        return time_delta >= UPDATE_RATE


def decode_image(image_str):
    return Image.open(io.BytesIO(base64.b64decode(image_str)))


class Renderer(bullpen.api.PluginRenderer[Data]):
    TRACK_IMG_BASE_HEIGHT = 23
    TRACK_IMG_BASE_WIDTH = 28

    def __init__(self, config: Config, layout: bullpen.api.Layout, colors: bullpen.api.Color):

        self.scrolling_speed = config.scrolling_speed
        self.time_fmt_str = config.time_fmt_str

        self.bg = colors.graphics_color("default.background")

        self.scroll_coords = layout.coords("f1.scrolling_text")
        self.scroll_font = layout.font("f1.scrolling_text")
        self.scroll_color = colors.graphics_color("f1.scrolling_text")
        self.separator_color = colors.graphics_color("f1.separator")

        self.track_coords = layout.coords("f1.track_image")
        self.track_color = colors.color("f1.track_image")
        with files("f1_board.meta").joinpath(f"tracks.json").open(mode="rb") as f:
            tracks = json.load(f)

        self.tracks = {k: decode_image(v) for k, v in tracks.items()}

        self.date_coords = layout.coords("f1.date")
        self.date_font = layout.font("f1.date")
        self.date_color = colors.graphics_color("f1.date")

        self.time_coords = layout.coords("f1.time")
        self.time_font = layout.font("f1.time")
        self.time_color = colors.graphics_color("f1.time")

        self.race_coords = layout.coords("f1.race")
        self.race_font = layout.font("f1.race")
        self.race_color = colors.graphics_color("f1.race")

    def can_render(self, data):
        return data.next_race is not None

    def wait_time(self) -> float:
        return self.scrolling_speed

    def render(
        self, data: Data, canvas: "Canvas", graphics: bullpen.api.renderer.graphics, scrolling_text_pos: int
    ) -> int:

        canvas.Fill(self.bg.red, self.bg.green, self.bg.blue)

        next_race = data.next_race
        assert next_race is not None
        time = next_race.get("time", "TBD")
        if time != "TBD":
            time = datetime.time.fromisoformat(time).strftime(self.time_fmt_str)
        date = datetime.datetime.strptime(next_race["date"], "%Y-%m-%d").strftime(os_datetime_format("%b %-d"))
        top_text = f' {next_race["raceName"]} - {next_race["Circuit"]["Location"]["locality"]} {next_race["Circuit"]["Location"]["country"]}'
        len = scrolling_text(
            canvas,
            graphics,
            self.scroll_coords["x"],
            self.scroll_coords["y"],
            self.scroll_coords["width"],
            self.scroll_font,
            self.scroll_color,
            self.bg,
            top_text,
            scrolling_text_pos,
            force_scroll=False,
        )

        icon = self.tracks.get(next_race["Circuit"]["circuitId"].lower())
        if icon:
            for x in range(icon.width):
                for y in range(icon.height):
                    pixel = icon.getpixel((x, y))
                    canvas.SetPixel(
                        self.track_coords["x"] + x,
                        self.track_coords["y"] + y,
                        pixel[0],
                        pixel[1],
                        pixel[2],
                    )

        graphics.DrawLine(
            canvas,
            0,
            self.scroll_coords["y"] + 1,
            canvas.width,
            self.scroll_coords["y"] + 1,
            self.separator_color,
        )

        graphics.DrawText(
            canvas,
            self.date_font["font"],
            self.date_coords["x"],
            self.date_coords["y"],
            self.date_color,
            date,
        )

        graphics.DrawText(
            canvas, self.time_font["font"], self.time_coords["x"], self.time_coords["y"], self.time_color, time
        )

        graphics.DrawText(
            canvas,
            self.race_font["font"],
            self.race_coords["x"],
            self.race_coords["y"],
            self.race_color,
            f"Race {next_race['round']}",
        )

        return len


def load() -> bullpen.api.PLUGIN_DEFINITION:
    return Config, Data, Renderer
