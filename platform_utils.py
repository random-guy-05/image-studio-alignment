"""Small cross-platform helpers for ImageStudio automation."""
import platform
import os
import subprocess
import time

import pyautogui


def get_largest_window(title=None):
    title = title or os.environ.get("IMAGESTUDIO_WINDOW_TITLE", "ImageStudio")
    system = platform.system()
    if system == "Darwin":
        raw = subprocess.check_output([
            "osascript", "-e",
            f'tell application "System Events" to tell process "{title}" to get position of every window & size of every window',
        ]).decode().strip()
        parts = []
        for value in raw.replace("{", "").replace("}", "").split(","):
            try:
                parts.append(int(value.strip()))
            except ValueError:
                parts.append(0)
        count = len(parts) // 4
        windows = []
        for i in range(count):
            x, y = parts[i * 2], parts[i * 2 + 1]
            w, h = parts[count * 2 + i * 2], parts[count * 2 + i * 2 + 1]
            if w and h:
                windows.append((x, y, w, h, w * h))
    elif system == "Windows":
        import pygetwindow
        windows = []
        for window in pygetwindow.getAllWindows():
            if title.lower() in window.title.lower() and window.width and window.height:
                windows.append((window.left, window.top, window.width, window.height,
                                window.width * window.height))
    else:
        screen_w, screen_h = pyautogui.size()
        windows = [(0, 0, screen_w, screen_h, screen_w * screen_h)]
    if not windows:
        raise RuntimeError(f"Could not find an {title} window")
    return max(windows, key=lambda item: item[4])[:4]


def activate_window(title=None):
    title = title or os.environ.get("IMAGESTUDIO_WINDOW_TITLE", "ImageStudio")
    if platform.system() == "Darwin":
        subprocess.run(["osascript", "-e", f'tell application "{title}" to activate'], check=True)
    elif platform.system() == "Windows":
        import pygetwindow
        windows = [window for window in pygetwindow.getAllWindows()
                   if title.lower() in window.title.lower()]
        if not windows:
            raise RuntimeError(f"Could not find an {title} window")
        windows[0].activate()
    time.sleep(0.4)


def capture_fullscreen(path):
    if platform.system() == "Darwin":
        subprocess.run(["screencapture", "-x", path], check=True)
    else:
        try:
            pyautogui.screenshot().save(path)
        except Exception:
            import PIL.ImageGrab
            PIL.ImageGrab.grab().save(path)
