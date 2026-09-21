import unittest
from urllib.parse import urlparse

from baseball_processor.server import (
    bind_host_for_mode,
    build_url,
    get_request_token,
    is_authorized,
)


class ServerSafetyTests(unittest.TestCase):
    def test_default_mode_binds_localhost_only(self):
        self.assertEqual("127.0.0.1", bind_host_for_mode(False))

    def test_lan_mode_binds_all_interfaces(self):
        self.assertEqual("0.0.0.0", bind_host_for_mode(True))

    def test_build_url_includes_encoded_token(self):
        self.assertEqual(
            "http://localhost:5555/?token=a%20b",
            build_url("localhost", 5555, "a b"),
        )

    def test_request_token_can_come_from_query_or_header(self):
        self.assertEqual("abc", get_request_token(urlparse("/api/add?token=abc"), {}))
        self.assertEqual("abc", get_request_token(urlparse("/api/add"), {"X-Add-Game-Token": "abc"}))
        self.assertEqual("abc", get_request_token(urlparse("/api/add"), {"Authorization": "Bearer abc"}))

    def test_post_authorization_requires_matching_token(self):
        parsed = urlparse("/api/add?token=good")

        self.assertTrue(is_authorized(parsed, {}, "good"))
        self.assertFalse(is_authorized(parsed, {}, "bad"))


