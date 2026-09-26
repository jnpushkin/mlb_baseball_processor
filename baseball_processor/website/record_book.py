"""Structured record candidates derived from published game facts.

Keep candidates per game so any subset of attended games can be ranked honestly.
A player's personal-best summary is not sufficient for scoped records.
"""

import math
import re
from collections import defaultdict

from .analysis_data import game_story

# Stable identity, label, category, unit, direction, display format.
DEFINITIONS = [
    ('comeback', 'Biggest Comeback', 'games', 'runs', 'max', 'number'),
    ('combined-runs', 'Most Combined Runs', 'games', 'runs', 'max', 'number'),
    ('victory', 'Biggest Victory', 'games', 'runs', 'max', 'number'),
    ('inning-runs', 'Most Runs in a Single Inning', 'games', 'runs', 'max', 'number'),
    ('team-runs', 'Most Runs by One Team', 'games', 'runs', 'max', 'number'),
    ('combined-hits', 'Most Combined Hits', 'games', 'hits', 'max', 'number'),
    ('fewest-combined-hits', 'Fewest Combined Hits', 'games', 'hits', 'min', 'number'),
    ('combined-hr', 'Most Combined HRs', 'games', 'home runs', 'max', 'number'),
    ('combined-triples', 'Most Combined Triples', 'games', 'triples', 'max', 'number'),
    ('combined-sb', 'Most Combined SBs in a Game', 'games', 'stolen bases', 'max', 'number'),
    ('combined-k', 'Most Combined Pitching Strikeouts', 'games', 'strikeouts', 'max', 'number'),
    ('fewest-combined-k', 'Fewest Combined Strikeouts', 'games', 'strikeouts', 'min', 'number'),
    ('combined-bb', 'Most Combined Walks', 'games', 'walks', 'max', 'number'),
    ('fewest-combined-bb', 'Fewest Combined Walks', 'games', 'walks', 'min', 'number'),
    ('player-hits', 'Most Hits by One Player', 'batting', 'hits', 'max', 'number'),
    ('player-hr', 'Most HRs by One Player', 'batting', 'home runs', 'max', 'number'),
    ('player-rbi', 'Most RBIs in a Game', 'batting', 'RBI', 'max', 'number'),
    ('player-tb', 'Most Total Bases by One Player', 'batting', 'total bases', 'max', 'number'),
    ('player-runs', 'Most Runs by One Player', 'batting', 'runs', 'max', 'number'),
    ('player-sb', 'Most SBs by One Player', 'batting', 'stolen bases', 'max', 'number'),
    ('team-hits', 'Most Hits by One Team', 'batting', 'hits', 'max', 'number'),
    ('fewest-team-hits', 'Fewest Hits by One Team', 'batting', 'hits', 'min', 'number'),
    ('team-hr', 'Most HRs by One Team', 'batting', 'home runs', 'max', 'number'),
    ('team-sb', 'Most SBs by One Team', 'batting', 'stolen bases', 'max', 'number'),
    ('player-k', 'Most Strikeouts by One Pitcher', 'pitching', 'strikeouts', 'max', 'number'),
    ('player-outs', 'Most Innings by One Pitcher', 'pitching', 'IP', 'max', 'outs'),
    ('player-pitches', 'Most Pitches by One Pitcher', 'pitching', 'pitches', 'max', 'number'),
    ('team-k', 'Most Pitching Strikeouts by One Team', 'pitching', 'strikeouts', 'max', 'number'),
    ('team-bb', 'Most Walks Issued by One Team', 'pitching', 'walks', 'max', 'number'),
    ('pitchers', 'Most Pitchers Used', 'pitching', 'pitchers', 'max', 'number'),
    ('fewest-pitchers', 'Fewest Pitchers Used', 'pitching', 'pitchers', 'min', 'number'),
    ('longest-innings', 'Longest Game by Innings', 'ballpark', 'innings', 'max', 'number'),
    ('longest-time', 'Longest Game by Time', 'ballpark', '', 'max', 'duration'),
    ('shortest-time', 'Shortest Game by Time', 'ballpark', '', 'min', 'duration'),
    ('coldest', 'Coldest Game', 'ballpark', '°F', 'min', 'number'),
    ('hottest', 'Hottest Game', 'ballpark', '°F', 'max', 'number'),
    ('attendance', 'Highest Attendance', 'ballpark', 'fans', 'max', 'number'),
    ('lowest-attendance', 'Lowest Attendance', 'ballpark', 'fans', 'min', 'number'),
    ('wind', 'Highest Wind Speed', 'ballpark', 'mph', 'max', 'number'),
    ('earliest', 'Earliest Start Time', 'ballpark', 'local start', 'min', 'clock'),
    ('latest', 'Latest Start Time', 'ballpark', 'local start', 'max', 'clock'),
]


def number(value):
    try:
        result = float(value)
        return result if math.isfinite(result) else None
    except (ValueError, TypeError):
        return None


