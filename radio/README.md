# Real-Time Audio Stream Monitoring and Transcription Service

This application is a complete, production-ready Python service designed to run on a Windows Server. It connects to multiple online radio streams, transcribes speech in real-time using Whisper, performs speaker diarization with Pyannote, and stores the results in daily JSON files and a MySQL database.

A lightweight FastAPI-based web dashboard is included for monitoring.

## Features

- **Multi-Stream Monitoring**: Connects to and monitors multiple MP3/AAC audio streams concurrently using `asyncio`.
- **Automatic Speech Recognition**: Uses `faster-whisper` for high-performance, local transcription.
- **Speaker Diarization**: Employs `pyannote.audio` to tag different speakers (e.g., S0, S1).
- **VAD**: Uses `webrtcvad` to filter out silence and music, processing only speech segments.
- **Dual Storage**: Saves transcription data to both daily rotated JSON files and a MySQL database.
- **Scalability**: Asynchronous design allows for efficient handling of many streams. GPU (CUDA) is used if available.
- **Dynamic Configuration**: A central `streams.json` file allows for adding/removing streams and changing settings without restarting the service.
- **Web Dashboard**: A simple GUI on `http://localhost:8000` shows the status of each stream and the latest transcriptions.
- **Windows Service Ready**: Includes instructions for deploying as a persistent Windows service.

## Project Structurec