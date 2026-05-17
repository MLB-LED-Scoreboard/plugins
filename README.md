# LightningLane LED Plugin

A [bullpen](https://github.com/MLB-LED-Scoreboard/mlb-led-scoreboard) plugin for the MLB LED Scoreboard that displays live Walt Disney World attraction wait times on an RGB LED matrix.

Powered by [LightningLane-Live-LED](https://github.com/jc214809/LightningLane-Live-LED) and the [ThemeParks Wiki API](https://api.themeparks.wiki) (no API key required).

## What it displays

For each operating WDW theme park, the plugin cycles through:

1. **Park info screen** — park name, operating hours, Lightning Lane Multi Pass price, and current weather
2. **Each open attraction** — ride name and current standby wait time

Parks and attractions with no live wait time data (closed, under refurbishment, or not yet updated) are skipped automatically. The display updates in the background every `refresh_seconds` (default 5 minutes).

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
      "refresh_seconds": 300
    }
  }
}
```

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `park_name` | string \| null | `null` | Filter to a single park by name (e.g. `"Magic Kingdom"`, `"EPCOT"`, `"Hollywood Studios"`, `"Animal Kingdom"`). `null` rotates through all four WDW theme parks. |
| `refresh_seconds` | int | `300` | How often (in seconds) the background thread re-fetches live wait times. |

## How it works

The plugin registers itself via the `bullpen.mlbled.plugin` entry point. When bullpen loads it, three objects are created:

- **`Config`** — reads `park_name` and `refresh_seconds` from `config.json`
- **`Data`** — on first update, fetches the WDW park list then starts a daemon background thread that polls live attraction wait times on the configured interval
- **`Renderer`** — cycles through each operating park: park info screen first, then one attraction per frame (8 seconds each)

The plugin only renders when at least one park has live attraction data, so it yields control back to the scoreboard automatically on off-hours.
