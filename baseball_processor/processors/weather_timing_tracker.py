"""
Enhanced Weather and Timing Tracker
Captures wind conditions, precipitation, start times, and day/night patterns
"""

import re
from datetime import datetime
from collections import defaultdict

class WeatherTimingTracker:
    """Track detailed weather and timing statistics."""
    
    def __init__(self):
        # Wind tracking
        self.wind_conditions = []
        self.highest_wind_speed = 0
        self.highest_wind_games = []
        self.calmest_wind_speed = float('inf')
        self.calmest_wind_games = []
        
        # Wind direction tracking
        self.wind_directions = defaultdict(int)
        self.wind_to_cf_games = []
        self.wind_to_lf_games = []
        self.wind_to_rf_games = []
        
        # Precipitation tracking
        self.precipitation_games = []
        self.clear_weather_games = []
        self.cloudy_games = []
        self.partly_cloudy_games = []
        
        # Start time tracking
        self.start_times = []
        self.earliest_start_time = None
        self.earliest_start_games = []
        self.latest_start_time = None
        self.latest_start_games = []
        
        # Day vs Night
        self.day_games = []
        self.night_games = []
        
        # Weekday patterns
        self.weekday_counts = defaultdict(int)
        self.weekend_games = []
        self.weekday_games = []
        
    def process_weather(self, game):
        """Extract detailed weather information."""
        game_id = game.get("game_id", "")
        basic_info = game.get("basic_info", {})
        weather_str = basic_info.get("weather", "")
        
        if not weather_str:
            return
        
        # Parse wind speed and direction
        wind_match = re.search(r'wind\s+(\d+)\s*mph\s+(.+?)(?:,|$)', weather_str, re.IGNORECASE)
        if wind_match:
            wind_speed = int(wind_match.group(1))
            wind_direction = wind_match.group(2).strip()
            
            self.wind_conditions.append({
                "game_id": game_id,
                "speed": wind_speed,
                "direction": wind_direction,
                "date": basic_info.get("date_yyyymmdd", ""),
                "weather_full": weather_str
            })
            
            # Track highest wind
            if wind_speed > self.highest_wind_speed:
                self.highest_wind_speed = wind_speed
                self.highest_wind_games = [game_id]
            elif wind_speed == self.highest_wind_speed:
                self.highest_wind_games.append(game_id)
            
            # Track calmest wind
            if wind_speed < self.calmest_wind_speed:
                self.calmest_wind_speed = wind_speed
                self.calmest_wind_games = [game_id]
            elif wind_speed == self.calmest_wind_speed:
                self.calmest_wind_games.append(game_id)
            
            # Track wind direction patterns
            if 'center' in wind_direction.lower() or 'cf' in wind_direction.lower():
                self.wind_to_cf_games.append(game_id)
                self.wind_directions['Centerfield'] += 1
            elif 'left' in wind_direction.lower() or 'lf' in wind_direction.lower():
                self.wind_to_lf_games.append(game_id)
                self.wind_directions['Left Field'] += 1
            elif 'right' in wind_direction.lower() or 'rf' in wind_direction.lower():
                self.wind_to_rf_games.append(game_id)
                self.wind_directions['Right Field'] += 1
        
        # Parse precipitation
        weather_lower = weather_str.lower()
        if 'no precipitation' in weather_lower or 'no precip' in weather_lower:
            self.clear_weather_games.append(game_id)
        elif any(precip in weather_lower for precip in ['rain', 'drizzle', 'shower', 'precipitation']):
            self.precipitation_games.append(game_id)
        
        # Parse cloud cover
        if 'cloudy' in weather_lower and 'partly' not in weather_lower:
            self.cloudy_games.append(game_id)
        elif 'partly cloudy' in weather_lower or 'partly sunny' in weather_lower:
            self.partly_cloudy_games.append(game_id)
    
    def process_timing(self, game):
        """Extract detailed timing information."""
        game_id = game.get("game_id", "")
        basic_info = game.get("basic_info", {})
        
        # Parse start time
        start_time_str = basic_info.get("start_time", "")
        if start_time_str:
            time_match = re.search(r'(\d{1,2}):(\d{2})\s*(a\.m\.|p\.m\.|AM|PM)', start_time_str, re.IGNORECASE)
            if time_match:
                hour = int(time_match.group(1))
                minute = int(time_match.group(2))
                period = time_match.group(3).upper()
                
                # Convert to 24-hour time
                if 'P' in period and hour != 12:
                    hour += 12
                elif 'A' in period and hour == 12:
                    hour = 0
                
                time_24h = hour * 100 + minute  # e.g., 1930 for 7:30 PM
                
                self.start_times.append({
                    "game_id": game_id,
                    "time_24h": time_24h,
                    "time_str": f"{hour:02d}:{minute:02d}",
                    "date": basic_info.get("date_yyyymmdd", "")
                })
                
                # Track earliest start
                if self.earliest_start_time is None or time_24h < self.earliest_start_time:
                    self.earliest_start_time = time_24h
                    self.earliest_start_games = [game_id]
                elif time_24h == self.earliest_start_time:
                    self.earliest_start_games.append(game_id)
                
                # Track latest start
                if self.latest_start_time is None or time_24h > self.latest_start_time:
                    self.latest_start_time = time_24h
                    self.latest_start_games = [game_id]
                elif time_24h == self.latest_start_time:
                    self.latest_start_games.append(game_id)
                
                # Classify as day or night game (before 5pm = day game)
                if time_24h < 1700:
                    self.day_games.append(game_id)
                else:
                    self.night_games.append(game_id)
        
        # Parse date for weekday analysis
        date_str = basic_info.get("date", "")
        if date_str:
            try:
                # Parse the full date string
                date_obj = datetime.strptime(date_str, "%A, %B %d, %Y")
                weekday = date_obj.strftime("%A")
                
                self.weekday_counts[weekday] += 1
                
                # Weekend vs weekday
                if weekday in ['Saturday', 'Sunday']:
                    self.weekend_games.append(game_id)
                else:
                    self.weekday_games.append(game_id)
            except Exception:
                pass
    
    def get_summary_stats(self):
        """Return summary statistics for reporting."""
        stats = {
            # Wind stats
            "highest_wind_speed": f"{self.highest_wind_speed} mph" if self.highest_wind_speed > 0 else "N/A",
            "highest_wind_games": len(self.highest_wind_games),
            "calmest_wind_speed": f"{self.calmest_wind_speed} mph" if self.calmest_wind_speed != float('inf') else "N/A",
            "calmest_wind_games": len(self.calmest_wind_games),
            
            # Wind direction breakdown
            "wind_directions": dict(self.wind_directions),
            "wind_to_cf_count": len(self.wind_to_cf_games),
            "wind_to_lf_count": len(self.wind_to_lf_games),
            "wind_to_rf_count": len(self.wind_to_rf_games),
            
            # Weather conditions
            "precipitation_games": len(self.precipitation_games),
            "clear_weather_games": len(self.clear_weather_games),
            "cloudy_games": len(self.cloudy_games),
            "partly_cloudy_games": len(self.partly_cloudy_games),
            
            # Timing
            "day_games": len(self.day_games),
            "night_games": len(self.night_games),
            "earliest_start": self._format_time(self.earliest_start_time) if self.earliest_start_time else "N/A",
            "latest_start": self._format_time(self.latest_start_time) if self.latest_start_time else "N/A",
            
            # Day of week
            "weekday_breakdown": dict(self.weekday_counts),
            "weekend_games": len(self.weekend_games),
            "weekday_games": len(self.weekday_games)
        }
        
        # Average wind speed
        if self.wind_conditions:
            avg_wind = sum(w["speed"] for w in self.wind_conditions) / len(self.wind_conditions)
            stats["average_wind_speed"] = f"{avg_wind:.1f} mph"
        
        return stats
    
    def _format_time(self, time_24h):
        """Format 24-hour time for display."""
        if time_24h is None:
            return "N/A"
        hour = time_24h // 100
        minute = time_24h % 100
        period = "AM" if hour < 12 else "PM"
        display_hour = hour if hour <= 12 else hour - 12
        if display_hour == 0:
            display_hour = 12
        return f"{display_hour}:{minute:02d} {period}"
