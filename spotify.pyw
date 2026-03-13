import spotipy
from spotipy.oauth2 import SpotifyOAuth
import keyboard
import threading
import time
import sys
from PIL import Image, ImageTk
from CheckIfTaskRunning import is_process_running
import subprocess
from Logger_Core import log
from PyQt6.QtWidgets import (
    QApplication, QWidget, QHBoxLayout, QVBoxLayout,
    QLineEdit, QPushButton, QLabel, QCheckBox
)
from PyQt6.QtCore import Qt, QEvent, QTimer, QTime, QObject, pyqtSignal, QThread
from PyQt6.QtGui import QPainter, QColor, QShortcut, QKeySequence, QPixmap, QFont, QGuiApplication
import win32gui
import win32con
import win32api
import json
import os
import mysql.connector

# TODO change the spotify credentials to be read from a config file


# get creds from a file
try:
    with open(r"C:\Central\creds.json", "r") as f:
        creds = json.load(f)
        client_id = creds.get("client_id", "")
        client_secret = creds.get("client_secret", "")
        redirect_uri = creds.get("redirect_uri", "")
        if not client_id or not client_secret or not redirect_uri:
            raise ValueError("Incomplete Spotify credentials in creds.json")
except Exception as e:
    log(f"Error reading creds.json: {e}")
    client_id = ""
    client_secret = ""
    redirect_uri = ""

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=client_id,
    client_secret=client_secret,
    redirect_uri=redirect_uri,
    scope='user-modify-playback-state user-read-playback-state'
    ))

db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="spotify_api",
    charset="utf8mb4",      
    use_unicode=True        
)

cursor = db.cursor()

# ===== Settings page =====
class SettingsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setGeometry(600, 400, 400, 300)

        # layout definition
        layout = QVBoxLayout()
        self.setLayout(layout)

        # give one liners for settings
        self.settings_label1 = QLabel("<a href='https://developer.spotify.com/dashboard'>Enter your client ID and Secret from Spotify Developer Dashboard. you can enter the page by clicking the text</a>", self)
        self.settings_label1.setFixedWidth(300)
        self.settings_label1.setWordWrap(True)
        self.settings_label1.setOpenExternalLinks(True)
        self.settings_label1.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
        # here will be a QLineEdit for client ID
        self.client_id_input = QLineEdit(self)
        self.client_id_input.setPlaceholderText("Client ID")
        self.client_id_input.setFixedWidth(300)
        # here will be a QLineEdit for client Secret
        self.client_secret_input = QLineEdit(self)
        self.client_secret_input.setPlaceholderText("Client Secret")
        self.client_secret_input.setFixedWidth(300)
        # here will be a QLineEdit for redirect URI
        self.redirect_uri_input = QLineEdit(self)
        self.redirect_uri_input.setPlaceholderText("Redirect URI")
        self.redirect_uri_input.setFixedWidth(300)

       
        # Push button to save settings
        self.save_button = QPushButton("Save Settings", self)
        self.save_button.clicked.connect(self.save_settings)

        # add to layout
        
        layout.addWidget(self.client_id_input)
        layout.addWidget(self.client_secret_input)
        layout.addWidget(self.redirect_uri_input)
        layout.addWidget(self.settings_label1)
        layout.addWidget(self.save_button)

    def save_settings(self):
        client_id = self.client_id_input.text().strip()
        client_secret = self.client_secret_input.text().strip()
        redirect_uri = self.redirect_uri_input.text().strip()
        # clear inputs
        self.client_id_input.clear()
        self.client_secret_input.clear()
        self.redirect_uri_input.clear()
         # Save to a JSON file
         # Ensure the directory exists

        try:
            with open(r"C:\Central\creds.json", "w") as f:
                json.dump({
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "redirect_uri": redirect_uri
                }, f)
            log("Settings saved successfully.")
        except Exception as e:
            log(f"Error saving settings: {e}")
        self.hide()

        # restart after saving settings
        python = sys.executable
        os.execl(python, python, * sys.argv)



