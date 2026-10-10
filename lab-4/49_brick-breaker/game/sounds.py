import math
import array
import pygame


def _tone(notes, volume=0.35, rate=44100):
    """notes: list of (freq_hz, ms). Returns mono 16-bit Sound."""
    buf = array.array("h")
    for freq, ms in notes:
        n = int(rate * ms / 1000)
        for i in range(n):
            env = 1 - i / n  # linear fade to avoid clicks
            s = math.sin(2 * math.pi * freq * i / rate) * env * volume
            buf.append(int(s * 32767))
    return pygame.mixer.Sound(buffer=buf.tobytes())


class Sounds:
    """Generates all effects at runtime (no asset files). Silently disables
    itself if no audio device / unexpected mixer format."""

    def __init__(self):
        self.enabled = False
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(44100, -16, 1, 512)
            if pygame.mixer.get_init()[1:] != (-16, 1):
                return
            self.brick = _tone([(660, 70)])
            self.paddle = _tone([(330, 60)])
            self.wall = _tone([(220, 40)], volume=0.25)
            self.lose_life = _tone([(180, 120)])
            self.win = _tone([(523, 120), (659, 120), (784, 120), (1047, 250)])
            self.lose = _tone([(392, 160), (330, 160), (262, 160), (196, 350)])
            self.enabled = True
        except pygame.error:
            self.enabled = False

    def play(self, name):
        if self.enabled:
            getattr(self, name).play()
