"""
sound.py — OneTask
Handles all sound effects. Gracefully fails if sound not available.
Uses pygame for reliable cross-platform audio.
"""

import os

_sounds = {}
_available = False

def init_sounds():
    global _available
    try:
        import pygame
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
        _available = True
        _load_sounds()
    except Exception as e:
        print(f"[Sound] Audio not available: {e}")
        _available = False


def _load_sounds():
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
            try:
                import pygame
                _sounds[key] = pygame.mixer.Sound(path)
            except Exception as e:
                print(f"[Sound] Could not load {filename}: {e}")


def play(sound_name):
    """Play a sound by name. Silently ignores if unavailable."""
    if not _available:
        return
    try:
        if sound_name in _sounds:
            _sounds[sound_name].play()
    except Exception as e:
        print(f"[Sound] Play error: {e}")
