from collections import defaultdict

# Global umpire tracking (used across multiple games)
umpire_counter = defaultdict(lambda: defaultdict(lambda: {"count": 0, "game_ids": set()}))