# plugins

The official plugin registry for [mlb-led-scoreboard](https://github.com/MLB-LED-Scoreboard/mlb-led-scoreboard).

Every plugin installable into mlb-led-scoreboard lives in this repository. Each plugin is a self-contained Python package under [`plugins/`](./plugins) that registers itself with the host via the `bullpen.mlbled.plugin` entry point.

## Currently in the registry

Browse [`plugins/`](./plugins) for the current list. Each subdirectory is an installable plugin; open its `README.md` for what it does, configuration, and supported board sizes.

## Installing a plugin

From your `mlb-led-scoreboard` directory:

```bash
sudo venv/bin/pip install "git+https://github.com/MLB-LED-Scoreboard/plugins.git#subdirectory=plugins/<plugin-name>"
```

For local development, clone this repo and install the plugin directory as editable:

```bash
venv/bin/pip install -e /path/to/plugins/plugins/<plugin-name>
```

## License

This project is licensed under the **GNU General Public License v3.0** (see [LICENSE](./LICENSE)).

All plugins contributed to this registry are subject to GPL v3. By submitting a plugin you agree that your code, and any derivative works, are distributed under the same license. Do not vendor incompatibly-licensed code into a plugin directory.

## Adding a new plugin

Start from [`example-plugin/`](./example-plugin) — it's a minimal, working reference that documents the `bullpen` plugin API (Config / Data / Renderer classes and the `load()` entry point). Copy it into `plugins/<your-plugin-name>/`, rename the package, and fill in the three classes.

A new plugin should:

1. Have a top-level `pyproject.toml` that builds an installable Python package.
2. Register at least one entry point in the `bullpen.mlbled.plugin` group.
3. Ship a `README.md` covering install, configuration, and supported board sizes.
4. Be GPL v3 compatible.

### `pyproject.toml` — what good looks like

Use [PEP 621](https://peps.python.org/pep-0621/) metadata with `setuptools` as the build backend. See [`example-plugin/pyproject.toml`](./example-plugin/pyproject.toml) for the canonical minimum. A more fleshed-out plugin looks like this:

```toml
[build-system]
requires = ["setuptools>=77.0.3"]
build-backend = "setuptools.build_meta"

[project]
name = "my-cool-plugin"
version = "0.1.0"
description = "One-line summary of what the plugin shows on the board."
readme = "README.md"
requires-python = ">=3.10"
license = "GPL-3.0-or-later"
authors = [{ name = "Your Name", email = "you@example.com" }]
dependencies = [
    "requests",
    "Pillow>=10.0.1,<12.0.0",
]

[project.urls]
Homepage = "https://github.com/MLB-LED-Scoreboard/plugins/tree/main/plugins/my-cool-plugin"
Issues = "https://github.com/MLB-LED-Scoreboard/plugins/issues"

[project.entry-points."bullpen.mlbled.plugin"]
my_cool_plugin = "my_cool_plugin:load"

[tool.setuptools.packages.find]
where = ["src"]
```

### Best Practices

- **Use a `src/` layout.** Put your package under `plugins/<plugin-name>/src/<python_package>/`. This prevents accidentally importing from the working directory during tests.
- **Match the distribution name to the directory.** The `[project] name` should match the folder name under `plugins/` (kebab-case). The importable Python package should be the snake_case form.
- **Pin floors, not ceilings.** Prefer `requests>=2.31` over `requests==2.31.0`. Only cap an upper bound when you know a specific newer release breaks you (e.g. `Pillow>=10.0.1,<12.0.0`).
- **Declare `requires-python`.** mlb-led-scoreboard runs on Raspberry Pi OS; target `>=3.9` unless you have a reason to go higher.
- **Always set `license = "GPL-3.0-or-later"`** as an SPDX identifier (requires `setuptools>=77`).
- **Register entry points under `bullpen.mlbled.plugin`** — this is how the host discovers your plugin. The key is the plugin's `kind` in the user's `config.json`; the value is `module:callable`.
- **Use `[tool.setuptools.package-data]`** if you ship JSON, fonts, or images alongside the code:
  ```toml
  [tool.setuptools.package-data]
  "*" = ["*.json", "*.png"]
  ```
- **Avoid `git+https://` dependencies** when possible. If a runtime dependency only exists as a Git URL, call it out in the plugin's README so users understand what they're installing.
- **Bump `version`** in every PR that changes behavior. Follow [SemVer](https://semver.org): patch for fixes, minor for new features, major for breaking config changes.

## Contributing

**All changes are submitted via pull request against `main`.** Direct pushes to `main` are not accepted, including for plugins you own.
