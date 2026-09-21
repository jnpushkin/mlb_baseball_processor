"""Source-aware plate appearances and pre/post-play state.

Unknown state stays None. Name resolution is restricted to participants in the
same game and side, and ambiguous names are never assigned an arbitrary ID.
"""

import re
import unicodedata
from collections import defaultdict

from .team_identity import display_team


def name_key(value):
    return re.sub(r"[^a-z0-9]", "", unicodedata.normalize("NFKD", value or "").encode("ascii", "ignore").decode().lower())


def event_type(play):
    kind = play.get("event_type", "")
    known = {
        "single", "double", "triple", "home_run", "walk", "intent_walk",
        "hit_by_pitch", "strikeout", "strikeout_double_play", "field_out",
        "force_out", "grounded_into_double_play", "double_play", "triple_play",
        "field_error", "fielders_choice", "fielders_choice_out", "sac_fly",
        "sac_bunt", "sac_fly_double_play", "sac_bunt_double_play", "catcher_interf",
    }
    if kind in known:
        return kind
    if kind.startswith(("pickoff", "caught_stealing", "stolen_base")) or kind in {"wild_pitch", "passed_ball", "balk", "defensive_indiff", "other_out"}:
        return "runner_event"
    d = (play.get("description") or "").lower()
    # A steal can accompany a completed PA. Classify the batter's result first.
    primary = re.split(r"[;,]", d, maxsplit=1)[0]
    if re.search(r"strikeout|strikes out|called out on strikes", primary):
        return "strikeout_double_play" if "double play" in primary else "strikeout"
    if re.match(r"intentional walk", primary):
        return "intent_walk"
    if re.match(r"walk\b", primary):
        return "walk"
    if re.search(r"^(wild pitch|passed ball|balk|pickoff|caught stealing|stolen base)|\b(steals|caught stealing|picked off|picks off)\b", primary):
        return "runner_event"
    if re.search(r"defensive indifference|baserunner out advancing|^e[1-9] on foul ball", d):
        return "runner_event"
    if '/sacrifice' in d:
        return "sac_bunt" if 'bunt' in d else "sac_fly"
    if re.search(r"^reached on e[1-9]", d):
        return "field_error"
    if 'interference by batter' in d:
        return "field_out"
    for pattern, label in [
        (r"sacrifice fly|sac fly", "sac_fly"), (r"sacrifice bunt|sac bunt", "sac_bunt"),
        (r"catcher.*interference|interference on c\b", "catcher_interf"),
        (r"triple play", "triple_play"), (r"double play", "grounded_into_double_play"),
        (r"home run|homered|homers|grand slam", "home_run"),
        (r"\btriples?\b", "triple"), (r"\bdoubles?\b", "double"),
        (r"\bsingles?\b", "single"), (r"hit by pitch", "hit_by_pitch"),
        (r"intentional walk|intentionally walks", "intent_walk"), (r"\bwalks?\b", "walk"),
        (r"strikeout|strikes out|called out on strikes", "strikeout"),
        (r"reached on error|reaches on.*error", "field_error"),
        (r"fielder.?s choice", "fielders_choice"),
        (r"groundout|flyout|lineout|popfly|flyball|forceout|grounds out|flies out|lines out|pops out|force out", "field_out"),
    ]:
        if re.search(pattern, d):
            return label
    return "unknown"


def _score(value):
    match = re.fullmatch(r"\s*(\d+)\s*-\s*(\d+)\s*", str(value or ""))
    return [int(match[1]), int(match[2])] if match else None


