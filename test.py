from PyQt6.QtWidgets import QLabel, QGraphicsOpacityEffect
from PyQt6.QtCore import QPropertyAnimation, QTimer
# assume `sp` is your authenticated spotipy.Spotify instance

class PlaybackWatcher:
    def __init__(self, sp, label: QLabel, poll_ms: int = 1000):
        self.sp = sp
        self.label = label

        # opacity effect (attach to label)
        self.opacity_effect = QGraphicsOpacityEffect(self.label)
        self.label.setGraphicsEffect(self.opacity_effect)
        self.opacity_effect.setOpacity(1.0)

        # single reusable animation (store as attribute so it's not GC'd)
        self.anim = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.anim.setDuration(500)  # 500 ms fade

        self.last_is_playing = None  # unknown at start

        # timer to poll playback without blocking the UI
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_if_song_playing)
        self.timer.start(poll_ms)

    def check_if_song_playing(self):
        # get fresh playback state each call
        # use current_playback() or appropriate method from your Spotify client
        playback = self.sp.current_playback()  # may return None or dict
        is_playing = bool(playback and playback.get('is_playing'))

        # only animate when state changed (avoid restarting animation repeatedly)
        if is_playing == self.last_is_playing:
            return

        self.last_is_playing = is_playing

        # animate to visible when playing, to transparent when paused
        current_opacity = self.opacity_effect.opacity()
        if is_playing:
            self.anim.stop()
            self.anim.setStartValue(current_opacity)
            self.anim.setEndValue(1.0)
            self.anim.start()
        else:
            self.anim.stop()
            self.anim.setStartValue(current_opacity)
            self.anim.setEndValue(0.0)
            self.anim.start()
