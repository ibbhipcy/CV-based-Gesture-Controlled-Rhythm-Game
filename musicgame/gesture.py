import cv2
import mediapipe as mp
import math
import numpy as np
import pygame

def calculate_angle(p1, p2, p3):
    v1 = [p1.x - p2.x, p1.y - p2.y]
    v2 = [p3.x - p2.x, p3.y - p2.y]
    dot_product = v1[0] * v2[0] + v1[1] * v2[1]
    magnitude_v1 = math.sqrt(v1[0] ** 2 + v1[1] ** 2)
    magnitude_v2 = math.sqrt(v2[0] ** 2 + v2[1] ** 2)
    if magnitude_v1 * magnitude_v2 == 0:
        return 0
    cos_angle = dot_product / (magnitude_v1 * magnitude_v2)
    cos_angle = max(-1, min(1, cos_angle))
    return math.degrees(math.acos(cos_angle))

def is_finger_extended(landmarks, finger_tip_idx, finger_pip_idx, finger_mcp_idx):
    angle = calculate_angle(landmarks[finger_mcp_idx], landmarks[finger_pip_idx], landmarks[finger_tip_idx])
    tip_mcp_dist = math.sqrt((landmarks[finger_tip_idx].x - landmarks[finger_mcp_idx].x) ** 2 +
                            (landmarks[finger_tip_idx].y - landmarks[finger_mcp_idx].y) ** 2)
    pip_mcp_dist = math.sqrt((landmarks[finger_pip_idx].x - landmarks[finger_mcp_idx].x) ** 2 +
                            (landmarks[finger_pip_idx].y - landmarks[finger_mcp_idx].y) ** 2)
    is_straight = angle > 160
    is_extended_dist = tip_mcp_dist > pip_mcp_dist * 1.2
    return is_straight and is_extended_dist

def is_thumb_extended(landmarks, thumb_tip_idx, thumb_ip_idx, thumb_mcp_idx):
    angle = calculate_angle(landmarks[thumb_mcp_idx], landmarks[thumb_ip_idx], landmarks[thumb_tip_idx])
    tip_mcp_dist = math.sqrt((landmarks[thumb_tip_idx].x - landmarks[thumb_mcp_idx].x) ** 2 +
                            (landmarks[thumb_tip_idx].y - landmarks[thumb_mcp_idx].y) ** 2)
    ip_mcp_dist = math.sqrt((landmarks[thumb_ip_idx].x - landmarks[thumb_mcp_idx].x) ** 2 +
                            (landmarks[thumb_ip_idx].y - landmarks[thumb_mcp_idx].y) ** 2)
    index_mcp = landmarks[5]
    tip_index_mcp_dist = math.sqrt((landmarks[thumb_tip_idx].x - index_mcp.x) ** 2 +
                                  (landmarks[thumb_tip_idx].y - index_mcp.y) ** 2)
    is_straight = angle > 160
    is_extended_dist = tip_mcp_dist > ip_mcp_dist * 1.3
    is_away_from_palm = tip_index_mcp_dist > 0.15
    return is_straight and is_extended_dist and is_away_from_palm

def detect_thumb_up(landmarks):
    thumb_tip = landmarks[mp.solutions.hands.HandLandmark.THUMB_TIP].y
    thumb_ip = landmarks[mp.solutions.hands.HandLandmark.THUMB_IP].y
    thumb_up = thumb_tip < thumb_ip - 0.03

    index_tip = landmarks[mp.solutions.hands.HandLandmark.INDEX_FINGER_TIP].y
    index_pip = landmarks[mp.solutions.hands.HandLandmark.INDEX_FINGER_PIP].y
    index_folded = index_tip > index_pip - 0.02

    mid_tip = landmarks[mp.solutions.hands.HandLandmark.MIDDLE_FINGER_TIP].y
    mid_pip = landmarks[mp.solutions.hands.HandLandmark.MIDDLE_FINGER_PIP].y
    mid_folded = mid_tip > mid_pip - 0.02

    ring_tip = landmarks[mp.solutions.hands.HandLandmark.RING_FINGER_TIP].y
    ring_pip = landmarks[mp.solutions.hands.HandLandmark.RING_FINGER_PIP].y
    ring_folded = ring_tip > ring_pip - 0.02

    pinky_tip = landmarks[mp.solutions.hands.HandLandmark.PINKY_TIP].y
    pinky_pip = landmarks[mp.solutions.hands.HandLandmark.PINKY_PIP].y
    pinky_folded = pinky_tip > pinky_pip - 0.02

    return thumb_up and index_folded and mid_folded and ring_folded and pinky_folded

def detect_number_two(landmarks):
    thumb_extended = is_thumb_extended(landmarks, 4, 3, 2)
    index_extended = is_finger_extended(landmarks, 8, 6, 5)
    middle_extended = is_finger_extended(landmarks, 12, 10, 9)
    ring_extended = is_finger_extended(landmarks, 16, 14, 13)
    pinky_extended = is_finger_extended(landmarks, 20, 18, 17)
    return index_extended and middle_extended and not ring_extended and not pinky_extended and not thumb_extended

def detect_three_fingers(landmarks):
    index_extended = landmarks[8].y < landmarks[6].y
    middle_extended = landmarks[12].y < landmarks[10].y
    ring_extended = landmarks[16].y < landmarks[14].y
    pinky_folded = landmarks[20].y > landmarks[18].y
    return index_extended and middle_extended and ring_extended and pinky_folded

class GestureController:
    def __init__(self):
        self.mp_hands = mp.solutions.hands
        self.mp_drawing = mp.solutions.drawing_utils
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=2,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.5
        )
        self.cap = cv2.VideoCapture(0)
        self.left = 0
        self.right = 0
        self.frame_surface = None

    def update(self):
        ret, frame = self.cap.read()
        if not ret:
            return

        # 翻转摄像头画面
        frame = cv2.flip(frame, 1)
        
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        res = self.hands.process(rgb)

        self.left = 0
        self.right = 0

        if res.multi_hand_landmarks and res.multi_handedness:
            for lm, hand_info in zip(res.multi_hand_landmarks, res.multi_handedness):
                label = hand_info.classification[0].label
                lms = lm.landmark

                val = 0
                if detect_thumb_up(lms):
                    val = 1
                elif detect_number_two(lms):
                    val = 2
                elif detect_three_fingers(lms):
                    val = 3

                if label == "Left":
                    self.left = val
                else:
                    self.right = val

        # 文字画在已经翻转的画面上 → 文字正向
        cv2.putText(frame, f"Left: {self.left}", (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 2)
        cv2.putText(frame, f"Right: {self.right}", (10, 80), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 2)

        small_frame = cv2.resize(frame, (240, 180))
        frame_rgb = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
        
        # 不再额外翻转！！！
        self.frame_surface = pygame.surfarray.make_surface(frame_rgb.swapaxes(0, 1))

    def get_frame(self):
        return self.frame_surface

    def close(self):
        self.cap.release()