def normalize_events(game):
    plays = game.get("raw_plays") or []
    basic = game.get("basic_info", {})
    names = defaultdict(set)
    for side in ("away", "home"):
        for role in ("batting", "pitching"):
            for p in game.get(role, {}).get(side, []):
                if p.get("player_id") and p.get("name"):
                    names[(side, name_key(p["name"]))].add(p["player_id"])

    def identity(play, role, side):
        candidates = names[(side, name_key(play.get(role)))]
        supplied = play.get(role + "_id")
        if len(candidates) == 1:
            return next(iter(candidates))
        return supplied or ""

    def before_bref(play):
        # BREF's score column is batting-team first; expose away/home everywhere.
        score = _score(play.get("score"))
        return list(reversed(score)) if score is not None and str(play.get("half", "")).lower() in {"bottom", "bot"} else score

    output = []
    previous_half = None
    previous_outs = None
    previous_score = None
    unordered_tail = False
    for i, play in enumerate(plays):
        half = str(play.get("half", "")).lower()
        inning = int(play.get("inning") or 0)
        half_key = (inning, half)
        side = "home" if half in ("bottom", "bot") else "away"
        other = "away" if side == "home" else "home"
        api = "away_score" in play or "home_score" in play
        if api:
            if previous_half and (inning, side == "home") < (previous_half[0], previous_half[1] in {"bottom", "bot"}):
                # A few old Gameday caches append supplemental plays after the
                # final inning. Their neighbors cannot supply pre-play state.
                unordered_tail = True
            before = previous_score if previous_score is not None else ([0, 0] if inning == 1 and half == "top" else None)
            after = [play["away_score"], play["home_score"]] if play.get("away_score") is not None and play.get("home_score") is not None else None
            outs_before = play.get("outs_before_play", previous_outs if half_key == previous_half else 0)
            outs_after = play.get("outs_after", play.get("outs_before"))
            bases = play.get("bases_before")
            if unordered_tail:
                before, outs_before = None, play.get("outs_before_play")
        else:
            before = before_bref(play)
            after = before_bref(plays[i + 1]) if i + 1 < len(plays) else None
            if i + 1 == len(plays):
                a, h = basic.get("away_score_value"), basic.get("home_score_value")
                if a is not None and h is not None:
                    after = [int(a), int(h)]
            outs_before = play.get("outs")
            nxt = plays[i + 1] if i + 1 < len(plays) else {}
            outs_after = nxt.get("outs") if (nxt.get("inning"), nxt.get("half")) == half_key else None
            raw_bases = play.get("runners_on_base")
            bases = [n for n in (1, 2, 3) if str(n) in raw_bases] if isinstance(raw_bases, str) else None
        kind = event_type(play)
        is_pa = kind not in ("unknown", "runner_event")
        is_ab = is_pa and kind not in {"walk", "intent_walk", "hit_by_pitch", "sac_fly", "sac_bunt", "sac_fly_double_play", "sac_bunt_double_play", "catcher_interf"}
        hit = kind in {"single", "double", "triple", "home_run"}
        score_diff = None if before is None else before[1 if side == "home" else 0] - before[0 if side == "home" else 1]
        runs = sum(after) - sum(before) if after is not None and before is not None else None
        output.append({
            "id": f"{game.get('game_id', '')}:{i}", "gameId": game.get("game_id", ""), "playIndex": i,
            "inning": inning, "half": "bottom" if side == "home" else "top",
            "batter": (play.get("batter") or "").replace("\xa0", " "),
            "batterId": identity(play, "batter", side),
            "pitcher": (play.get("pitcher") or "").replace("\xa0", " "),
            "pitcherId": identity(play, "pitcher", other),
            "team": display_team(basic.get(side + "_team_code", "")),
            "opponent": display_team(basic.get(other + "_team_code", "")),
            "eventType": kind, "description": play.get("description", ""),
            "isPA": is_pa, "isAB": is_ab, "isHit": hit,
            "isHomeRun": kind == "home_run", "isWalk": kind in {"walk", "intent_walk"},
            "isStrikeout": kind in {"strikeout", "strikeout_double_play"},
            "isHitByPitch": kind == "hit_by_pitch", "basesBefore": bases,
            "outsBefore": outs_before, "outsAfter": outs_after,
            "scoreBefore": before, "scoreAfter": after, "scoreDiff": score_diff,
            "runs": runs, "rbi": play.get("rbi"), "pitchCount": play.get("pitch_count"),
            "isGrandSlam": kind == "home_run" and (bases == [1, 2, 3] or bool(play.get("grand_slam"))),
            "source": "mlb" if api else "bref",
        })
        previous_score, previous_outs, previous_half = after, outs_after, half_key
    return output
