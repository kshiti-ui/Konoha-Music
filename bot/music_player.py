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
        self.is_playing = False
        self.is_paused = False
        self.loop_mode = "off"  # "off", "current", "queue"
        self.volume = 1.0
        self.previous_songs = []  # Store previous songs for previous command
        self.logger = logging.getLogger(__name__)
        self.cleanup_task = None
        self.setup_panels = []  # Store setup panel references
        self.sync_task = None  # Continuous sync task
        self.last_sync_state = None  # Track last known state

    async def connect(self, channel):
        """Connect to voice channel."""
        try:
            if self.voice_client is None:
                self.voice_client = await channel.connect()
                # Self deafen the bot when joining
                await self.voice_client.guild.me.edit(deafen=True, mute=False)
            elif self.voice_client.channel != channel:
                await self.voice_client.move_to(channel)
                # Self deafen the bot when moving
                await self.voice_client.guild.me.edit(deafen=True, mute=False)
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
        # Handle loop modes
        if self.loop_mode == "current" and self.current_song:
            # Loop current song - add it back to front of queue
            self.queue.add_to_front(self.current_song)
        elif self.loop_mode == "queue" and self.current_song:
            # Loop queue - add current song to end of queue
            self.queue.add(self.current_song)
        elif self.loop_mode == "off" and self.current_song:
            # No loop - add to previous songs
            self.previous_songs.append(self.current_song)
            # Keep only last 10 previous songs
            if len(self.previous_songs) > 10:
                self.previous_songs.pop(0)

        if self.queue.is_empty():
            self.is_playing = False
            self.current_song = None
            # Set status when queue is empty
            await self.update_channel_status("Konoha Music was here")
            # Sync panels to show "No Song Playing" state
            await self.sync_setup_panels()
            # Auto-disconnect after queue ends
            await asyncio.sleep(10)  # Wait 10 seconds before disconnecting
            if self.queue.is_empty() and not self.is_playing:
                await self.cleanup()
                if self.guild_id in self.bot.music_players:
                    del self.bot.music_players[self.guild_id]
                self.logger.info("Auto-disconnected due to empty queue")
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
            source = await YTDLSource.create_source(song_info['url'], volume=self.volume)
            if not source:
                self.logger.error(f"Failed to create audio source for {song_info['title']}")
                await self.play_next()
                return

            # Set volume
            if hasattr(source, 'volume'):
                source.volume = self.volume

            def after_playing(error):
                if error:
                    self.logger.error(f"Player error: {error}")
                else:
                    self.logger.info(f"Finished playing: {song_info['title']}")

                # Schedule next song
                coro = self.play_next()
                future = asyncio.run_coroutine_threadsafe(coro, self.bot.loop)
                try:
                    future.result()
                except Exception as e:
                    self.logger.error(f"Error in after_playing: {e}")

            # Play audio
            self.voice_client.play(source, after=after_playing)

            self.current_song = song_info
            self.is_playing = True
            self.is_paused = False

            # Update channel status with now playing
            await self.update_channel_status(f"Now Playing: {song_info['title']}")

            # Sync setup panels
            await self.sync_setup_panels()

            self.logger.info(f"Now playing: {song_info['title']}")

        except Exception as e:
            self.logger.error(f"Error playing song: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
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
            # Update status to show paused state
            if self.current_song:
                asyncio.create_task(self.update_channel_status(f"⏸️ Paused: {self.current_song['title']}"))
            # Sync panels
            asyncio.create_task(self.sync_setup_panels())

    def resume(self):
        """Resume playback."""
        if self.voice_client and self.voice_client.is_paused():
            self.voice_client.resume()
            self.is_paused = False
            # Update status back to now playing
            if self.current_song:
                asyncio.create_task(self.update_channel_status(f"Now Playing: {self.current_song['title']}"))
            # Sync panels
            asyncio.create_task(self.sync_setup_panels())

    def stop(self):
        """Stop playback."""
        if self.voice_client and self.voice_client.is_playing():
            self.voice_client.stop()
        self.is_playing = False
        self.is_paused = False
        self.current_song = None
        # Set status when stopped
        asyncio.create_task(self.update_channel_status("Konoha Music was here"))
        # Sync panels
        asyncio.create_task(self.sync_setup_panels())

    def register_setup_panel(self, panel):
        """Register a setup panel for auto-updates."""
        self.setup_panels.append(panel)
        
        # Start continuous sync if not already running
        if not self.sync_task or self.sync_task.done():
            self.sync_task = asyncio.create_task(self.continuous_sync())

    async def continuous_sync(self):
        """Continuously sync panels with real-time state monitoring."""
        while self.setup_panels:
            try:
                await asyncio.sleep(2)  # Check every 2 seconds
                
                # Get current state
                current_state = self.get_current_state()
                
                # Only sync if state changed
                if current_state != self.last_sync_state:
                    await self.sync_setup_panels()
                    self.last_sync_state = current_state
                    self.logger.info(f"Panel synced - State: {current_state}")
                
            except Exception as e:
                self.logger.error(f"Error in continuous sync: {e}")
                await asyncio.sleep(5)  # Wait longer if error
        
        # Stop task if no panels
        if self.sync_task and not self.sync_task.done():
            self.sync_task.cancel()

    def get_current_state(self):
        """Get current player state for comparison."""
        return {
            'is_playing': self.is_playing,
            'is_paused': self.is_paused,
            'loop_mode': self.loop_mode,
            'volume': self.volume,
            'current_song': self.current_song['title'] if self.current_song else None,
            'queue_length': len(self.queue.get_all()),
            'voice_connected': self.voice_client is not None and self.voice_client.is_connected()
        }

    async def sync_setup_panels(self):
        """Sync all registered setup panels."""
        panels_to_remove = []
        for panel in self.setup_panels:
            try:
                await panel.sync_panel()
                # Update button states
                if hasattr(panel, 'update_button_states'):
                    panel.update_button_states(self)
            except Exception as e:
                self.logger.error(f"Panel sync error: {e}")
                # Mark for removal
                panels_to_remove.append(panel)
        
        # Remove invalid panels
        for panel in panels_to_remove:
            self.setup_panels.remove(panel)

    def skip(self):
        """Skip current song."""
        if self.voice_client and self.voice_client.is_playing():
            self.voice_client.stop()

    def toggle_loop(self):
        """Toggle loop mode between off, current, and queue."""
        if self.loop_mode == "off":
            self.loop_mode = "current"
        elif self.loop_mode == "current":
            self.loop_mode = "queue"
        else:
            self.loop_mode = "off"
        
        # Sync panels
        asyncio.create_task(self.sync_setup_panels())
        return self.loop_mode

    def set_volume(self, volume):
        """Set the volume (0.0 to 1.0)."""
        self.volume = max(0.0, min(1.0, volume))
        
        # Update current playing source volume if exists
        if self.voice_client and self.voice_client.source:
            if hasattr(self.voice_client.source, 'volume'):
                self.voice_client.source.volume = self.volume
        
        # Sync panels to update volume display
        asyncio.create_task(self.sync_setup_panels())

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

    async def update_channel_status(self, status):
        """Update the voice channel status."""
        try:
            if self.voice_client and self.voice_client.channel:
                await self.voice_client.channel.edit(status=status)
                self.logger.info(f"Updated channel status: {status}")
        except Exception as e:
            self.logger.error(f"Failed to update channel status: {e}")

    async def cleanup(self):
        """Clean up resources."""
        # Set disconnect status before cleanup
        await self.update_channel_status("Konoha Music was here")

        # Stop continuous sync task
        if self.sync_task and not self.sync_task.done():
            self.sync_task.cancel()

        self.stop()
        await self.disconnect()
        self.queue.clear()
        self.previous_songs.clear()
        self.setup_panels.clear()