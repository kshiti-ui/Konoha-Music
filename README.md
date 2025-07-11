# Discord Music Bot

A comprehensive Discord music bot that plays music from YouTube, Spotify, and SoundCloud with advanced queue management and slash commands.

## Features

🎵 **Multi-Platform Support**
- YouTube (Primary source)
- Spotify (Converted to YouTube search)
- SoundCloud (Direct support)

🎮 **Slash Commands**
- `/play` - Play music from any supported platform
- `/pause` - Pause current song
- `/resume` - Resume paused song
- `/skip` - Skip to next song
- `/stop` - Stop and clear queue
- `/queue` - Show current queue
- `/loop` - Toggle loop mode
- `/shuffle` - Shuffle the queue
- `/rewind` - Restart current song
- `/previous` - Play previous song
- `/clear` - Clear chat messages
- `/disconnect` - Disconnect from voice
- `/ping` - Check bot latency
- `/setup` - Show setup information

🎛️ **Advanced Features**
- Queue management with shuffle and loop
- Previous songs history (last 10 tracks)
- Platform-specific emojis and thumbnails
- Auto-disconnect when alone in voice channel
- Rich embeds with song information

## Quick Start

1. **Get Discord Bot Token**
   - Go to https://discord.com/developers/applications
   - Create a new application
   - Go to "Bot" section and create a bot
   - Copy the token and add it to your environment

2. **Set up Environment**
   ```bash
   cp .env.example .env
   # Edit .env and add your DISCORD_TOKEN
   ```

3. **Run the Bot**
   ```bash
   python main.py
   ```

## Usage Examples

### Playing Music
```
/play Never Gonna Give You Up
/play https://www.youtube.com/watch?v=dQw4w9WgXcQ
/play https://open.spotify.com/track/4uLU6hMCjMI75M1A2tKUQC
/play https://soundcloud.com/artist/track-name
```

### Queue Management
```
/queue          # Show current queue
/shuffle        # Shuffle queue
/skip           # Skip current song
/previous       # Play previous song
/rewind         # Restart current song
/loop           # Toggle loop mode
```

### Bot Control
```
/setup          # Show bot setup information
/clear 10       # Clear 10 messages
/disconnect     # Disconnect from voice
/ping           # Check bot latency
```

## Bot Permissions Required

- Connect (Voice channels)
- Speak (Voice channels)
- Use Voice Activity
- Send Messages
- Use Slash Commands
- Manage Messages (for clear command)

## Supported Platforms

| Platform | Support Type | Notes |
|----------|-------------|-------|
| YouTube | Direct | Primary source, highest quality |
| Spotify | Converted | Converts to YouTube search |
| SoundCloud | Direct | Native support via yt-dlp |

## Architecture

The bot uses a modular architecture with:
- **MusicBot**: Main bot class handling Discord connection
- **MusicPlayer**: Per-guild music player instances
- **QueueManager**: FIFO queue with shuffle/loop support
- **YTDLSource**: Multi-platform audio source handler
- **MusicCommands**: Slash command handlers

## Dependencies

- `discord.py` - Discord API interaction
- `yt-dlp` - Multi-platform audio extraction
- `python-dotenv` - Environment variable management
- `FFmpeg` - Audio processing (system dependency)

## License

This project is open source and available under the MIT License.