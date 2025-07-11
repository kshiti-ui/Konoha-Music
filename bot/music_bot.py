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
        """Handle messages in setup channels."""
        if message.author.bot:
            return
        
        # Check if message is in a setup channel
        if hasattr(self, 'cogs') and 'MusicCommands' in [cog.__class__.__name__ for cog in self.cogs.values()]:
            music_cog = discord.utils.get(self.cogs.values(), qualified_name='MusicCommands')
            if music_cog and message.guild and message.guild.id in music_cog.setup_channels:
                if message.channel.id == music_cog.setup_channels[message.guild.id]:
                    # This is a setup channel, treat message as a song request
                    if not message.author.voice:
                        await message.add_reaction("❌")
                        await message.reply("❌ You need to be in a voice channel to request songs!", delete_after=10)
                        return
                    
                    # Add song to queue
                    voice_channel = message.author.voice.channel
                    music_player = self.get_music_player(message.guild.id)
                    
                    if not await music_player.connect(voice_channel):
                        await message.add_reaction("❌")
                        await message.reply("❌ Failed to connect to voice channel!", delete_after=10)
                        return
                    
                    # Add to queue
                    song_info = await music_player.add_to_queue(message.content, message.author)
                    if song_info:
                        await message.add_reaction("✅")
                        platform_emoji = {
                            'youtube': '🎥',
                            'spotify': '🎵',
                            'soundcloud': '🔊'
                        }.get(song_info.get('platform', 'youtube'), '🎵')
                        
                        embed = discord.Embed(
                            title=f"{platform_emoji} Added to Queue",
                            description=f"**{song_info['title']}**\nRequested by {message.author.mention}",
                            color=discord.Color.green()
                        )
                        if song_info.get('thumbnail'):
                            embed.set_thumbnail(url=song_info['thumbnail'])
                        
                        await message.reply(embed=embed, delete_after=15)
                    else:
                        await message.add_reaction("❌")
                        await message.reply("❌ Failed to find or add the song to queue!", delete_after=10)
                    
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
