import json
import logging
import datetime
import os
import mysql.connector
from mysql.connector import Error
import aiofiles
from typing import Dict, Any

from .config import config_manager

# Setup logging
logger = logging.getLogger(__name__)

class StorageManager:
    """
    Handles writing transcription data to JSON files and a MySQL database.
    """
    def __init__(self):
        self._db_connection = None
        self._ensure_output_dir()

    def _ensure_output_dir(self):
        if not os.path.exists('output'):
            os.makedirs('output')

    def get_db_connection(self):
        """Establishes and returns a MySQL database connection."""
        if self._db_connection and self._db_connection.is_connected():
            return self._db_connection
        
        try:
            db_config = config_manager.get_mysql_config()
            self._db_connection = mysql.connector.connect(**db_config)
            if self._db_connection.is_connected():
                logger.info("Successfully connected to MySQL database.")
                return self._db_connection
        except Error as e:
            logger.error(f"Error connecting to MySQL database: {e}")
            self._db_connection = None
            return None

    async def save_json(self, data: Dict[str, Any]):
        """Appends a transcription segment to the daily JSON file for the stream."""
        stream_name = data['stream']
        today = datetime.datetime.utcnow().strftime('%Y-%m-%d')
        filename = f"output/{stream_name}-{today}.json"

        try:
            async with aiofiles.open(filename, mode='a') as f:
                await f.write(json.dumps(data) + '\n')
        except Exception as e:
            logger.error(f"Failed to write to JSON file {filename}: {e}")

    def save_to_db(self, data: Dict[str, Any]):
        """Inserts a transcription segment into the MySQL database."""
        conn = self.get_db_connection()
        if not conn:
            logger.error("Cannot save to database, no connection available.")
            return

        cursor = None
        try:
            cursor = conn.cursor()
            query = """
                INSERT INTO stream_transcripts 
                (stream_name, timestamp_start, timestamp_end, speaker, text) 
                VALUES (%s, %s, %s, %s, %s)
            """
            values = (
                data['stream'],
                data['timestamp_start'],
                data['timestamp_end'],
                data['speaker'],
                data['text']
            )
            cursor.execute(query, values)
            conn.commit()
        except Error as e:
            logger.error(f"Failed to insert record into MySQL: {e}")
            # Attempt to reconnect on next call if connection is lost
            if e.errno == 2006: # MySQL server has gone away
                self._db_connection = None
        finally:
            if cursor:
                cursor.close()

    async def store_segment(self, segment_data: Dict[str, Any]):
        """Saves a transcription segment to both JSON and the database."""
        await self.save_json(segment_data)
        self.save_to_db(segment_data)

# Global storage instance
storage_manager = StorageManager()