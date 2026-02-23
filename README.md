# 🎯 Hand Gun Shooting Game (AI + Computer Vision)

An interactive real-time browser-based shooting game powered by **MediaPipe Hand Tracking**, **OpenCV**, and **Streamlit WebRTC**.

The player controls a crosshair using their index finger and shoots bouncing balls using a custom hand gesture. The game runs entirely in the browser with real-time AI inference.

---

## 🚀 Features

- 🖐 Real-time hand tracking using MediaPipe Tasks API  
- 🎮 Gesture-controlled shooting (custom 3D angle logic)  
- 🎯 Dynamic ball physics with collision detection  
- ⏱ Countdown timer with bonus time per hit  
- 📊 Real-time scoring system  
- 🔴 Visual shooting feedback (crosshair + color change)  
- 🧠 AI-powered gesture recognition logic  
- 🌐 Browser-based webcam streaming via WebRTC  


---


## 🎮 Game Mechanics

### 🎯 Objective
Pop as many bouncing balls as possible before time runs out.

### 🖐 Controls
- Index finger controls cursor position  
- Shooting gesture:
  - Thumb bent  
  - Index extended  
  - Middle finger folded  

### ⏳ Timer
- Starts at 10 seconds  
- +2 seconds per successful hit  
- Game ends at 0 seconds  

### 🧮 Scoring
- 1 point per ball hit  

---

## 🧠 Gesture Detection Logic

Gesture recognition is implemented using:

- 3D joint angle calculation  
- Vector mathematics between hand landmarks  
- Angle threshold classification  
- Cursor smoothing via interpolation  

This avoids simple heuristics and instead uses geometric reasoning in 3D space.

---

## 📦 Installation (Local Setup)

```bash
git clone https://github.com/yourusername/hand-gun-shooting-game.git
cd hand-gun-shooting-game

pip install -r requirements.txt
streamlit run app.py
