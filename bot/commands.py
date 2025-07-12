import discord
from discord.ext import commands
from discord import app_commands
import logging
from .utils import format_duration
import asyncio

class MusicCommands(commands.Cog):
    """Music commands for the Discord bot."""
    
    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger(__name__)
    
    @app_commands.command(name="play", description="Play a song or add it to queue")
    async def play_slash(self, interaction: discord.Interaction, query: str):
        """Play command via slash command."""
        await interaction.response.defer()
        
        # Check if user is in voice channel
        if not interaction.user.voice:
            await interaction.followup.send("❌ You need to be in a voice channel to use this command!")
            return
        
        voice_channel = interaction.user.voice.channel
        music_player = self.bot.get_music_player(interaction.guild.id)
        
        # Connect to voice channel
        if not await music_player.connect(voice_channel):
            await interaction.followup.send("❌ Failed to connect to voice channel!")
            return
        
        # Add to queue
        song_info = await music_player.add_to_queue(query, interaction.user)
        if song_info:
            platform_emoji = {
                'youtube': '🎥',
                'spotify': '🎵',
                'soundcloud': '🔊'
            }.get(song_info.get('platform', 'youtube'), '🎵')
            
            embed = discord.Embed(
                title=f"{platform_emoji} Added to Queue",
                description=f"**[{song_info['title']}]({song_info.get('url', '')})**\nRequested by {interaction.user.mention}",
                color=discord.Color.green()
            )
            if song_info.get('duration'):
                embed.add_field(name="⏱️ Duration", value=format_duration(song_info['duration']), inline=True)
            if song_info.get('uploader'):
                embed.add_field(name="👤 Author", value=song_info['uploader'], inline=True)
            embed.add_field(name="🔗 Source", value=song_info.get('platform', 'youtube').title(), inline=True)
            if song_info.get('url'):
                embed.add_field(name="🎵 Watch", value=f"[Link]({song_info['url']})", inline=True)
            if song_info.get('thumbnail'):
                embed.set_thumbnail(url=song_info['thumbnail'])
            await interaction.followup.send(embed=embed)
        else:
            await interaction.followup.send("❌ Failed to find or add the song to queue!")
    
    @app_commands.command(name="pause", description="Pause the current song")
    async def pause_slash(self, interaction: discord.Interaction):
        """Pause command via slash command."""
        music_player = self.bot.get_music_player(interaction.guild.id)
        
        if not music_player.is_playing:
            await interaction.response.send_message("❌ Nothing is currently playing!")
            return
        
        music_player.pause()
        await interaction.response.send_message("⏸️ Paused the current song")
    
    @app_commands.command(name="resume", description="Resume the paused song")
    async def resume_slash(self, interaction: discord.Interaction):
        """Resume command via slash command."""
        music_player = self.bot.get_music_player(interaction.guild.id)
        
        if not music_player.is_paused:
            await interaction.response.send_message("❌ Nothing is currently paused!")
            return
        
        music_player.resume()
        await interaction.response.send_message("▶️ Resumed the song")
    
    @app_commands.command(name="skip", description="Skip the current song")
    async def skip_slash(self, interaction: discord.Interaction):
        """Skip command via slash command."""
        music_player = self.bot.get_music_player(interaction.guild.id)
        
        if not music_player.is_playing:
            await interaction.response.send_message("❌ Nothing is currently playing!")
            return
        
        music_player.skip()
        await interaction.response.send_message("⏭️ Skipped the current song")
    
    @app_commands.command(name="stop", description="Stop playing and clear the queue")
    async def stop_slash(self, interaction: discord.Interaction):
        """Stop command via slash command."""
        music_player = self.bot.get_music_player(interaction.guild.id)
        
        music_player.stop()
        music_player.clear_queue()
        await interaction.response.send_message("⏹️ Stopped playing and cleared the queue")
    
    @app_commands.command(name="loop", description="Toggle loop mode")
    async def loop_slash(self, interaction: discord.Interaction):
        """Loop command via slash command."""
        music_player = self.bot.get_music_player(interaction.guild.id)
        
        loop_status = music_player.toggle_loop()
        status_text = "enabled" if loop_status else "disabled"
        await interaction.response.send_message(f"🔄 Loop mode {status_text}")
    
    @app_commands.command(name="queue", description="Show the current queue")
    async def queue_slash(self, interaction: discord.Interaction):
        """Queue command via slash command."""
        music_player = self.bot.get_music_player(interaction.guild.id)
        queue_info = music_player.get_queue_info()
        
        embed = discord.Embed(title="🎵 Current Queue", color=discord.Color.blue())
        
        if queue_info['current']:
            embed.add_field(
                name="Now Playing",
                value=f"**{queue_info['current']['title']}**\nRequested by {queue_info['current']['requester'].mention}",
                inline=False
            )
        
        if queue_info['queue']:
            queue_text = ""
            for i, song in enumerate(queue_info['queue'][:10]):  # Show first 10 songs
                queue_text += f"{i+1}. **{song['title']}** - {song['requester'].mention}\n"
            
            if len(queue_info['queue']) > 10:
                queue_text += f"... and {len(queue_info['queue']) - 10} more songs"
            
            embed.add_field(name="Up Next", value=queue_text, inline=False)
        else:
            embed.add_field(name="Up Next", value="Queue is empty", inline=False)
        
        # Add status info
        status_text = f"Playing: {queue_info['is_playing']}\n"
        status_text += f"Paused: {queue_info['is_paused']}\n"
        status_text += f"Loop: {queue_info['loop_mode']}"
        embed.add_field(name="Status", value=status_text, inline=True)
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="clear", description="Clear messages from the channel")
    async def clear_slash(self, interaction: discord.Interaction, amount: int = 10):
        """Clear messages command via slash command."""
        if not interaction.user.guild_permissions.manage_messages:
            await interaction.response.send_message("❌ You don't have permission to manage messages!")
            return
        
        if amount < 1 or amount > 100:
            await interaction.response.send_message("❌ Amount must be between 1 and 100!")
            return
        
        await interaction.response.defer()
        
        try:
            deleted = await interaction.channel.purge(limit=amount)
            await interaction.followup.send(f"🗑️ Deleted {len(deleted)} messages", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ Failed to delete messages: {e}")
    
    @app_commands.command(name="disconnect", description="Disconnect the bot from voice channel")
    async def disconnect_slash(self, interaction: discord.Interaction):
        """Disconnect command via slash command."""
        music_player = self.bot.get_music_player(interaction.guild.id)
        
        await music_player.cleanup()
        if interaction.guild.id in self.bot.music_players:
            del self.bot.music_players[interaction.guild.id]
        
        await interaction.response.send_message("👋 Disconnected from voice channel")
    
    @app_commands.command(name="shuffle", description="Shuffle the current queue")
    async def shuffle_slash(self, interaction: discord.Interaction):
        """Shuffle command via slash command."""
        music_player = self.bot.get_music_player(interaction.guild.id)
        
        if music_player.queue.is_empty():
            await interaction.response.send_message("❌ Queue is empty!")
            return
        
        music_player.queue.shuffle()
        await interaction.response.send_message("🔀 Shuffled the queue!")
    
    @app_commands.command(name="rewind", description="Restart the current song")
    async def rewind_slash(self, interaction: discord.Interaction):
        """Rewind command via slash command."""
        music_player = self.bot.get_music_player(interaction.guild.id)
        
        if not music_player.current_song:
            await interaction.response.send_message("❌ No song is currently playing!")
            return
        
        # Stop current song and replay it
        if music_player.voice_client and music_player.voice_client.is_playing():
            music_player.voice_client.stop()
        
        # Add current song to front of queue
        music_player.queue.add_to_front(music_player.current_song)
        
        await interaction.response.send_message("⏪ Rewinding current song!")
    
    @app_commands.command(name="previous", description="Go back to previous song")
    async def previous_slash(self, interaction: discord.Interaction):
        """Previous command via slash command."""
        music_player = self.bot.get_music_player(interaction.guild.id)
        
        if not hasattr(music_player, 'previous_songs') or not music_player.previous_songs:
            await interaction.response.send_message("❌ No previous songs available!")
            return
        
        # Get previous song
        prev_song = music_player.previous_songs.pop()
        
        # Stop current song
        if music_player.voice_client and music_player.voice_client.is_playing():
            music_player.voice_client.stop()
        
        # Add current song back to queue if it exists
        if music_player.current_song:
            music_player.queue.add_to_front(music_player.current_song)
        
        # Add previous song to front of queue
        music_player.queue.add_to_front(prev_song)
        
        await interaction.response.send_message("⏮️ Playing previous song!")
    
    @app_commands.command(name="ping", description="Check bot latency")
    async def ping_slash(self, interaction: discord.Interaction):
        """Ping command via slash command."""
        latency = round(self.bot.latency * 1000)
        await interaction.response.send_message(f"🏓 Pong! Latency: {latency}ms")
    
    @app_commands.command(name="commands", description="Display all available bot commands")
    async def commands_slash(self, interaction: discord.Interaction):
        """Commands command via slash command."""
        embed = discord.Embed(
            title="🎵 Music Bot Commands",
            description="Here are all the available commands for the music bot:",
            color=0x9932CC
        )
        
        # Music commands
        embed.add_field(
            name="🎵 Music Commands",
            value=(
                "`/play <song>` - Play a song or add it to queue\n"
                "`/pause` - Pause the current song\n"
                "`/resume` - Resume the paused song\n"
                "`/skip` - Skip the current song\n"
                "`/stop` - Stop playing and clear the queue\n"
                "`/loop` - Toggle loop mode\n"
                "`/queue` - Show the current queue\n"
                "`/shuffle` - Shuffle the current queue\n"
                "`/rewind` - Restart the current song\n"
                "`/previous` - Go back to previous song"
            ),
            inline=False
        )
        
        # Utility commands
        embed.add_field(
            name="🛠️ Utility Commands",
            value=(
                "`/disconnect` - Disconnect from voice channel\n"
                "`/clear <amount>` - Clear messages from channel\n"
                "`/ping` - Check bot latency\n"
                "`/setup` - Setup music control panel\n"
                "`/commands` - Display this help message"
            ),
            inline=False
        )
        
        # Platform support
        embed.add_field(
            name="🌐 Supported Platforms",
            value=(
                "🎥 **YouTube** - Direct playback\n"
                "🎵 **Spotify** - Converted to YouTube search\n"
                "🔊 **SoundCloud** - Direct playback"
            ),
            inline=False
        )
        
        embed.set_footer(text="Use slash commands (/) to interact with the bot")
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="setup", description="Setup interactive music control panel")
    async def setup_slash(self, interaction: discord.Interaction):
        """Setup command to create music control panel."""
        await interaction.response.defer()
        
        # Clear the channel (delete last 50 messages)
        try:
            deleted = await interaction.channel.purge(limit=50)
            self.logger.info(f"Cleared {len(deleted)} messages for setup")
        except Exception as e:
            self.logger.error(f"Failed to clear messages: {e}")
        
        # Wait 3 seconds
        await asyncio.sleep(3)
        
        # Get music player info
        music_player = self.bot.get_music_player(interaction.guild.id)
        
        # Create the main embed for current song
        if music_player.current_song:
            current = music_player.current_song
            platform_emoji = {
                'youtube': '🎥',
                'spotify': '🎵', 
                'soundcloud': '🔊'
            }.get(current.get('platform', 'youtube'), '🎵')
            
            # Status based on playing state
            if music_player.is_paused:
                status = "⏸️ Paused"
            elif music_player.is_playing:
                status = "🎵 Now Playing"
            else:
                status = "⏹️ Stopped"
                
            embed = discord.Embed(
                title=f"[ {status} ]",
                description=f"**{current['title']}**",
                color=discord.Color.purple()
            )
            
            # Add song details in a clean layout
            embed.add_field(
                name="🎵 Song Details",
                value=(
                    f"**{platform_emoji} {current['title']}**\n"
                    f"🎤 **Author:** {current.get('uploader', 'Unknown')}\n"
                    f"🔗 **Source:** {current.get('platform', 'youtube').title()}\n"
                    f"⏱️ **Duration:** {format_duration(current.get('duration', 0))}\n"
                    f"👤 **Requested By:** {current['requester'].mention}"
                ),
                inline=False
            )
            
            # Add thumbnail if available
            if current.get('thumbnail'):
                embed.set_image(url=current['thumbnail'])
            
            # Add volume info
            embed.add_field(
                name="🔊 Volume",
                value=f"{int(music_player.volume * 100)}%",
                inline=True
            )
            
            # Add loop status
            loop_status = "🔄 On" if music_player.loop_mode else "🔄 Off"
            embed.add_field(
                name="Loop Mode",
                value=loop_status,
                inline=True
            )
            
            # Add queue count
            queue_count = len(music_player.queue.get_all())
            embed.add_field(
                name="📋 Queue",
                value=f"{queue_count} songs",
                inline=True
            )
            
        else:
            embed = discord.Embed(
                title="[ No Song Playing ]",
                description="Use `/play <song>` to start playing music!",
                color=discord.Color.purple()
            )
            embed.add_field(
                name="🎵 Status",
                value="No music playing\nQueue is empty",
                inline=False
            )
        
        embed.set_footer(text="Music Control Panel • Use buttons below to control playback")
        
        # Send the embed with control buttons
        message = await interaction.followup.send(
            embed=embed,
            view=SetupControlView(self.bot, interaction.channel.id)
        )
    
    # Text-based commands for backward compatibility
    @commands.command(name="play", aliases=['p'])
    async def play_text(self, ctx, *, query):
        """Play command via text."""
        if not ctx.author.voice:
            await ctx.send("❌ You need to be in a voice channel to use this command!")
            return
        
        voice_channel = ctx.author.voice.channel
        music_player = self.bot.get_music_player(ctx.guild.id)
        
        if not await music_player.connect(voice_channel):
            await ctx.send("❌ Failed to connect to voice channel!")
            return
        
        song_info = await music_player.add_to_queue(query, ctx.author)
        if song_info:
            await ctx.send(f"🎵 Added **{song_info['title']}** to queue")
        else:
            await ctx.send("❌ Failed to find or add the song to queue!")
    
    @commands.command(name="pause")
    async def pause_text(self, ctx):
        """Pause command via text."""
        music_player = self.bot.get_music_player(ctx.guild.id)
        
        if not music_player.is_playing:
            await ctx.send("❌ Nothing is currently playing!")
            return
        
        music_player.pause()
        await ctx.send("⏸️ Paused the current song")
    
    @commands.command(name="resume")
    async def resume_text(self, ctx):
        """Resume command via text."""
        music_player = self.bot.get_music_player(ctx.guild.id)
        
        if not music_player.is_paused:
            await ctx.send("❌ Nothing is currently paused!")
            return
        
        music_player.resume()
        await ctx.send("▶️ Resumed the song")
    
    @commands.command(name="skip", aliases=['s'])
    async def skip_text(self, ctx):
        """Skip command via text."""
        music_player = self.bot.get_music_player(ctx.guild.id)
        
        if not music_player.is_playing:
            await ctx.send("❌ Nothing is currently playing!")
            return
        
        music_player.skip()
        await ctx.send("⏭️ Skipped the current song")
    
    @commands.command(name="stop")
    async def stop_text(self, ctx):
        """Stop command via text."""
        music_player = self.bot.get_music_player(ctx.guild.id)
        
        music_player.stop()
        music_player.clear_queue()
        await ctx.send("⏹️ Stopped playing and cleared the queue")
    
    @commands.command(name="loop")
    async def loop_text(self, ctx):
        """Loop command via text."""
        music_player = self.bot.get_music_player(ctx.guild.id)
        
        loop_status = music_player.toggle_loop()
        status_text = "enabled" if loop_status else "disabled"
        await ctx.send(f"🔄 Loop mode {status_text}")
    
    @commands.command(name="queue", aliases=['q'])
    async def queue_text(self, ctx):
        """Queue command via text."""
        music_player = self.bot.get_music_player(ctx.guild.id)
        queue_info = music_player.get_queue_info()
        
        embed = discord.Embed(title="🎵 Current Queue", color=discord.Color.blue())
        
        if queue_info['current']:
            embed.add_field(
                name="Now Playing",
                value=f"**{queue_info['current']['title']}**\nRequested by {queue_info['current']['requester'].mention}",
                inline=False
            )
        
        if queue_info['queue']:
            queue_text = ""
            for i, song in enumerate(queue_info['queue'][:10]):
                queue_text += f"{i+1}. **{song['title']}** - {song['requester'].mention}\n"
            
            if len(queue_info['queue']) > 10:
                queue_text += f"... and {len(queue_info['queue']) - 10} more songs"
            
            embed.add_field(name="Up Next", value=queue_text, inline=False)
        else:
            embed.add_field(name="Up Next", value="Queue is empty", inline=False)
        
        await ctx.send(embed=embed)
    
    @commands.command(name="clear")
    @commands.has_permissions(manage_messages=True)
    async def clear_text(self, ctx, amount: int = 10):
        """Clear messages command via text."""
        if amount < 1 or amount > 100:
            await ctx.send("❌ Amount must be between 1 and 100!")
            return
        
        try:
            deleted = await ctx.channel.purge(limit=amount + 1)  # +1 to include the command message
            await ctx.send(f"🗑️ Deleted {len(deleted) - 1} messages", delete_after=5)
        except Exception as e:
            await ctx.send(f"❌ Failed to delete messages: {e}")

