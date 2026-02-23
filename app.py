import streamlit as st
import cv2
import mediapipe as mp
import numpy as np
import random
import math
import time


if "camera" not in st.session_state:
    st.session_state.camera = None

if "game_started" not in st.session_state:
    st.session_state.game_started = False

if "score" not in st.session_state:
    st.session_state.score = 0

if "time_left" not in st.session_state:
    st.session_state.time_left = 10

if "start_time" not in st.session_state:
    st.session_state.start_time = None

HAND_CONNECTIONS = [
    (0,1),(1,2),(2,3),(3,4),
    (0,5),(5,6),(6,7),(7,8),
    (5,9),(9,10),(10,11),(11,12),
    (9,13),(13,14),(14,15),(15,16),
    (13,17),(17,18),(18,19),(19,20),
    (0,17)
]

# ---------------- UI CONFIG ----------------
st.set_page_config(layout="wide")

st.markdown("""
<style>
div.stButton > button:first-child {
    background-color: #00C853;
    color: white;
    font-size: 26px;
    height: 80px;
    width: 300px;
    border-radius: 12px;
    border: none;
}
div.stButton > button:first-child:hover {
    background-color: #00A844;
    color: white;
}
</style>
""", unsafe_allow_html=True)

st.title("Hand Gun Shooting Game")

# Layout: main game + small camera window
col1, col2 = st.columns([3,1])  # bigger game area
game_frame = col1.empty()
camera_frame = col2.empty()
# ---------------- SETTINGS ----------------
WIDTH, HEIGHT = 900, 600
score = 0
hit_margin = 25

# ---------------- BALL CLASS ----------------
class Ball:
    def __init__(self):
        self.radius = random.randint(20, 35)
        self.x = random.randint(self.radius, WIDTH - self.radius)
        self.y = random.randint(self.radius, HEIGHT - self.radius)
        self.dx = random.choice([-4, -3, 3, 4])
        self.dy = random.choice([-4, -3, 3, 4])
        self.color = (
            random.randint(50,255),
            random.randint(50,255),
            random.randint(50,255)
        )

    def move(self):
        self.x += self.dx
        self.y += self.dy
        if self.x <= self.radius or self.x >= WIDTH - self.radius:
            self.dx *= -1
        if self.y <= self.radius or self.y >= HEIGHT - self.radius:
            self.dy *= -1

balls = [Ball() for _ in range(5)]

def distance(x1,y1,x2,y2):
    return math.hypot(x2-x1, y2-y1)

# ---------------- MEDIAPIPE ----------------
BaseOptions = mp.tasks.BaseOptions
HandLandmarker = mp.tasks.vision.HandLandmarker
HandLandmarkerOptions = mp.tasks.vision.HandLandmarkerOptions
VisionRunningMode = mp.tasks.vision.RunningMode

options = HandLandmarkerOptions(
    base_options=BaseOptions(model_asset_path="hand_landmarker.task"),
    running_mode=VisionRunningMode.VIDEO,
    num_hands=1
)

landmarker = HandLandmarker.create_from_options(options)
cap = cv2.VideoCapture(0)

smooth_x, smooth_y = WIDTH//2, HEIGHT//2
SMOOTHING = 0.3

def calculate_angle_3d(a, b, c):
    ba = (a.x-b.x, a.y-b.y, a.z-b.z)
    bc = (c.x-b.x, c.y-b.y, c.z-b.z)

    dot = ba[0]*bc[0] + ba[1]*bc[1] + ba[2]*bc[2]
    mag_ba = math.sqrt(sum(i*i for i in ba))
    mag_bc = math.sqrt(sum(i*i for i in bc))

    if mag_ba * mag_bc == 0:
        return 180

    cos_angle = dot / (mag_ba * mag_bc)
    cos_angle = max(-1, min(1, cos_angle))
    return math.degrees(math.acos(cos_angle))

# ---------------- MAIN LOOP ----------------


score = 0
cursor_x, cursor_y = WIDTH // 2, HEIGHT // 2

if not st.session_state.game_started:
    with st.expander("Game Rules", expanded=True):
        st.write("""
    Objective:
    Pop as many balls as possible before time runs out.

    Controls:
    - Index finger controls the cursor.
    - Shooting gesture: thumb bent, index straight, middle folded.

    Timer:
    - Starts at 10 seconds.
    - +2 seconds per hit.
    - Game ends at 0.

    Scoring:
    - 1 point per ball.
    """)
    col_left, col_center, col_right = st.columns([1,2,1])
    with col_center:
        if st.button("START GAME"):
            st.session_state.game_started = True
            st.session_state.score = 0
            st.session_state.time_left = 10
            st.session_state.start_time = time.time()
            st.session_state.camera = cv2.VideoCapture(0)


