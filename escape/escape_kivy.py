# Escape - Kivy Interface Layer

import os
from collections import namedtuple

# -- Config MUST come before any other kivy imports --------------------------
from kivy.config import Config

SCREEN_W = 720
SCREEN_H = 1612

# Scale the 800x800 game world to fit screen width
SCALE = SCREEN_W / 800  # ~0.9 on Moto G 5G

Config.set('graphics', 'fullscreen', '0')
Config.set('graphics', 'borderless', '1')
Config.set('graphics', 'width',  str(SCREEN_W))
Config.set('graphics', 'height', str(SCREEN_H))

# -- Kivy imports -------------------------------------------------------------
from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.clock import Clock as KivyClock
from kivy.graphics import Rectangle, Color, Line
from kivy.core.image import Image as CoreImage
from kivy.core.audio import SoundLoader
from kivy.core.window import Window


# ============================================================================
# RECT
# ============================================================================
_RectBase = namedtuple('Rect', ['x', 'y', 'width', 'height'])

class Rect(_RectBase):
    def __new__(cls, pos, size):
        return super().__new__(cls, pos[0], pos[1], size[0], size[1])


# ============================================================================
# IMAGE SHIM
# ============================================================================
_IMAGE_DIR = os.path.join(os.path.dirname(__file__), 'images')
_image_cache = {}

class _ImageProxy:
    def __init__(self, name):
        self._name = name
        self._core = None

    def _load(self):
        if self._core is None:
            path = os.path.join(_IMAGE_DIR, self._name + '.png')
            if not os.path.exists(path):
                raise FileNotFoundError(f"Image not found: {path}")
            self._core = CoreImage(path)
        return self._core

    def get_width(self):
        return self._load().width

    def get_height(self):
        return self._load().height

    @property
    def texture(self):
        return self._load().texture

    def __repr__(self):
        return f"<Image '{self._name}'>"


class _ImageNamespace:
    def __getattr__(self, name):
        if name.startswith('_'):
            raise AttributeError(name)
        if name not in _image_cache:
            _image_cache[name] = _ImageProxy(name)
        return _image_cache[name]


images = _ImageNamespace()


# ============================================================================
# SOUND SHIM
# ============================================================================
_SOUND_DIR = os.path.join(os.path.dirname(__file__), 'sounds')
_sound_cache = {}

class _SoundProxy:
    def __init__(self, name):
        self._name = name
        self._sound = None

    def _load(self):
        if self._sound is None:
            for ext in ('.wav', '.ogg', '.mp3'):
                path = os.path.join(_SOUND_DIR, self._name + ext)
                if os.path.exists(path):
                    self._sound = SoundLoader.load(path)
                    break
        return self._sound

    def play(self, loops=1):
        s = self._load()
        if s:
            s.loop = (loops > 1)
            s.play()

    def stop(self):
        s = self._load()
        if s:
            s.stop()


class _SoundNamespace:
    def __getattr__(self, name):
        if name.startswith('_'):
            raise AttributeError(name)
        if name not in _sound_cache:
            _sound_cache[name] = _SoundProxy(name)
        return _sound_cache[name]


sounds = _SoundNamespace()


# ============================================================================
# CLOCK SHIM
# ============================================================================
_scheduled = {}

class _Clock:
    def schedule_interval(self, fn, interval):
        self.unschedule(fn)
        handle = KivyClock.schedule_interval(lambda dt: fn(), interval)
        _scheduled[fn] = handle

    def schedule_unique(self, fn, delay):
        self.unschedule(fn)
        handle = KivyClock.schedule_once(lambda dt: fn(), delay)
        _scheduled[fn] = handle

    def schedule(self, fn, delay):
        self.unschedule(fn)
        handle = KivyClock.schedule_once(lambda dt: fn(), delay)
        _scheduled[fn] = handle

    def unschedule(self, fn):
        handle = _scheduled.pop(fn, None)
        if handle:
            handle.cancel()


clock = _Clock()


# ============================================================================
# KEYBOARD SHIM
# ============================================================================
class _Keyboard:
    def __init__(self):
        self._held = set()
        Window.bind(on_key_down=self._on_down, on_key_up=self._on_up)

    def _on_down(self, window, key, scancode, codepoint, modifier):
        self._held.add(codepoint)

    def _on_up(self, window, key, scancode, codepoint, modifier):
        self._held.discard(codepoint)

    def __getattr__(self, name):
        arrow_map = {'left': 'left', 'right': 'right', 'up': 'up', 'down': 'down'}
        if name in arrow_map:
            return arrow_map[name] in self._held
        return name in self._held


keyboard = _Keyboard()


# ============================================================================
# SCREEN SHIM
# ============================================================================
_draw_queue = []
_clip_rect  = None

class _DrawHelper:
    def filled_rect(self, rect, color):
        _draw_queue.append(('filled_rect', rect, color))

    def rect(self, rect, color):
        _draw_queue.append(('rect', rect, color))

    def text(self, text, pos, color='white', fontsize=20, **kwargs):
        _draw_queue.append(('text', text, pos, color, fontsize))


class _Screen:
    draw = _DrawHelper()

    def blit(self, image, pos):
        _draw_queue.append(('blit', image, pos))

    class _Surface:
        def set_clip(self, rect):
            global _clip_rect
            _clip_rect = rect

    surface = _Surface()


screen = _Screen()


# ============================================================================
# TOUCH BUTTONS
# ============================================================================
def _make_hold_button(label_text, key, layout, pos_hint, size_hint):
    btn = Button(
        text=label_text,
        pos_hint=pos_hint,
        size_hint=size_hint,
        background_color=(0.2, 0.2, 0.2, 0.7),
        font_size='18sp'
    )
    btn.bind(on_press=lambda b: keyboard._held.add(key))
    btn.bind(on_release=lambda b: keyboard._held.discard(key))
    layout.add_widget(btn)
    return btn