class CompanionEditorTests(unittest.TestCase):
    def setUp(self):
        import json
        import tempfile
        from pathlib import Path

        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.games = [
            {
                "gameId": "CLE201605280",
                "date": "05/28/2016",
                "venue": "Progressive Field",
                "awayTeam": "BAL",
                "homeTeam": "CLE",
            },
            {
                "gameId": "NYN202609140",
                "date": "09/14/2026",
                "venue": "Citi Field",
                "awayTeam": "BAL",
                "homeTeam": "NYM",
            },
        ]
        (self.root / "data.json").write_text(json.dumps({"games": self.games}))
        (self.root / "companions.csv").write_text(
            "GameID,Companions,Date,Matchup,Venue\nCLE\u00a0201605280.00,Dad,05/28/2016,BAL @ CLE,Progressive Field\nCLE201605280,,05/28/2016,BAL @ CLE,Progressive Field\nNYN202609140,,09/14/2026,BAL @ NYM,Citi Field\n"
        )

    def payload(self):
        from baseball_processor.companion_manager import read_records

        return {"gameId": "NYN202609140", "companions": ["Dad"], "revision": read_records(self.root)["revision"]}

    def test_normalization_merges_companions_without_collapsing_game_numbers(self):
        from baseball_processor.utils.companions import companion_map, normalize_companion_game_id

        self.assertEqual("CLE201605280", normalize_companion_game_id("CLE\u00a0201605280.00"))
        self.assertEqual("MIA202609140", normalize_companion_game_id("MIA202609140"))
        self.assertEqual("MNYN202609140", normalize_companion_game_id("MNYN202609140"))
        rows = [
            {"GameID": "CLE\u00a0201605280.00", "Companions": "Dad"},
            {"GameID": "CLE201605280", "Companions": "Charles|Dad"},
            {"GameID": "CLE201605280", "Companions": ""},
            {"GameID": "CLE201605281", "Companions": "Mom"},
        ]
        self.assertEqual({"CLE201605280": ["Dad", "Charles"], "CLE201605281": ["Mom"]}, companion_map(rows))

    def test_serialization_and_sync_match_spreadsheet_formatted_ids(self):
        import pandas as pd
        from unittest.mock import patch
        from baseball_processor.main import _sync_companions_csv
        from baseball_processor.website.serializers import DataSerializer

        serializer = DataSerializer()
        serializer.data = {
            "game_log": pd.DataFrame(
                [
                    {
                        "GameID": "CLE201605280",
                        "Venue": "Progressive Field",
                        "Date": "05/28/2016",
                        "Home": "CLE",
                        "Away": "BAL",
                    }
                ]
            )
        }
        with patch("baseball_processor.utils.constants.BASE_DIR", self.root):
            result = serializer._serialize_companions()
        self.assertEqual(1, result["companions"]["Dad"]["totalGames"])
        self.assertEqual(["Dad"], result["gameCompanions"]["CLE201605280"])
        path = self.root / "companions.csv"
        path.write_text("GameID,Companions\nCLE\u00a0201605280.00,Dad\n")
        before = path.read_bytes()
        with patch("baseball_processor.main.BASE_DIR", self.root):
            _sync_companions_csv([{"game_id": "CLE201605280", "basic_info": {"date_yyyymmdd": "20160528"}}])
        self.assertEqual(before, path.read_bytes())

    def test_save_preserves_other_games_and_rejects_stale_or_invalid_edits(self):
        from baseball_processor.companion_manager import CompanionConflict, read_records, save_edit, validate_edit

        payload = self.payload()
        with self.assertRaisesRegex(ValueError, "attended archive"):
            validate_edit(self.root, {**payload, "gameId": "not-a-game"})
        for names in ["Dad", ["bad|separator"], ["\n"], ["A" * 61], [None]]:
            with self.assertRaises(ValueError):
                validate_edit(self.root, {**payload, "companions": names})
        self.assertEqual(["Dad"], validate_edit(self.root, {**payload, "companions": ["dad", "Dad"]})["companions"])
        save_edit(self.root, payload)
        records = read_records(self.root)
        self.assertTrue(all(g["companions"] == ["Dad"] for g in records["games"]))
        self.assertEqual(1, len(list((self.root / "cache/companion_backups").glob("*.csv"))))
        with self.assertRaises(CompanionConflict):
            save_edit(self.root, payload)
        save_edit(self.root, {**payload, "revision": records["revision"], "companions": []})
        records = read_records(self.root)
        self.assertEqual(["Dad"], records["games"][0]["companions"])
        self.assertEqual([], records["games"][1]["companions"])

    def test_publish_failure_preserves_saved_companions_and_never_deploys_failed_build(self):
        import subprocess
        from unittest.mock import patch
        from baseball_processor import server
        from baseball_processor.companion_manager import read_records

        with (
            patch.object(server, "PROJECT_DIR", self.root),
            patch.object(server.subprocess, "run", side_effect=subprocess.CalledProcessError(1, ["build"])),
            patch.object(server, "deploy_to_surge") as deploy,
        ):
            result = server.update_companions(self.payload())
        self.assertTrue(result["saved"])
        self.assertFalse(result["processed"])
        self.assertFalse(result["deployed"])
        deploy.assert_not_called()
        self.assertEqual(["Dad"], read_records(self.root)["games"][1]["companions"])

    def test_authenticated_api_queues_and_reports_stale_edits(self):
        import json
        import threading
        from http.server import ThreadingHTTPServer
        from types import SimpleNamespace
        from unittest.mock import patch
        from urllib.error import HTTPError
        from urllib.request import Request, urlopen
        from baseball_processor import server

        payload = self.payload()
        submitted = []
        store = SimpleNamespace(
            submit_companions=lambda value: submitted.append(value) or {"id": "test-job", "state": "queued"}
        )
        http = ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
        thread = threading.Thread(target=http.serve_forever, daemon=True)
        url = f"http://127.0.0.1:{http.server_port}/api/companions"
        with (
            patch.object(server, "PROJECT_DIR", self.root),
            patch.object(server, "_server_token", "test-token"),
            patch.object(server, "get_job_store", return_value=store),
        ):
            thread.start()
            try:
                for method in ["GET", "POST"]:
                    with self.assertRaises(HTTPError) as denied:
                        urlopen(Request(url, method=method, data=b"{}" if method == "POST" else None), timeout=2)
                    self.assertEqual(403, denied.exception.code)
                with urlopen(Request(url, headers={"X-Add-Game-Token": "test-token"}), timeout=2) as response:
                    self.assertEqual(["Dad"], json.load(response)["games"][0]["companions"])
                with urlopen(
                    Request(
                        url,
                        method="POST",
                        headers={"X-Add-Game-Token": "test-token"},
                        data=json.dumps(payload).encode(),
                    ),
                    timeout=2,
                ) as response:
                    self.assertEqual(202, response.status)
                self.assertEqual([payload], submitted)
                with self.assertRaises(HTTPError) as stale:
                    urlopen(
                        Request(
                            url,
                            method="POST",
                            headers={"X-Add-Game-Token": "test-token"},
                            data=json.dumps({**payload, "revision": "old"}).encode(),
                        ),
                        timeout=2,
                    )
                self.assertEqual(409, stale.exception.code)
            finally:
                http.shutdown()
                http.server_close()
                thread.join(timeout=2)

    def test_companion_and_add_jobs_share_one_serial_worker(self):
        import threading
        from baseball_processor.jobs import JobStore

        started = threading.Event()
        finish = threading.Event()
        order = []

        def add(pk, on_progress):
            started.set()
            finish.wait(3)
            order.append("add")
            return {"ok": True}

        def companions(payload, on_progress):
            order.append("companions")
            return {"ok": True, "saved": True, "processed": True, "deployed": True}

        store = JobStore(self.root / "jobs.json", add, companions)
        try:
            store.submit(1)
            self.assertTrue(started.wait(2))
            first = store.submit_companions(self.payload())
            self.assertEqual(first["id"], store.submit_companions(self.payload())["id"])
            self.assertEqual([], order)
            finish.set()
            store.executor.shutdown(wait=True)
            self.assertEqual(["add", "companions"], order)
            self.assertTrue(store.get(first["id"])["deployed"])
        finally:
            finish.set()
            store.executor.shutdown(wait=True)


if __name__ == "__main__":
    unittest.main()
