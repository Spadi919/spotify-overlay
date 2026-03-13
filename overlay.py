from PyQt6.QtWidgets import QApplication, QLabel, QWidget, QGraphicsDropShadowEffect
from PyQt6.QtCore import Qt, QTimer, QObject, pyqtSignal, QThread, QPropertyAnimation, QByteArray
from PyQt6.QtGui import QFont, QColor
import sys
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import time
import ctypes
from Logger_Core import log

# --- SPOTIFY SETUP ---
try:
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
        client_id='5b9511b4528c451590aba6923786544f',
        client_secret='148a00e96c724020974e68ccff1424e4',
        redirect_uri='http://127.0.0.1:8888/callback',
        scope='user-modify-playback-state user-read-playback-state'
    ))
except Exception as e:
    log(f"Spotipy Auth Error in Overlay: {e}")
    sp = None

# --- WORKER CLASSES ---

class SongChecker(QObject):
    song_changed = pyqtSignal(str)     # New song name
    playback_state = pyqtSignal(bool)  # True if playing, False if paused

    def __init__(self):
        super().__init__()
        self.current_song = None
        self.running = True

    def start_checking(self):
        while self.running:
            try:
                if sp:
                    playback = sp.current_playback()
                    
                    # 1. Check Playback Status (For fading)
                    is_playing = playback and playback.get('is_playing', False)
                    self.playback_state.emit(is_playing)

                    # 2. Check Song Name
                    if playback and playback.get('item'):
                        song_name = playback['item']['name']
                        if song_name != self.current_song:
                            self.current_song = song_name
                            self.song_changed.emit(song_name)
                else:
                    time.sleep(5)
            except Exception as e:
                log(f"Overlay Checker Error: {e}")
            
            time.sleep(1)

    def stop(self):
        self.running = False

class CheckerThread(QThread):
    def __init__(self, checker):
        super().__init__()
        self.checker = checker

    def run(self):
        self.checker.start_checking()
    
    def stop(self):
        self.checker.stop()
        self.quit()
        self.wait()

# --- MAIN OVERLAY CLASS ---

class Overlay(QWidget):
    def __init__(self):
        super().__init__()
        # Window Flags
        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint | 
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.Tool
        )

        # --- FIX: Use Native Window Opacity instead of QGraphicsOpacityEffect ---
        self.setWindowOpacity(0.0) # Start hidden

        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        
        # Windows Click-Through Hack
        try:
            hwnd = self.winId().__int__()
            extended_style = ctypes.windll.user32.GetWindowLongW(hwnd, -20)
            ctypes.windll.user32.SetWindowLongW(hwnd, -20, extended_style | 0x00000020)
        except Exception as e:
            log(f"Overlay Window Style Error: {e}") # <---- would it fuck up something? yes it would dumbass it says on the top what it does
        # Positioning
        
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)
        self.resize(1600, 200)
        # Effects (Shadows/Glows are fine on child widgets)
        self.glow_effect = QGraphicsDropShadowEffect()
        self.glow_effect.setBlurRadius(40)
        self.glow_effect.setColor(QColor(255, 255, 255))
        self.glow_effect.setOffset(0, 0)

        self.glow_effectblue = QGraphicsDropShadowEffect()
        self.glow_effectblue.setBlurRadius(80)
        self.glow_effectblue.setColor(QColor(0, 255, 255))
        self.glow_effectblue.setOffset(0, 0)

        # UI Elements
        self.label = QLabel("Now Playing:", self)
        self.label.setGraphicsEffect(self.glow_effect)
        self.label.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        self.label.setStyleSheet("color: #FFFFFF; font-family: VT323;")
        self.label.move(0, 0)

        self.label1 = QLabel("", self)
        self.label1.setGraphicsEffect(self.glow_effectblue)
        self.label1.setFont(QFont("Arial", 16))
        self.label1.setStyleSheet("color: #00FFFF; font-family: Quantico;")
        self.label1.setWordWrap(True)   
        self.label1.setFixedWidth(1400)
        self.label1.move(0, 30)

        # Typewriter Variables
        self.full_text = ""
        self.current_index = 0
        self.typewriter_timer = QTimer(self)
        self.typewriter_timer.timeout.connect(self.update_text_step)

        # Logic Setup
        self.checker = SongChecker()
        self.checker.song_changed.connect(self.on_song_changed)
        self.checker.playback_state.connect(self.fade_overlay)
        
        self.checker_thread = CheckerThread(self.checker)
        self.checker_thread.start()

        self.show()
        
        # Initialize fade animation variable
        self.fade_animation = None

        self.move(0, 0)

    def on_song_changed(self, song_name):
        try:
            playback = sp.current_playback()
            if playback and playback.get('item'):
                artist = playback['item']['artists'][0]['name']
                self.full_text = f"{song_name} - {artist}"
                self.current_index = 0
                self.label1.setText("")
                self.typewriter_timer.start(50)
        except Exception as e:
            log(f"Overlay Update Error: {e}")

    def update_text_step(self):
        if self.current_index < len(self.full_text):
            self.label1.setText(self.label1.text() + self.full_text[self.current_index])
            self.current_index += 1
        else:
            self.typewriter_timer.stop()

    def fade_overlay(self, is_playing):
        # Use native windowOpacity property
        target_opacity = 1.0 if is_playing else 0.0
        current_opacity = self.windowOpacity()
        with open(r"C:\Central\Miscellaneous\is_playing.txt", "w") as f:
            f.write(str(is_playing))

        if abs(current_opacity - target_opacity) < 0.01:
            return

        if self.fade_animation:
            self.fade_animation.stop()

        # Animate 'windowOpacity' instead of 'opacity' on an effect
        self.fade_animation = QPropertyAnimation(self, b"windowOpacity")
        self.fade_animation.setDuration(500) 
        self.fade_animation.setStartValue(current_opacity)
        self.fade_animation.setEndValue(target_opacity)
        self.fade_animation.start()
    
    def closeEvent(self, event):
        if self.checker_thread:
            self.checker_thread.stop()
        super().closeEvent(event)

# --- FACTORY FUNCTION ---
def create_overlay():
    return Overlay()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Overlay()
    sys.exit(app.exec())