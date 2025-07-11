import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Configuration settings for the Discord music bot."""
    
    # Discord bot token
    DISCORD_TOKEN = os.getenv("DISCORD_TOKEN", "your_discord_bot_token")
    
    # Bot settings
    COMMAND_PREFIX = "!"
    MAX_QUEUE_SIZE = 100
    DEFAULT_VOLUME = 0.5
    
    # Audio extraction settings (YouTube, Spotify, SoundCloud)
    YTDL_OPTIONS = {
        'format': 'bestaudio/best',
        'extractaudio': True,
        'audioformat': 'mp3',
        'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
        'restrictfilenames': True,
        'noplaylist': True,
        'nocheckcertificate': True,
        'ignoreerrors': False,
        'logtostderr': False,
        'quiet': True,
        'no_warnings': True,
        'default_search': 'ytsearch',
        'source_address': '0.0.0.0',
        'extract_flat': False,
        'cookiefile': None,
        'age_limit': None,
        'geo_bypass': True,
        'geo_bypass_country': None
    }
    
    # Search priority order (YouTube gets highest priority)
    SEARCH_PRIORITY = ['youtube', 'soundcloud', 'spotify']
    
    # Supported platforms
    SUPPORTED_PLATFORMS = {
        'youtube': ['youtube.com', 'youtu.be', 'music.youtube.com'],
        'spotify': ['open.spotify.com'],
        'soundcloud': ['soundcloud.com']
    }
    
    # FFmpeg options
    FFMPEG_OPTIONS = {
        'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 -nostdin',
        'options': '-vn'
    }