class MusicControlView(discord.ui.View):
    """Interactive music control panel with buttons."""
    
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot
    
    @discord.ui.button(label="Pause", style=discord.ButtonStyle.primary, emoji="⏸️")
    async def pause_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Pause button handler."""
        music_player = self.bot.get_music_player(interaction.guild.id)
        
        if not music_player.is_playing:
            await interaction.response.send_message("❌ Nothing is currently playing!", ephemeral=True)
            return
        
        music_player.pause()
        await interaction.response.send_message("⏸️ Paused the current song", ephemeral=True)
    
    @discord.ui.button(label="Previous", style=discord.ButtonStyle.secondary, emoji="⏮️")
    async def previous_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Previous button handler."""
        music_player = self.bot.get_music_player(interaction.guild.id)
        
        if not hasattr(music_player, 'previous_songs') or not music_player.previous_songs:
            await interaction.response.send_message("❌ No previous songs available!", ephemeral=True)
            return
        
        prev_song = music_player.previous_songs.pop()
        
        if music_player.voice_client and music_player.voice_client.is_playing():
            music_player.voice_client.stop()
        
        if music_player.current_song:
            music_player.queue.add_to_front(music_player.current_song)
        
        music_player.queue.add_to_front(prev_song)
        await interaction.response.send_message("⏮️ Playing previous song!", ephemeral=True)
    
    @discord.ui.button(label="Skip", style=discord.ButtonStyle.secondary, emoji="⏭️")
    async def skip_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Skip button handler."""
        music_player = self.bot.get_music_player(interaction.guild.id)
        
        if not music_player.is_playing:
            await interaction.response.send_message("❌ Nothing is currently playing!", ephemeral=True)
            return
        
        music_player.skip()
        await interaction.response.send_message("⏭️ Skipped the current song", ephemeral=True)
    
    @discord.ui.button(label="Stop", style=discord.ButtonStyle.danger, emoji="⏹️")
    async def stop_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Stop button handler."""
        music_player = self.bot.get_music_player(interaction.guild.id)
        
        music_player.stop()
        music_player.clear_queue()
        await interaction.response.send_message("⏹️ Stopped playing and cleared the queue", ephemeral=True)
    
    @discord.ui.button(label="Repair", style=discord.ButtonStyle.secondary, emoji="🔧")
    async def repair_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Repair button handler (reconnect to voice)."""
        await interaction.response.defer(ephemeral=True)
        
        if not interaction.user.voice:
            await interaction.followup.send("❌ You need to be in a voice channel for repair!", ephemeral=True)
            return
        
        music_player = self.bot.get_music_player(interaction.guild.id)
        
        # Disconnect and reconnect
        if music_player.voice_client:
            await music_player.voice_client.disconnect()
        
        # Reconnect to voice channel
        voice_channel = interaction.user.voice.channel
        if await music_player.connect(voice_channel):
            await interaction.followup.send("🔧 Repaired voice connection!", ephemeral=True)
        else:
            await interaction.followup.send("❌ Failed to repair voice connection!", ephemeral=True)

# Setup Control Panel View
class SetupControlView(discord.ui.View):
    """Comprehensive music control panel for setup command."""
    
    def __init__(self, bot, channel_id):
        super().__init__(timeout=None)
        self.bot = bot
        self.channel_id = channel_id
        
        # Set initial button states
        guild_id = None
        for guild in bot.guilds:
            for channel in guild.channels:
                if channel.id == channel_id:
                    guild_id = guild.id
                    break
            if guild_id:
                break
        
        if guild_id:
            music_player = bot.get_music_player(guild_id)
            
            # Set pause/resume button
            pause_button = [item for item in self.children if hasattr(item, 'label') and 'Pause' in item.label][0]
            if music_player.is_paused:
                pause_button.label = "Resume"
                pause_button.emoji = "▶️"
            
            # Set loop button
            loop_button = [item for item in self.children if hasattr(item, 'label') and 'Loop' in item.label][0]
            if music_player.loop_mode:
                loop_button.label = "Loop On"
                loop_button.style = discord.ButtonStyle.success
    
    async def update_panel(self, interaction):
        """Update the control panel with current song info."""
        music_player = self.bot.get_music_player(interaction.guild.id)
        
        if music_player.current_song:
            current = music_player.current_song
            platform_emoji = {
                'youtube': '🎥',
                'spotify': '🎵', 
                'soundcloud': '🔊'
            }.get(current.get('platform', 'youtube'), '🎵')
            
            # Status based on playing state
            if music_player.is_paused:
                status = "⏸️ Paused"
            elif music_player.is_playing:
                status = "🎵 Now Playing"
            else:
                status = "⏹️ Stopped"
                
            embed = discord.Embed(
                title=f"[ {status} ]",
                description=f"**{current['title']}**",
                color=discord.Color.purple()
            )
            
            # Add song details
            embed.add_field(
                name="🎵 Song Details",
                value=(
                    f"**{platform_emoji} {current['title']}**\n"
                    f"🎤 **Author:** {current.get('uploader', 'Unknown')}\n"
                    f"🔗 **Source:** {current.get('platform', 'youtube').title()}\n"
                    f"⏱️ **Duration:** {format_duration(current.get('duration', 0))}\n"
                    f"👤 **Requested By:** {current['requester'].mention}"
                ),
                inline=False
            )
            
            if current.get('thumbnail'):
                embed.set_image(url=current['thumbnail'])
            
            # Status info
            embed.add_field(
                name="🔊 Volume",
                value=f"{int(music_player.volume * 100)}%",
                inline=True
            )
            
            loop_status = "🔄 On" if music_player.loop_mode else "🔄 Off"
            embed.add_field(
                name="Loop Mode",
                value=loop_status,
                inline=True
            )
            
            queue_count = len(music_player.queue.get_all())
            embed.add_field(
                name="📋 Queue",
                value=f"{queue_count} songs",
                inline=True
            )
        else:
            embed = discord.Embed(
                title="[ No Song Playing ]",
                description="Use `/play <song>` to start playing music!",
                color=discord.Color.purple()
            )
            embed.add_field(
                name="🎵 Status",
                value="No music playing\nQueue is empty",
                inline=False
            )
        
        embed.set_footer(text="Music Control Panel • Use buttons below to control playback")
        
        # Update the message
        try:
            await interaction.response.edit_message(embed=embed, view=self)
        except:
            try:
                await interaction.edit_original_response(embed=embed, view=self)
            except:
                await interaction.followup.edit_message(interaction.message.id, embed=embed, view=self)
    
    @discord.ui.button(label="Pause", style=discord.ButtonStyle.primary, emoji="⏸️", row=0)
    async def pause_resume_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Toggle pause/resume button."""
        music_player = self.bot.get_music_player(interaction.guild.id)
        
        if music_player.is_paused:
            music_player.resume()
            button.label = "Pause"
            button.emoji = "⏸️"
        elif music_player.is_playing:
            music_player.pause()
            button.label = "Resume"
            button.emoji = "▶️"
        else:
            await interaction.response.send_message("❌ Nothing is currently playing!", ephemeral=True)
            return
        
        await self.update_panel(interaction)
    
    @discord.ui.button(label="Previous", style=discord.ButtonStyle.secondary, emoji="⏮️", row=0)
    async def previous_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Previous song button."""
        music_player = self.bot.get_music_player(interaction.guild.id)
        
        if not hasattr(music_player, 'previous_songs') or not music_player.previous_songs:
            await interaction.response.send_message("❌ No previous songs available!", ephemeral=True)
            return
        
        prev_song = music_player.previous_songs.pop()
        
        if music_player.voice_client and music_player.voice_client.is_playing():
            music_player.voice_client.stop()
        
        if music_player.current_song:
            music_player.queue.add_to_front(music_player.current_song)
        
        music_player.queue.add_to_front(prev_song)
        
        await asyncio.sleep(1)  # Wait for song to start
        await self.update_panel(interaction)
    
    @discord.ui.button(label="Skip", style=discord.ButtonStyle.secondary, emoji="⏭️", row=0)
    async def skip_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Skip song button."""
        music_player = self.bot.get_music_player(interaction.guild.id)
        
        if not music_player.is_playing:
            await interaction.response.send_message("❌ Nothing is currently playing!", ephemeral=True)
            return
        
        music_player.skip()
        await asyncio.sleep(1)  # Wait for next song to start
        await self.update_panel(interaction)
    
    @discord.ui.button(label="Stop", style=discord.ButtonStyle.danger, emoji="⏹️", row=0)
    async def stop_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Stop playback button."""
        music_player = self.bot.get_music_player(interaction.guild.id)
        
        music_player.stop()
        music_player.clear_queue()
        await self.update_panel(interaction)
    
    @discord.ui.button(label="Queue", style=discord.ButtonStyle.secondary, emoji="📋", row=1)
    async def queue_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Show queue button."""
        music_player = self.bot.get_music_player(interaction.guild.id)
        queue_info = music_player.get_queue_info()
        
        embed = discord.Embed(title="🎵 Current Queue", color=discord.Color.blue())
        
        if queue_info['current']:
            embed.add_field(
                name="Now Playing",
                value=f"**{queue_info['current']['title']}**\nRequested by {queue_info['current']['requester'].mention}",
                inline=False
            )
        
        if queue_info['queue']:
            queue_text = ""
            for i, song in enumerate(queue_info['queue'][:10]):
                queue_text += f"{i+1}. **{song['title']}** - {song['requester'].mention}\n"
            
            if len(queue_info['queue']) > 10:
                queue_text += f"... and {len(queue_info['queue']) - 10} more songs"
            
            embed.add_field(name="Up Next", value=queue_text, inline=False)
        else:
            embed.add_field(name="Up Next", value="Queue is empty", inline=False)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @discord.ui.button(label="Rewind", style=discord.ButtonStyle.secondary, emoji="⏪", row=1)
    async def rewind_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Rewind current song button."""
        music_player = self.bot.get_music_player(interaction.guild.id)
        
        if not music_player.current_song:
            await interaction.response.send_message("❌ No song is currently playing!", ephemeral=True)
            return
        
        if music_player.voice_client and music_player.voice_client.is_playing():
            music_player.voice_client.stop()
        
        music_player.queue.add_to_front(music_player.current_song)
        
        await asyncio.sleep(1)  # Wait for song to restart
        await self.update_panel(interaction)
    
    @discord.ui.button(label="Loop Off", style=discord.ButtonStyle.secondary, emoji="🔄", row=1)
    async def loop_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Toggle loop mode button."""
        music_player = self.bot.get_music_player(interaction.guild.id)
        
        loop_status = music_player.toggle_loop()
        if loop_status:
            button.label = "Loop On"
            button.style = discord.ButtonStyle.success
        else:
            button.label = "Loop Off"
            button.style = discord.ButtonStyle.secondary
        
        await self.update_panel(interaction)
    
    async def on_timeout(self):
        """Called when the view times out."""
        # Disable all buttons
        for item in self.children:
            item.disabled = True
    
    @discord.ui.button(label="Ping", style=discord.ButtonStyle.secondary, emoji="🏓", row=1)
    async def ping_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Ping button."""
        latency = round(self.bot.latency * 1000)
        await interaction.response.send_message(f"🏓 Pong! Latency: {latency}ms", ephemeral=True)

# Second row of buttons
class MusicControlView2(discord.ui.View):
    """Second row of music control buttons."""
    
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot
    
    @discord.ui.button(label="Shuffle", style=discord.ButtonStyle.secondary, emoji="🔀")
    async def shuffle_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Shuffle button handler."""
        music_player = self.bot.get_music_player(interaction.guild.id)
        
        if music_player.queue.is_empty():
            await interaction.response.send_message("❌ Queue is empty!", ephemeral=True)
            return
        
        music_player.queue.shuffle()
        await interaction.response.send_message("🔀 Shuffled the queue!", ephemeral=True)
    
    @discord.ui.button(label="Loop", style=discord.ButtonStyle.secondary, emoji="🔄")
    async def loop_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Loop button handler."""
        music_player = self.bot.get_music_player(interaction.guild.id)
        
        loop_status = music_player.toggle_loop()
        status_text = "enabled" if loop_status else "disabled"
        await interaction.response.send_message(f"🔄 Loop mode {status_text}", ephemeral=True)
    
    @discord.ui.button(label="Rewind", style=discord.ButtonStyle.secondary, emoji="⏪")
    async def rewind_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Rewind button handler."""
        music_player = self.bot.get_music_player(interaction.guild.id)
        
        if not music_player.current_song:
            await interaction.response.send_message("❌ No song is currently playing!", ephemeral=True)
            return
        
        if music_player.voice_client and music_player.voice_client.is_playing():
            music_player.voice_client.stop()
        
        music_player.queue.add_to_front(music_player.current_song)
        await interaction.response.send_message("⏪ Rewinding current song!", ephemeral=True)
    
    @discord.ui.button(label="Clear", style=discord.ButtonStyle.danger, emoji="🗑️")
    async def clear_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Clear button handler."""
        if not interaction.user.guild_permissions.manage_messages:
            await interaction.response.send_message("❌ You need manage messages permission!", ephemeral=True)
            return
        
        await interaction.response.defer(ephemeral=True)
        
        try:
            deleted = await interaction.channel.purge(limit=10)
            await interaction.followup.send(f"🗑️ Deleted {len(deleted)} messages", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ Failed to delete messages: {e}", ephemeral=True)
    
    @discord.ui.button(label="Ping", style=discord.ButtonStyle.secondary, emoji="🏓")
    async def ping_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Ping button handler."""
        latency = round(self.bot.latency * 1000)
        await interaction.response.send_message(f"🏓 Pong! Latency: {latency}ms", ephemeral=True)
