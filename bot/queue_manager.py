from collections import deque
import logging

class QueueManager:
    """Manages the music queue for a guild."""
    
    def __init__(self):
        self.queue = deque()
        self.logger = logging.getLogger(__name__)
    
    def add(self, song_info):
        """Add song to queue."""
        self.queue.append(song_info)
        self.logger.info(f"Added to queue: {song_info['title']}")
    
    def add_to_front(self, song_info):
        """Add song to front of queue."""
        self.queue.appendleft(song_info)
    
    def get_next(self):
        """Get next song from queue."""
        if self.queue:
            return self.queue.popleft()
        return None
    
    def is_empty(self):
        """Check if queue is empty."""
        return len(self.queue) == 0
    
    def size(self):
        """Get queue size."""
        return len(self.queue)
    
    def clear(self):
        """Clear the queue."""
        self.queue.clear()
    
    def get_all(self):
        """Get all songs in queue."""
        return list(self.queue)
    
    def remove(self, index):
        """Remove song at specific index."""
        if 0 <= index < len(self.queue):
            song = self.queue[index]
            del self.queue[index]
            return song
        return None
    
    def shuffle(self):
        """Shuffle the queue."""
        import random
        queue_list = list(self.queue)
        random.shuffle(queue_list)
        self.queue = deque(queue_list)
