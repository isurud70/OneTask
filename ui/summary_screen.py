"""
summary_screen.py — OneTask
End of day summary. Shows what was done, skipped, rescued.
Honest. No shame. Just awareness.
"""

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.animation import Animation
from kivy.clock import Clock

import core.database as db
import core.sound as sound
from core.theme import *
from ui.widgets import RoundedButton, CardWidget


class StatCard(CardWidget):
    """A small stat display card."""
    def __init__(self, emoji, value, label, color=None, **kwargs):
        super().__init__(
            orientation='vertical',
            padding=[12, 14, 12, 14],
            **kwargs
        )
        self.add_widget(Label(
            text=f"{emoji}  {value}",
            font_size=FONT_LG,
            bold=True,
            color=color or TEXT_PRIMARY,
            halign='center',
            size_hint_y=0.55
        ))
        self.add_widget(Label(
            text=label,
            font_size=FONT_XS,
            color=TEXT_SECONDARY,
            halign='center',
            size_hint_y=0.45
        ))


class SummaryScreen(Screen):
    def __init__(self, session_date, **kwargs):
        super().__init__(**kwargs)
        self.session_date = session_date
        self.root_layout = BoxLayout(
            orientation='vertical',
            padding=[PAD_LG, 40, PAD_LG, PAD_LG],
            spacing=PAD_MD
        )
        self.add_widget(self.root_layout)

    def on_enter(self):
        """Rebuild UI every time we enter — data may have changed."""
        self.root_layout.clear_widgets()  # Prevent memory leak
        self._build()

    def _build(self):
        done, skipped, rescued, total = db.get_day_summary(self.session_date)
        streak, longest = db.get_streak()

        # ── Title
        if total == 0:
            title = "No tasks today"
            title_color = TEXT_SECONDARY
        elif done == total:
            title = "PERFECT DAY! 🏆"
            title_color = GREEN
            sound.play('perfect')
        elif done > 0:
            title = "Day Complete! 📋"
            title_color = TEXT_PRIMARY
        else:
            title = "Tomorrow is a new day 💪"
            title_color = TEXT_SECONDARY

        title_lbl = Label(
            text=title,
            font_size=FONT_LG,
            bold=True,
            color=title_color,
            size_hint_y=None,
            height=52,
            halign='center'
        )
        self.root_layout.add_widget(title_lbl)

        # Animate title in
        title_lbl.opacity = 0
        Clock.schedule_once(
            lambda dt: Animation(opacity=1, duration=0.4).start(title_lbl),
            0.1
        )

        # ── Streak display
        streak_lbl = Label(
            text=f"🔥 {streak} day streak   |   Best: {longest} days",
            font_size=FONT_SM,
            color=AMBER,
            size_hint_y=None,
            height=36,
            halign='center'
        )
        self.root_layout.add_widget(streak_lbl)

        self.root_layout.add_widget(Widget(size_hint_y=None, height=8))

        # ── Stat cards row
        stat_row = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=100,
            spacing=10
        )
        stat_row.add_widget(StatCard("✅", done, "done", color=GREEN))
        stat_row.add_widget(StatCard("⏭️", skipped, "skipped", color=GRAY))
        stat_row.add_widget(StatCard("🔁", rescued, "carried over", color=AMBER))
        self.root_layout.add_widget(stat_row)

        self.root_layout.add_widget(Widget(size_hint_y=None, height=12))

        # ── Honest message
        if rescued > 0:
            msg = f"⚠️  {rescued} task(s) were skipped twice.\nCarry them to tomorrow?"
            msg_color = AMBER
        elif skipped > 0:
            msg = "Some tasks skipped — that's okay.\nTomorrow, try to do the hardest one first."
            msg_color = TEXT_SECONDARY
        elif done == total and total > 0:
            msg = "You completed everything! 🎉\nYour streak grows stronger."
            msg_color = GREEN
        else:
            msg = "Start fresh tomorrow. One task at a time."
            msg_color = TEXT_SECONDARY

        self.root_layout.add_widget(Label(
            text=msg,
            font_size=FONT_SM,
            color=msg_color,
            halign='center',
            size_hint_y=None,
            height=64
        ))

        self.root_layout.add_widget(Widget())  # flexible spacer

        # ── Plan tomorrow button
        tomorrow_btn = RoundedButton(
            text="Plan Tomorrow →",
            bg_color=BLUE,
            size_hint_y=None,
            height=BTN_PRIMARY
        )
        tomorrow_btn.bind(on_release=self._plan_tomorrow)
        self.root_layout.add_widget(tomorrow_btn)

        self.root_layout.add_widget(Widget(size_hint_y=None, height=8))

        # ── Go back to focus (if tasks still pending)
        pending = db.get_current_task(self.session_date)
        if pending:
            back_btn = RoundedButton(
                text="← Back to Tasks",
                bg_color=GRAY_DARK,
                size_hint_y=None,
                height=BTN_SECONDARY
            )
            back_btn.bind(on_release=lambda x: setattr(
                self.manager, 'current', 'focus'
            ))
            self.root_layout.add_widget(back_btn)

    def _plan_tomorrow(self, instance):
        self.manager.current = 'morning'
