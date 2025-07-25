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
            
            # Create FFmpeg source with proper executable path
            ffmpeg_options = Config.FFMPEG_OPTIONS.copy()
            ffmpeg_options['executable'] = 'ffmpeg'
            
            return cls(
                discord.FFmpegPCMAudio(filename, **ffmpeg_options),
                data=data,
                volume=volume
            )
        except Exception as e:
            logging.error(f"Error creating audio source: {e}")
            logging.error(f"URL: {url}")
            logging.error(f"Data: {data if 'data' in locals() else 'No data'}")
            return None
    
    @classmethod
    async def search(cls, query):
        """Search for a song and return info from multiple platforms."""
        loop = asyncio.get_event_loop()
        
        # Faster YTDL options for quicker searches
        fast_ytdl_options = Config.YTDL_OPTIONS.copy()
        fast_ytdl_options.update({
            'extract_flat': False,
            'no_warnings': True,
            'quiet': True,
            'skip_download': True
        })
        ytdl = yt_dlp.YoutubeDL(fast_ytdl_options)
        
        try:
            # Handle different types of queries
            if query.startswith(('http://', 'https://')):
                # Direct URL - detect platform and handle accordingly
                platform = cls._detect_platform(query)
                if platform == 'spotify':
                    # For Spotify URLs, convert to YouTube search
                    youtube_query = await cls._convert_spotify_to_youtube(query)
                    if youtube_query:
                        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(youtube_query, download=False))
                    else:
                        return None
                else:
                    data = await loop.run_in_executor(None, lambda: ytdl.extract_info(query, download=False))
            else:
                # Text search - use YouTube first for speed
                search_query = f"ytsearch1:{query}"
                data = await loop.run_in_executor(None, lambda: ytdl.extract_info(search_query, download=False))
            
            if 'entries' in data and data['entries']:
                # Take first search result
                data = data['entries'][0]
            elif not data:
                return None
            
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
            ytdl = yt_dlp.YoutubeDL({
                'quiet': True, 
                'no_warnings': True,
                'extract_flat': False,
                'skip_download': True
            })
            
            # Try to extract Spotify track info
            data = await loop.run_in_executor(None, lambda: ytdl.extract_info(spotify_url, download=False))
            
            if data:
                title = data.get('title', '')
                artist = data.get('artist', '') or data.get('uploader', '') or data.get('creator', '')
                album = data.get('album', '')
                
                # Create YouTube search query with artist and title
                if artist and title:
                    return f"ytsearch1:{artist} - {title}"
                elif title:
                    return f"ytsearch1:{title}"
                else:
                    # Fallback: extract from URL if possible
                    import re
                    track_match = re.search(r'/track/([a-zA-Z0-9]+)', spotify_url)
                    if track_match:
                        return f"ytsearch1:spotify track {track_match.group(1)}"
            
            return None
        except Exception as e:
            logging.error(f"Error converting Spotify URL: {e}")
            # Fallback: try to extract track ID from URL
            try:
                import re
                track_match = re.search(r'/track/([a-zA-Z0-9]+)', spotify_url)
                if track_match:
                    return f"ytsearch1:track {track_match.group(1)}"
            except:
                pass
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
