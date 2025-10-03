import json
import logging
import asyncio
import aiofiles
from typing import Dict, Any, List

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Config:
    """
    Handles loading, periodic reloading, and modification of the application configuration.
    """
    def __init__(self, path: str, reload_interval: int = 60):
        self.path = path
        self.reload_interval = reload_interval
        self._lock = asyncio.Lock()
        self.config_data = self._load_config_sync() # Initial load is synchronous
        self._running = False
        self._reload_task = None

    def _load_config_sync(self) -> Dict[str, Any]:
        """Synchronously loads configuration from the JSON file for initial setup."""
        try:
            with open(self.path, 'r') as f:
                logger.info(f"Loading configuration from {self.path}")
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.error(f"Error loading config file {self.path}: {e}")
            # Return a default structure if the file is invalid or not found
            return {"mysql": {}, "streams": []}

    async def _load_config_async(self) -> Dict[str, Any]:
        """Asynchronously loads configuration from the JSON file."""
        try:
            async with aiofiles.open(self.path, 'r') as f:
                content = await f.read()
                return json.loads(content)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.error(f"Error loading config file {self.path}: {e}")
            return self.config_data # Return old data on failure

    async def _save_config_async(self):
        """Asynchronously saves the current configuration data to the JSON file."""
        async with self._lock:
            try:
                async with aiofiles.open(self.path, 'w') as f:
                    await f.write(json.dumps(self.config_data, indent=2))
                logger.info(f"Configuration saved to {self.path}")
            except Exception as e:
                logger.error(f"Failed to save config file: {e}")

    async def add_stream(self, new_stream: Dict[str, Any]):
        """Adds a new stream to the configuration and saves the file."""
        async with self._lock:
            # Ensure the stream doesn't already exist by name
            if any(s['name'] == new_stream['name'] for s in self.config_data['streams']):
                logger.warning(f"Stream '{new_stream['name']}' already exists. Not adding.")
                return
            self.config_data['streams'].append(new_stream)
        await self._save_config_async()

    async def remove_stream(self, stream_name: str):
        """Removes a stream from the configuration by name and saves the file."""
        async with self._lock:
            initial_count = len(self.config_data['streams'])
            self.config_data['streams'] = [s for s in self.config_data['streams'] if s['name'] != stream_name]
            if len(self.config_data['streams']) < initial_count:
                logger.info(f"Stream '{stream_name}' has been removed.")
            else:
                logger.warning(f"Stream '{stream_name}' not found for removal.")
        await self._save_config_async()

    async def _reload_loop(self):
        """Periodically reloads the configuration file."""
        while self._running:
            await asyncio.sleep(self.reload_interval)
            logger.info("Checking for configuration updates...")
            async with self._lock: # Acquire lock to prevent reading while GUI is writing
                new_config = await self._load_config_async()
            if new_config and new_config != self.config_data:
                self.config_data = new_config
                logger.info("Configuration has been reloaded.")

    async def start_reload_watcher(self):
        """Starts the background task for reloading configuration."""
        if not self._running:
            self._running = True
            self._reload_task = asyncio.create_task(self._reload_loop())
            logger.info(f"Configuration auto-reload watcher started. Interval: {self.reload_interval} seconds.")

    async def stop_reload_watcher(self):
        """Stops the background configuration reloading task."""
        if self._running and self._reload_task:
            self._running = False
            self._reload_task.cancel()
            try:
                await self._reload_task
            except asyncio.CancelledError:
                logger.info("Configuration reload watcher stopped.")

    def get_streams(self) -> List[Dict[str, Any]]:
        """Returns the list of all streams from the configuration."""
        return self.config_data.get("streams", [])

    def get_mysql_config(self) -> Dict[str, str]:
        """Returns MySQL connection details."""
        return self.config_data.get("mysql", {})

    def get_whisper_model(self) -> str:
        """Returns the Whisper model size."""
        return self.config_data.get("whisper_model", "base")

    def is_diarization_enabled(self) -> bool:
        """Checks if diarization is enabled."""
        return self.config_data.get("diarization_enabled", False)

# Global config instance
config_manager = Config('streams.json')