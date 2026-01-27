import logging
import os
import datetime as dt
import json
import win32file, win32pipe
import inspect

import time

date = dt.datetime.now().strftime('%Y-%m-%d-%h-%min')
logpath = f"Logs/{date}"
PIPE_NAME = r'\\.\pipe\EEVEELogger'
INPUT_PIPE_NAME = r'\\.\pipe\EEVEEInputLogger'

# TODO could do log filter by date (every day in another file)
        



# File logging setup
logging.basicConfig(
    filename=r"C:\Central\log.json",
    level=logging.INFO,
    format="%(message)s - %(levelname)s"
)


def get_filename():
    stack = inspect.stack()
    # The last frame in the stack ([-1]) is usually the entry script (top-level caller)
    top_frame = stack[-1]
    top_filename = top_frame.filename
    return os.path.basename(top_filename)

def log(message, level="INFO"):
    timestamp = dt.datetime.now().strftime('%D-%m-%d %H:%M:%S')
    filename = os.path.basename(__file__)
    full_message = f"[{get_filename()}] {message}  [{timestamp}]"
    
    # write to file
    getattr(logging, level.lower())(full_message) 

    # try to send it via pipe
    try:
        handle = win32file.CreateFile(
            PIPE_NAME,
            win32file.GENERIC_WRITE,
            0, None,
            win32file.OPEN_EXISTING,
            0, None
        )
        win32file.WriteFile(handle, full_message.encode())
    except Exception as e:
        pass


def feed(message):
    log(message)
    while True:
        pipe = win32pipe.CreateNamedPipe(
            INPUT_PIPE_NAME,
            win32pipe.PIPE_ACCESS_DUPLEX,
            win32pipe.PIPE_TYPE_MESSAGE | win32pipe.PIPE_READMODE_MESSAGE | win32pipe.PIPE_WAIT,
            1, 65536, 65536,
            0, None
        )
        win32pipe.ConnectNamedPipe(pipe, None)
        result, data = win32file.ReadFile(pipe, 64*1024)
        win32file.CloseHandle(pipe)  # close pipe when done so next client can connect
        return data.decode()
        
