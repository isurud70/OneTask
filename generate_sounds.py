"""
generate_sounds.py — OneTask
Generates all required sound effects programmatically.
Run this once to create the assets/sounds/ files.
No downloads needed — pure Python math.
"""

import wave
import struct
import math
import os

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), 'assets', 'sounds')


def write_wav(filename, frames, sample_rate=44100):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    path = os.path.join(OUTPUT_DIR, filename)
    with wave.open(path, 'w') as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(sample_rate)
        f.writeframes(frames)
    print(f"[Sound] Created: {path}")


def tone(freq, duration, sample_rate=44100, volume=0.5, fade_out=True):
    """Generate a pure sine wave tone."""
    n_samples = int(sample_rate * duration)
    frames = []
    for i in range(n_samples):
        t = i / sample_rate
        sample = math.sin(2 * math.pi * freq * t)
        # Fade out last 20% to avoid click
        if fade_out and i > n_samples * 0.8:
            fade = 1.0 - (i - n_samples * 0.8) / (n_samples * 0.2)
            sample *= fade
        value = int(sample * volume * 32767)
        frames.append(struct.pack('<h', value))
    return b''.join(frames)


def generate_complete():
    """Happy ascending two-tone chime."""
    part1 = tone(523, 0.12, volume=0.6)   # C5
    part2 = tone(659, 0.12, volume=0.6)   # E5
    part3 = tone(784, 0.2,  volume=0.7)   # G5
    write_wav('complete.wav', part1 + part2 + part3)


def generate_skip():
    """Short neutral descending tick."""
    part1 = tone(440, 0.07, volume=0.3)   # A4
    part2 = tone(330, 0.1,  volume=0.25)  # E4
    write_wav('skip.wav', part1 + part2)


def generate_perfect():
    """Triumphant four-note fanfare for perfect day."""
    p1 = tone(523, 0.1, volume=0.7)   # C5
    p2 = tone(659, 0.1, volume=0.7)   # E5
    p3 = tone(784, 0.1, volume=0.7)   # G5
    p4 = tone(1047, 0.3, volume=0.8)  # C6
    write_wav('perfect.wav', p1 + p2 + p3 + p4)


def generate_tick():
    """Soft body-double background tick (very quiet)."""
    frames = tone(1200, 0.03, volume=0.08)
    write_wav('tick.wav', frames)


def generate_all():
    print("[Sound] Generating all sound effects...")
    generate_complete()
    generate_skip()
    generate_perfect()
    generate_tick()
    print("[Sound] All sounds generated successfully!")


if __name__ == '__main__':
    generate_all()
