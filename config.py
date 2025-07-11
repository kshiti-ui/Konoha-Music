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
        'format': 'bestaudio[ext=webm]/bestaudio/best',
        'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
        'restrictfilenames': True,
        'noplaylist': True,
        'nocheckcertificate': True,
        'ignoreerrors': False,
        'logtostderr': False,
        'quiet': True,
        'no_warnings': True,
        'default_search': 'auto',
        'source_address': '0.0.0.0',
        'extract_flat': False,
        'skip_download': True,
        'prefer_ffmpeg': True,
        'geo_bypass': True,
        'playlist_items': '1',
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