if st.session_state.game_started:

    while st.session_state.game_started:

        ret, frame = st.session_state.camera.read()
        if not ret:
            break

        frame = cv2.flip(frame, 1)
        frame = cv2.resize(frame, (WIDTH, HEIGHT))
        game_canvas = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)

        # ---- TIMER ----
        elapsed = time.time() - st.session_state.start_time
        st.session_state.time_left = max(0, 10 - int(elapsed))

        if st.session_state.time_left <= 0:
            if st.session_state.camera:
                st.session_state.camera.release()
                st.session_state.camera = None
            # Dark overlay
            overlay = game_canvas.copy()
            cv2.rectangle(overlay, (0,0), (WIDTH, HEIGHT), (0,0,0), -1)
            game_canvas = cv2.addWeighted(overlay, 0.7, game_canvas, 0.3, 0)

            cv2.putText(game_canvas,
                        "GAME OVER",
                        (WIDTH//2 - 250, HEIGHT//2 - 20),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        2,
                        (0,0,255),
                        5)

            cv2.putText(game_canvas,
                        f"Final Score: {st.session_state.score}",
                        (WIDTH//2 - 200, HEIGHT//2 + 60),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        1.5,
                        (255,255,255),
                        4)

            game_frame.image(game_canvas, channels="BGR")
            camera_frame.image(frame, channels="BGR")
           
            st.session_state.game_started = False
            break

        # ---- HAND DETECTION ----
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        timestamp = int(time.time() * 1000)
        result = landmarker.detect_for_video(mp_image, timestamp)

        shoot_triggered = False

        if result.hand_landmarks:
            landmarks = result.hand_landmarks[0]

            # Draw skeleton on camera preview
            cam_points = []
            for lm in landmarks:
                x = int(lm.x * WIDTH)
                y = int(lm.y * HEIGHT)
                cam_points.append((x, y))

            for connection in HAND_CONNECTIONS:
                cv2.line(frame,
                         cam_points[connection[0]],
                         cam_points[connection[1]],
                         (255, 0, 0), 2)

            for point in cam_points:
                cv2.circle(frame, point, 5, (0,255,0), -1)

            # Cursor smoothing
            index_tip = landmarks[8]
            index_px = (int(index_tip.x * WIDTH),
                        int(index_tip.y * HEIGHT))

            smooth_x = int(smooth_x + (index_px[0] - smooth_x) * SMOOTHING)
            smooth_y = int(smooth_y + (index_px[1] - smooth_y) * SMOOTHING)

            cursor_x, cursor_y = smooth_x, smooth_y

            thumb_angle = calculate_angle_3d(landmarks[2], landmarks[3], landmarks[4])
            index_angle = calculate_angle_3d(landmarks[5], landmarks[6], landmarks[8])
            middle_angle = calculate_angle_3d(landmarks[9], landmarks[10], landmarks[12])

            if thumb_angle < 150 and index_angle > 100 and middle_angle < 150:
                shoot_triggered = True

        # ---- BALLS ----
        for ball in balls:
            ball.move()

            if shoot_triggered:
                if distance(cursor_x, cursor_y,
                            ball.x, ball.y) < ball.radius + hit_margin:
                    ball.__init__()
                    st.session_state.score += 1
                    st.session_state.start_time += 2

            cv2.circle(game_canvas,
                       (int(ball.x), int(ball.y)),
                       ball.radius,
                       ball.color,
                       -1)

        # ---- CURSOR ----
        # ---- CROSSHAIR ----
        if shoot_triggered:
            color = (0, 0, 255)   # red
            radius = 18
        else:
            color = (255, 255, 0)   # green
            radius = 14

        # Outer circle (not filled)
        cv2.circle(game_canvas, (cursor_x, cursor_y), radius, color, 2)

        # Horizontal line
        cv2.line(game_canvas,
                (cursor_x - radius, cursor_y),
                (cursor_x + radius, cursor_y),
                color, 2)

        # Vertical line
        cv2.line(game_canvas,
                (cursor_x, cursor_y - radius),
                (cursor_x, cursor_y + radius),
                color, 2)

        # Center dot
        cv2.circle(game_canvas, (cursor_x, cursor_y), 3, color, -1)
        # ---- HUD ----
        cv2.putText(game_canvas,
                    f"Score: {st.session_state.score}",
                    (30,50),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1.2,
                    (255,255,255),
                    3)

        cv2.putText(game_canvas,
                    f"Time: {st.session_state.time_left}",
                    (30,100),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1.2,
                    (0,255,255),
                    3)

        game_frame.image(game_canvas, channels="BGR")
        camera_frame.image(frame, channels="BGR")
        

        time.sleep(0.02)  # ~50 FPS


    if not st.session_state.game_started and st.session_state.time_left <= 0:

        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            if st.button("RESTART GAME"):
                st.session_state.score = 0
                st.session_state.time_left = 10
                st.session_state.start_time = time.time()
                st.session_state.game_started = True


import atexit

def release_camera():
    if "camera" in st.session_state and st.session_state.camera is not None:
        st.session_state.camera.release()
        st.session_state.camera = None

atexit.register(release_camera)