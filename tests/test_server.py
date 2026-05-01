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


if __name__ == "__main__":
    unittest.main()
