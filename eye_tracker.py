import cv2
import mediapipe as mp
import math

class EyeTracker:
    def __init__(self):
        self.mp_face_mesh = mp.solutions.face_mesh
        # refine_landmarks=True gives us the 468-477 iris landmarks
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        self.mp_draw = mp.solutions.drawing_utils
        
        # Landmark Indices for the Right Eye (from the camera's perspective, this is the user's left eye)
        self.EYE_LEFT_CORNER = 33
        self.EYE_RIGHT_CORNER = 133
        self.EYE_TOP = 159
        self.EYE_BOTTOM = 145
        self.IRIS_CENTER = 468  # 468 is the center of the right eye iris (camera left)
        
    def find_face_and_eyes(self, frame):
        """Processes the frame and returns the raw results."""
        img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.face_mesh.process(img_rgb)
        return results

    def get_gaze_ratio(self, frame, results):
        """
        Returns (x_ratio, y_ratio) indicating where the user is looking.
        Values typically range from 0.0 to 1.0.
        """
        if not results.multi_face_landmarks:
            return None
            
        landmarks = results.multi_face_landmarks[0].landmark
        
        iris = landmarks[self.IRIS_CENTER]
        left = landmarks[self.EYE_LEFT_CORNER]
        right = landmarks[self.EYE_RIGHT_CORNER]
        top = landmarks[self.EYE_TOP]
        bottom = landmarks[self.EYE_BOTTOM]
        
        # Calculate horizontal ratio (0.0 = looking left, 1.0 = looking right)
        eye_width = abs(right.x - left.x)
        if eye_width == 0: return None
        x_ratio = (iris.x - left.x) / eye_width
        
        # Calculate vertical ratio (0.0 = looking up, 1.0 = looking down)
        eye_height = abs(bottom.y - top.y)
        if eye_height == 0: return None
        y_ratio = (iris.y - top.y) / eye_height
        
        return (x_ratio, y_ratio)
        
    def is_blinking(self, frame, results, threshold=0.18):
        """
        Calculates Eye Aspect Ratio (EAR). Returns True if blinking.
        """
        if not results.multi_face_landmarks:
            return False
            
        landmarks = results.multi_face_landmarks[0].landmark
        
        left = landmarks[self.EYE_LEFT_CORNER]
        right = landmarks[self.EYE_RIGHT_CORNER]
        top = landmarks[self.EYE_TOP]
        bottom = landmarks[self.EYE_BOTTOM]
        
        # EAR = vertical_dist / horizontal_dist
        vert_dist = math.hypot(top.x - bottom.x, top.y - bottom.y)
        horz_dist = math.hypot(right.x - left.x, right.y - left.y)
        
        if horz_dist == 0:
            return False
            
        ear = vert_dist / horz_dist
        
        return ear < threshold

    def draw_eye_markers(self, frame, results):
        """Draws visual markers around the eye and iris for debugging."""
        if not results.multi_face_landmarks:
            return frame
            
        landmarks = results.multi_face_landmarks[0].landmark
        h, w, _ = frame.shape
        
        # Draw Iris
        iris_x = int(landmarks[self.IRIS_CENTER].x * w)
        iris_y = int(landmarks[self.IRIS_CENTER].y * h)
        cv2.circle(frame, (iris_x, iris_y), 3, (0, 255, 0), -1)
        
        # Draw Eye Bounding Box
        pts = [self.EYE_LEFT_CORNER, self.EYE_TOP, self.EYE_RIGHT_CORNER, self.EYE_BOTTOM]
        for p in pts:
            px = int(landmarks[p].x * w)
            py = int(landmarks[p].y * h)
            cv2.circle(frame, (px, py), 2, (0, 0, 255), -1)
            
        return frame
