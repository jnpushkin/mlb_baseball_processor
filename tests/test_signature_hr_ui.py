import unittest

import pandas as pd

from baseball_processor.website.react_chunks.badges import CODE as BADGES_CODE
from baseball_processor.website.serializers import DataSerializer


class SignatureHRUiTests(unittest.TestCase):
    def test_signature_hr_serializer_includes_player_id(self):
        rows = pd.DataFrame([{
            "Date": "08/29/2026",
            "Player": "Lars Nootbaar",
            "PlayerID": "nootbla01",
            "Team": "ARI",
            "Opponent": "SF",
            "Pitcher": "Ryan Walker",
            "Signature HR Number": "McCovey Cove HR #69",
            "GameID": "SFN202608291",
        }])

        serialized = DataSerializer()._serialize_signature_hrs(rows)

        self.assertEqual("nootbla01", serialized[0]["playerId"])
        self.assertEqual("SFN202608291", serialized[0]["gameId"])

    def test_signature_hr_tab_has_summary_filters_and_mobile_layout(self):
        self.assertIn("const SignatureHRsView", BADGES_CODE)
        self.assertIn("Witnessed landmarks", BADGES_CODE)
        self.assertIn("signatureType", BADGES_CODE)
        self.assertIn("filterOptions", BADGES_CODE)
        self.assertIn("mobileCard", BADGES_CODE)
        self.assertIn("<SignatureHRBadge", BADGES_CODE)


if __name__ == "__main__":
    unittest.main()
