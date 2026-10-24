# Gesture-Controlled Rhythm Game Based on Computer Vision

## Project Overview
This project is a motion-sensing rhythm game based on Computer Vision technology. By capturing hand movements via a local webcam, it utilizes a machine learning model to recognize gestures in real-time and maps them to in-game key inputs. The project eliminates traditional mouse and keyboard inputs, aiming to explore the potential of multimodal interaction in gaming experiences.

## Core Features
- **Real-time Gesture Recognition**: Hand tracking built with MediaPipe, supporting simultaneous recognition of both hands.
- **Multi-Gesture Mapping**: Defines various gesture commands (e.g., Thumbs Up, Number Two, Three Fingers) and maps them to different in-game tracks.
- **Rhythm Game Mechanics**: Includes full chart parsing (JSON format), note-scrolling judgment, combo feedback, HP system, and hold note mechanics.
- **Real-time Visual Feedback**: Displays a webcam preview in the top-right corner of the game screen, providing players with immediate skeletal and recognition feedback.

## System Architecture
The project consists of two main modules:

1. **Vision & Gesture Control Module (`gesture.py`)**
   - **Libraries**: OpenCV, MediaPipe, Pygame, Numpy.
   - **Implementation**:
     - Captures frames using OpenCV, applying mirror flipping and color space conversion (BGR to RGB).
     - Utilizes MediaPipe Hands to extract 21 hand landmark coordinates and handedness classification.
     - Employs custom spatial geometry algorithms (calculating vector angles and landmark distances) to determine finger extension and flexion states, accurately recognizing Thumbs Up, Peace Sign (Number 2), and Three Fingers.
     - Converts recognition results into digital signals (0-3) and transforms them into Pygame surface textures for the main program.

2. **Game Loop Module (`main.py`)**
   - **Libraries**: Pygame, JSON, Time.
   - **Implementation**:
     - **Chart System**: Reads note data from JSON files and preloads assets (backgrounds, notes, judgment effects).
     - **Judgment Logic**: Drives note scrolling based on the background music playback position (`pygame.mixer.music.get_pos`). Compares the time difference between player gesture input and the note reaching the judgment line to achieve Perfect/Miss judgments.
     - **State Machine**: Manages game states (Start, Pause, Game Over, Clear) and transitions upon zero HP or song completion.
     - **UI/UX**: Renders the game scene, Gaussian blur backgrounds, glowing text effects, and judgment animations.

## Dependencies
- Python 3.8+
- OpenCV (`pip install opencv-python`)
- MediaPipe (`pip install mediapipe`)
- Pygame (`pip install pygame`)
- Numpy (`pip install numpy`)

## Directory Structure
```text
├── gesture.py         # Gesture recognition module
├── main.py            # Main game program
├── chart.json         # Game chart data file
├── gamepic/           # Game graphics assets (notes, backgrounds, UI)
└── music/             # Game audio files