import json
import joblib
import numpy as np
import os
import math
import collections

# Import the original recognizer to inherit geometric fallbacks
from gesture_recognizer import GestureRecognizer

class MLGestureRecognizer(GestureRecognizer):
    def __init__(self, model_path="gesture_rf_model.pkl", map_path="gesture_label_map.json", smoothing_window=7):
        super().__init__()
        
        self.rf_model = None
        self.label_map = []
        self.smoothing_window = smoothing_window
        self.history = collections.defaultdict(lambda: collections.deque(maxlen=smoothing_window))
        
        if os.path.exists(model_path) and os.path.exists(map_path):
            print(f"Loading ML gesture model from {model_path}...")
            self.rf_model = joblib.load(model_path)
            with open(map_path, "r") as f:
                self.label_map = json.load(f)
        else:
            print(f"Warning: {model_path} or {map_path} not found. ML predictions will fail.")
            
    def _normalize_landmarks(self, landmark_list):
        if not landmark_list or len(landmark_list) < 21:
            return None
            
        xs = [pt[1] for pt in landmark_list]
        ys = [pt[2] for pt in landmark_list]
        
        wrist_x, wrist_y = xs[0], ys[0]
        
        xs = [x - wrist_x for x in xs]
        ys = [y - wrist_y for y in ys]
        
        max_dist = max(math.hypot(x, y) for x, y in zip(xs, ys))
        if max_dist == 0:
            return None
            
        features = []
        for x, y in zip(xs, ys):
            features.extend([x / max_dist, y / max_dist])
            
        return features
            
    def classify(self, landmark_list, handedness="Right", pinch_threshold=35, thumb_sens=10, finger_sens=0):
        """
        Returns a tuple: (gesture_label, fingers_array)
        Uses ML for general gestures, and geometric rules for PINCH and PINKY.
        """
        if not landmark_list:
            if handedness in self.history:
                self.history[handedness].clear()
            return "NONE", [0, 0, 0, 0, 0]

        # Calculate geometric fingers state for the fallbacks and debugging output
        fingers = self.fingers_up(landmark_list, handedness, thumb_sens, finger_sens)
        # Calculate hand size for scaling
        hand_size = self.distance(landmark_list, 0, 9)
        if hand_size == 0: hand_size = 1.0
        scaled_pinch = pinch_threshold * (hand_size / 100.0)
        
        lm = {idx: (x, y) for idx, x, y, z in landmark_list}
        
        raw_pred = "UNKNOWN"
        
        # 1. FIST FALLBACK (geometric) - FIST is the safe state. 
        # Must evaluate before PINCH because in a fist, thumb and index are close together.
        if sum(fingers) == 0:
            raw_pred = "FIST"
            
        # 2. PINCH FALLBACKS (geometric) - Requires precise finger distance
        # Thumb + Index
        elif self.distance(landmark_list, 4, 8) < scaled_pinch:
            raw_pred = "PINCH_CLICK"
            
        # Thumb + Middle
        elif self.distance(landmark_list, 4, 12) < scaled_pinch:
            raw_pred = "PINCH_RIGHT_CLICK"
            
        # 3. PINKY FALLBACK (geometric) - Not in HaGRID
        elif fingers == [0, 0, 0, 0, 1]:
            raw_pred = "PINKY"
            
        # 4. POINT FALLBACK (geometric) - Extremely rigid for stability, but thumb is ignored
        elif fingers[1:] == [1, 0, 0, 0]:
            raw_pred = "POINT"
            
        # 5. OPEN PALM FALLBACK (geometric) - Extremely rigid, no need for ML
        elif sum(fingers) == 5:
            raw_pred = "OPEN_PALM"
            
        # 6. ML PREDICTION
        elif self.rf_model is not None:
            features = self._normalize_landmarks(landmark_list)
            if features is not None:
                # Scikit-learn expects 2D array
                X = np.array([features], dtype=np.float32)
                # Get probability distribution instead of just the top prediction
                probas = self.rf_model.predict_proba(X)[0]
                pred_idx = np.argmax(probas)
                confidence = probas[pred_idx]
                
                # Check for valid prediction index and reasonable confidence
                if 0 <= pred_idx < len(self.label_map) and confidence >= 0.35:
                    raw_pred = self.label_map[pred_idx]
                else:
                    raw_pred = "UNKNOWN"
                    
        # Apply Temporal Smoothing
        self.history[handedness].append(raw_pred)
        counter = collections.Counter(self.history[handedness])
        smoothed_pred = counter.most_common(1)[0][0]

        return smoothed_pred, fingers
