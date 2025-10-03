import asyncio
import logging
import signal
import uvicorn
import torch
import os
from faster_whisper import WhisperModel
from pyannote.audio import Pipeline

from .config import config_manager
from .stream_worker import StreamWorker
from .gui import app as fastapi_app, update_stream_status

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ServiceManager:
    def __init__(self):
        self.workers = {}
        self.whisper_model = None
        self.diarization_pipeline = None
        self.hf_token = os.environ.get("HUGGINGFACE_TOKEN") # For pyannote

    async def initialize_models(self):
        """Initializes the ML models."""
        model_size = config_manager.get_whisper_model()
        device = "cuda" if torch.cuda.is_available() else "cpu"
        compute_type = "float16" if device == "cuda" else "int8"
        
        logger.info(f"Initializing Whisper model '{model_size}' on device '{device}' with compute type '{compute_type}'")
        try:
            self.whisper_model = WhisperModel(model_size, device=device, compute_type=compute_type)
        except Exception as e:
            logger.error(f"Failed to load Whisper model: {e}")
            raise

        if config_manager.is_diarization_enabled():
            logger.info("Initializing Pyannote diarization pipeline.")
            if not self.hf_token:
                logger.warning("Hugging Face token not found. Diarization will fail if models are not cached.")
            
            pipeline = None
            try:
                # *** THIS IS THE CORRECTED MODEL NAME ***
                pipeline = Pipeline.from_pretrained(
                    "pyannote/speaker-diarization-3.1",
                    use_auth_token=self.hf_token
                )
                if pipeline:
                    if device == "cuda":
                        pipeline.to(torch.device("cuda"))
                    self.diarization_pipeline = pipeline
                    logger.info("Successfully initialized Pyannote diarization pipeline.")
                else:
                    raise ValueError("Pipeline loading returned None.")
            except Exception as e:
                logger.error(f"Failed to load Pyannote pipeline. Diarization will be disabled. Error: {e}")
                self.diarization_pipeline = None


    async def update_workers(self):
        """Compares running workers with the current config and starts/stops them."""
        active_streams_config = {s['name']: s for s in config_manager.get_streams()}
        running_streams_names = set(self.workers.keys())
        config_stream_names = set(active_streams_config.keys())

        # Stop workers for streams that are no longer in config or disabled
        for name in running_streams_names - config_stream_names:
            logger.info(f"Stopping worker for removed/disabled stream: {name}")
            await self.workers[name].stop()
            del self.workers[name]

        # Start workers for new or re-enabled streams
        for name, config in active_streams_config.items():
            if name not in running_streams_names:
                logger.info(f"Starting worker for new/enabled stream: {name}")
                worker = StreamWorker(config, self.whisper_model, self.diarization_pipeline, self.hf_token)
                self.workers[name] = worker
                await worker.start()

    async def main_loop(self):
        """Main application loop."""
        await config_manager.start_reload_watcher()
        await self.initialize_models()

        while True:
            await self.update_workers()
            await asyncio.sleep(config_manager.reload_interval)

async def main():
    manager = ServiceManager()
    
    # Run FastAPI in the background
    config = uvicorn.Config(fastapi_app, host="0.0.0.0", port=8000, log_level="info")
    server = uvicorn.Server(config)
    
    # Start the FastAPI server and the main application loop concurrently
    await asyncio.gather(
        server.serve(),
        manager.main_loop()
    )


if __name__ == "__main__":
    # This allows graceful shutdown on Ctrl+C
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Shutting down service.")