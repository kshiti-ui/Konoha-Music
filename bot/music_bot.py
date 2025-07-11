import discord
from discord.ext import commands
import logging
from .music_player import MusicPlayer
from .commands import MusicCommands
from config import Config

# Load Opus library for voice support
import os
import ctypes.util

def load_opus():
    # Try to load opus library
    if not discord.opus.is_loaded():
        # Try different possible opus library names
        opus_libs = [
            'libopus.so.0',
            'libopus.so',
            'opus',
            ctypes.util.find_library('opus')
        ]
        
        for lib in opus_libs:
            if lib:
                try:
                    discord.opus.load_opus(lib)
                    print(f"Successfully loaded opus library: {lib}")
                    break
                except Exception as e:
                    print(f"Failed to load {lib}: {e}")
                    continue
        else:
            print("Could not load opus library - trying to continue without it")

load_opus()

class MusicBot(commands.Bot):
    """Main Discord music bot class."""
    
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.voice_states = True
        intents.guilds = True
        
        super().__init__(
            command_prefix=Config.COMMAND_PREFIX,
            intents=intents,
            help_command=None
        )
        
        self.music_players = {}
        self.logger = logging.getLogger(__name__)
        
    async def setup_hook(self):
        """Setup hook called when bot is ready."""
        # Add music commands cog
        await self.add_cog(MusicCommands(self))
        
        # Sync slash commands
        try:
            synced = await self.tree.sync()
            self.logger.info(f"Synced {len(synced)} slash commands")
        except Exception as e:
            self.logger.error(f"Failed to sync slash commands: {e}")
    
    async def on_ready(self):
        """Event triggered when bot is ready."""
        self.logger.info(f'{self.user} has connected to Discord!')
        self.logger.info(f'Bot is in {len(self.guilds)} guilds')
        
        # Set bot status
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.listening, 
                name="music | /play"
            )
        )
    
    async def on_voice_state_update(self, member, before, after):
        """Handle voice state updates."""
        if member == self.user:
            return
            
        guild_id = member.guild.id
        if guild_id not in self.music_players:
            return
            
        voice_client = self.music_players[guild_id].voice_client
        if not voice_client:
            return
            
        # Check if bot is alone in voice channel
        if len(voice_client.channel.members) == 1:
            await self.music_players[guild_id].cleanup()
            del self.music_players[guild_id]
    
    async def on_message(self, message):
        """Handle messages."""
        if message.author.bot:
            return
        
        # Process regular commands
        await self.process_commands(message)
    
    def get_music_player(self, guild_id):
        """Get or create music player for guild."""
        if guild_id not in self.music_players:
            self.music_players[guild_id] = MusicPlayer(self, guild_id)
        return self.music_players[guild_id]
    
    async def on_command_error(self, ctx, error):
        """Handle command errors."""
        if isinstance(error, commands.CommandNotFound):
            return
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"❌ Missing required argument: {error.param}")
        elif isinstance(error, commands.BadArgument):
            await ctx.send(f"❌ Invalid argument provided")
        else:
            self.logger.error(f"Command error: {error}")
            await ctx.send("❌ An error occurred while processing the command")
