# LightningLane LED Plugin

A [bullpen](https://github.com/MLB-LED-Scoreboard/mlb-led-scoreboard) plugin for the MLB LED Scoreboard that displays live Walt Disney World attraction wait times on an RGB LED matrix.

Powered by [LightningLane-Live-LED](https://github.com/jc214809/LightningLane-Live-LED) and the [ThemeParks Wiki API](https://api.themeparks.wiki) (no API key required).

## What it displays

Each cycle through the plugin shows (8 seconds per frame):

1. **Mickey Mouse silhouette** — intro screen
2. **Trip countdown** *(if `trip_dates` is configured)* — "COUNTDOWN TO DISNEY X Days", or "Have a Magical Trip!" within 7 days after the trip
3. **For each operating WDW park:**
   - Park info screen — park name, hours, Lightning Lane Multi Pass price, and current weather
   - Each displayable attraction — ride name and standby wait time

Attractions that are CLOSED or under REFURBISHMENT are skipped. DOWN rides are shown with their downtime in red. The display updates in the background every `refresh_seconds` (default 5 minutes). When no parks have live data (e.g. overnight), the plugin yields its turn back to the scoreboard automatically.

**Supported board sizes:** 64×32 and 64×64

## Installation

**Raspberry Pi** (from your mlb-led-scoreboard directory):

```bash
sudo venv/bin/pip install git+https://github.com/jc214809/lightninglane-led-plugin.git
```

**Mac / local development** (editable install):

```bash
git clone https://github.com/jc214809/lightninglane-led-plugin.git
cd /path/to/mlb-led-scoreboard
venv/bin/pip install -e /path/to/lightninglane-led-plugin
```

## Configuration

Add a screen entry to `rotation.screens` and a `"plugins"` section to your MLB LED Scoreboard `config.json`:

```json
{
  "rotation": {
    "screens": [
      {
        "kind": "lightninglane",
        "seconds": 60,
        "with_priority": 2
      }
    ]
  },
  "plugins": {
    "lightninglane": {
      "park_name": null,
      "refresh_seconds": 300,
      "trip_dates": ["2026-12-01"]
    }
  }
}
```

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `park_name` | string \| null | `null` | Filter to a single park by name (e.g. `"Magic Kingdom"`, `"EPCOT"`, `"Hollywood Studios"`, `"Animal Kingdom"`). `null` rotates through all four WDW theme parks. |
| `refresh_seconds` | int | `300` | How often (in seconds) the background thread re-fetches live wait times. |
| `trip_dates` | list | `[]` | List of upcoming trip dates in `YYYY-MM-DD` format. Drives the countdown screen. Multiple dates are supported; the nearest upcoming date is shown. |

## How it works

The plugin registers itself via the `bullpen.mlbled.plugin` entry point. When bullpen loads it, three objects are created:

- **`Config`** — reads `park_name`, `refresh_seconds`, and `trip_dates` from `config.json`
- **`Data`** — on first update, fetches the WDW park list then starts a daemon background thread that polls live attraction wait times on the configured interval
- **`Renderer`** — runs a phase-based cycle: Mickey intro → trip countdown (if active) → parks; resumes where it left off if the scoreboard rotates away mid-cycle
