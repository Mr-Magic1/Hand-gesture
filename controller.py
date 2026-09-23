"""
controller.py
Translates gesture "intents" into actual OS actions:
mouse movement/clicks, scrolling, keyboard shortcuts, volume, brightness.

Uses pyautogui for cross-platform input simulation (mouse/keyboard/media keys)
and screen_brightness_control for brightness (best-effort, may not work on
every OS/monitor combo).
"""

import time
import pyautogui

pyautogui.FAILSAFE = False  # we manage our own bounds; don't abort on screen edges
pyautogui.PAUSE = 0

try:
    import screen_brightness_control as sbc
    BRIGHTNESS_AVAILABLE = True
except ImportError:
    BRIGHTNESS_AVAILABLE = False

SCREEN_W, SCREEN_H = pyautogui.size()


class PCController:
    def __init__(self, smoothening=6, frame_reduction=100, cam_w=640, cam_h=480):
        self.smoothening = smoothening
        self.frame_reduction = frame_reduction
        self.cam_w = cam_w
        self.cam_h = cam_h

        self.prev_x, self.prev_y = 0, 0
        self.curr_x, self.curr_y = 0, 0

        self.last_click_time = 0
        self.last_action_time = 0
        self.click_cooldown = 0.4
        self.action_cooldown = 1.0

    # ---------- Cursor ----------
    def move_mouse(self, x, y):
        target_x = self._map_range(x, self.frame_reduction, self.cam_w - self.frame_reduction, 0, SCREEN_W)
        target_y = self._map_range(y, self.frame_reduction, self.cam_h - self.frame_reduction, 0, SCREEN_H)

        self.curr_x = self.prev_x + (target_x - self.prev_x) / self.smoothening
        self.curr_y = self.prev_y + (target_y - self.prev_y) / self.smoothening

        pyautogui.moveTo(self.curr_x, self.curr_y)
        self.prev_x, self.prev_y = self.curr_x, self.curr_y

    @staticmethod
    def _map_range(value, in_min, in_max, out_min, out_max):
        value = max(min(value, in_max), in_min)
        return (value - in_min) / (in_max - in_min) * (out_max - out_min) + out_min

    def left_click(self):
        now = time.time()
        if now - self.last_click_time > self.click_cooldown:
            pyautogui.click()
            self.last_click_time = now

    def right_click(self):
        now = time.time()
        if now - self.last_click_time > self.click_cooldown:
            pyautogui.click(button="right")
            self.last_click_time = now

    def scroll(self, amount):
        pyautogui.scroll(amount)

    # ---------- Media / Volume ----------
    def volume_up(self):
        now = time.time()
        # Fast cooldown (0.1s) for smooth volume adjustment
        if now - getattr(self, "last_vol_time", 0) > 0.1:
            pyautogui.press("volumeup")
            self.last_vol_time = now

    def volume_down(self):
        now = time.time()
        if now - getattr(self, "last_vol_time", 0) > 0.1:
            pyautogui.press("volumedown")
            self.last_vol_time = now

    def mute(self):
        now = time.time()
        if now - self.last_action_time > self.action_cooldown:
            pyautogui.press("volumemute")
            self.last_action_time = now

    def play_pause(self):
        now = time.time()
        if now - self.last_action_time > self.action_cooldown:
            pyautogui.press("playpause")
            self.last_action_time = now

    def next_track(self):
        pyautogui.press("nexttrack")

    def prev_track(self):
        pyautogui.press("prevtrack")

    # ---------- Tab / Browser navigation ----------
    def next_tab(self):
        """Switch to the next browser/app tab (Ctrl+Tab)."""
        now = time.time()
        if now - self.last_action_time > 0.5:
            pyautogui.hotkey("ctrl", "tab")
            self.last_action_time = now

    def prev_tab(self):
        """Switch to the previous browser/app tab (Ctrl+Shift+Tab)."""
        now = time.time()
        if now - self.last_action_time > 0.5:
            pyautogui.hotkey("ctrl", "shift", "tab")
            self.last_action_time = now

    def browser_back(self):
        """Go back in browser history (Alt+Left)."""
        now = time.time()
        if now - self.last_action_time > 0.8:
            pyautogui.hotkey("alt", "left")
            self.last_action_time = now

    def browser_forward(self):
        """Go forward in browser history (Alt+Right)."""
        now = time.time()
        if now - self.last_action_time > 0.8:
            pyautogui.hotkey("alt", "right")
            self.last_action_time = now

    # ---------- Brightness ----------
    def brightness_up(self, step=10):
        if not BRIGHTNESS_AVAILABLE:
            return
        try:
            curr = sbc.get_brightness(display=0)[0]
            sbc.set_brightness(min(curr + step, 100))
        except Exception:
            pass

    def brightness_down(self, step=10):
        if not BRIGHTNESS_AVAILABLE:
            return
        try:
            curr = sbc.get_brightness(display=0)[0]
            sbc.set_brightness(max(curr - step, 0))
        except Exception:
            pass

    # ---------- Window / Desktop shortcuts ----------
    def switch_window(self):
        now = time.time()
        if now - self.last_action_time > self.action_cooldown:
            pyautogui.hotkey("alt", "tab")
            self.last_action_time = now

    def close_window(self):
        now = time.time()
        if now - self.last_action_time > self.action_cooldown:
            pyautogui.hotkey("alt", "f4")
            self.last_action_time = now
            
    def maximize_window(self):
        now = time.time()
        if now - self.last_action_time > self.action_cooldown:
            pyautogui.hotkey("win", "up")
            self.last_action_time = now

    def show_desktop(self):
        now = time.time()
        if now - self.last_action_time > self.action_cooldown:
            pyautogui.hotkey("win", "d")
            self.last_action_time = now

    def switch_desktop_right(self):
        now = time.time()
        if now - self.last_action_time > self.action_cooldown:
            pyautogui.hotkey("ctrl", "win", "right")  # Windows virtual desktops
            self.last_action_time = now

    def switch_desktop_left(self):
        now = time.time()
        if now - self.last_action_time > self.action_cooldown:
            pyautogui.hotkey("ctrl", "win", "left")
            self.last_action_time = now

    def minimize_window(self):
        now = time.time()
        if now - self.last_action_time > self.action_cooldown:
            pyautogui.hotkey("win", "down")
            self.last_action_time = now

    # ---------- Editing shortcuts ----------
    def copy(self):
        pyautogui.hotkey("ctrl", "c")

    def paste(self):
        pyautogui.hotkey("ctrl", "v")

    def undo(self):
        pyautogui.hotkey("ctrl", "z")

    def zoom_in(self):
        pyautogui.hotkey("ctrl", "+")

    def zoom_out(self):
        pyautogui.hotkey("ctrl", "-")

    # ---------- Misc ----------
    def screenshot(self, save_dir="."):
        now = time.time()
        if now - self.last_action_time > self.action_cooldown:
            img = pyautogui.screenshot()
            fname = f"{save_dir}/screenshot_{int(now)}.png"
            img.save(fname)
            self.last_action_time = now
            return fname
        return None
