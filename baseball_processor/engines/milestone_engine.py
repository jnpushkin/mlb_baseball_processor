import re
import unicodedata
from ..utils.stat_utils import StatUtils
from ..utils.helpers import standardize_team_code
from ..excel.generators import ExcelGeneratorUtils
from ..utils.log import debug

class MilestoneEngine:
    """
    Comprehensive milestone detection engine for MLB games.
    Detects 40+ milestone types across batting and pitching categories.
    """

    MILESTONE_KEYS = [
        # Batting milestones
        'multi_hr_games', 'three_hr_games', 'cycles', 'five_hit_games',
        'four_hit_games', 'six_rbi_games', 'five_rbi_games',
        'four_rbi_games', 'multi_triple_games',
        'multi_steal_games', 'four_walk_games', 'perfect_batting_games',
        'four_run_games',
        # Pitching milestones
        'complete_games', 'shutouts', 'no_hitters', 'perfect_games',
        'quality_starts', 'fifteen_k_games', 'twelve_k_games', 'ten_k_games',
        'eight_k_games', 'maddux_games', 'seven_inning_shutouts',
        'one_hitters', 'two_hitters',
        'immaculate_inning_pitchers', 'no_walk_starts',
    ]

    def __init__(self, game_data):
        self.game_data = game_data
        ms = self.game_data.setdefault('milestone_stats', {})

        for key in self.MILESTONE_KEYS:
            ms.setdefault(key, [])

    def _normalize_name_for_comparison(self, name):
        """Normalize name for comparison by removing accents and standardizing."""
        if not name:
            return ""
        
        # Remove accents and normalize unicode
        normalized = unicodedata.normalize('NFD', name)
        # Remove accent characters (combining characters)
        ascii_name = ''.join(char for char in normalized if unicodedata.category(char) != 'Mn')
        
        return ascii_name.strip().lower()

    def process(self):
        """Main entry point to run all milestone checks."""
        self.process_batting_milestones()
        self.process_pitching_milestones()
        self.extract_multi_hr_from_footer()
        
        return self.game_data

    def get_player_hr_count(self, player, team_type):
        """Get HR count for player, preferring footer data over box score."""
        footer_summary = self.game_data.get("footer_summary", {})
        hr_blob = footer_summary.get(team_type, {}).get("HR", "")
        
        if hr_blob:
            # Check if this player appears in footer HR data
            player_name_normalized = self._normalize_name_for_comparison(player.get('name', ''))
            for name, count in ExcelGeneratorUtils.extract_stat_counts(hr_blob):
                footer_name_normalized = self._normalize_name_for_comparison(name)
                if footer_name_normalized == player_name_normalized:
                    return count
        
        # Fallback to box score data
        return player.get('HR', 0)

    def get_footer_stat_count(self, player_name, team_type, stat_type):
        """Get stat count for player from footer data."""
        footer_summary = self.game_data.get("footer_summary", {})
        stat_blob = footer_summary.get(team_type, {}).get(stat_type, "")
        
        if stat_blob:
            player_name_normalized = self._normalize_name_for_comparison(player_name)
            for name, count in ExcelGeneratorUtils.extract_stat_counts(stat_blob):
                footer_name_normalized = self._normalize_name_for_comparison(name)
                if footer_name_normalized == player_name_normalized:
                    return count
        return 0

    def get_enhanced_stat_count(self, player, team_type, stat_key, box_score_key):
        """Get stat count prioritizing footer over box score."""
        footer_count = self.get_footer_stat_count(player.get('name', ''), team_type, stat_key)
        box_count = player.get(box_score_key, 0)
        return footer_count if footer_count > 0 else box_count

    def get_footer_prioritized_player_stats(self, player_name, player_box_stats, team_type):
        """Get complete player stats with footer data prioritized over box score."""
        if not player_box_stats:
            return {}
        
        # Start with box score stats
        stats = dict(player_box_stats)
        
        # Override with footer stats where available
        for stat_key in ['HR', '2B', '3B']:
            footer_count = self.get_footer_stat_count(player_name, team_type, stat_key)
            if footer_count > 0:
                stats[stat_key] = footer_count
                debug(f"Using footer {stat_key} for {player_name}: {footer_count}")
        
        return stats

    def process_batting_milestones(self):
        ms = self.game_data['milestone_stats']
        basic = self.game_data.get("basic_info", {})
        game_id = self.game_data.get("game_id", "")
        game_date = basic.get("date_yyyymmdd", "")
        final_score = (
            f"{basic.get('away_team_code')} {basic.get('away_score_value')} – "
            f"{basic.get('home_score_value')} {basic.get('home_team_code')}"
        )

        batting_milestones = {}

        for team_type in ['home', 'away']:
            team_name = basic.get(f'{team_type}_team', '')
            team_code = basic.get(f'{team_type}_team_code', '')
            opposing_team = basic.get('away_team' if team_type == 'home' else 'home_team', '')
            opponent_code = basic.get('home_team_code' if team_type == 'away' else 'away_team_code')

            for player in self.game_data['batting'].get(team_type, []):
                player_id = player.get('player_id')
                if not player_id:
                    continue

                name = player.get('name', '')
                doubles = self.get_enhanced_stat_count(player, team_type, '2B', '2B')
                triples = self.get_enhanced_stat_count(player, team_type, '3B', '3B')
                home_runs = self.get_enhanced_stat_count(player, team_type, 'HR', 'HR')
                hits = player.get('H', 0)
                rbi = player.get('RBI', 0)
                singles = hits - (doubles + triples + home_runs)

                batting_milestones[player_id] = {
                    'player': name,
                    'player_id': player_id,
                    'team': team_name,
                    'team_code': team_code,
                    'opposing_team': opposing_team,
                    'opponent_code': opponent_code,
                    'singles': singles,
                    'doubles': doubles,
                    'triples': triples,
                    'home_runs': home_runs, 
                    'hits': hits,
                    'rbi': rbi,
                    # Add complete batting line for enhanced milestone display
                    'ab': player.get('AB', 0),
                    'runs': player.get('R', 0),
                    'bb': player.get('BB', 0),
                    'so': player.get('SO', 0),
                    'hbp': player.get('HBP', 0),
                    'sf': player.get('SF', 0),
                    'sh': player.get('SH', 0),
                    'game_id': game_id,
                    'game_date': game_date,
                    'final_score': final_score,
                    'is_home_game': team_type == 'home'
                }

        for pid, stats in batting_milestones.items():
            self.check_batting_milestones(pid, stats)

    def check_batting_milestones(self, pid, stats):
        ms = self.game_data['milestone_stats']

        player_name = stats['player']
        hr_count = stats['home_runs']
        hits = stats['hits']
        rbi = stats['rbi']
        doubles = stats['doubles']
        triples = stats['triples']
        singles = stats['singles']
        runs = stats.get('runs', 0)
        bb = stats.get('bb', 0)
        ab = stats.get('ab', 0)
        sb = stats.get('sb', 0)

        # HR milestones
        if hr_count >= 3:
            ms['three_hr_games'].append(stats)
        elif hr_count >= 2:
            debug(f"Found multi-HR game for {player_name}: {hr_count} HRs")
            ms['multi_hr_games'].append(stats)

        # Cycle
        if all(stats[k] > 0 for k in ['singles', 'doubles', 'triples', 'home_runs']):
            ms['cycles'].append(stats)

        # Hit milestones
        if hits >= 5:
            ms['five_hit_games'].append(stats)
        elif hits >= 4:
            debug(f"4+ Hit Game - {player_name}: HR={hr_count}, 2B={doubles}, 3B={triples}, H={hits}")
            ms['four_hit_games'].append(stats)

        # RBI milestones
        if rbi >= 6:
            ms['six_rbi_games'].append(stats)
        elif rbi >= 5:
            ms['five_rbi_games'].append(stats)
        elif rbi >= 4:
            ms['four_rbi_games'].append(stats)

        # Extra base hit milestones
        if triples >= 2:
            ms['multi_triple_games'].append(stats)

        # Runs scored
        if runs >= 4:
            ms['four_run_games'].append(stats)

        # Walks
        if bb >= 4:
            ms['four_walk_games'].append(stats)

        # Stolen bases
        if sb >= 2:
            ms['multi_steal_games'].append(stats)

        # Perfect batting (4+ AB, all hits)
        if ab >= 4 and hits == ab:
            ms['perfect_batting_games'].append(stats)

    def extract_multi_hr_from_footer(self):
        """Extract multi-HR events from the footer summary - enhanced version."""
        fs = self.game_data.get("footer_summary", {})
        basic = self.game_data.get("basic_info", {})
        game_id = self.game_data.get("game_id", "")
        game_date = basic.get("date_yyyymmdd", "")
        final_score = (
            f"{basic.get('away_team_code')} {basic.get('away_score_value')} – "
            f"{basic.get('home_score_value')} {basic.get('home_team_code')}"
        )
        
        # Track players already processed from box score to avoid duplicates
        processed_players = {
            item.get('player_id', '') for item in self.game_data['milestone_stats']['multi_hr_games']
        }
        
        for side in ("home", "away"):
            hr_blob = fs.get(side, {}).get("HR", "")
            if not hr_blob:
                continue
                
            team_name = basic.get(f"{side}_team", "")
            team_code = basic.get(f"{side}_team_code", "")
            opposing_team = basic.get("home_team") if side == "away" else basic.get("away_team")
            opponent_code = basic.get("home_team_code") if side == "away" else basic.get("away_team_code")

            for name, count in ExcelGeneratorUtils.extract_stat_counts(hr_blob):
                if count >= 2:
                    # Try to find player_id from batting data using normalized names
                    player_id = ""
                    player_box_stats = None
                    footer_name_normalized = self._normalize_name_for_comparison(name)
                    for player in self.game_data.get('batting', {}).get(side, []):
                        batting_name_normalized = self._normalize_name_for_comparison(player.get('name', ''))
                        if batting_name_normalized == footer_name_normalized:
                            player_id = player.get('player_id', '')
                            player_box_stats = player
                            debug(f"Matched footer '{name}' to batting '{player.get('name', '')}' via normalization")
                            break
                    
                    # FIXED: Skip if already processed
                    if player_id and player_id in processed_players:
                        continue  # Skip, already processed in box score
                    
                    # FIXED: Get footer-prioritized stats instead of just box score
                    enhanced_stats = self.get_footer_prioritized_player_stats(name, player_box_stats, side)
                    
                    doubles = enhanced_stats.get('2B', 0)
                    triples = enhanced_stats.get('3B', 0)
                    hits = enhanced_stats.get('H', 0)
                    rbi = enhanced_stats.get('RBI', 0)
                    runs = enhanced_stats.get('R', 0)
                    ab = enhanced_stats.get('AB', 0)
                    bb = enhanced_stats.get('BB', 0)
                    so = enhanced_stats.get('SO', 0)
                    
                    debug(f"Found multi-HR from footer for {name}: {count} HRs, {doubles} 2B, {triples} 3B")
                    self.game_data['milestone_stats']['multi_hr_games'].append({
                        "player": name,
                        "player_id": player_id,
                        "team": team_name,
                        "team_code": team_code,
                        "opposing_team": opposing_team,
                        "opponent_code": opponent_code,
                        "home_runs": count,  # Footer count
                        "hits": hits,
                        "doubles": doubles,
                        "triples": triples,
                        "rbi": rbi,
                        "runs": runs,
                        "ab": ab,
                        "bb": bb,
                        "so": so,
                        "game_id": game_id,
                        "game_date": game_date,
                        "final_score": final_score,
                        "is_home_game": side == "home"
                    })

    def process_pitching_milestones(self):
        ms = self.game_data['milestone_stats']
        linescore = self.game_data.get("linescore", {})
        basic = self.game_data.get("basic_info", {})
        game_id = self.game_data.get("game_id", "")
        game_date = basic.get("date_yyyymmdd", "")

        final_score = (
            f"{basic.get('away_team_code')} {basic.get('away_score_value')} – "
            f"{basic.get('home_score_value')} {basic.get('home_team_code')}"
        )

        for team_type in ['home', 'away']:
            team_name = basic.get(f'{team_type}_team', '')
            team_code = basic.get(f'{team_type}_team_code', '')
            opposing_team = basic.get('away_team' if team_type == 'home' else 'home_team', '')
            opponent_code = basic.get('home_team_code' if team_type == 'away' else 'away_team_code', '')

            team_innings = max(
                len(linescore.get('home', {}).get('innings', [])),
                len(linescore.get('away', {}).get('innings', []))
            )

            for pitcher in self.game_data['pitching'][team_type]:
                pid = pitcher.get('player_id')
                if not pid:
                    continue

                name = pitcher.get('name', '')
                ip = pitcher.get('IP', '0')
                so = pitcher.get('SO', 0)
                hits = pitcher.get('H', 0)
                runs = pitcher.get('R', 0)
                er = pitcher.get('ER', 0)
                walks = pitcher.get('BB', 0)
                decision = pitcher.get('decision', '')
                pitches = (
                    pitcher.get('Pit')
                    or pitcher.get('PIT')
                    or pitcher.get('pitches')
                    or pitcher.get('Pitch Count')
                    or 0
                )
                save = pitcher.get('save', False)

                try:
                    outs = StatUtils.ip_to_outs(ip)
                    if outs is None:
                        continue
                except Exception:
                    continue

                milestone_common = {
                    'player': name,
                    'player_id': pid,
                    'team': team_name,
                    'team_code': team_code,
                    'opposing_team': opposing_team,
                    'opponent_code': opponent_code,
                    'pitch_count': pitches,
                    'innings_pitched': ip,
                    'runs_allowed': runs,
                    'earned_runs': er,
                    'walks_allowed': walks,
                    'strikeouts': so,
                    'decision': decision,
                    'save': save,
                    'is_home_game': team_type == 'home',
                    'game_id': game_id,
                    'game_date': game_date,
                    'final_score': final_score
                }

                # Debug output for pitcher analysis
                debug(f"\n{'='*60}")
                debug(f"PITCHER: {name} ({team_type})")
                debug(f"{'='*60}")
                debug(f"IP: {ip}, Outs: {outs}, Runs: {runs}, SO: {so}, ER: {er}")
                debug(f"Team innings: {team_innings}, Required outs: {team_innings * 3}")
                debug(f"Check CG: {outs} >= {team_innings * 3}? {outs >= team_innings * 3}")
                debug(f"Check QS: {outs} >= 18 and {er} <= 3? {outs >= 18 and er <= 3}")

                # Add stats to milestone_common
                milestone_common.update({
                    'hits': hits, 'walks': walks, 'runs': runs,
                    'earned_runs': er, 'strikeouts': so, 'pitch_count': pitches
                })

                # Strikeout milestones
                if so >= 15:
                    ms['fifteen_k_games'].append(dict(milestone_common))
                elif so >= 12:
                    ms['twelve_k_games'].append(dict(milestone_common))
                elif so >= 10:
                    debug(f"✓ 10+ K Game detected")
                    ms['ten_k_games'].append(dict(milestone_common))
                elif so >= 8:
                    ms['eight_k_games'].append(dict(milestone_common))

                # Complete game milestones
                if outs >= team_innings * 3 and outs >= 27:
                    debug(f"✓✓✓ COMPLETE GAME DETECTED ✓✓✓")
                    ms['complete_games'].append(dict(milestone_common))

                    # Maddux (CG < 100 pitches)
                    if pitches and int(pitches) < 100:
                        ms['maddux_games'].append(dict(milestone_common))

                    # Low-hit complete games
                    if hits == 1:
                        ms['one_hitters'].append(dict(milestone_common))
                    elif hits == 2:
                        ms['two_hitters'].append(dict(milestone_common))

                    if runs == 0:
                        debug(f"✓✓✓ SHUTOUT DETECTED ✓✓✓")
                        ms['shutouts'].append(dict(milestone_common))

                    if hits == 0:
                        debug(f"✓✓✓ NO-HITTER DETECTED ✓✓✓")
                        ms['no_hitters'].append(dict(milestone_common))

                    if runs == 0 and walks == 0 and hits == 0:
                        debug(f"✓✓✓ PERFECT GAME DETECTED ✓✓✓")
                        ms['perfect_games'].append(dict(milestone_common))
                else:
                    debug(f"✗ NOT a complete game")

                # 7+ IP shutout (not CG)
                if outs >= 21 and runs == 0 and outs < 27:
                    ms['seven_inning_shutouts'].append(dict(milestone_common))

                # Quality starts (6+ IP, 3 or fewer ER)
                if outs >= 18 and er <= 3:
                    debug(f"✓ Quality Start detected")
                    ms['quality_starts'].append(dict(milestone_common))

                # No-walk start (6+ IP, 0 BB)
                if outs >= 18 and walks == 0:
                    ms['no_walk_starts'].append(dict(milestone_common))

                debug(f"{'='*60}\n")