"""
config.py
Central place to tune camera settings, smoothing, and gesture->action mapping.
Edit this file to remap gestures without touching main.py logic.
"""

CAM_WIDTH = 640
CAM_HEIGHT = 480

TRACKING_MODE = "HAND"    # Set to "HAND" or "EYE" to switch between hand and eye control.

FRAME_REDUCTION = 130     # inner "active" rectangle margin (px) for cursor mapping
SMOOTHENING = 20          # higher = smoother but more laggy cursor movement

# --- GESTURE SENSITIVITY TUNING ---
PINCH_THRESHOLD = 40      # px distance between thumb/finger tip to count as a pinch. Increase if pinches aren't registering.
THUMB_SENSITIVITY = 0     # px distance thumb must be extended past joint to count as "up". Increase if thumb triggers accidentally.
FINGER_SENSITIVITY = 0    # px distance finger tip must be above PIP joint. Increase to require fingers to be straighter.

SWIPE_PIXEL_THRESHOLD = 60    # min horizontal palm movement (px) to count as a swipe
SWIPE_TIME_WINDOW = 0.5       # seconds - swipe must happen within this window
OPEN_PALM_HOLD_TIME = 1.0     # seconds - holding palm still this long triggers "show desktop"

SCROLL_MULTIPLIER = 15        # Multiply hand movement by this amount for faster scrolling

# Human-readable reference only (main.py wires these explicitly);
# edit this table first if you want to remember / redesign the mapping.
GESTURE_ACTIONS = {
    "POINT":              "Move mouse cursor (index finger only)",
    "PINCH_CLICK":        "Left click (thumb + index pinch)",
    "PINCH_RIGHT_CLICK":  "Right click (thumb + middle pinch)",
    "TWO_FINGERS":        "Scroll UP/DOWN | Swipe LEFT=Prev Tab | Swipe RIGHT=Next Tab",
    "THREE_FINGERS":      "Switch window (Alt+Tab)",
    "OPEN_PALM":          "Hold 1s=Show desktop | Swipe left/right=Switch virtual desktop",
    "FIST":               "Idle / no action (safe pose)",
    "THUMBS_UP":          "Volume up",
    "PINKY":              "Volume down",
    "GUN":                "Mute / unmute audio",
    "ROCK":               "Play / pause media",
    "DISLIKE":            "Go back in browser (Browser Back)",
    "CALL":               "Go forward in browser (Browser Forward)",
    "FOUR_FINGERS":       "Maximize window (Win+Up)",
    "STOP":               "Close window (Alt+F4)",
    "NONE":               "Idle for 2 seconds -> Enters Wake-on-Motion Sleep Mode"
}
