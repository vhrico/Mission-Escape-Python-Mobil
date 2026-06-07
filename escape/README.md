# Escape — A Python Adventure

**Original game by Sean McManus** ([sean.co.uk](http://www.sean.co.uk))
**Art by Rafael Pimenta**
**Kivy port and fixes by Vic**

---

## What is this?

Escape is a top-down tile-based adventure game set aboard a space station on a distant planet. You play as an astronaut whose suit has been breached. Air is leaking. You have a limited time to explore the station, collect and combine items, solve puzzles, and radio for rescue before you run out of air — or energy — and the mission fails.

The game was originally written for **Pygame Zero**. This repository contains a full **Kivy port** (`escape_kivy.py`) that allows it to run on Android and other mobile platforms, along with a set of bug fixes applied to both files.

---

## Files

| File | Purpose |
|---|---|
| `escape_game.py` | Core game logic — map, objects, player, hazards, interactions |
| `escape_kivy.py` | Kivy interface layer — shims for images, sounds, clock, keyboard, screen drawing |

---

## Setup

### Requirements

- Python 3.8+
- Kivy 2.x (`pip install kivy`)

### Running

```bash
python escape_kivy.py
```

`escape_kivy.py` is the entry point. It sets up the Kivy window and imports `escape_game.py` at the right moment in the app lifecycle.

### Customise your character names

Open `escape_game.py` and edit the top three variables:

```python
PLAYER_NAME  = "Sean"   # your name
FRIEND1_NAME = "Karen"  # a friend's name
FRIEND2_NAME = "Leo"    # another friend's name
```

These names appear in room labels, locked doors, and item descriptions throughout the game.

---

## Gameplay

### Objective

Your spacesuit is leaking air. You start in **Room 31 — The Airlock Entry Bay**. You need to:

1. Find and repair your suit
2. Locate the crashed **Poodle lander** on the planet surface to retrieve its radio
3. Assemble a working communications system
4. Radio for rescue from **Main Mission Control**

Do all of this before your **AIR** or **ENERGY** bars hit zero.

### The Map

The station has **50 rooms** arranged on a 5×10 grid, plus a 5×5 grid of outdoor planet surface sectors (rooms 1–25). Indoor rooms include labs, corridors, sleeping quarters, a greenhouse, a bathroom, an engineering bay, and Mission Control. The planet surface contains the crash site of the Poodle lander, randomised each game.

### HUD

At the bottom of the screen:

- **AIR** (blue bar) — drains over time. Reaches zero = game over.
- **ENERGY** (yellow bar) — depleted by hazards and toxic floors. Reaches zero = game over.

### Controls

**Keyboard**

| Key | Action |
|---|---|
| Arrow keys | Move |
| G | Pick up object |
| D | Drop carried item |
| U | Use carried item |
| Space | Examine object in front |
| Tab | Cycle through inventory |

**On-screen touch buttons** (mobile)

A D-pad is shown at the bottom-left. Action buttons (Pick up, Use, Examine, Drop, Item) are at the bottom-right.

### Items and Crafting

Many items can be **combined** to create new ones. Carry one item and `Use` it near another to attempt a combination. For example: filling a bin with water, threading a needle, sharpening scissors on a rock. The game has 11 crafting recipes in total — experimenting is part of the puzzle.

Carriable items include tools, access cards, food, and components for the communications system.

### Hazards

Several rooms contain moving hazards — drones, energy balls — that bounce around and deplete your energy on contact. They cannot leave their rooms.

### Doors and Access

Many doors require access cards belonging to specific crew members, or need to be opened remotely from Mission Control. The airlock has a two-person pressure sensor. An engineering door has a 60-second time lock. Plan your route.

---

## Kivy Port — Technical Notes

### Architecture

`escape_kivy.py` provides shim objects that mirror the Pygame Zero API:

- `images` — lazy-loading image proxy, reads PNGs from `./images/`
- `sounds` — lazy-loading sound proxy, reads `.wav`/`.ogg`/`.mp3` from `./sounds/`
- `clock` — wraps Kivy's `Clock` to match Pygame Zero's `schedule_interval` / `schedule_unique` / `schedule` / `unschedule`
- `keyboard` — wraps Kivy window key events
- `screen` — queues draw calls, flushed each frame by `GameWidget`
- `Rect` — namedtuple matching Pygame Zero's `Rect(pos, size)` signature

All shims are injected into `builtins` before `escape_game` is imported, so the game code uses them without any `import` statements.

### Screen Size

The window is hardcoded to **720×1612** (`SCREEN_W` / `SCREEN_H` in `escape_kivy.py`). This matches the Moto G 5G display. Kivy's `Window.size` cannot be reliably read before the app is running on this device, so the values are not read dynamically — they are set directly via `Config` before any Kivy imports.

The game world (800×800 logical pixels) is scaled to fit the screen width using `SCALE = SCREEN_W / 800` (~0.9).

---

## Bug Fixes Applied

The following bugs were identified in the original Pygame Zero → Kivy conversion and fixed in this version.

---

### Fix 1 — `schedule()` leaked old Kivy handles *(escape_kivy.py)*

**Problem:** `_Clock.schedule()` stored a new handle into `_scheduled[fn]` without cancelling the previous one. If the same function was scheduled twice, the old Kivy handle was silently orphaned and could never be cancelled.

**Fix:** Added `self.unschedule(fn)` at the top of `schedule()`, consistent with `schedule_interval()` and `schedule_unique()`.

```python
# Before
def schedule(self, fn, delay):
    handle = KivyClock.schedule_once(lambda dt: fn(), delay)
    _scheduled[fn] = handle

# After
def schedule(self, fn, delay):
    self.unschedule(fn)                                      # cancel any prior handle
    handle = KivyClock.schedule_once(lambda dt: fn(), delay)
    _scheduled[fn] = handle
```

---

### Fix 2 — Arrow keys never detected *(escape_kivy.py)*

**Problem:** Kivy passes `codepoint=None` for special keys including all four arrow keys. The original `_Keyboard` class stored keys using `codepoint`, so arrow presses were silently discarded. Player movement via keyboard was completely broken.

**Fix:** Arrow keys are now tracked separately by their Kivy numeric key codes (273=up, 274=down, 275=right, 276=left) in a second set `_held_arrows`. `__getattr__` checks this set for direction names.

```python
_ARROW_KEYCODES = {273: 'up', 274: 'down', 275: 'right', 276: 'left'}

class _Keyboard:
    def __init__(self):
        self._held = set()          # printable characters
        self._held_arrows = set()   # arrow directions
        Window.bind(on_key_down=self._on_down, on_key_up=self._on_up)

    def _on_down(self, window, key, scancode, codepoint, modifier):
        if key in _ARROW_KEYCODES:
            self._held_arrows.add(_ARROW_KEYCODES[key])
        elif codepoint is not None:
            self._held.add(codepoint)

    def __getattr__(self, name):
        if name in ('left', 'right', 'up', 'down'):
            return name in self._held_arrows
        return name in self._held
```

---

### Fix 3 — Module-level clock calls fired before Kivy event loop was ready *(escape_game.py + escape_kivy.py)*

**Problem:** The `## START ##` block at the bottom of `escape_game.py` ran at **import time** — calling `clock.schedule_interval()`, `clock.schedule_unique()`, and `sounds.mission.play()` directly. These calls happen inside `_start_game()`, which is deferred via `KivyClock.schedule_once(..., 0.1)`. While the delay usually works, it is not guaranteed that the Kivy event loop is fully initialised at that point, risking silent scheduling failures.

**Fix:** The `## START ##` block is wrapped in a `def start_game():` function in `escape_game.py`. `escape_kivy.py` calls `escape_game.start_game()` explicitly after the import completes, at which point the event loop is guaranteed to be running.

```python
# escape_game.py — was bare module-level code, now:
def start_game():
    global DEMO_OBJECTS
    DEMO_OBJECTS = [images.floor, images.pillar, images.soil]  # see Fix 5
    generate_map()
    clock.schedule_interval(game_loop, 0.03)
    clock.schedule_interval(adjust_wall_transparency, 0.05)
    clock.schedule_unique(display_inventory, 1)
    clock.schedule_unique(draw_energy_air, 0.5)
    clock.schedule_unique(alarm, 10)
    clock.schedule_interval(air_countdown, 5)
    sounds.mission.play()

# escape_kivy.py — _start_game() now calls it explicitly:
import escape_game
self._game_module = escape_game
escape_game.start_game()
self._game_ready = True
```

---

### Fix 4 — `time.sleep` patched after import, too late *(escape_kivy.py)*

**Problem:** `escape_kivy.py` patched `time.sleep` to a no-op *after* `import escape_game`. Any `time.sleep()` call that executes during the import (e.g. at module level) would block the Kivy main thread before the patch was applied.

**Fix:** The patch is applied *before* `import escape_game`.

```python
# After
import time as _t
_t.sleep = lambda s: None   # patch FIRST

import escape_game           # now safe to import
```

---

### Fix 5 — `DEMO_OBJECTS` used `images` before the shim was injected *(escape_game.py)*

**Problem:** At module level, `escape_game.py` had:

```python
DEMO_OBJECTS = [images.floor, images.pillar, images.soil]
```

The `images` shim is injected into `builtins` by `_start_game()` just before `import escape_game`. This works only because of exact execution order — the injection lines run before the import line. Any future refactor that reorders those lines would cause a silent `NameError` at import time.

**Fix:** `DEMO_OBJECTS` is initialised to an empty list at module level and populated inside `start_game()` after the shim is guaranteed to be available.

```python
# Module level — safe, no dependency on shims
DEMO_OBJECTS = []  # populated in start_game() after images shim is injected

# Inside start_game() — shim is guaranteed present
global DEMO_OBJECTS
DEMO_OBJECTS = [images.floor, images.pillar, images.soil]
```

---

## Known Remaining Issues

- **Window height hardcoded** — `_WINDOW_H = SCREEN_H` in `escape_kivy.py` is used for Y-axis coordinate flipping. If the device renders at a different height, drawing will be misaligned. This is intentional for the Moto G 5G target device.
- **`time.sleep` in `game_loop`** — the original code calls `time.sleep(0.05)` during player animation. This is patched to a no-op; the intended per-step delay is replaced by the 30ms `game_loop` interval. Animation plays slightly differently from the Pygame Zero original but does not block the UI.
- **Debug `print()` statements** — checksum verification prints fire on every game load. These are harmless but can be removed or gated behind a `DEBUG` flag for a release build.
