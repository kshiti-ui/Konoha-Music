import asyncio
import logging
from bot.music_bot import MusicBot
from config import Config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def main():
    """Main entry point for the Discord music bot."""
    try:
        # Initialize and run the bot
        bot = MusicBot()
        await bot.start(Config.DISCORD_TOKEN)
    except Exception as e:
        logging.error(f"Failed to start bot: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
