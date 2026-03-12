import cv2
import numpy as np
import base64
import os


MEDIAPIPE_AVAILABLE = False
face_mesh_instance = None
face_detector_instance = None

try:
    import mediapipe as mp

    if hasattr(mp, 'solutions') and hasattr(mp.solutions, 'face_mesh'):
        # Use max_num_faces=2 so we can detect if there's more than one person
        face_mesh_instance = mp.solutions.face_mesh.FaceMesh(
            max_num_faces=2,
            refine_landmarks=True,
            min_detection_confidence=0.6,
            min_tracking_confidence=0.6
        )
        MEDIAPIPE_AVAILABLE = True
        print("Eye tracking: Using MediaPipe legacy FaceMesh API")

    # Also try to load face detection for accurate multi-face counting
    if hasattr(mp, 'solutions') and hasattr(mp.solutions, 'face_detection'):
        face_detector_instance = mp.solutions.face_detection.FaceDetection(
            model_selection=0,
            min_detection_confidence=0.5
        )
        print("Eye tracking: MediaPipe FaceDetection also available")
except Exception as e:
    print(f"MediaPipe FaceMesh not available: {e}")

if not MEDIAPIPE_AVAILABLE:
    print("Eye tracking: Falling back to OpenCV Haar Cascade face/eye detection")

# Warning type constants
WARNING_NO_FACE = "Face not detected"
WARNING_MULTIPLE_FACES = "There is someone else"
WARNING_NOT_FOCUSED = "Focus on the display"


