import discord
import yt_dlp
import asyncio
import logging
from config import Config

class YTDLSource(discord.PCMVolumeTransformer):
    """Audio source for YouTube videos."""
    
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')
        self.duration = data.get('duration')
        self.uploader = data.get('uploader')
        
    @classmethod
    async def create_source(cls, url, *, loop=None, volume=0.5):
        """Create audio source from URL."""
        loop = loop or asyncio.get_event_loop()
        
        ytdl = yt_dlp.YoutubeDL(Config.YTDL_OPTIONS)
        
        try:
            data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=False))
            
            if 'entries' in data:
                # Take first item from playlist
                data = data['entries'][0]
            
            filename = data['url']
            
            return cls(
                discord.FFmpegPCMAudio(filename, **Config.FFMPEG_OPTIONS),
                data=data,
                volume=volume
            )
        except Exception as e:
            logging.error(f"Error creating audio source: {e}")
            return None
    
    @classmethod
    async def search(cls, query):
        """Search for a song and return info from multiple platforms."""
        loop = asyncio.get_event_loop()
        
        ytdl = yt_dlp.YoutubeDL(Config.YTDL_OPTIONS)
        
        try:
            # Handle different types of queries
            if query.startswith(('http://', 'https://')):
                # Direct URL - detect platform and handle accordingly
                platform = cls._detect_platform(query)
                if platform == 'spotify':
                    # For Spotify URLs, search on YouTube instead
                    query = await cls._convert_spotify_to_youtube(query)
                    if not query:
                        return None
                
                data = await loop.run_in_executor(None, lambda: ytdl.extract_info(query, download=False))
            else:
                # Text search - prioritize YouTube
                search_queries = [
                    f"ytsearch:{query}",
                    f"scsearch:{query}",  # SoundCloud search
                ]
                
                data = None
                for search_query in search_queries:
                    try:
                        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(search_query, download=False))
                        if data and 'entries' in data and data['entries']:
                            break
                    except Exception as e:
                        logging.warning(f"Search failed for {search_query}: {e}")
                        continue
                
                if not data:
                    return None
            
            if 'entries' in data:
                # Take first search result
                data = data['entries'][0]
            
            return {
                'title': data.get('title', 'Unknown'),
                'url': data.get('webpage_url') or data.get('url'),
                'duration': data.get('duration'),
                'uploader': data.get('uploader', 'Unknown'),
                'thumbnail': data.get('thumbnail'),
                'platform': cls._detect_platform(data.get('webpage_url', ''))
            }
        except Exception as e:
            logging.error(f"Error searching for song: {e}")
            return None
    
    @classmethod
    def _detect_platform(cls, url):
        """Detect which platform a URL belongs to."""
        if not url:
            return 'youtube'  # Default
        
        for platform, domains in Config.SUPPORTED_PLATFORMS.items():
            if any(domain in url for domain in domains):
                return platform
        return 'youtube'  # Default fallback
    
    @classmethod
    async def _convert_spotify_to_youtube(cls, spotify_url):
        """Convert Spotify URL to YouTube search query."""
        try:
            # Extract track info from Spotify URL using yt-dlp
            loop = asyncio.get_event_loop()
            ytdl = yt_dlp.YoutubeDL({'quiet': True, 'no_warnings': True})
            
            # Try to extract Spotify track info
            data = await loop.run_in_executor(None, lambda: ytdl.extract_info(spotify_url, download=False))
            
            if data:
                title = data.get('title', '')
                artist = data.get('uploader', '') or data.get('artist', '')
                
                # Create YouTube search query
                if artist and title:
                    return f"ytsearch:{artist} {title}"
                elif title:
                    return f"ytsearch:{title}"
            
            return None
        except Exception as e:
            logging.error(f"Error converting Spotify URL: {e}")
            return None

def format_duration(seconds):
    """Format duration in seconds to MM:SS format."""
    if not seconds:
        return "Unknown"
    
    minutes = seconds // 60
    seconds = seconds % 60
    
    if minutes >= 60:
        hours = minutes // 60
        minutes = minutes % 60
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    else:
        return f"{minutes:02d}:{seconds:02d}"

def create_embed(title, description, color=discord.Color.blue()):
    """Create a standard embed."""
    embed = discord.Embed(
        title=title,
        description=description,
        color=color
    )
    return embed

def is_url(text):
    """Check if text is a URL."""
    return text.startswith(('http://', 'https://'))

def truncate_string(text, max_length=100):
    """Truncate string to max length."""
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."
