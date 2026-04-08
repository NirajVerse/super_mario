import os, sys, time, traceback
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

print("Starting imports...")

try:
    import cv2
    print("cv2")
    import mediapipe as mp
    print("mediapipe")
    import pyautogui
    pyautogui.FAILSAFE = False
    print("pyautogui")
except Exception as e:
    print(f"Import failed: {e}")
    traceback.print_exc()
    sys.exit(1)

print("Setting up MediaPipe hands...")
mp_hands = mp.solutions.hands
mp_draw  = mp.solutions.drawing_utils
hands    = mp_hands.Hands(
    max_num_hands=1,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7
)
print("Hands ready")

print("Setting up Gesture Recognizer...")
try:
    MODEL_PATH = os.path.expanduser(
        "~/Documents/emulator/gesture_recognizer.task"
    )
    if not os.path.exists(MODEL_PATH):
        print(f"Model not found at {MODEL_PATH}")
        sys.exit(1)
    print(f"Model found: {MODEL_PATH}")

    BaseOptions              = mp.tasks.BaseOptions
    GestureRecognizer        = mp.tasks.vision.GestureRecognizer
    GestureRecognizerOptions = mp.tasks.vision.GestureRecognizerOptions
    VisionRunningMode        = mp.tasks.vision.RunningMode

    options = GestureRecognizerOptions(
        base_options=BaseOptions(model_asset_path=MODEL_PATH),
        running_mode=VisionRunningMode.IMAGE,
        num_hands=1
    )
    print("Gesture recognizer options ready")
except Exception as e:
    print(f"Gesture recognizer setup failed: {e}")
    traceback.print_exc()
    sys.exit(1)

# ── Key control ──────────────────────────────────────
# Nestopia input layout: A = jump, B = run.
KEY_RIGHT = 'right'
KEY_LEFT = 'left'
KEY_RUN = 'z'
KEY_JUMP = 'a'

KEYS = [KEY_RIGHT, KEY_LEFT, KEY_RUN, KEY_JUMP]
pending_key_releases = {}

def release_all():
    for k in KEYS:
        try: pyautogui.keyUp(k)
        except: pass
    pending_key_releases.clear()

def queue_key_release(key, delay_seconds):
    pending_key_releases[key] = time.time() + delay_seconds

def service_key_releases():
    now = time.time()
    expired = [key for key, release_at in pending_key_releases.items() if now >= release_at]
    for key in expired:
        try: pyautogui.keyUp(key)
        except: pass
        pending_key_releases.pop(key, None)

def press_walk():
    release_all(); pyautogui.keyDown(KEY_RIGHT)

def press_run():
    release_all()
    pyautogui.keyDown(KEY_RIGHT)
    pyautogui.keyDown(KEY_RUN)

def press_left():
    release_all(); pyautogui.keyDown(KEY_LEFT)

def press_low_jump():
    release_all()
    pyautogui.keyDown(KEY_JUMP)
    queue_key_release(KEY_JUMP, 0.08)

def press_high_jump():
    release_all()
    pyautogui.keyDown(KEY_RIGHT)
    pyautogui.keyDown(KEY_JUMP)
    queue_key_release(KEY_JUMP, 0.22)

def press_stop():
    release_all()

GESTURE_MAP = {
    'Pointing_Up' : ('walk',      press_walk),
    'Victory'     : ('run',       press_run),
    'Closed_Fist' : ('move_left', press_left),
    'Open_Palm'   : ('stop',      press_stop),
    'Thumb_Up'    : ('low_jump',  press_low_jump),
    'ILoveYou'    : ('high_jump', press_high_jump),
}

# ── Wrist motion rules ───────────────────────────────
wrist_history = []

def rule_based_gesture(landmarks):
    wrist_y = landmarks[0].y
    wrist_history.append(wrist_y)
    if len(wrist_history) > 8:
        wrist_history.pop(0)
    if len(wrist_history) < 4:
        return None
    speed = wrist_history[-4] - wrist_history[-1]
    if speed > 0.04:
        return ('low_jump', press_low_jump)
    if speed > 0.015 and wrist_y < 0.35:
        return ('high_jump', press_high_jump)
    return None

# ── HUD ─────────────────────────────────────────────
COLORS = {
    'walk': (0,220,0), 'run': (0,180,255),
    'move_left': (255,180,0), 'low_jump': (100,100,255),
    'high_jump': (220,50,220), 'stop': (150,150,150),
}
DISPLAY_SIDE = 720
PANEL_WIDTH = 360