class EyeTrackingService:
    def __init__(self):
        self.face_mesh = face_mesh_instance
        self.face_detector = face_detector_instance
        self.use_mediapipe = MEDIAPIPE_AVAILABLE

        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
        self.eye_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_eye.xml'
        )

    def analyze(self, base64_image):
        try:
            if ',' in base64_image:
                base64_image = base64_image.split(',')[1]

            img_bytes = base64.b64decode(base64_image)
            nparr = np.frombuffer(img_bytes, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            if frame is None:
                return {"looking_at_screen": True, "warning": None, "warning_type": None}

            if self.use_mediapipe and self.face_mesh:
                return self._analyze_mediapipe(frame)
            else:
                return self._analyze_opencv(frame)

        except Exception as e:
            print(f"Eye Tracking Error: {e}")
            return {"looking_at_screen": True, "warning": None, "warning_type": None}

    def _count_faces_detector(self, frame):
        """Use MediaPipe FaceDetection for accurate face counting."""
        if not self.face_detector:
            return None
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.face_detector.process(rgb)
        if results.detections:
            return len(results.detections)
        return 0

    def _analyze_mediapipe(self, frame):
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.face_mesh.process(rgb_frame)

        if not results.multi_face_landmarks:
            return {
                "looking_at_screen": False,
                "warning": WARNING_NO_FACE,
                "warning_type": "no_face"
            }

        # Check for multiple faces
        face_count = len(results.multi_face_landmarks)

        # Also cross-check with face detector if available for better accuracy
        detector_count = self._count_faces_detector(frame)
        if detector_count is not None and detector_count > 1:
            face_count = max(face_count, detector_count)

        if face_count > 1:
            return {
                "looking_at_screen": False,
                "warning": WARNING_MULTIPLE_FACES,
                "warning_type": "multiple_faces"
            }

        landmarks = results.multi_face_landmarks[0].landmark

        # Iris landmarks (from refine_landmarks=True)
        left_iris = landmarks[468]
        right_iris = landmarks[473]

        # Eye corner landmarks
        left_eye_outer = landmarks[33]
        left_eye_inner = landmarks[133]
        right_eye_inner = landmarks[362]
        right_eye_outer = landmarks[263]

        # Eye top/bottom for vertical ratio
        left_eye_top = landmarks[159]
        left_eye_bottom = landmarks[145]
        right_eye_top = landmarks[386]
        right_eye_bottom = landmarks[374]

        # Head pose landmarks
        nose_tip = landmarks[1]
        chin = landmarks[152]
        forehead = landmarks[10]
        left_cheek = landmarks[234]
        right_cheek = landmarks[454]

        left_eye_width = left_eye_inner.x - left_eye_outer.x
        right_eye_width = right_eye_outer.x - right_eye_inner.x

        if left_eye_width > 0.001 and right_eye_width > 0.001:
            # Horizontal gaze ratio
            left_h_ratio = (left_iris.x - left_eye_outer.x) / left_eye_width
            right_h_ratio = (right_iris.x - right_eye_inner.x) / right_eye_width
            avg_h_ratio = (left_h_ratio + right_h_ratio) / 2

            # Vertical gaze ratio (average both eyes)
            left_eye_height = left_eye_bottom.y - left_eye_top.y
            right_eye_height = right_eye_bottom.y - right_eye_top.y
            left_v_ratio = (left_iris.y - left_eye_top.y) / left_eye_height if left_eye_height > 0.001 else 0.5
            right_v_ratio = (right_iris.y - right_eye_top.y) / right_eye_height if right_eye_height > 0.001 else 0.5
            avg_v_ratio = (left_v_ratio + right_v_ratio) / 2

            # Head orientation check
            head_h_centered = 0.25 < nose_tip.x < 0.75
            head_v_centered = 0.15 < nose_tip.y < 0.85

            # Head turn detection: if face is significantly asymmetric
            face_width = right_cheek.x - left_cheek.x
            nose_offset = (nose_tip.x - left_cheek.x) / face_width if face_width > 0.01 else 0.5
            head_turned = nose_offset < 0.30 or nose_offset > 0.70

            # Tighter gaze thresholds for better accuracy
            h_centered = 0.20 < avg_h_ratio < 0.80
            v_centered = 0.15 < avg_v_ratio < 0.85

            if head_turned:
                return {
                    "looking_at_screen": False,
                    "warning": WARNING_NOT_FOCUSED,
                    "warning_type": "not_focused"
                }

            if h_centered and v_centered and head_h_centered and head_v_centered:
                return {"looking_at_screen": True, "warning": None, "warning_type": None}
            else:
                return {
                    "looking_at_screen": False,
                    "warning": WARNING_NOT_FOCUSED,
                    "warning_type": "not_focused"
                }

        return {
            "looking_at_screen": False,
            "warning": WARNING_NO_FACE,
            "warning_type": "no_face"
        }

    def _analyze_opencv(self, frame):
        h, w, _ = frame.shape
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        # Histogram equalization for better detection in varied lighting
        gray = cv2.equalizeHist(gray)

        faces = self.face_cascade.detectMultiScale(
            gray, scaleFactor=1.2, minNeighbors=6, minSize=(80, 80)
        )

        if len(faces) == 0:
            return {
                "looking_at_screen": False,
                "warning": WARNING_NO_FACE,
                "warning_type": "no_face"
            }

        if len(faces) > 1:
            return {
                "looking_at_screen": False,
                "warning": WARNING_MULTIPLE_FACES,
                "warning_type": "multiple_faces"
            }

        face = max(faces, key=lambda f: f[2] * f[3])
        fx, fy, fw, fh = face

        face_center_x = (fx + fw / 2) / w
        face_center_y = (fy + fh / 2) / h

        if not (0.15 < face_center_x < 0.85 and 0.1 < face_center_y < 0.9):
            return {
                "looking_at_screen": False,
                "warning": WARNING_NOT_FOCUSED,
                "warning_type": "not_focused"
            }

        face_roi = gray[fy:fy + fh, fx:fx + fw]
        eyes = self.eye_cascade.detectMultiScale(face_roi, 1.1, 4, minSize=(25, 25))

        if len(eyes) == 0:
            return {
                "looking_at_screen": False,
                "warning": WARNING_NOT_FOCUSED,
                "warning_type": "not_focused"
            }

        return {"looking_at_screen": True, "warning": None, "warning_type": None}
