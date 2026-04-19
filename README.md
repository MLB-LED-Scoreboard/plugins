# f1-board

Show the upcoming race.

A plugin for [mlb-led-scoreboard](https://github.com/WardBrian/mlb-led-scoreboard).

Based on the [tronbyt plugin](https://github.com/tronbyt/apps/tree/main/apps/formula1)


## Example config

`colors/scoreboard.json`:
```json
{
  "plugins" : {
    "f1": {
      "scrolling_text": {
        "r": 255,
        "g": 255,
        "b": 255
      },
      "separator": {
        "r": 220,
        "g": 84,
        "b": 231
      },
      "track_image": {
        "r": 255,
        "g": 255,
        "b": 255
      },
      "date": {
        "r": 255,
        "g": 255,
        "b": 255
      },
      "time": {
        "r": 255,
        "g": 255,
        "b": 255
      },
      "race": {
        "r": 255,
        "g": 255,
        "b": 255
      }
    }
  }
}
```

`coordinates/w64h32.json`:

```json
{
  "plugins": {
    "f1": {
      "scrolling_text": {
        "x": 0,
        "y": 7,
        "width": 64,
        "font_name": "5x8"
      },
      "track_image": {
        "x": 0,
        "y": 8
      },
      "date": {
        "x": 32,
        "y": 16,
        "font_name": "5x8"
      },
      "time": {
        "x": 32,
        "y": 23
      },
      "race": {
        "x": 32,
        "y": 30
      }
    }
  }
}
```