# ===== Dimmed Background =====
class Background(QWidget):
    def __init__(self, parent = None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self.resize(1920, 1080)

    def paintEvent(self, event):
        painter = QPainter()
        if not painter.begin(self):
            return
        try:
            painter.fillRect(self.rect(), QColor(0, 0, 0, 180))
        finally:
            painter.end()



class SongChecker(QObject):
    song_changed = pyqtSignal(str, str)

    def __init__(self):
        super().__init__()
        self.current_song = None
        self.running = True

    def start_checking(self):
        while self.running:
            try:
                playback = sp.current_playback()
                if playback and playback['item']:
                    song_name = playback['item']['name']
                    artist = playback['item']['artists'][0]['name']

                    if song_name != self.current_song:
                        self.current_song = song_name
                        self.song_changed.emit(song_name, artist)
                else:
                    # No active playback
                    if self.current_song is not None:
                        self.current_song = None
                        self.song_changed.emit("No song playing")
            except Exception as e:
                log(f"Error checking playback: {e}")
            time.sleep(2)

    def stop(self):
        self.running = False



def hotkey_listener():
    while True:
        keyboard.wait("ctrl+shift+[")
        log("detected hotkey")
        app.postEvent(window2, ToggleEvent())
        app.postEvent(window, ToggleEvent())


class ToggleEvent(QEvent):
     def __init__(self):
        super().__init__(QEvent.Type(QEvent.registerEventType()))

class SpotifyJarvis(QWidget):
    def __init__(self, parent = None):
        super().__init__(parent)
        
        # Add these near the start after super().__init__
        self.setMinimumWidth(600)
        self.setMaximumWidth(600)
        self.setMinimumHeight(400)
        self.setMaximumHeight(400)
        


        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self.setObjectName("spotify_window")

        #===== BASIC WINDOW SETTINGS =====
        self.setWindowTitle("EEVEE Spotify Integration")
        self.setStyleSheet("background: none;")
        self.bg = QPixmap(r"C:\Users\Admin\Documents\background.png")
        self.resize(600, 400)
        self.adjustSize()  # Let the layout determine proper size
        self.center_on_screen()
        log(self.geometry())
        
        #===== QUICK EXIT =====
        quick_exit = QShortcut("Esc", self)
        quick_exit.activated.connect(self.quick_exit)

        #===== MAIN lAYOUT =====
        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)

        #===== ADD STUFF =====

        self.time_label = QLabel("")
        self.time_label.setStyleSheet("font-size: 24px; font-weight: bold; color: white;")
        self.main_layout.addWidget(self.time_label, alignment=Qt.AlignmentFlag.AlignCenter)

        self.song_name_label = QLabel("")
        self.song_name_label.setStyleSheet("font-size: 18px; color: white; font-weight: bold;")
        self.song_name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.main_layout.addWidget(self.song_name_label, alignment=Qt.AlignmentFlag.AlignCenter)

        self.play_button = QPushButton("Play")
        self.play_button.clicked.connect(self.play_music)
        

        self.stop_button = QPushButton("Pause")
        self.stop_button.clicked.connect(self.pause_music)
        
        
        self.next_button = QPushButton("Next")
        self.next_button.clicked.connect(self.next_track)
        

        self.previous_button = QPushButton("Previous")
        self.previous_button.clicked.connect(self.previous_track)

        # the settings button is too low so move it up
        # self.settings_button = QPushButton("Settings")
        # self.settings_button.setFixedWidth(20)
        # self.settings_button.setFixedHeight(20)
        # self.settings_button.move(580, 0)
        # self.settings_button.clicked.connect(lambda: window3.show())
    
  
        self.full_text = ""
        self.current_index = 0

        self.timer2 = QTimer(self)
        self.timer2.timeout.connect(self.update_text)
        
        
        self.song_name_label.setWordWrap(True)   
        self.song_name_label.setFixedWidth(600)


        self.timer2 = QTimer(self)
        self.timer2.timeout.connect(self.update_text)
        self.timer2.start(50)

        self.checker = SongChecker()
        self.checker.song_changed.connect(self.update_song)
        
        # Create and start the checker thread
        self.checker_thread = QThread()
        self.checker.moveToThread(self.checker_thread)
        self.checker_thread.started.connect(self.checker.start_checking)
        self.checker_thread.start()

        # ===== BUTTON LAYOUT =====

        buttons_layout = QVBoxLayout()
        # buttons_layout.setSpacing(20)
        # buttons_layout.addWidget(self.play_button)
        # buttons_layout.addWidget(self.stop_button)
        # buttons_layout.addWidget(self.next_button)
        # buttons_layout.addWidget(self.previous_button)
        # # buttons_layout.addWidget(self.settings_button)
        self.main_layout.addWidget(self.play_button, alignment=Qt.AlignmentFlag.AlignCenter)
        self.main_layout.addWidget(self.stop_button, alignment=Qt.AlignmentFlag.AlignCenter)
        self.main_layout.addWidget(self.next_button, alignment=Qt.AlignmentFlag.AlignCenter)
        self.main_layout.addWidget(self.previous_button, alignment=Qt.AlignmentFlag.AlignCenter)
        # self.main_layout.addWidget(self.settings_button, alignment=Qt.AlignmentFlag.AlignTop |
        

        container = QWidget()
        # container.setLayout(buttons_layout)
        self.main_layout.addWidget(container, alignment=Qt.AlignmentFlag.AlignCenter)

        #===== TIME UPDATE =====
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_time)

        #===== Initial Sync =====
        self.last_second = -1  # Initialize with an invalid second to ensure the first update
        
        self.update_time()
        ms_until_next_second = 1000 - QTime.currentTime().msec()
        QTimer.singleShot(ms_until_next_second, self.start_timer)

        



        #===== SPOTIFY FLOWS =====

    def play_music(self):
        try:
            sp.start_playback()
        except Exception as e:
            log(f"Error starting playback: {e}")
    def pause_music(self):
        try:
            sp.pause_playback()
        except Exception as e:
            log(f"Error pausing playback: {e}")

    def next_track(self):
        try:
            sp.next_track()
        except Exception as e:
            log(f"Error skipping to next track: {e}")

    def previous_track(self):
        try:
            sp.previous_track()
        except Exception as e:
            log(f"Error skipping to previous track: {e}")

    def play_playlist(self, playlist_uri):
        try:
            sp.start_playback(context_uri=playlist_uri)
        except Exception as e:
            log(f"Error playing playlist: {e}")

    #===== Miscellaneous =====

    def quick_exit(self):
        window.hide()
        window2.hide()


    def update_song(self, song_name, artist):
        # Ask Spotify for the full data safely
        playback = sp.current_playback()
        if playback and playback['item']:

            # get the last commit
            sql = "select * from history order by id desc limit 1;"
            cursor.execute(sql)
            last_played = cursor.fetchone()
            last_played = last_played[0]
            

            
            sql = "INSERT INTO history (song_name, author) VALUES (%s, %s)"
            val = (song_name, artist)

            try:
                if last_played != playback['item']['name']:
                    cursor.execute(sql, val)
                    db.commit()
            except Exception as e:
                log(f"Database error: {e}")

            self.full_text = f"{song_name} - {artist}"
            self.current_index = 0
            self.song_name_label.setText("")
            self.timer2.start(50)
            
    def update_text(self):
        if self.current_index < len(self.full_text):
            self.song_name_label.setText(self.song_name_label.text() + self.full_text[self.current_index])
            self.current_index += 1
        else:
            self.timer2.stop()


    def customEvent(self, event):
        if isinstance(event, ToggleEvent):
            if window.isVisible():
                window.hide()
                window2.hide()
            else:
                window2.show()
                window.show()
                self.raise_()
                self.activateWindow()
                self.force_foreground()
                self.setFocus()
                


    def center_on_screen(self):
        # Get the screen geometry
        screen = QGuiApplication.primaryScreen().availableGeometry()
        
        # Force the window to calculate its real size
        self.adjustSize()
        
        # Calculate center position
        x = int((screen.width() - self.frameGeometry().width()) / 2)
        y = int((screen.height() - self.frameGeometry().height()) / 2)
        
        # Move the window
        self.move(x, y)
            

    def force_foreground(self):
        
        hwnd = int(self.winId())  # Get native window handle\
        log(hwnd)
        win32api.keybd_event(win32con.VK_MENU, 0, 0, 0)  # ALT down
        win32gui.SetForegroundWindow(hwnd)
        win32api.keybd_event(win32con.VK_MENU, 0, win32con.KEYEVENTF_KEYUP, 0)  # ALT up
        win32gui.ShowWindow(hwnd, win32con.SW_SHOWNORMAL)  # Restore if minimized
        win32gui.SetForegroundWindow(hwnd)  # Force that bitch

    def start_timer(self):
        self.timer.start(200)  # check 5 times a second

    def update_time(self):
        current_time = QTime.currentTime()
        if current_time.second != self.last_second:
            self.last_second = current_time.second()
            self.time_label.setText(f"{current_time.toString('hh:mm:ss')}")



    def paintEvent(self, event):
        painter = QPainter()
        if not painter.begin(self):      # safe begin guard
            return
        try:
            if not self.bg.isNull():
                pix = self.bg.scaled(self.size(),
                                 Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                                 Qt.TransformationMode.SmoothTransformation)
                painter.drawPixmap(self.rect(), pix)
            else:
                painter.fillRect(self.rect(), QColor(0,0,0,0))
        finally:
            painter.end()
# def start_overlay_sp():
#     from overlay import overlay, create_overlay
#     overlay_widget = create_overlay()

    



# overlay_thread = threading.Thread(target=start_overlay_sp)




if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = SpotifyJarvis()
    window2 = Background()
    window3 = SettingsPage()


    threading.Thread(target=hotkey_listener, daemon=True).start()
    

    from overlay import create_overlay
    overlay_widget = create_overlay()

    sys.exit(app.exec())