# ============================================================================
# COLOR HELPER
# ============================================================================
def _color_norm(color):
    if isinstance(color, str):
        named = {
            'white':  (1, 1, 1, 1), 'black':  (0, 0, 0, 1),
            'red':    (1, 0, 0, 1), 'green':  (0, 1, 0, 1),
            'blue':   (0, 0, 1, 1), 'yellow': (1, 1, 0, 1),
        }
        return named.get(color.lower(), (1, 1, 1, 1))
    if len(color) == 3:
        return (color[0]/255, color[1]/255, color[2]/255, 1.0)
    return (color[0]/255, color[1]/255, color[2]/255, color[3]/255)


# ============================================================================
# GAME WIDGET
# ============================================================================
_WINDOW_H = SCREEN_H

class GameWidget(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._game_ready = False
        self._game_module = None
        KivyClock.schedule_once(self._start_game, 0.1)

    def _start_game(self, dt):
        import builtins
        builtins.images   = images
        builtins.sounds   = sounds
        builtins.clock    = clock
        builtins.keyboard = keyboard
        builtins.screen   = screen
        builtins.Rect     = Rect

        # Patch time.sleep BEFORE importing escape_game so any sleep calls
        # during import are already neutered (fix 5).
        import time as _t
        _t.sleep = lambda s: None

        import escape_game
        self._game_module = escape_game

        # Fix 4: module-level clock calls removed from escape_game.py;
        # call start_game() here once Kivy event loop is fully running.
        escape_game.start_game()

        self._game_ready = True

    def _flush_draw_queue(self):
        global _draw_queue, _clip_rect
        S = SCALE

        with self.canvas:
            self.canvas.clear()
            for cmd in _draw_queue:

                if cmd[0] == 'filled_rect':
                    _, rect, color = cmd
                    Color(*_color_norm(color))
                    ky = _WINDOW_H - (rect.y * S) - (rect.height * S)
                    Rectangle(pos=(rect.x * S, ky),
                              size=(rect.width * S, rect.height * S))

                elif cmd[0] == 'rect':
                    _, rect, color = cmd
                    Color(*_color_norm(color))
                    ky = _WINDOW_H - (rect.y * S) - (rect.height * S)
                    Line(rectangle=(rect.x * S, ky,
                                    rect.width * S, rect.height * S), width=1.5)

                elif cmd[0] == 'blit':
                    _, image, pos = cmd
                    x, py = pos
                    w = image.get_width()  * S
                    h = image.get_height() * S
                    ky = _WINDOW_H - (py * S) - h
                    Color(1, 1, 1, 1)
                    Rectangle(texture=image.texture,
                              pos=(x * S, ky), size=(w, h))

                elif cmd[0] == 'text':
                    _, text, pos, color, fontsize = cmd
                    lbl = Label(text=str(text),
                                font_size=f'{int(fontsize * S)}sp',
                                color=_color_norm(color))
                    lbl.texture_update()
                    if lbl.texture:
                        tw, th = lbl.texture.size
                        ky = _WINDOW_H - (pos[1] * S) - th
                        Color(1, 1, 1, 1)
                        Rectangle(texture=lbl.texture,
                                  pos=(pos[0] * S, ky), size=(tw, th))

        _draw_queue = []

    def update(self, dt):
        if not self._game_ready:
            return
        draw_fn = getattr(self._game_module, 'draw', None)
        if draw_fn:
            draw_fn()
        self._flush_draw_queue()


# ============================================================================
# APP
# ============================================================================
class EscapeApp(App):
    def build(self):
        # Force window to full screen size
        Window.clearcolor = (0, 0, 0, 1)
        Window.size = (SCREEN_W, SCREEN_H)
        Window.left = 0
        Window.top  = 0

        root = FloatLayout()

        self.game_widget = GameWidget(
            size=(SCREEN_W, SCREEN_H),
            pos=(0, 0),
            size_hint=(1, 1)
        )
        root.add_widget(self.game_widget)

        # D-Pad (bottom-left)
        dpad_size   = (0.08, 0.07)
        dpad_left   = 0.01
        dpad_bottom = 0.01

        _make_hold_button('▲', 'up',    root,
            {'x': dpad_left + 0.085, 'y': dpad_bottom + 0.13}, dpad_size)
        _make_hold_button('▼', 'down',  root,
            {'x': dpad_left + 0.085, 'y': dpad_bottom},        dpad_size)
        _make_hold_button('◀', 'left',  root,
            {'x': dpad_left,         'y': dpad_bottom + 0.065}, dpad_size)
        _make_hold_button('▶', 'right', root,
            {'x': dpad_left + 0.17,  'y': dpad_bottom + 0.065}, dpad_size)

        # Action buttons (bottom-right)
        asize = (0.1, 0.065)
        ax    = 0.76
        _make_hold_button('Pick up\n[G]',   'g',  root, {'x': ax,      'y': 0.17}, asize)
        _make_hold_button('Use\n[U]',       'u',  root, {'x': ax,      'y': 0.10}, asize)
        _make_hold_button('Examine\n[SPC]', ' ',  root, {'x': ax,      'y': 0.03}, asize)
        _make_hold_button('Drop\n[D]',      'd',  root, {'x': ax+0.11, 'y': 0.10}, asize)
        _make_hold_button('Item\n[TAB]',    '\t', root, {'x': ax+0.11, 'y': 0.03}, asize)

        KivyClock.schedule_interval(self.game_widget.update, 1/33)

        return root


if __name__ == '__main__':
    EscapeApp().run()
