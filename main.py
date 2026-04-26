"""
main.py — OneTask
Entry point. Sets up everything and decides which screen to show first.
"""

import os

# Silence Kivy's noisy startup logs before importing anything
os.environ['KIVY_NO_ENV_CONFIG'] = '1'
os.environ.setdefault('KIVY_LOG_LEVEL', 'warning')

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, FadeTransition
from kivy.core.window import Window
from kivy.clock import Clock

# Local imports
import core.database as db
import core.sound as sound
from core.theme import BG_DARK
from ui.morning_screen import MorningScreen
from ui.focus_screen import FocusScreen
from ui.summary_screen import SummaryScreen


class OneTaskApp(App):

    def build(self):
        # ── Window setup (phone size for desktop testing)
        Window.size = (390, 844)  # iPhone 14 proportions — good proxy
        Window.clearcolor = BG_DARK

        # ── Initialize subsystems
        db.init_db()
        db.reset_streak_if_missed()   # Fix streak if user missed a day
        sound.init_sounds()           # Load audio (gracefully fails if unavailable)

        # ── Get session date (safe, clock-independent)
        self.session_date = db.get_session_date()

        # ── Build screen manager
        sm = ScreenManager(transition=FadeTransition(duration=0.2))
        sm.add_widget(MorningScreen(name='morning', session_date=self.session_date))
        sm.add_widget(FocusScreen(name='focus',    session_date=self.session_date))
        sm.add_widget(SummaryScreen(name='summary', session_date=self.session_date))

        # ── Decide starting screen intelligently
        tasks = db.get_today_tasks(self.session_date)

        if not tasks:
            # First open of the day — plan tasks
            sm.current = 'morning'
        else:
            pending = db.get_current_task(self.session_date)
            if pending:
                # Resume where user left off
                sm.current = 'focus'
            else:
                # All done or all skipped
                sm.current = 'summary'

        return sm

    def on_pause(self):
        """Android: app goes to background. Return True to keep alive."""
        return True

    def on_resume(self):
        """Android: app comes back from background."""
        # Refresh session date in case day changed while backgrounded
        new_date = db.get_session_date()
        if new_date != self.session_date:
            # Day changed — restart cleanly
            self.session_date = new_date
            self.root.current = 'morning'


if __name__ == '__main__':
    OneTaskApp().run()
