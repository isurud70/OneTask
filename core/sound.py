"""
sound.py — OneTask
Uses Kivy's built-in audio — works on Android without pygame.
"""

_sounds = {}
_available = False

def init_sounds():
    global _available
    try:
        from kivy.core.audio import SoundLoader
        _available = True
        _load_sounds()
    except Exception as e:
        print(f"[Sound] Audio not available: {e}")

def _load_sounds():
    import os
    from kivy.core.audio import SoundLoader
    sound_dir = os.path.join(os.path.dirname(__file__), '..', 'assets', 'sounds')
    sound_files = {
        'complete': 'complete.wav',
        'skip':     'skip.wav',
        'perfect':  'perfect.wav',
        'tick':     'tick.wav',
    }
    for key, filename in sound_files.items():
        path = os.path.join(sound_dir, filename)
        if os.path.exists(path):
            sound = SoundLoader.load(path)
            if sound:
                _sounds[key] = sound

def play(sound_name):
    if not _available:
        return
    try:
        if sound_name in _sounds:
            _sounds[sound_name].play()
    except Exception as e:
        print(f"[Sound] Play error: {e}")
