from types import SimpleNamespace

from baseball_processor import main as main_mod


def _args(**overrides):
    values = {
        "excel_only": False,
        "quick_stats": False,
        "skip_ncaa_player_refresh": False,
        "surge_domain": None,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def test_should_refresh_ncaa_shared_players_respects_flag_and_env(monkeypatch):
    assert main_mod._should_refresh_ncaa_shared_players(_args()) is True

    assert main_mod._should_refresh_ncaa_shared_players(
        _args(skip_ncaa_player_refresh=True)
    ) is False

    monkeypatch.setenv("MLB_PROCESSOR_SKIP_NCAA_REFRESH", "1")
    assert main_mod._should_refresh_ncaa_shared_players(_args()) is False


def test_website_sync_exports_mlb_before_refreshing_ncaa(monkeypatch):
    calls = []
    processed_data = {}
    games_data = [{"game_id": "SFN202604070"}]

    def fake_export(data, games, args, automatic=False):
        calls.append(("mlb", list(data.get("_raw_games", [])), automatic))
        return "/tmp/shared_players.json"

    def fake_refresh(args):
        calls.append(("ncaa", None, None))
        return True

    monkeypatch.setattr(main_mod, "_export_mlb_shared_players", fake_export)
    monkeypatch.setattr(main_mod, "_refresh_ncaa_shared_players", fake_refresh)

    main_mod._sync_shared_player_exports_for_website(processed_data, games_data, _args())

    assert processed_data["_raw_games"] == games_data
    assert calls == [
        ("mlb", games_data, True),
        ("ncaa", None, None),
    ]


def test_website_sync_skips_ncaa_refresh_when_mlb_export_fails(monkeypatch):
    calls = []

    def fake_export(data, games, args, automatic=False):
        calls.append("mlb")
        return None

    def fake_refresh(args):
        calls.append("ncaa")
        return True

    monkeypatch.setattr(main_mod, "_export_mlb_shared_players", fake_export)
    monkeypatch.setattr(main_mod, "_refresh_ncaa_shared_players", fake_refresh)

    main_mod._sync_shared_player_exports_for_website({}, [], _args())

    assert calls == ["mlb"]
