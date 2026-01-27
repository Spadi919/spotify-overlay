from PyQt6.QtWidgets import QApplication, QLabel, QWidget, QGraphicsDropShadowEffect, QHBoxLayout, QVBoxLayout
from PyQt6.QtCore import Qt, QTimer, QObject, pyqtSignal, QThread, QPropertyAnimation, QByteArray, QRect, QSize
from PyQt6.QtGui import QFont, QColor, QPixmap, QIcon, QPainter, QBrush, QImage
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

# class SongChecker(QObject):
#     song_changed = pyqtSignal(str)     # New song name
#     playback_state = pyqtSignal(bool)  # True if playing, False if paused

#     def __init__(self):
#         super().__init__()
#         self.current_song = None
#         self.running = True

#     def start_checking(self):
#         while self.running:
#             try:
#                 if sp:
#                     playback = sp.current_playback()
                    
#                     # 1. Check Playback Status (For fading)
#                     is_playing = playback and playback.get('is_playing', False)
#                     self.playback_state.emit(is_playing)

#                     # 2. Check Song Name
#                     if playback and playback.get('item'):
#                         song_name = playback['item']['name']
#                         if song_name != self.current_song:
#                             self.current_song = song_name
#                             self.song_changed.emit(song_name)
#                 else:
#                     time.sleep(5)
#             except Exception as e:
#                 log(f"Overlay Checker Error: {e}")
            
#             time.sleep(1)

#     def stop(self):
#         self.running = False

# class CheckerThread(QThread):
#     def __init__(self, checker):
#         super().__init__()
#         self.checker = checker

#     def run(self):
#         self.checker.start_checking()
    
#     def stop(self):
#         self.checker.stop()
#         self.quit()
#         self.wait()

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
        self.setWindowOpacity(1) # Start hidden

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
        
        self.resize(1000, 1000)
        self.move(x, y)

        
        # hbox = QVBoxLayout()     
        # self.setLayout(hbox)   



        # create a rectangle
        self.rectangle1 = QLabel("")
        self.rectangle1.setGeometry(200, 10, 500, 75)
        self.rectangle1.setStyleSheet("Background-color: #e8a374;border-radius:20px;")
        self.rectangle1.setParent(self)
        
        self.smallrec1 = QLabel("")
        self.album_cover = QPixmap("cover.jpg")
        self.cover_scaled = self.album_cover.scaled(160, 160)
        self.smallrec1.setPixmap(self.cover_scaled)
        self.smallrec1.setGeometry(20, 0, 160,160)
        self.smallrec1.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.smallrec1.setParent(self)

        self.song_name = QLabel("Espresso")
        self.song_name.setStyleSheet("font-family: Inter,system-ui,Avenir,Helvetica,Arial,sans-serif; font-weight:900; color: #ffffff;")
        self.song_name.setGeometry(215, -75, 200, 200)
        self.song_name.setParent(self)
        
        self.artist_name = QLabel("Sabrina Carpenter")
        self.artist_name.setStyleSheet("font-family: Inter,system-ui,Avenir,Helvetica,Arial,sans-serif; color:#f2ebeb; font-weight: 600; ")
        self.artist_name.setGeometry(215, -50, 200, 200)
        self.artist_name.setParent(self)


        self.rectangle2 = QLabel("")
        self.rectangle2.setGeometry(200, 100, 500, 50)
        self.rectangle2.setStyleSheet("Background-color: #e8a374;border-radius:20px;")
        self.rectangle2.setParent(self)

        self.rectangle3 = QLabel("")
        self.rectangle3.setGeometry(220, 500, 440, 25)
        self.rectangle3.setStyleSheet("Background-color: #b8805a;border-radius:50px;")
        self.rectangle3.setParent(self)

        self.rectangle1.show()
        self.smallrec1.show()
        self.song_name.show()
        self.artist_name.show()
        





# --- FACTORY FUNCTION ---
# def create_overlay():
#     return Overlay()



if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Overlay()
    window.show()
    sys.exit(app.exec())