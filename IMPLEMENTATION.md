# Hand Gesture PC Control — Implementation

Control your mouse, keyboard shortcuts, volume, brightness, and media playback
using only hand gestures, via a webcam, OpenCV, and MediaPipe Hands.

## 1. Architecture

```
gesture_pc_control/
├── main.py                # Entry point: capture loop, dispatch gestures
├── hand_tracker.py        # MediaPipe wrapper: detects 21 hand landmarks
├── gesture_recognizer.py  # Turns landmarks into a gesture label (rule-based)
├── controller.py          # Executes OS actions (mouse/keyboard/volume/brightness)
├── config.py              # Tunable constants + gesture→action reference table
└── requirements.txt
```

**Data flow per frame:**

```
Webcam frame
   → HandTracker.find_hands()        (MediaPipe detection + drawing)
   → HandTracker.get_landmark_list() (21 (x, y, z) points)
   → GestureRecognizer.classify()    ("POINT", "PINCH_CLICK", "OPEN_PALM", ...)
   → main.py dispatch                (if/elif on gesture label)
   → PCController.<action>()         (pyautogui / screen_brightness_control)
```

Each module is independent and replaceable — you can swap `gesture_recognizer.py`
for an ML classifier later without touching `controller.py` or `main.py`.

## 2. How gesture detection works

MediaPipe Hands returns 21 landmarks per hand (wrist, then 4 points per finger).
`gesture_recognizer.py` uses two simple techniques instead of a trained model:

1. **Finger up/down state**: a finger is "up" if its tip landmark sits above
   (smaller y) its own PIP joint. The thumb is checked on the x-axis instead,
   because it bends sideways, and the comparison direction flips based on
   which hand (left/right) MediaPipe reports.
2. **Pinch distance**: Euclidean distance between the thumb tip and another
   fingertip. Below a threshold (default 35px at 640×480) counts as a pinch.

The resulting 5-element `[thumb, index, middle, ring, pinky]` up/down pattern
is matched against a lookup table to produce a gesture name. This is fast
(no inference cost) and easy to retune by eye.

## 3. Gesture → Action map

| Gesture | Hand shape | Action |
|---|---|---|
| `POINT` | Index finger only | Move mouse cursor |
| `PINCH_CLICK` | Thumb + index tips touch | Left click |
| `PINCH_RIGHT_CLICK` | Thumb + middle tips touch | Right click |
| `TWO_FINGERS` | Index + middle up | Scroll (move hand up/down) |
| `THREE_FINGERS` | Index + middle + ring up | Switch window (Alt+Tab) |
| `OPEN_PALM` (held still) | All 5 fingers up, static | Show desktop (Win+D) |
| `OPEN_PALM` (swiped) | All 5 fingers up, moved sideways fast | Switch virtual desktop (Ctrl+Win+←/→) |
| `FIST` | No fingers up | Idle / safe pose (no action) |
| `THUMBS_UP` | Thumb up, others down | Volume up |
| `PINKY` | Pinky only | Volume down |
| `GUN` | Thumb + index in an L | Take a screenshot |
| `ROCK` | Thumb + index + pinky ("horns") | Play / pause media |

Cursor mapping only uses the inner region of the frame (`FRAME_REDUCTION` margin
in `config.py`) so you don't have to reach to the camera's edges to hit screen
corners, and movement is smoothed (`SMOOTHENING`) to reduce jitter.

`PCController` also ships ready-to-wire methods you can bind to any gesture:
`copy()`, `paste()`, `undo()`, `zoom_in()`, `zoom_out()`, `minimize_window()`,
`next_track()`, `prev_track()`, `mute()`.

## 4. Setup

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

**Controls while running:** `q` quits, `p` pauses/resumes gesture actions
(camera preview stays open so you can see tracking without triggering actions).

## 5. Platform notes

- **Volume/media keys** (`volumeup`, `playpause`, etc.) work via `pyautogui.press()`
  on Windows and most Linux desktop environments; macOS support for these
  virtual keys is inconsistent — you may need `osascript` calls instead.
- **`Ctrl+Win+←/→`** (virtual desktop switch) and **`Win+D`** are Windows
  shortcuts. On macOS, remap `switch_desktop_left/right` in `controller.py` to
  `Ctrl+←/→` (Mission Control spaces) and `show_desktop` to F11.
- **Brightness control** depends on `screen_brightness_control`'s OS backend;
  it works well on most Windows laptops and many Linux setups, less reliably
  on external monitors or macOS.
- Run in good, even lighting for reliable landmark detection, and keep one
  hand clearly in frame — `max_hands=1` in `hand_tracker.py` keeps CPU usage low.

## 6. Tuning tips

- Cursor too jittery → increase `SMOOTHENING` in `config.py`.
- Clicks not registering / firing too easily → adjust `PINCH_THRESHOLD`.
- Actions repeating too fast → increase `click_cooldown` / `action_cooldown`
  in `controller.py`.
- Add a new gesture: add a pattern check in `GestureRecognizer.classify()`,
  add a matching `elif` branch in `main.py`, and (optionally) a method in
  `PCController`.

## 7. Suggested features to add next

- **Two-hand gestures** — e.g., pinch-with-both-hands to zoom in/out (like a
  pinch-to-zoom trackpad), or one hand for cursor + other hand for clicks.
- **Custom gesture trainer** — record landmark sequences for your own
  gestures and train a small classifier (scikit-learn or a tiny neural net)
  instead of hardcoded rules, for gestures rule-based logic can't express well.
- **Drag-and-drop** — pinch-and-hold (instead of a quick pinch) to pick up a
  window/icon, move hand, release pinch to drop.
- **Gesture macros** — let the user record a custom key sequence and bind it
  to a gesture at runtime, rather than editing code.
- **App launcher gestures** — a specific gesture opens a chosen app or a
  gesture-driven radial menu.
- **Wake gesture / lock mode** — require a specific "activation" gesture
  before the system starts acting, to avoid accidental triggers when you're
  just talking with your hands.
- **System tray GUI** — a small tray icon with on/off toggle, sensitivity
  sliders, and a live gesture-mapping editor instead of editing `config.py`.
- **Presentation mode** — dedicated gestures for next/previous slide, laser
  pointer, and blank-screen, for PowerPoint/Google Slides/Keynote.
- **Multi-monitor awareness** — detect which screen the cursor should map to,
  or use a gesture to throw the cursor to the next monitor.
- **Voice + gesture hybrid** — combine with `speech_recognition` so a
  gesture can be confirmed or parameterized by a short voice command.
- **On-screen gesture guide overlay** — show the current gesture's action
  and a cheat-sheet overlay toggled by a gesture, so new users don't need to
  memorize the table.
- **Logging/analytics** — log which gestures fire and how often, useful for
  tuning thresholds and spotting gestures that misfire.
- **Performance** — move camera capture to its own thread so frame grabbing
  never blocks gesture processing/UI rendering; drop to `max_hands=1` (already
  default) and lower camera resolution on low-end hardware.
- **Packaging** — bundle as a background service with a hotkey (e.g. a
  keyboard shortcut) to toggle gesture control on/off system-wide, and add
  auto-start on login.