def draw_side_panel(canvas, x0, gesture, source, conf, fps, hand_seen):
    h, w = canvas.shape[:2]
    cv2.rectangle(canvas, (x0, 0), (w, h), (14,14,14), -1)

    color = COLORS.get(gesture, (80,80,80))
    label = gesture.upper().replace('_',' ') if gesture else 'NO GESTURE'
    cv2.putText(canvas, label, (x0 + 16, 48),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
    cv2.putText(canvas, f"[{source}]", (x0 + 16, 80),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (180,180,180), 1)
    if conf:
        cv2.putText(canvas, f"{conf:.0%}", (x0 + 130, 80),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (200,200,200), 1)

    cv2.putText(canvas, f"FPS: {fps:.1f}", (x0 + 16, 120),
                cv2.FONT_HERSHEY_SIMPLEX, 0.65, (120, 230, 120), 2)
    cv2.putText(canvas, "Finger tips", (x0 + 16, 160),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (230, 230, 230), 2)

    tips = [
        "Pointing_Up = move right",
        "Victory = run right",
        "Closed_Fist = move left",
        "Thumb_Up = jump (A)",
        "ILoveYou = high jump (A + hold)",
    ]
    y = 196
    for tip in tips:
        cv2.putText(canvas, tip, (x0 + 16, y),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.52, (210, 210, 210), 1)
        y += 34

    if not hand_seen:
        cv2.putText(canvas, "No hand detected", (x0 + 16, h - 36),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.58, (100, 220, 255), 2)

# ── Open webcam ──────────────────────────────────────
print("Opening webcam...")
WINDOW_NAME = "Mario Gesture Controller"
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Webcam not found!")
    sys.exit(1)

# Request a smaller capture size to reduce CPU load and latency.
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
# Keep only a tiny camera buffer to reduce latency.
cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
actual_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
actual_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

# Use a resizable window and start with a larger preview.
cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
cv2.resizeWindow(WINDOW_NAME, DISPLAY_SIDE + PANEL_WIDTH, DISPLAY_SIDE)
print("Webcam open")
print(f"Camera resolution: {actual_w}x{actual_h}")

print("\nMario Gesture Controller READY")
print("="*40)
print("Pointing_Up = Move right")
print("Victory = Run right")
print("Closed_Fist = Move left")
print("Thumb_Up = Jump (A)")
print("ILoveYou = High jump (A + hold)")
print("="*40)
print(f"Nestopia controls: RIGHT={KEY_RIGHT} LEFT={KEY_LEFT} B(run)={KEY_RUN} A(jump)={KEY_JUMP}")
print("Focus Nestopia window now!")
print("Press Q in camera window to quit\n")

# ── Main loop ────────────────────────────────────────
prev_gesture     = None
last_action_time = 0
COOLDOWN         = 0.12
TRANSIENT_GESTURES = {'low_jump', 'high_jump'}
fps              = 0.0
fps_tick_count   = 0
fps_tick_time    = time.time()
PROCESS_SCALE    = 0.50

try:
    with GestureRecognizer.create_from_options(options) as recognizer:
        print("Recognizer active — running main loop...")
        while True:
            service_key_releases()
            ret, frame = cap.read()
            if not ret:
                print("Frame grab failed")
                break

            frame = cv2.flip(frame, 1)
            h0, w0 = frame.shape[:2]
            square_side = min(h0, w0)
            x0 = (w0 - square_side) // 2
            y0 = (h0 - square_side) // 2
            square = frame[y0:y0 + square_side, x0:x0 + square_side]
            square = cv2.resize(square, (DISPLAY_SIDE, DISPLAY_SIDE), interpolation=cv2.INTER_LINEAR)

            small = cv2.resize(square, None, fx=PROCESS_SCALE, fy=PROCESS_SCALE,
                               interpolation=cv2.INTER_AREA)
            rgb   = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)

            hand_result    = hands.process(rgb)
            mp_image       = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
            gesture_result = recognizer.recognize(mp_image)

            detected_gesture = None
            action_fn        = None
            source           = "none"
            confidence       = None
            hand_seen        = False

            if hand_result.multi_hand_landmarks:
                hand_seen = True
                for hl in hand_result.multi_hand_landmarks:
                    mp_draw.draw_landmarks(square, hl, mp_hands.HAND_CONNECTIONS)
                lm   = hand_result.multi_hand_landmarks[0].landmark
                rule = rule_based_gesture(lm)
                if rule:
                    detected_gesture, action_fn = rule
                    source = "motion"

            if not detected_gesture and gesture_result.gestures:
                top  = gesture_result.gestures[0][0]
                name = top.category_name
                conf = top.score
                if name in GESTURE_MAP and conf > 0.75:
                    detected_gesture, action_fn = GESTURE_MAP[name]
                    source     = "MediaPipe"
                    confidence = conf

            now = time.time()
            if detected_gesture and action_fn and (
                detected_gesture != prev_gesture or
                (detected_gesture not in TRANSIENT_GESTURES and now - last_action_time > COOLDOWN)
            ):
                action_fn()
                prev_gesture     = detected_gesture
                last_action_time = now
            elif not detected_gesture:
                if prev_gesture not in (None, 'stop'):
                    release_all()
                prev_gesture = None

            fps_tick_count += 1
            now_fps = time.time()
            elapsed = now_fps - fps_tick_time
            if elapsed >= 0.5:
                fps = fps_tick_count / elapsed
                fps_tick_count = 0
                fps_tick_time = now_fps

            canvas = cv2.copyMakeBorder(
                square, 0, 0, 0, PANEL_WIDTH,
                cv2.BORDER_CONSTANT, value=(0, 0, 0)
            )
            draw_side_panel(canvas, DISPLAY_SIDE, detected_gesture, source, confidence, fps, hand_seen)
            cv2.imshow(WINDOW_NAME, canvas)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

except Exception as e:
    print(f"\nError in main loop: {e}")
    traceback.print_exc()

finally:
    release_all()
    cap.release()
    cv2.destroyAllWindows()
    print(" Controller stopped cleanly.")