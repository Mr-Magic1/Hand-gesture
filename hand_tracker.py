"""
hand_tracker.py
Thin wrapper around MediaPipe's Hands solution.
Handles frame processing, landmark drawing, and landmark extraction.
"""

import cv2
import mediapipe as mp


class HandTracker:
    def __init__(self, max_hands=1, detection_conf=0.7, tracking_conf=0.7):
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=max_hands,
            min_detection_confidence=detection_conf,
            min_tracking_confidence=tracking_conf,
        )
        self.mp_draw = mp.solutions.drawing_utils
        self.mp_styles = mp.solutions.drawing_styles
        self.results = None

    def find_hands(self, frame, draw=True):
        """Runs detection on a BGR frame and optionally draws landmarks on it."""
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        rgb.flags.writeable = False
        self.results = self.hands.process(rgb)

        if draw and self.results.multi_hand_landmarks:
            for hand_landmarks in self.results.multi_hand_landmarks:
                self.mp_draw.draw_landmarks(
                    frame,
                    hand_landmarks,
                    self.mp_hands.HAND_CONNECTIONS,
                    self.mp_styles.get_default_hand_landmarks_style(),
                    self.mp_styles.get_default_hand_connections_style(),
                )
        return frame

    def get_landmark_list(self, frame, hand_index=0):
        """Returns [(id, x_px, y_px, z), ...] for the requested hand, or []."""
        landmark_list = []
        if self.results and self.results.multi_hand_landmarks:
            if hand_index >= len(self.results.multi_hand_landmarks):
                return landmark_list
            hand = self.results.multi_hand_landmarks[hand_index]
            h, w, _ = frame.shape
            for idx, lm in enumerate(hand.landmark):
                landmark_list.append((idx, int(lm.x * w), int(lm.y * h), lm.z))
        return landmark_list

    def get_handedness(self, hand_index=0):
        """Returns 'Left' or 'Right' (as seen by the camera) or None."""
        if self.results and self.results.multi_handedness:
            if hand_index < len(self.results.multi_handedness):
                return self.results.multi_handedness[hand_index].classification[0].label
        return None
