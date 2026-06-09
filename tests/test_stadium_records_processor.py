import unittest

from baseball_processor.processors.stadium_records_processor import StadiumRecordsProcessor


class StadiumRecordsProcessorTests(unittest.TestCase):
    def test_unify_stadium_name_uses_shared_aliases(self):
        processor = StadiumRecordsProcessor([])

        cases = {
            "Yankee Stadium III": "Yankee Stadium",
            "Busch Stadium III": "Busch Stadium",
            "AT&T Park": "Oracle Park",
            "SBC Park": "Oracle Park",
            "RingCentral Coliseum": "Oakland Coliseum",
        }

        for raw, canonical in cases.items():
            with self.subTest(raw=raw):
                self.assertEqual(canonical, processor._unify_stadium_name(raw))

    def test_unify_stadium_name_keeps_distinct_historical_stadiums(self):
        processor = StadiumRecordsProcessor([])

        self.assertEqual("Yankee Stadium II", processor._unify_stadium_name("Yankee Stadium II"))
        self.assertEqual("Busch Stadium II", processor._unify_stadium_name("Busch Stadium II"))


if __name__ == "__main__":
    unittest.main()
