"""Cross-platform terminal ESC cancellation for long-running actions."""
import atexit
import os
import platform
import select
import sys
import threading
import time


class AbortRequested(Exception):
    pass


_stop = threading.Event()
_abort = threading.Event()
_thread = None
_termios_state = None


def _listen():
    global _termios_state
    try:
        from pynput import keyboard

        def on_press(key):
            if key == keyboard.Key.esc:
                _abort.set()
                return False

        listener = keyboard.Listener(on_press=on_press)
        listener.start()
        while not _stop.is_set() and listener.is_alive():
            time.sleep(0.03)
        listener.stop()
        return
    except Exception:
        # Fall back to terminal input when global keyboard hooks are blocked.
        pass

    if platform.system() == "Windows":
        import msvcrt
        while not _stop.is_set():
            if msvcrt.kbhit() and msvcrt.getwch() == "\x1b":
                _abort.set()
                return
            time.sleep(0.03)
        return

    if not sys.stdin.isatty():
        return
    import termios
    import tty
    fd = sys.stdin.fileno()
    _termios_state = termios.tcgetattr(fd)
    tty.setcbreak(fd)
    try:
        while not _stop.is_set():
            ready, _, _ = select.select([fd], [], [], 0.03)
            if ready and os.read(fd, 1) == b"\x1b":
                _abort.set()
                return
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, _termios_state)


def start():
    global _thread
    _stop.clear()
    _abort.clear()
    _thread = threading.Thread(target=_listen, daemon=True)
    _thread.start()


def stop():
    _stop.set()
    if _thread and _thread.is_alive():
        _thread.join(timeout=0.2)


def check():
    if _abort.is_set():
        raise AbortRequested("ESC pressed")


def sleep(seconds):
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        check()
        time.sleep(min(0.03, end - time.monotonic()))


atexit.register(stop)