def unique_performances(rows):
    """Avoid double counting repeated source rows, without merging doubleheaders."""
    seen = set()
    for row in rows:
        key = (row.get('gameId'), row.get('playerId') or row.get('name') or row.get('player'), row.get('team'))
        if key not in seen:
            seen.add(key)
            yield row


def build_record_book(data):
    book = {id_: dict(id=id_, label=label, category=category, unit=unit,
                     direction=direction, format=fmt, candidates=[], coverage='games')
            for id_, label, category, unit, direction, fmt in DEFINITIONS}
    games = {g['gameId']: g for g in data.get('games', [])}
    batting, pitching = defaultdict(list), defaultdict(list)
    for target, key in [(batting, 'playerGames'), (pitching, 'pitcherGames')]:
        for row in unique_performances(data.get(key, [])):
            if row.get('gameId') in games:
                target[row['gameId']].append(row)

    def add(id_, gid, value, holder='', **context):
        value = number(value)
        if value is None:
            return
        book[id_]['candidates'].append(dict(gameId=gid, value=value, holder=holder, **context))

    for gid, game in games.items():
        lines = game.get('linescore') or {}
        away, home = lines.get('away') or {}, lines.get('home') or {}
        teams = [game.get('awayTeam', ''), game.get('homeTeam', '')]
        runs = [number(row.get('runs')) for row in (away, home)]
        hits = [number(row.get('hits')) for row in (away, home)]
        if all(v is not None for v in runs):
            add('combined-runs', gid, sum(runs))
            if runs[0] != runs[1]:
                add('victory', gid, abs(runs[0]-runs[1]), teams[int(runs[1] > runs[0])])
            for team, value in zip(teams, runs, strict=True):
                add('team-runs', gid, value, team)
        if all(v is not None for v in hits):
            for id_ in ('combined-hits', 'fewest-combined-hits'):
                add(id_, gid, sum(hits))
        for team, side in zip(teams, (away, home), strict=True):
            for id_ in ('team-hits', 'fewest-team-hits'):
                add(id_, gid, side.get('hits'), team)
        story = game_story(game)
        if story and story['complete']:
            if story['comeback'] and all(v is not None for v in runs):
                add('comeback', gid, story['comeback'], teams[int(runs[1] > runs[0])],
                    detail='Largest deficit overcome by the eventual winner, measured after each half-inning.')
            for half in story['timeline']:
                if half['runs']:
                    side = int(half['half'] == 'bottom')
                    add('inning-runs', gid, half['runs'], teams[side],
                        detail=f"{'Bottom' if side else 'Top'} {half['inning']}")
            add('longest-innings', gid, max(h['inning'] for h in story['timeline']))
        for rows, metrics in [(batting[gid], [('h', 'player-hits'), ('hr', 'player-hr'),
                                             ('rbi', 'player-rbi'), ('r', 'player-runs'), ('sb', 'player-sb')]),
                              (pitching[gid], [('so', 'player-k'), ('outs', 'player-outs'), ('totalPitches', 'player-pitches')])]:
            for row in rows:
                for stat, id_ in metrics:
                    if (number(row.get(stat)) or 0) > 0:
                        add(id_, gid, row[stat], row.get('name', ''), playerId=row.get('playerId', ''), team=row.get('team', ''))
        for row in batting[gid]:
            if all(number(row.get(k)) is not None for k in ('h', 'doubles', 'triples', 'hr')):
                tb = row['h'] + row['doubles'] + 2*row['triples'] + 3*row['hr']
                if tb:
                    add('player-tb', gid, tb, row.get('name', ''), playerId=row.get('playerId', ''), team=row.get('team', ''))
        for rows, metrics in [(batting[gid], [('hr', 'team-hr', 'combined-hr'), ('sb', 'team-sb', 'combined-sb'), ('triples', None, 'combined-triples')]),
                              (pitching[gid], [('so', 'team-k', 'combined-k'), ('bb', 'team-bb', 'combined-bb')])]:
            for stat, team_id, combined_id in metrics:
                groups = [[r for r in rows if r.get('team') == team] for team in teams]
                # A missing team's boxscore is unknown, never a zero.
                valid = [bool(group) and all(number(r.get(stat)) is not None for r in group) for group in groups]
                totals = [sum(number(r.get(stat)) or 0 for r in group) for group in groups]
                for team, value, known in zip(teams, totals, valid, strict=True):
                    if known and team_id:
                        add(team_id, gid, value, team)
                if all(valid):
                    add(combined_id, gid, sum(totals))
                    if stat in ('so', 'bb') and rows is pitching[gid]:
                        add('fewest-' + combined_id, gid, sum(totals))
        if pitching[gid] and all(any(r.get('team') == t for r in pitching[gid]) for t in teams):
            for id_ in ('pitchers', 'fewest-pitchers'):
                add(id_, gid, len(pitching[gid]))
        match = re.fullmatch(r'(\d+):(\d{2})', str(game.get('gameLength', '')).strip())
        if match and int(match[2]) < 60 and int(match[1])*60+int(match[2]) > 0:
            for id_ in ('longest-time', 'shortest-time'):
                add(id_, gid, int(match[1])*60+int(match[2]))
        for id_ in ('coldest', 'hottest'):
            add(id_, gid, game.get('temperature'))
        if (number(game.get('attendance')) or 0) > 0:
            for id_ in ('attendance', 'lowest-attendance'):
                add(id_, gid, game['attendance'])
        wind = re.search(r'(\d+)\s*mph', game.get('weather') or '', re.I)
        if wind:
            add('wind', gid, wind[1])
        start = re.search(r'(\d{1,2}):(\d{2})\s*([ap])\.?m', game.get('startTime') or '', re.I)
        if start and 1 <= int(start[1]) <= 12 and int(start[2]) < 60:
            for id_ in ('earliest', 'latest'):
                add(id_, gid, (int(start[1]) % 12)*60 + int(start[2]) + (720 if start[3].lower() == 'p' else 0))
    # Preserve the historical WPA record without pretending its one summary row
    # can provide rankings, progression, or a recomputed scoped record.
    for row in data.get('summary', []):
        if row['record'] == 'Most Clutch Single Game (WPA)':
            ids = [s.strip() for s in row.get('gameIds', '').split(',') if s.strip() in games]
            if ids and number(row['value']) is not None:
                book['wpa'] = dict(id='wpa', label=row['record'], category='batting', unit='WPA',
                                   direction='max', format='wpa', coverage='holders-only',
                                   candidates=[dict(gameId=gid, value=float(row['value']), holder=row.get('detail', '')) for gid in ids])
    # Five places per game, including all ties at the cutoff, retain everything
    # needed for top-five rankings and record history under any game scope.
    for record in book.values():
        by_game = defaultdict(list)
        for row in record['candidates']:
            by_game[row['gameId']].append(row)
        kept = []
        for rows in by_game.values():
            rows.sort(key=lambda r: r['value'], reverse=record['direction'] == 'max')
            cutoff = rows[min(4, len(rows)-1)]['value']
            retained = [r for r in rows if (r['value'] >= cutoff if record['direction'] == 'max' else r['value'] <= cutoff)]
            # A large tie at first can fill all five places. Preserve the next
            # distinct mark too, so the runner-up gap remains correct.
            next_mark = next((r for r in rows if r['value'] != rows[0]['value']), None)
            if next_mark is not None and next_mark not in retained:
                retained.append(next_mark)
            kept.extend(retained)
        record['candidates'] = kept
    return [r for r in book.values() if r['candidates']]


