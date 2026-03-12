# Syntatic — AI Powered Interview Simulator

Syntatic is a sophisticated AI-driven application designed to simulate technical interviews. It helps candidates practice DSA questions and behavioral interviews in a realistic environment.

## Features

-   **Round 1: DSA Coding Challenge:** Solve AI-generated Data Structures and Algorithms problems in a real-time editor with syntax highlighting.
-   **Round 2: AI Interview:** Engage in a voice-based interview where an AI interviewer asks follow-up questions based on your domain and responses.
-   **Voice Recognition & TTS:** Speak your answers naturally, and listen to the AI's questions.
-   **Eye Tracking:** Validates interview integrity by monitoring eye gaze.
-   **Performance Analytics:** Receive detailed scores and feedback on your performance.

## Tech Stack

-   **Frontend:** HTML5, CSS3, Vanilla JavaScript, Firebase (for history).
-   **Backend:** Python, Flask, Google Gemini API (AI Logic), OpenCV (Eye Tracking).

## Setup & Run

1.  **Backend:**
    ```bash
    cd backend
    pip install -r requirements.txt
    python app.py
    ```

2.  **Frontend:**
    Open `http://localhost:5000` in your browser.

## API Key Configuration

Ensure your Gemini API key is correctly set in `backend/app.py`.
