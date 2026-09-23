"""
main.py
Entry point: opens the webcam, runs hand detection + gesture classification
every frame, and dispatches the recognized gesture to PCController.
"""

import time
import cv2

from hand_tracker import HandTracker
from ml_gesture_recognizer import MLGestureRecognizer
from controller import PCController
from eye_tracker import EyeTracker
import config


def main():
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.CAM_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.CAM_HEIGHT)

    tracker = HandTracker(max_hands=1)
    recognizer = MLGestureRecognizer()
    eye_tracker = EyeTracker()
    controller = PCController(
        smoothening=config.SMOOTHENING,
        frame_reduction=config.FRAME_REDUCTION,
        cam_w=config.CAM_WIDTH,
        cam_h=config.CAM_HEIGHT,
    )

    prev_scroll_y = None

    # Open-palm swipe / hold-to-show-desktop state
    palm_history   = []   # list of (timestamp, x_px)
    open_palm_start = None
    last_swipe_time = 0

    # Two-finger swipe state (tab switching)
    two_finger_history = []
    last_tab_swipe_time = 0

    # Three-finger swipe state (waving)
    # (Removed dynamic waving, keeping only static alt+tab)

    # Eye tracking state
    last_blink_time = 0

    # Wake-on-Motion state
    prev_gray = None
    last_hand_time = time.time()
    is_sleeping = False

    prev_frame_time = 0
    running = True

    print("Hand Gesture PC Control started.")
    print("Press 'q' to quit, 'p' to pause/resume.")

    while True:
        success, frame = cap.read()
        if not success:
            print("Could not read from webcam.")
            break

        frame = cv2.flip(frame, 1)  # mirror for natural interaction
        
        # --- Wake-on-Motion Logic ---
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21, 21), 0)
        
        motion_detected = False
        if prev_gray is not None:
            diff = cv2.absdiff(prev_gray, gray)
            thresh = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)[1]
            motion_pixels = cv2.countNonZero(thresh)
            if motion_pixels > 500:  # arbitrary threshold for movement
                motion_detected = True
        prev_gray = gray
        
        now = time.time()
        
        if motion_detected:
            is_sleeping = False
        elif now - last_hand_time > 2.0 and getattr(config, "TRACKING_MODE", "HAND") == "HAND":
            is_sleeping = True
            
        if is_sleeping:
            cv2.putText(frame, "SLEEPING (Move to wake)", (10, 80), cv2.FONT_HERSHEY_PLAIN, 1.5, (0, 0, 255), 2)
            cv2.imshow("Hand Gesture PC Control", frame)
            
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            continue
        # ----------------------------
        
        # --- Eye Tracking Mode ---
        mode = getattr(config, "TRACKING_MODE", "HAND")
        if mode == "EYE":
            results = eye_tracker.find_face_and_eyes(frame)
            frame = eye_tracker.draw_eye_markers(frame, results)
            
            ratios = eye_tracker.get_gaze_ratio(frame, results)
            if ratios is not None:
                x_ratio, y_ratio = ratios
                # Map ratios back to camera coordinates so controller can map them to screen
                cam_x = x_ratio * config.CAM_WIDTH
                cam_y = y_ratio * config.CAM_HEIGHT
                controller.move_mouse(cam_x, cam_y)
                
                if eye_tracker.is_blinking(frame, results):
                    if now - last_blink_time > 0.5:
                        controller.left_click()
                        print("Blink -> Left Click")
                        last_blink_time = now
                        
            cv2.putText(frame, "EYE TRACKING MODE", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 255), 2)
            cv2.imshow("Hand Gesture PC Control", frame)
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            continue
        # -------------------------
        # -------------------------
        frame = tracker.find_hands(frame)
        landmark_list = tracker.get_landmark_list(frame)
        handedness = tracker.get_handedness() or "Right"

        gesture = "NONE"
        fingers = [0, 0, 0, 0, 0]
        if landmark_list:
            last_hand_time = now
        gesture, fingers = recognizer.classify(
            landmark_list, 
            handedness, 
            config.PINCH_THRESHOLD,
            getattr(config, "THUMB_SENSITIVITY", 10),
            getattr(config, "FINGER_SENSITIVITY", 0)
        )

        if running and landmark_list:
            if gesture == "POINT":
                x, y = landmark_list[8][1], landmark_list[8][2]
                controller.move_mouse(x, y)
                prev_scroll_y = None
                open_palm_start, palm_history = None, []

            elif gesture == "PINCH_CLICK":
                controller.left_click()
                prev_scroll_y = None
                open_palm_start, palm_history = None, []

            elif gesture == "PINCH_RIGHT_CLICK":
                controller.right_click()
                prev_scroll_y = None
                open_palm_start, palm_history = None, []

            elif gesture == "TWO_FINGERS":
                now = time.time()
                x = landmark_list[8][1]
                y = landmark_list[8][2]

                # Track position history for swipe detection
                two_finger_history.append((now, x, y))
                two_finger_history = [
                    p for p in two_finger_history
                    if now - p[0] < config.SWIPE_TIME_WINDOW
                ]

                # Detect horizontal swipe -> tab switching
                if len(two_finger_history) >= 2 and now - last_tab_swipe_time > 0.8:
                    dx = two_finger_history[-1][1] - two_finger_history[0][1]
                    dy = two_finger_history[-1][2] - two_finger_history[0][2]
                    
                    hand_size = recognizer.distance(landmark_list, 0, 9)
                    scaled_swipe = config.SWIPE_PIXEL_THRESHOLD * (max(hand_size, 1) / 100.0)
                    
                    # Only trigger swipe if horizontal motion dominates vertical
                    if abs(dx) > scaled_swipe and abs(dx) > abs(dy) * 1.5:
                        if dx > 0:
                            controller.next_tab()
                            print("Swipe RIGHT -> Next Tab")
                        else:
                            controller.prev_tab()
                            print("Swipe LEFT -> Previous Tab")
                        last_tab_swipe_time = now
                        two_finger_history = []
                    elif abs(dy) > 5 and abs(dy) >= abs(dx):  # vertical -> scroll
                        delta = prev_scroll_y - y if prev_scroll_y is not None else 0
                        if abs(delta) > 5:
                            scroll_mult = getattr(config, "SCROLL_MULTIPLIER", 15)
                            controller.scroll(delta * scroll_mult)

                prev_scroll_y = y
                open_palm_start, palm_history = None, []

            elif gesture == "THREE_FINGERS":
                controller.switch_window()
                prev_scroll_y = None
                two_finger_history = []
                open_palm_start, palm_history = None, []
                
            elif gesture == "DISLIKE":
                controller.browser_back()
                print("DISLIKE -> Browser Back")
                prev_scroll_y = None
                two_finger_history = []
                open_palm_start, palm_history = None, []
                
            elif gesture == "CALL":
                controller.browser_forward()
                print("CALL -> Browser Forward")
                prev_scroll_y = None
                two_finger_history = []
                open_palm_start, palm_history = None, []

            elif gesture == "FOUR_FINGERS":
                controller.maximize_window()
                print("FOUR_FINGERS -> Maximize Window")
                prev_scroll_y = None
                two_finger_history = []
                open_palm_start, palm_history = None, []

            elif gesture == "STOP":
                controller.close_window()
                print("STOP -> Close Window")
                prev_scroll_y = None
                two_finger_history = []
                open_palm_start, palm_history = None, []

            elif gesture == "THUMBS_UP":
                controller.volume_up()
                prev_scroll_y = None
                two_finger_history = []

            elif gesture == "PINKY":
                controller.volume_down()
                prev_scroll_y = None
                two_finger_history = []

            elif gesture == "GUN":
                controller.mute()
                prev_scroll_y = None
                two_finger_history = []

            elif gesture == "ROCK":
                controller.play_pause()
                prev_scroll_y = None
                two_finger_history = []

            elif gesture == "OPEN_PALM":
                prev_scroll_y = None
                cx = landmark_list[9][1]  # middle-finger MCP as palm-center x
                now = time.time()
                
                # -1 means the action already triggered; wait until gesture changes to reset
                if open_palm_start is None:
                    open_palm_start = now
                    
                palm_history.append((now, cx))
                palm_history = [p for p in palm_history if now - p[0] < config.SWIPE_TIME_WINDOW]

                if len(palm_history) >= 2:
                    dx = palm_history[-1][1] - palm_history[0][1]
                    
                    hand_size = recognizer.distance(landmark_list, 0, 9)
                    scaled_swipe = config.SWIPE_PIXEL_THRESHOLD * (max(hand_size, 1) / 100.0)
                    
                    # If there is a large horizontal swipe, trigger virtual desktop switch
                    if abs(dx) > scaled_swipe and now - last_swipe_time > 1.0:
                        if dx > 0:
                            controller.switch_desktop_right()
                        else:
                            controller.switch_desktop_left()
                        last_swipe_time = now
                        open_palm_start = None  # Reset hold timer since they swiped
                        palm_history = []
                
                # If they held their hand still (open_palm_start wasn't reset by a swipe)
                if open_palm_start != -1 and open_palm_start is not None and now - open_palm_start > config.OPEN_PALM_HOLD_TIME:
                    controller.show_desktop()
                    open_palm_start = -1  # Reset so it doesn't spam Win+D
                    palm_history = []

            else:  # FIST, UNKNOWN, etc. -> idle
                prev_scroll_y = None
                two_finger_history = []
                open_palm_start, palm_history = None, []


        # ---- HUD overlay ----
        now = time.time()
        fps = 1 / (now - prev_frame_time) if prev_frame_time else 0
        prev_frame_time = now

        cv2.putText(frame, f"FPS: {int(fps)}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        status = "RUNNING" if running else "PAUSED"
        color = (0, 200, 0) if running else (0, 0, 255)
        cv2.putText(frame, status, (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
        
        # Display each hand's status
        cv2.putText(frame, f"Gesture: {gesture} {fingers}", (10, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 100, 255), 2)

        cv2.imshow("Hand Gesture PC Control", frame)
        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            break
        elif key == ord("p"):
            running = not running

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
