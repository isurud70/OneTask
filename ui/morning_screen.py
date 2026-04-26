"""
morning_screen.py — OneTask
Where the user adds up to 3 tasks for the day.
"""

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget
from kivy.graphics import Color, RoundedRectangle
from kivy.animation import Animation
from kivy.clock import Clock
from datetime import datetime
from core.theme import *
from ui.widgets import RoundedButton, CardWidget


class TaskInput(BoxLayout):
    """Styled task input field with number badge."""
    def __init__(self, number, hint, **kwargs):
        super().__init__(
            orientation='horizontal',
            size_hint_y=None,
            height=56,
            spacing=10,
            **kwargs
        )
        # Number badge
        badge = Label(
            text=str(number),
            font_size=FONT_SM,
            bold=True,
            color=TEXT_SECONDARY,
            size_hint=(None, 1),
            width=28
        )
        self.add_widget(badge)

        # Input field
        self.input = TextInput(
            hint_text=hint,
            hint_text_color=list(TEXT_HINT),
            foreground_color=list(TEXT_PRIMARY),
            background_color=list(BG_INPUT),
            cursor_color=list(GREEN),
            multiline=False,
            font_size=FONT_SM,
            padding=[14, 16, 14, 16]
        )
        self.add_widget(self.input)

    @property
    def text(self):
        return self.input.text.strip()


class MorningScreen(Screen):
    def __init__(self, session_date, **kwargs):
        super().__init__(**kwargs)
        self.session_date = session_date
        self.task_inputs = []
        self._build()

    def _build(self):
        # Root layout
        root = BoxLayout(
            orientation='vertical',
            padding=[PAD_LG, 40, PAD_LG, PAD_LG],
            spacing=PAD_MD
        )

        # Greeting
        hour = datetime.now().hour
        if hour < 12:
            greet = "Good morning! 🌤️"
        elif hour < 18:
            greet = "Good afternoon! ☀️"
        else:
            greet = "Good evening! 🌙"

        root.add_widget(Label(
            text=greet,
            font_size=FONT_LG,
            bold=True,
            color=TEXT_PRIMARY,
            size_hint_y=None,
            height=44,
            halign='left'
        ))

        root.add_widget(Label(
            text="What are your 3 tasks today?\nMax 3. Choose wisely.",
            font_size=FONT_SM,
            color=TEXT_SECONDARY,
            size_hint_y=None,
            height=48,
            halign='left',
            valign='top'
        ))

        root.add_widget(Widget(size_hint_y=None, height=8))

        # Task input fields
        hints = [
            "Most important task...",
            "Second task...",
            "Third task (optional)..."
        ]
        for i, hint in enumerate(hints):
            inp = TaskInput(number=i + 1, hint=hint)
            self.task_inputs.append(inp)
            root.add_widget(inp)

        root.add_widget(Widget(size_hint_y=None, height=16))

        # Error message label
        self.error_label = Label(
            text='',
            font_size=FONT_XS,
            color=(0.9, 0.35, 0.35, 1),
            size_hint_y=None,
            height=24,
            halign='center'
        )
        root.add_widget(self.error_label)

        # Start button
        start_btn = RoundedButton(
            text="Start My Day  ✅",
            bg_color=GREEN,
            size_hint_y=None,
            height=BTN_PRIMARY
        )
        start_btn.bind(on_release=self._on_start)
        root.add_widget(start_btn)

        # ADHD tip at bottom
        root.add_widget(Widget())  # flexible spacer

        tip = Label(
            text="💡 Tip: Only add tasks you can actually finish today.",
            font_size=FONT_XS,
            color=TEXT_HINT,
            halign='center',
            size_hint_y=None,
            height=32
        )
        root.add_widget(tip)

        self.add_widget(root)

    def _on_start(self, instance):
        import core.database as db

        saved = 0
        self.error_label.text = ''

        for i, inp in enumerate(self.task_inputs):
            title = inp.text
            if not title:
                continue
            ok, reason = db.add_task(title, i, self.session_date)
            if ok:
                saved += 1
            else:
                self.error_label.text = reason
                # Shake the button
                btn = instance
                anim = (
                    Animation(x=btn.x + 8, duration=0.05) +
                    Animation(x=btn.x - 8, duration=0.05) +
                    Animation(x=btn.x + 5, duration=0.05) +
                    Animation(x=btn.x, duration=0.05)
                )
                anim.start(btn)
                return

        if saved == 0:
            self.error_label.text = "Enter at least 1 task to start!"
            return

        self.manager.current = 'focus'
