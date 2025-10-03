import asyncio
import logging
import datetime
import time
import numpy as np
import torch
import webrtcvad
import ffmpeg
from faster_whisper import WhisperModel
from pyannote.audio import Pipeline
from typing import Dict, Any

from .storage import storage_manager
from .gui import update_stream_status

# Setup logging
logger = logging.getLogger(__name__)

class StreamWorker:
    """
    Manages the entire pipeline for a single audio stream:
    capturing, VAD, diarization, transcription, and storage.
    """
    def __init__(self, stream_config: Dict[str, Any], whisper_model: WhisperModel, diarization_pipeline: Pipeline, hf_token: str):
        self.stream_config = stream_config
        self.name = stream_config['name']
        self.url = stream_config['url']
        self.whisper_model = whisper_model
        self.diarization_pipeline = diarization_pipeline
        self.hf_token = hf_token
        self.is_running = False
        self._task = None

        # VAD settings
        self.vad = webrtcvad.Vad(3)  # Aggressiveness mode 3
        self.sample_rate = 16000
        self.frame_duration = 30  # ms
        self.frame_size = int(self.sample_rate * self.frame_duration / 1000)
        
        self.speech_buffer = bytearray()
        self.silence_duration = 0
        
        # Audio processing triggers
        self.min_speech_duration_ms = 1000
        self.silence_threshold_ms = 1500
        
        # *** NEW: Add a max buffer size trigger ***
        self.max_buffer_duration_ms = 30000 # Process audio every 30 seconds max
        self.max_buffer_size = int(self.max_buffer_duration_ms / 1000 * self.sample_rate * 2) # 2 bytes per sample (s16le)

    async def start(self):
        """Starts the stream processing task."""
        if not self.is_running:
            self.is_running = True
            self._task = asyncio.create_task(self._monitor_stream())
            logger.info(f"Started worker for stream: {self.name}")
            update_stream_status(self.name, "Running", "Starting worker...")

    async def stop(self):
        """Stops the stream processing task."""
        if self.is_running and self._task:
            self.is_running = False
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            logger.info(f"Stopped worker for stream: {self.name}")
            update_stream_status(self.name, "Stopped", "Worker has been stopped.")

    async def _monitor_stream(self):
        """The main loop for monitoring and processing the stream."""
        while self.is_running:
            try:
                await self._process_stream()
            except Exception as e:
                logger.error(f"[{self.name}] Error in processing loop: {e}")
                update_stream_status(self.name, "Error", str(e))
                logger.info(f"[{self.name}] Retrying in 15 seconds...")
                await asyncio.sleep(15)

    async def _process_stream(self):
        """Connects to the stream with ffmpeg and processes audio chunks."""
        logger.info(f"[{self.name}] Connecting to stream URL: {self.url}")
        update_stream_status(self.name, "Connecting", f"Connecting to {self.url}")

        headers_str = (
            'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36\r\n'
            'Accept: */*\r\n'
            'Connection: keep-alive\r\n'
            'Icy-MetaData: 1\r\n'
        )

        process = (
            ffmpeg
            .input(
                self.url,
                reconnect=1,
                reconnect_streamed=1,
                reconnect_delay_max=5,
                headers=headers_str
            )
            .output('pipe:', format='s16le', acodec='pcm_s16le', ac=1, ar=self.sample_rate)
            .run_async(pipe_stdout=True, pipe_stderr=True)
        )
        
        update_stream_status(self.name, "Running", "Connected and monitoring audio.")
        last_log_time = time.time()

        while self.is_running:
            in_bytes = await asyncio.get_event_loop().run_in_executor(
                None, process.stdout.read, self.frame_size * 2
            )
            if not in_bytes:
                logger.warning(f"[{self.name}] Stream ended or connection lost.")
                update_stream_status(self.name, "Reconnecting", "Stream ended, attempting to reconnect.")
                break
            
            current_time = time.time()
            if current_time - last_log_time > 60:
                logger.info(f"[{self.name}] Still monitoring stream. Current speech buffer size: {len(self.speech_buffer)} bytes.")
                last_log_time = current_time

            is_speech = self.vad.is_speech(in_bytes, self.sample_rate)

            if is_speech:
                self.speech_buffer.extend(in_bytes)
                self.silence_duration = 0
            else:
                self.silence_duration += self.frame_duration

            # *** UPDATED: Logic with two triggers: silence or max buffer size ***
            silence_trigger = self.silence_duration > self.silence_threshold_ms and len(self.speech_buffer) > 0
            size_trigger = len(self.speech_buffer) >= self.max_buffer_size

            if silence_trigger or size_trigger:
                min_buffer_size = self.min_speech_duration_ms / 1000 * self.sample_rate * 2
                if len(self.speech_buffer) >= min_buffer_size:
                    audio_to_process = self.speech_buffer
                    self.speech_buffer = bytearray()
                    self.silence_duration = 0
                    
                    if size_trigger:
                        logger.info(f"[{self.name}] Max buffer size reached. Processing audio chunk.")
                    
                    asyncio.create_task(self._process_audio_chunk(bytes(audio_to_process)))
                else:
                    logger.info(f"[{self.name}] Discarding speech buffer of {len(self.speech_buffer)} bytes, too short to process.")
                    self.speech_buffer = bytearray()
                    self.silence_duration = 0

        process.kill()
        
    async def _process_audio_chunk(self, audio_chunk: bytes):
        """Processes a chunk of audio containing speech."""
        timestamp_start = datetime.datetime.utcnow()
        logger.info(f"[{self.name}] Processing audio chunk of length {len(audio_chunk)} bytes.")
        
        try:
            audio_np = np.frombuffer(audio_chunk, dtype=np.int16).astype(np.float32) / 32768.0

            segments, _ = self.whisper_model.transcribe(audio_np)
            transcribed_text = " ".join([seg.text for seg in segments])
            
            if not transcribed_text.strip():
                logger.info(f"[{self.name}] No speech detected in chunk by Whisper.")
                return

            if self.diarization_pipeline:
                try:
                    audio_tensor = torch.from_numpy(audio_np).unsqueeze(0)
                    diarization = self.diarization_pipeline({"waveform": audio_tensor, "sample_rate": self.sample_rate})
                    
                    speaker = "S_UNKNOWN"
                    if diarization.labels():
                        speaker = diarization.labels()[0]

                except Exception as dia_err:
                    logger.error(f"[{self.name}] Diarization failed: {dia_err}")
                    speaker = "S_DIARIZATION_ERROR"
            else:
                speaker = "S_DISABLED"
            
            timestamp_end = datetime.datetime.utcnow()

            result = {
                "stream": self.name,
                "timestamp_start": timestamp_start.isoformat() + "Z",
                "timestamp_end": timestamp_end.isoformat() + "Z",
                "speaker": speaker,
                "text": transcribed_text.strip()
            }
            
            logger.info(f"[{self.name}]-[{speaker}] {transcribed_text.strip()}")
            update_stream_status(self.name, "Running", transcribed_text.strip())

            await storage_manager.store_segment(result)

        except Exception as e:
            logger.error(f"[{self.name}] Error during audio chunk processing: {e}")
            update_stream_status(self.name, "Error", f"Processing Error: {e}")