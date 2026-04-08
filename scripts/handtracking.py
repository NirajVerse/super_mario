# scripts/test_handtracking.py
import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

import cv2
import mediapipe as mp

mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils
hands = mp_hands.Hands(
    max_num_hands=1,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7
)

cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print(" Webcam not found! Try VideoCapture(1)")
    exit()

print(" Webcam opened! Show your hand. Press Q to quit.")

while True:
    ret, frame = cap.read()
    if not ret:
        print(" Failed to grab frame")
        break

    frame = cv2.flip(frame, 1)
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result = hands.process(rgb)

    landmarks = []
    if result.multi_hand_landmarks:
       for hand_landmarks in result.multi_hand_landmarks:
            mp_draw.draw_landmarks(
                frame,
                hand_landmarks,
                mp_hands.HAND_CONNECTIONS
            )
            for lm in hand_landmarks.landmark:
                landmarks.extend([lm.x, lm.y, lm.z])

        cv2.putText(frame, f" Hand Detected | Points: {len(landmarks)}",
                    (10, 40), cv2.FONT_HERSHEY_SIMPLEX,
                    0.8, (0, 255, 0), 2)
    else:
        cv2.putText(frame, " No Hand Detected",
                    (10, 40), cv2.FONT_HERSHEY_SIMPLEX,
                    0.8, (0, 0, 255), 2)

    cv2.putText(frame, "Press Q to quit",
                (10, 70), cv2.FONT_HERSHEY_SIMPLEX,
                0.6, (255, 255, 0), 1)

    cv2.imshow("Hand Tracking Test", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
print(" Hand tracking test complete!")