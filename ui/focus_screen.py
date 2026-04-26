"""
focus_screen.py — OneTask
The main screen. Shows ONE task. Big. Clear. Nothing else.
"""

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.widget import Widget
from kivy.animation import Animation
from kivy.clock import Clock
from kivy.graphics import Color, Ellipse, RoundedRectangle
import random

import core.database as db
import core.sound as sound
from core.theme import *
from ui.widgets import (
    RoundedButton, StreakBadge, TaskCard, ProgressBar, CardWidget
)


class CelebrationParticle(Widget):
    """A single colored particle for the completion animation."""
    pass


class FocusScreen(Screen):
    def __init__(self, session_date, **kwargs):
        super().__init__(**kwargs)
        self.session_date = session_date
        self.current_task = None
        self._build()

    def _build(self):
        self.root_layout = BoxLayout(
            orientation='vertical',
            padding=[PAD_LG, 36, PAD_LG, PAD_LG],
            spacing=PAD_MD
        )

        # ── Top row: streak badge + progress
        top_row = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=48,
            spacing=12
        )
        self.streak_badge = StreakBadge(streak=0)
        self.streak_badge.size_hint_x = 0.55

        self.progress_label = Label(
            text='0 / 0 done',
            font_size=FONT_XS,
            color=TEXT_SECONDARY,
            halign='right'
        )
        top_row.add_widget(self.streak_badge)
        top_row.add_widget(self.progress_label)
        self.root_layout.add_widget(top_row)

        # ── Progress bar
        self.progress_bar = ProgressBar(value=0, max_value=3)
        self.root_layout.add_widget(self.progress_bar)

        self.root_layout.add_widget(Widget(size_hint_y=None, height=12))

        # ── Task card (main focus area)
        self.task_card = TaskCard(
            task_title='Loading...',
            size_hint_y=0.38
        )
        self.root_layout.add_widget(self.task_card)

        self.root_layout.add_widget(Widget(size_hint_y=None, height=20))

        # ── Done button
        self.done_btn = RoundedButton(
            text="✅   Done!",
            bg_color=GREEN,
            size_hint_y=None,
            height=BTN_PRIMARY,
            font_size=FONT_MD
        )
        self.done_btn.bind(on_release=self._on_done)
        self.root_layout.add_widget(self.done_btn)

        self.root_layout.add_widget(Widget(size_hint_y=None, height=8))

        # ── Skip button
        self.skip_btn = RoundedButton(
            text="⏭   Skip for now",
            bg_color=GRAY_DARK,
            size_hint_y=None,
            height=BTN_SECONDARY,
            font_size=FONT_SM
        )
        self.skip_btn.bind(on_release=self._on_skip)
        self.root_layout.add_widget(self.skip_btn)

        # ── Body double toggle
        self.root_layout.add_widget(Widget())  # flexible spacer

        body_row = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=36,
            spacing=10
        )
        self.body_double_label = Label(
            text="🎧 Body double mode: OFF",
            font_size=FONT_XS,
            color=TEXT_HINT,
            halign='left'
        )
        body_btn = RoundedButton(
            text="Toggle",
            bg_color=GRAY_DARK,
            size_hint_x=None,
            width=80,
            height=32,
            font_size=FONT_XS
        )
        body_btn.bind(on_release=self._toggle_body_double)
        body_row.add_widget(self.body_double_label)
        body_row.add_widget(body_btn)
        self.root_layout.add_widget(body_row)

        self.add_widget(self.root_layout)

        # Body double state
        self._body_double_on = False
        self._tick_event = None

    def on_enter(self):
        """Called every time this screen becomes active."""
        self._refresh()

    def _refresh(self):
        """Load current task and update all UI elements."""
        streak, longest = db.get_streak()
        self.streak_badge.update(streak)

        done, skipped, rescued, total = db.get_day_summary(self.session_date)
        finished = done + skipped + rescued
        self.progress_label.text = f'{done} / {total} done'
        self.progress_bar.set_progress(done, total)

        task = db.get_current_task(self.session_date)

        if task:
            self.current_task = task
            self.task_card.set_task(task['title'])
            self.done_btn.disabled = False
            self.skip_btn.disabled = False
        else:
            # No more pending tasks — go to summary
            Clock.schedule_once(lambda dt: setattr(
                self.manager, 'current', 'summary'
            ), 0.3)

    def _on_done(self, instance):
        if not self.current_task:
            return

        self.done_btn.disabled = True
        db.complete_task(self.current_task['id'])
        new_streak = db.try_update_streak(self.session_date)
        sound.play('complete')
        self._show_dopamine_popup(new_streak)

    def _on_skip(self, instance):
        if not self.current_task:
            return

        sound.play('skip')
        db.skip_task(self.current_task['id'])

        # Brief skip animation on card
        anim = (
            Animation(opacity=0.4, duration=0.1) +
            Animation(opacity=1.0, duration=0.15)
        )
        anim.bind(on_complete=lambda *a: self._refresh())
        anim.start(self.task_card)

    def _show_dopamine_popup(self, streak):
        messages = [
            ("CRUSHED IT! 💥", f"🔥 {streak} day streak!"),
            ("NAILED IT! 🎯",  f"🔥 {streak} days strong!"),
            ("YOU GOT IT! ⚡",  f"Keep going! {streak} days!"),
            ("DONE! 🏆",        f"🔥 Streak: {streak} days"),
        ]
        title_text, sub_text = random.choice(messages)

        content = BoxLayout(
            orientation='vertical',
            padding=24,
            spacing=16
        )

        title_lbl = Label(
            text=title_text,
            font_size='28sp',
            bold=True,
            color=GREEN,
            size_hint_y=0.45,
            halign='center'
        )
        sub_lbl = Label(
            text=sub_text,
            font_size=FONT_MD,
            color=AMBER,
            size_hint_y=0.25,
            halign='center'
        )
        next_btn = RoundedButton(
            text="Next Task →",
            bg_color=GREEN,
            size_hint_y=None,
            height=BTN_PRIMARY
        )

        content.add_widget(title_lbl)
        content.add_widget(sub_lbl)
        content.add_widget(next_btn)

        popup = Popup(
            title='',
            content=content,
            size_hint=(0.82, 0.42),
            background_color=list(BG_CARD) + [1],
            separator_height=0,
            auto_dismiss=False
        )

        def _next(instance):
            popup.dismiss()
            self._refresh()

        next_btn.bind(on_release=_next)

        # Animate popup entrance
        content.opacity = 0
        popup.open()
        Animation(opacity=1, duration=0.2).start(content)

        # Bounce the title
        Clock.schedule_once(lambda dt: (
            Animation(font_size='32sp', duration=0.12) +
            Animation(font_size='28sp', duration=0.12, t='out_bounce')
        ).start(title_lbl), 0.1)

    def _toggle_body_double(self, instance):
        self._body_double_on = not self._body_double_on

        if self._body_double_on:
            self.body_double_label.text = "🎧 Body double mode: ON"
            self.body_double_label.color = GREEN
            # Play a soft tick every 25 seconds
            self._tick_event = Clock.schedule_interval(
                lambda dt: sound.play('tick'), 25
            )
        else:
            self.body_double_label.text = "🎧 Body double mode: OFF"
            self.body_double_label.color = TEXT_HINT
            if self._tick_event:
                self._tick_event.cancel()
                self._tick_event = None

    def on_leave(self):
        """Stop body double ticking when leaving this screen."""
        if self._tick_event:
            self._tick_event.cancel()
            self._tick_event = None
