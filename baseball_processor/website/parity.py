"""
Website data parity checks.

These checks compare processed workbook-style datasets with the JSON payload
used by the static website. They are intentionally non-blocking so generation
can continue while still making silent drift visible.
"""

from __future__ import annotations


def _tabular_count(value) -> int:
    if value is None:
        return 0
    empty = getattr(value, "empty", None)
    if empty is True:
        return 0
    try:
        return len(value)
    except TypeError:
        return 0


def _json_count(value) -> int | None:
    if value is None:
        return None
    if isinstance(value, dict):
        if "matrix" in value and isinstance(value["matrix"], list):
            return len(value["matrix"])
        return len(value)
    if isinstance(value, (list, tuple)):
        return len(value)
    return None


def _milestone_count(milestones, excluded_milestone_types=None) -> int:
    if not milestones:
        return 0

    excluded = set(excluded_milestone_types or [])
    count = 0
    for milestone_type, frame in milestones.items():
        if milestone_type in excluded:
            continue
        count += _tabular_count(frame)
    return count


def _weather_summary_count(weather_tracker) -> int:
    if weather_tracker is None:
        return 0

    stats = weather_tracker.get_summary_stats()
    count = 0
    for value in stats.values():
        if isinstance(value, dict):
            count += len(value)
        else:
            count += 1
    return count


def _call_count(obj, method_name, *args, **kwargs) -> int:
    if obj is None:
        return 0

    method = getattr(obj, method_name, None)
    if method is None:
        return 0

    return _tabular_count(method(*args, **kwargs))


def _core_sources(processed_data, excluded_milestone_types):
    return [
        ("Summary", "summary", _tabular_count(processed_data.get("summary_rows"))),
        (
            "Milestones",
            "milestones",
            _milestone_count(processed_data.get("milestones"), excluded_milestone_types),
        ),
        ("Hitters", "players", _tabular_count(processed_data.get("hitters"))),
        ("Pitchers", "pitchers", _tabular_count(processed_data.get("pitchers"))),
        ("Hall of Famers", "hallOfFamers", _tabular_count(processed_data.get("hofers_seen"))),
        (
            "Players Without Stats",
            "playersWithoutStats",
            _tabular_count(processed_data.get("players_without_stats")),
        ),
        ("Team Records", "teams", _tabular_count(processed_data.get("team_records"))),
        ("Game Log", "games", _tabular_count(processed_data.get("game_log"))),
        ("Stadiums", "stadiums", _tabular_count(processed_data.get("stadiums"))),
        ("Orioles Stadiums", "orioles", _tabular_count(processed_data.get("ori_stads"))),
        ("MLB Debuts", "debuts", _tabular_count(processed_data.get("mlb_debut_rows"))),
        ("Final Games", "finalGames", _tabular_count(processed_data.get("final_game_rows"))),
        ("Signature Home Runs", "signatureHRs", _tabular_count(processed_data.get("df_splash"))),
        ("Matchup Matrix", "matchupMatrix", _tabular_count(processed_data.get("df_matchups"))),
    ]


def _feature_gap_sources(processed_data):
    situation_tracker = processed_data.get("situation_tracker")
    defense_tracker = processed_data.get("defense_tracker")

    return [
        (
            "Weather & Timing",
            "weatherTiming",
            _weather_summary_count(processed_data.get("weather_tracker")),
        ),
        (
            "WPA Leaders",
            "wpaLeaders",
            _call_count(processed_data.get("saber_tracker"), "create_wpa_dataframe"),
        ),
        (
            "RISP Performance",
            "rispPerformance",
            _call_count(situation_tracker, "create_risp_dataframe", min_ab=5),
        ),
        (
            "2-Out Performance",
            "twoOutPerformance",
            _call_count(situation_tracker, "create_two_out_dataframe", min_ab=5),
        ),
        (
            "RISP + 2 Outs",
            "rispTwoOutPerformance",
            _call_count(situation_tracker, "create_clutch_situations_dataframe", min_ab=3),
        ),
        (
            "Bases Loaded",
            "basesLoaded",
            _call_count(situation_tracker, "create_bases_loaded_dataframe"),
        ),
        (
            "Late & Close",
            "lateClose",
            _call_count(situation_tracker, "create_late_close_dataframe", min_ab=5),
        ),
        (
            "Defensive Leaders",
            "defensiveLeaders",
            _call_count(defense_tracker, "create_defensive_leaders_dataframe", min_games=1),
        ),
        (
            "Lineup Analysis",
            "lineupAnalysis",
            _call_count(defense_tracker, "create_lineup_analysis_dataframe", min_games=1),
        ),
        (
            "Lineup Matrix",
            "lineupMatrix",
            _call_count(defense_tracker, "create_lineup_position_matrix"),
        ),
    ]


def collect_website_data_parity_issues(
    processed_data,
    json_data,
    excluded_milestone_types=None,
    include_feature_gaps=True,
):
    """Return non-blocking parity issues between processed data and website JSON."""
    issues = []

    for dataset, json_key, source_count in _core_sources(processed_data, excluded_milestone_types):
        website_count = _json_count(json_data.get(json_key))
        if source_count != (website_count or 0):
            issues.append(
                {
                    "severity": "warning",
                    "kind": "count_mismatch",
                    "dataset": dataset,
                    "jsonKey": json_key,
                    "sourceCount": source_count,
                    "websiteCount": website_count,
                    "message": (
                        f"{dataset} has {source_count} processed row(s), "
                        f"but website key {json_key!r} has {website_count or 0} row(s)."
                    ),
                }
            )

    if not include_feature_gaps:
        return issues

    for dataset, json_key, source_count in _feature_gap_sources(processed_data):
        if source_count == 0:
            continue

        website_count = _json_count(json_data.get(json_key))
        if website_count is None:
            issues.append(
                {
                    "severity": "info",
                    "kind": "missing_website_dataset",
                    "dataset": dataset,
                    "jsonKey": json_key,
                    "sourceCount": source_count,
                    "websiteCount": None,
                    "message": (
                        f"{dataset} has {source_count} processed row(s), "
                        f"but website key {json_key!r} is not serialized yet."
                    ),
                }
            )
        elif source_count != website_count:
            issues.append(
                {
                    "severity": "warning",
                    "kind": "count_mismatch",
                    "dataset": dataset,
                    "jsonKey": json_key,
                    "sourceCount": source_count,
                    "websiteCount": website_count,
                    "message": (
                        f"{dataset} has {source_count} processed row(s), "
                        f"but website key {json_key!r} has {website_count} row(s)."
                    ),
                }
            )

    return issues
