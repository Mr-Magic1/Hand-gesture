"""
gesture_recognizer.py
Turns a 21-point landmark list into a named gesture using simple,
explainable geometric rules (finger-up/down state + fingertip distances).
No ML model needed - fast and easy to tune.
"""

import math


class GestureRecognizer:
    TIP_IDS = [4, 8, 12, 16, 20]  # thumb, index, middle, ring, pinky

    def fingers_up(self, landmark_list, handedness="Right", thumb_sens=10, finger_sens=0):
        """Returns [thumb, index, middle, ring, pinky] as 1 (up) / 0 (down)."""
        if not landmark_list or len(landmark_list) < 21:
            return [0, 0, 0, 0, 0]

        # Calculate a reference scale: distance from wrist (0) to middle finger base (9)
        hand_size = self.distance(landmark_list, 0, 9)
        if hand_size == 0: hand_size = 1.0
        
        # Scale the sensitivities based on a "standard" 100px hand
        scale = hand_size / 100.0
        scaled_thumb_sens = thumb_sens * scale
        scaled_finger_sens = finger_sens * scale
        scaled_tuck_dist = 80 * scale

        lm = {idx: (x, y) for idx, x, y, z in landmark_list}
        fingers = []

        tip_x, tip_y = lm[4]
        joint_x, joint_y = lm[3]
        pinky_base_x, pinky_base_y = lm[17]
        
        dist_to_pinky = math.hypot(tip_x - pinky_base_x, tip_y - pinky_base_y)
        
        is_thumb_out = False
        if handedness == "Right":
            is_thumb_out = tip_x > joint_x + scaled_thumb_sens
        else:
            is_thumb_out = tip_x < joint_x - scaled_thumb_sens
            
        # Only count as up if it's out and not tucked into the palm
        fingers.append(1 if (is_thumb_out and dist_to_pinky > scaled_tuck_dist) else 0)

        # Other four fingers: tip above (smaller y) its PIP joint => up
        for tip_id in self.TIP_IDS[1:]:
            fingers.append(1 if lm[tip_id][1] < lm[tip_id - 2][1] - scaled_finger_sens else 0)

        return fingers

    def distance(self, landmark_list, id1, id2):
        lm = {idx: (x, y) for idx, x, y, z in landmark_list}
        x1, y1 = lm[id1]
        x2, y2 = lm[id2]
        return math.hypot(x2 - x1, y2 - y1)

    def _is_thumb_pointing_up(self, landmark_list):
        lm = {idx: (x, y) for idx, x, y, z in landmark_list}
        return lm[4][1] < lm[0][1] - 40  # tip well above wrist

    def classify(self, landmark_list, handedness="Right", pinch_threshold=35, thumb_sens=10, finger_sens=0):
        """Returns a tuple: (gesture_label, fingers_array)"""
        if not landmark_list:
            return "NONE", [0, 0, 0, 0, 0]

        fingers = self.fingers_up(landmark_list, handedness, thumb_sens, finger_sens)
        total = sum(fingers)

        # Pinches take priority
        if self.distance(landmark_list, 4, 8) < pinch_threshold:
            return "PINCH_CLICK", fingers
        if self.distance(landmark_list, 4, 12) < pinch_threshold:
            return "PINCH_RIGHT_CLICK", fingers

        if total == 0:
            return "FIST", fingers
        if fingers == [0, 1, 0, 0, 0]:
            return "POINT", fingers
        if fingers == [0, 1, 1, 0, 0]:
            return "TWO_FINGERS", fingers
        if fingers == [0, 1, 1, 1, 0]:
            return "THREE_FINGERS", fingers
        if fingers == [0, 0, 0, 0, 1]:
            return "PINKY", fingers
        if fingers == [1, 1, 0, 0, 1]:
            return "ROCK", fingers
        if fingers == [1, 1, 0, 0, 0]:
            return "GUN", fingers
        if fingers == [1, 0, 0, 0, 0]:
            gesture = "THUMBS_UP" if self._is_thumb_pointing_up(landmark_list) else "THUMB_SIDE"
            return gesture, fingers
        if total == 5:
            return "OPEN_PALM", fingers

        return "UNKNOWN", fingers
