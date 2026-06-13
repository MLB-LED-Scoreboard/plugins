# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

A [bullpen](https://github.com/MLB-LED-Scoreboard/mlb-led-scoreboard) plugin that displays Walt Disney World attraction wait times on an RGB LED matrix. It is installed alongside the MLB LED Scoreboard and registered via the `bullpen.mlbled.plugin` entry point.

## Setup

```bash
pip install -e .
```

The plugin depends on `lightninglane-live-led` (pulled from the `feature/firework` branch of the sibling repo). During local development the sibling repo lives at `../LightningLane-Live-LED`.

## Plugin architecture

The bullpen framework expects a single `load()` function (registered in `pyproject.toml` under `[project.entry-points.'bullpen.mlbled.plugin']`) that returns a `(Config, Data, Renderer)` triple. All three classes live in `src/lightninglane_plugin/__init__.py`.

| Class | Role |
|-------|------|
| `Config` | Reads plugin config keys (`park_name`, `refresh_seconds`) from `base.plugin_config` |
| `Data` | On first `update()` call, fetches the WDW park list then starts a daemon background thread (`live_data_updater`) that refreshes live wait-time data in-place on a shared list |
| `Renderer` | Cycles through `data.open_rides()` one at a time (8 s per ride); calls `initialize_fonts` once on the first render pass |

## Dependency library layout (`lightninglane-live-led`)

The display and data logic lives in the dependency, not this plugin:

- `api/disney_api.py` — synchronous park/schedule fetching + async per-attraction live data via `aiohttp`; data source is the [ThemeParks Wiki API](https://api.themeparks.wiki)
- `updater/data_updater.py` — `live_data_updater()` loop; merges new live data into the shared `parks_data` list in-place so the renderer always sees the latest state
- `display/display.py` — font loading (`initialize_fonts`) keyed by matrix height (32 or 64); color definitions
- `display/park/` and `display/attractions/` — rendering functions called by `Renderer.render()`

## Running tests (in the dependency repo)

```bash
cd ../LightningLane-Live-LED
pytest
```

## Key config options (set in bullpen's `config.json`)

```json
{
  "plugin_config": {
    "park_name": "Magic Kingdom",   // omit to show all WDW parks
    "refresh_seconds": 300
  }
}
```
