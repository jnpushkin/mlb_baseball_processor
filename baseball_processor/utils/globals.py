from collections import defaultdict

class UmpireTracker:
    """Tracks umpire appearances across games."""
    
    def __init__(self):
        # Create a fresh counter for each instance
        self.counter = defaultdict(lambda: defaultdict(lambda: {"count": 0, "game_ids": set()}))
    
    def record_umpire(self, name, position, game_id):
        """Record that an umpire worked a position in a game."""
        self.counter[name][position]["count"] += 1
        self.counter[name][position]["game_ids"].add(game_id)
        self.counter[name]["Total"]["count"] += 1
        self.counter[name]["Total"]["game_ids"].add(game_id)
    
    def get_counter(self):
        """Get the current counter data."""
        return self.counter