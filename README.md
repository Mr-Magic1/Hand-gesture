# Hand Gesture PC Control

A computer vision-based application that allows you to control your PC using hand gestures and eye tracking. Built with Python, OpenCV, and MediaPipe, this tool maps specific hand gestures and eye movements to system-level commands like mouse movement, clicking, scrolling, media control, and window navigation.

## Features

- **Hand Gesture Control:** Map distinct hand poses (e.g., Pointing, Pinching, Open Palm, Fist) to various actions.
- **Eye Tracking Mode:** Control the mouse cursor using your gaze and click by blinking!
- **Smart Wake-on-Motion:** Automatically enters a low-resource "Sleep Mode" if no hand is detected for 2 seconds. Any significant motion wakes it up instantly.
- **Customizable Configuration:** Easily tweak sensitivities, scroll speed, and camera settings via the `config.py` file.
- **Floating HUD:** Provides a draggable, resizable topmost webcam overlay showing real-time FPS and recognized gestures.

## Prerequisites

Make sure you have Python 3.9+ installed. You can install all dependencies via the provided `requirements.txt`.

```bash
pip install -r requirements.txt
```

### Dependencies
- `opencv-python>=4.9.0`
- `mediapipe==0.10.9`
- `pyautogui>=0.9.54`
- `numpy>=1.26.0`
- `screen-brightness-control>=0.22.2`
- `scikit-learn>=1.3.0`

## How to Run

1. Open a terminal in the project directory.
2. Run the main entry script:
   ```bash
   python main.py
   ```
3. A floating window named **"Hand Gesture PC Control"** will appear on your screen.
4. Show your hand to the camera or use eye tracking (configured in `config.py`) to start controlling your PC.

### Overlay Controls
While the window is active:
- **`q`** : Quit the application.
- **`p`** : Pause or resume gesture detection.
- **`+` / `=`** : Increase the overlay window size.
- **`-`** : Decrease the overlay window size.
- **Click and Drag** inside the overlay to move it around your screen.

## Gestures and Actions

The core application provides an extensive mapping of hand gestures to mouse, keyboard, and system events.

### Mouse Controls
- **POINT (Index finger only):** Moves the mouse cursor smoothly across the screen.
- **PINCH_CLICK (Thumb + Index pinch):** Performs a Left Click.
- **PINCH_RIGHT_CLICK (Thumb + Middle pinch):** Performs a Right Click.

### Scrolling & Browser Navigation
- **TWO_FINGERS (Index & Middle up):** 
  - **Move UP / DOWN:** Scroll the current page up or down.
  - **Swipe LEFT:** Go to the Previous Browser Tab (`Ctrl + Shift + Tab`).
  - **Swipe RIGHT:** Go to the Next Browser Tab (`Ctrl + Tab`).
- **DISLIKE (Thumb down):** Go back in browser history (`Alt + Left`).
- **CALL (Thumb & Pinky out):** Go forward in browser history (`Alt + Right`).

### Window & Desktop Management
- **THREE_FINGERS (Index, Middle, Ring up):** Switch active window (`Alt + Tab`).
- **FOUR_FINGERS (Index, Middle, Ring, Pinky up):** Maximize current window (`Win + Up`).
- **STOP (Open palm facing camera):** Close the active window (`Alt + F4`).
- **OPEN_PALM:** 
  - **Hold still for 1 second:** Show Desktop (`Win + D`).
  - **Swipe LEFT / RIGHT:** Switch Virtual Desktops (`Ctrl + Win + Left/Right`).

### Media Controls
- **THUMBS_UP:** Increase Volume.
- **PINKY:** Decrease Volume.
- **GUN (Thumb + Index up, others closed):** Mute / Unmute Audio.
- **ROCK (Index + Pinky up):** Play / Pause Media.

### Safe Pose
- **FIST:** Safe idle pose. The system stops interacting with the PC, allowing you to freely move your hand without triggering accidental commands.

## Sleep Mode (Wake-on-Motion)

If no hand is detected in the frame for **2 seconds** (and the system is in `HAND` tracking mode), the application intelligently enters **Sleep Mode**. 
During Sleep Mode, the app displays "SLEEPING (Move to wake)". To wake up the app, simply wave or introduce significant movement in front of the camera.

## Customization

You can tweak the behavior of the application by editing `config.py`. Key properties you might want to adjust include:

- `TRACKING_MODE`: Switch between `"HAND"` (default) and `"EYE"`.
- `SMOOTHENING`: Higher values make the mouse movement smoother but introduce slight lag.
- `PINCH_THRESHOLD`: Adjust how close fingers must be to register a pinch.
- `SCROLL_MULTIPLIER`: Change how fast page scrolling occurs.
- `SWIPE_PIXEL_THRESHOLD` & `SWIPE_TIME_WINDOW`: Tune horizontal swipe sensitivity for changing tabs and virtual desktops.

## Project Structure

- `main.py`: The entry point that captures video, runs the state machine, and renders the UI.
- `controller.py`: The OS-level interface executing commands via `pyautogui` and `screen-brightness-control`.
- `config.py`: The configuration file containing thresholds, modes, and mappings.
- `hand_tracker.py` & `eye_tracker.py` (assumed): Contain logic to encapsulate MediaPipe's tracking features.
- `ml_gesture_recognizer.py` (assumed): Uses scikit-learn to classify the landmarks into explicit gestures.

---
Enjoy a hands-free, sci-fi PC experience!
