# Discord Music Bot

## Overview

This is a comprehensive Discord music bot built with Python that allows users to play music from multiple sources including YouTube, Spotify, and SoundCloud. The bot uses Discord.py for Discord API interactions, yt-dlp for multi-platform audio extraction, and FFmpeg for audio processing. The architecture follows a modular design with separate components for bot management, music playback, queue management, and command handling.

## User Preferences

Preferred communication style: Simple, everyday language.

## Recent Changes (2025-07-11)

✓ Enhanced multi-platform support for YouTube, Spotify, and SoundCloud
✓ Added Spotify URL conversion to YouTube search for playback
✓ Implemented comprehensive slash command system
✓ Added advanced queue management features (shuffle, rewind, previous)
✓ Created enhanced embeds with platform-specific emojis and thumbnails
✓ Implemented previous songs history (last 10 tracks)
✓ Fixed all audio issues - installed FFmpeg, libopus, and PyNaCl
✓ Resolved Opus library loading with automatic detection
✓ Added interactive setup panel with control buttons
✓ Implemented direct song requests via text messages in setup channels
✓ Created comprehensive button controls (pause, skip, loop, shuffle, etc.)
✓ Added auto-deafen functionality and voice connection repair

## System Architecture

The bot follows a modular architecture with clear separation of concerns:

- **Main Bot Class**: Handles Discord connection and overall bot lifecycle
- **Music Player**: Manages audio playback for individual guilds
- **Queue Manager**: Handles song queuing and playlist management
- **Commands Module**: Processes user commands via slash commands
- **Utils Module**: Provides audio source handling and YouTube integration

## Key Components

### Core Bot Infrastructure
- **MusicBot**: Main bot class extending Discord.py's commands.Bot
- **Configuration**: Centralized config management with environment variables
- **Logging**: Structured logging across all components

### Music System
- **MusicPlayer**: Per-guild music player instances managing voice connections and playback
- **QueueManager**: FIFO queue system with additional features like shuffle and loop
- **YTDLSource**: Audio source wrapper for YouTube content using yt-dlp

### Command Interface
- **MusicCommands**: Slash command handlers for user interactions
- **Command Processing**: Async command handling with proper error responses

### Interactive Control Panel
- **MusicControlView**: Button-based control interface with pause, skip, stop, repair
- **MusicControlView2**: Secondary button row with shuffle, loop, rewind, clear, ping
- **Setup Channel Integration**: Direct song requests via text messages in designated channels
- **Message Listener**: Automatically processes song requests typed in setup channels

## Data Flow

1. **User Interaction**: Users invoke slash commands (e.g., `/play`)
2. **Command Processing**: Commands cog validates user permissions and channel presence
3. **Audio Resolution**: Utils module extracts audio information from YouTube
4. **Queue Management**: Songs are added to guild-specific queues
5. **Voice Connection**: Bot connects to or moves between voice channels as needed
6. **Audio Playback**: FFmpeg processes and streams audio to Discord voice channels

## External Dependencies

### Core Libraries
- **discord.py**: Discord API interaction and bot framework
- **yt-dlp**: Multi-platform audio extraction (YouTube, Spotify, SoundCloud)
- **python-dotenv**: Environment variable management

### System Dependencies
- **FFmpeg**: Audio processing and streaming (configured via FFMPEG_OPTIONS)
- **YouTube**: Primary audio source via yt-dlp integration
- **Spotify**: Secondary source (converts to YouTube search)
- **SoundCloud**: Tertiary source via yt-dlp integration

### Configuration Requirements
- **Discord Bot Token**: Required for Discord API authentication
- **Voice Channel Permissions**: Bot needs voice channel connect/speak permissions
- **Optional API Keys**: Spotify and SoundCloud credentials for enhanced features

## Deployment Strategy

### Environment Setup
- Uses `.env` file for configuration management
- Supports environment variable override for sensitive data
- Configurable bot prefix and audio quality settings

### Bot Permissions
- Requires Discord bot token from Discord Developer Portal
- Needs voice channel permissions (Connect, Speak, Use Voice Activity)
- Slash command permissions for user interactions

### Scalability Considerations
- Per-guild music player instances prevent cross-server interference
- Queue size limits (MAX_QUEUE_SIZE) prevent memory issues
- Async architecture supports concurrent operations across multiple guilds

### Error Handling
- Comprehensive logging for debugging and monitoring
- Graceful error responses for user-facing commands
- Connection retry logic for voice channel stability

The architecture prioritizes modularity and maintainability while providing a responsive music bot experience. The separation of concerns allows for easy extension of features like playlist management, music controls, and additional audio sources.