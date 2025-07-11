import discord
import asyncio
import logging
from .queue_manager import QueueManager
from .utils import YTDLSource
from config import Config

class MusicPlayer:
    """Music player for a specific guild."""
    
    def __init__(self, bot, guild_id):
        self.bot = bot
        self.guild_id = guild_id
        self.voice_client = None
        self.queue = QueueManager()
        self.current_song = None
        self.previous_songs = []  # Store previous songs for previous command
        self.is_playing = False
        self.is_paused = False
        self.loop_mode = False
        self.volume = Config.DEFAULT_VOLUME
        self.logger = logging.getLogger(__name__)
        
    async def connect(self, channel):
        """Connect to voice channel."""
        try:
            if self.voice_client is None:
                self.voice_client = await channel.connect()
            elif self.voice_client.channel != channel:
                await self.voice_client.move_to(channel)
            return True
        except Exception as e:
            self.logger.error(f"Failed to connect to voice channel: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from voice channel."""
        if self.voice_client:
            await self.voice_client.disconnect()
            self.voice_client = None
    
    async def play_next(self):
        """Play next song in queue."""
        # Add current song to previous songs if it exists
        if self.current_song and not self.loop_mode:
            self.previous_songs.append(self.current_song)
            # Keep only last 10 previous songs
            if len(self.previous_songs) > 10:
                self.previous_songs.pop(0)
        
        if self.loop_mode and self.current_song:
            # Add current song back to front of queue for looping
            self.queue.add_to_front(self.current_song)
        
        if self.queue.is_empty():
            self.is_playing = False
            self.current_song = None
            return
        
        next_song = self.queue.get_next()
        await self.play_song(next_song)
    
    async def play_song(self, song_info):
        """Play a specific song."""
        try:
            if not self.voice_client:
                self.logger.error("No voice client available")
                return
            
            # Create audio source
            source = await YTDLSource.create_source(song_info['url'])
            if not source:
                self.logger.error(f"Failed to create audio source for {song_info['title']}")
                await self.play_next()
                return
            
            # Set volume
            if hasattr(source, 'volume'):
                source.volume = self.volume
            
            # Play audio
            self.voice_client.play(
                source,
                after=lambda e: asyncio.run_coroutine_threadsafe(
                    self.play_next(), self.bot.loop
                ) if not e else self.logger.error(f"Player error: {e}")
            )
            
            self.current_song = song_info
            self.is_playing = True
            self.is_paused = False
            
        except Exception as e:
            self.logger.error(f"Error playing song: {e}")
            await self.play_next()
    
    async def add_to_queue(self, query, requester):
        """Add song to queue."""
        try:
            song_info = await YTDLSource.search(query)
            if not song_info:
                return None
            
            song_info['requester'] = requester
            self.queue.add(song_info)
            
            # If nothing is playing, start playing
            if not self.is_playing:
                await self.play_next()
            
            return song_info
        except Exception as e:
            self.logger.error(f"Error adding to queue: {e}")
            return None
    
    def pause(self):
        """Pause playback."""
        if self.voice_client and self.voice_client.is_playing():
            self.voice_client.pause()
            self.is_paused = True
    
    def resume(self):
        """Resume playback."""
        if self.voice_client and self.voice_client.is_paused():
            self.voice_client.resume()
            self.is_paused = False
    
    def stop(self):
        """Stop playback."""
        if self.voice_client and self.voice_client.is_playing():
            self.voice_client.stop()
        self.is_playing = False
        self.is_paused = False
        self.current_song = None
    
    def skip(self):
        """Skip current song."""
        if self.voice_client and self.voice_client.is_playing():
            self.voice_client.stop()
    
    def toggle_loop(self):
        """Toggle loop mode."""
        self.loop_mode = not self.loop_mode
        return self.loop_mode
    
    def clear_queue(self):
        """Clear the queue."""
        self.queue.clear()
    
    def get_queue_info(self):
        """Get queue information."""
        return {
            'current': self.current_song,
            'queue': self.queue.get_all(),
            'is_playing': self.is_playing,
            'is_paused': self.is_paused,
            'loop_mode': self.loop_mode
        }
    
    async def cleanup(self):
        """Clean up resources."""
        self.stop()
        await self.disconnect()
        self.queue.clear()
        self.previous_songs.clear()
