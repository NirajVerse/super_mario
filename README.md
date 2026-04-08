# Gesture Recognizer - Super Mario Emulator

A computer vision-based application that uses hand tracking and gesture recognition to play Super Mario NES game hands-free.

## Overview

This project uses MediaPipe for hand detection and tracking to recognize gestures that control a Super Mario NES emulator. The program captures video from your webcam and translates hand movements into game controls.

## Features

- **Hand Tracking**: Real-time hand detection and tracking using MediaPipe
- **Gesture Recognition**: Recognize hand gestures to control game actions
- **NES Emulation**: Play Super Mario on an NES emulator using hand gestures
- **Automated Gameplay**: Custom scripts for automated game interaction

## Directory Structure

- `scripts/play_mario.py` - Main script to play Mario with hand gestures
- `scripts/handtracking.py` - Hand tracking and gesture recognition module
- `supermario.nes` - Super Mario NES ROM file
- `gesture_recognizer.task` - Task configuration file
- `requirements.txt` - Python dependencies

## Installation

1. Clone the repository
2. Create a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

Run the main game script:
```bash
python scripts/play_mario.py
```

## Requirements

- Python 3.8+
- Webcam
- See `requirements.txt` for all dependencies

## Key Dependencies

- **MediaPipe**: Hand tracking and gesture detection
- **OpenCV**: Computer vision and image processing
- **PyAutoGUI**: Automated keyboard/mouse control
- **NumPy & SciPy**: Numerical computations
- **PyTorch**: Machine learning models

## License

This project is for educational purposes.