THRESHOLDS = [('4+ Hit Games', 'playerGames', 'h', 4), ('5+ RBI Games', 'playerGames', 'rbi', 5),
              ('Multi-HR Games', 'playerGames', 'hr', 2), ('10+ K Games', 'pitcherGames', 'so', 10)]


def repair_summary_counts(data):
    """Rebuild inclusive threshold counts and links from the same performances."""
    games = {g['gameId']: g for g in data.get('games', []) if g.get('gameType') != 'spring'}
    replacements = {}
    for label, source, stat, threshold in THRESHOLDS:
        rows = [r for r in unique_performances(data.get(source, []))
                if r.get('gameId') in games and (number(r.get(stat)) or 0) >= threshold]
        units = {'h': 'hits', 'rbi': 'RBI', 'hr': 'home runs', 'so': 'strikeouts'}
        replacements[label] = [{**r, 'detail': f"{r[stat]} {units[stat]}"} for r in rows]
    # Non-threshold milestones retain detector semantics, but share game scope
    # and must never drop their links merely because there are many results.
    all_ms = data.get('allMilestones') or data.get('milestones') or []
    for label in ('Quality Starts', 'Complete Games', 'Shutouts', 'No-Hitters', 'Cycles'):
        rows = [r for r in all_ms if r.get('type') == label and r.get('gameId') in games]
        if any(r.get('type') == label for r in all_ms):
            replacements[label] = list(unique_performances(rows))
    summaries = []
    for original in data.get('summary', []):
        row = dict(original)
        label = row['record']
        if label in replacements:
            rows = replacements[label]
            ids = sorted({r['gameId'] for r in rows})
            people = {r.get('playerId') or r.get('name') or r.get('player') for r in rows}
            row.update(value=str(len(rows)), gameIds=', '.join(ids),
                       detail=f'{len(rows)} performances by {len(people)} different players',
                       performances=[dict(gameId=r['gameId'], holder=r.get('name') or r.get('player', ''),
                                          playerId=r.get('playerId', ''), team=r.get('team', ''), detail=r.get('detail', '')) for r in rows])
        summaries.append(row)
    data['summary'] = summaries
