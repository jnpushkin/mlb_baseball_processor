"""Rebuild only website assets from the current serialized data; no network enrichment."""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from baseball_processor.website.bundle import build_site
from baseball_processor.website.serializers import DataSerializer


def read_payload(path):
    value = json.loads(path.read_text())
    for ref in value.pop("__dataSidecars", []):
        part = json.loads((path.parent / ref["path"]).read_text())
        if part["mode"] == "append":
            value[part["key"]] = value.get(part["key"], []) + part["items"]
        else:
            value[part["key"]] = part["value"]
    return value


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--retain-index", action="append", default=[],
                    help="Keep an additional local hashed index and its data available to open tabs (up to two).")
parser.add_argument("--refresh-companions", action="store_true", help="Refresh companions from their source records.")
args = parser.parse_args()
root = Path(__file__).resolve().parents[1]
data = read_payload(root / "data.json")
if data.get("__schemaVersion") == 2:
    libraries = data["__libraries"]
    game_files = data["__gameFiles"]
    generated = data["generatedAt"]
    data = {k: json.loads((root / v).read_text()) for k, v in libraries.items()}
    data["games"] = [json.loads((root / v).read_text()) for v in game_files.values()]
    data["generatedAt"] = generated
elif (root / "award-data.json").exists():
    data["awardChecklists"] = read_payload(root / "award-data.json")
if args.refresh_companions:
    serializer = DataSerializer()
    serializer.data = {"game_log": pd.DataFrame([
        {"GameID": g["gameId"], "Date": g["date"], "Venue": g["venue"],
         "Home Team": g["homeTeam"], "Away Team": g["awayTeam"]}
        for g in data["games"]
    ])}
    data["companionData"] = serializer._serialize_companions()
    data["generatedAt"] = datetime.now().strftime("%B %d, %Y at %I:%M %p")
print(build_site(data, root / "MLB Game Passport - BREF.html", retain_indexes=args.retain_index))
