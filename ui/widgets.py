"""
widgets.py — OneTask
Reusable custom widgets with animations.
All UI components live here — screens just assemble them.
"""

from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.widget import Widget
from kivy.animation import Animation
from kivy.graphics import Color, RoundedRectangle, Rectangle
from kivy.clock import Clock
from core.theme import *


class RoundedButton(Button):
    """
    A button with rounded corners, custom colors,
    and a satisfying press animation.
    """
    def __init__(self, bg_color=GREEN, **kwargs):
        super().__init__(**kwargs)
        self.bg_color = bg_color
        self.background_color = (0, 0, 0, 0)  # Hide default
        self.background_normal = ''
        self.color = TEXT_PRIMARY
        self.bold = True
        self.font_size = FONT_MD
        self._draw_bg()
        self.bind(pos=self._draw_bg, size=self._draw_bg)

    def _draw_bg(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*self.bg_color)
            RoundedRectangle(
                pos=self.pos,
                size=self.size,
                radius=[14]
            )

    def on_press(self):
        # Shrink animation on press
        anim = Animation(size=(self.width * 0.95, self.height * 0.92),
                         duration=0.07)
        anim.start(self)

    def on_release(self):
        # Spring back
        anim = Animation(size=(self.width / 0.95, self.height / 0.92),
                         duration=0.12,
                         t='out_elastic')
        anim.start(self)


class CardWidget(BoxLayout):
    """A rounded card container."""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(pos=self._draw, size=self._draw)

    def _draw(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*BG_CARD)
            RoundedRectangle(
                pos=self.pos,
                size=self.size,
                radius=[16]
            )


class StreakBadge(BoxLayout):
    """Animated streak counter badge."""
    def __init__(self, streak=0, **kwargs):
        super().__init__(
            orientation='horizontal',
            size_hint_y=None,
            height=44,
            spacing=8,
            padding=[12, 6, 12, 6],
            **kwargs
        )
        self._draw_bg()
        self.bind(pos=self._draw_bg, size=self._draw_bg)

        self.fire_label = Label(
            text='🔥',
            font_size='22sp',
            size_hint_x=None,
            width=30
        )
        self.streak_label = Label(
            text=f'{streak} day streak',
            font_size=FONT_SM,
            color=AMBER,
            bold=True
        )
        self.add_widget(self.fire_label)
        self.add_widget(self.streak_label)

    def _draw_bg(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(0.18, 0.14, 0.05, 1)
            RoundedRectangle(
                pos=self.pos,
                size=self.size,
                radius=[22]
            )

    def update(self, streak):
        self.streak_label.text = f'{streak} day streak'
        # Pulse animation
        anim = (Animation(font_size='26sp', duration=0.15) +
                Animation(font_size='22sp', duration=0.15))
        anim.start(self.fire_label)


class TaskCard(CardWidget):
    """The big centered task display card."""
    def __init__(self, task_title='', **kwargs):
        super().__init__(
            orientation='vertical',
            padding=PAD_LG,
            spacing=12,
            **kwargs
        )
        self.focus_lbl = Label(
            text='FOCUS ON THIS NOW',
            font_size=FONT_XS,
            color=TEXT_SECONDARY,
            size_hint_y=None,
            height=24,
            halign='center',
            letter_spacing='3sp'
        )
        self.task_lbl = Label(
            text=task_title,
            font_size=FONT_LG,
            color=TEXT_PRIMARY,
            bold=True,
            halign='center',
            valign='middle'
        )
        self.task_lbl.bind(size=self.task_lbl.setter('text_size'))
        self.add_widget(self.focus_lbl)
        self.add_widget(self.task_lbl)

    def set_task(self, title):
        # Fade out, change text, fade in
        anim_out = Animation(opacity=0, duration=0.15)
        def _set_and_fadein(dt):
            self.task_lbl.text = title
            Animation(opacity=1, duration=0.2).start(self.task_lbl)
        anim_out.bind(on_complete=lambda *a: Clock.schedule_once(_set_and_fadein, 0))
        anim_out.start(self.task_lbl)


class ProgressBar(Widget):
    """Simple animated progress bar."""
    def __init__(self, value=0, max_value=3, **kwargs):
        super().__init__(size_hint_y=None, height=8, **kwargs)
        self.value = value
        self.max_value = max_value
        self.bind(pos=self._draw, size=self._draw)

    def _draw(self, *args):
        self.canvas.clear()
        with self.canvas:
            # Background track
            Color(*GRAY_DARK)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[4])
            # Fill
            if self.max_value > 0:
                ratio = self.value / self.max_value
                fill_w = self.width * ratio
                if fill_w > 0:
                    Color(*GREEN)
                    RoundedRectangle(
                        pos=self.pos,
                        size=(fill_w, self.height),
                        radius=[4]
                    )

    def set_progress(self, value, max_value):
        self.value = value
        self.max_value = max_value
        self._draw()


class Spacer(Widget):
    """Flexible empty space widget."""
    pass
