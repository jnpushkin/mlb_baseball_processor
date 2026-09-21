"""Validate the exact compiled release bundle before deployment."""

import argparse
import hashlib
import json
from pathlib import Path


def validate_release(directory):
    directory = Path(directory)
    manifest = json.loads((directory / "release.json").read_text())
    for name, expected in manifest["files"].items():
        path = directory / name
        if not path.is_file():
            raise ValueError(f"Missing release file: {name}")
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected["sha256"]:
            raise ValueError(f"Release file changed after build: {name}")
    index = json.loads((directory / manifest["index"]).read_text())
    refs = [*index["__libraries"].values(), *index["__gameFiles"].values()]
    for ref in refs:
        if ref not in manifest["files"]:
            raise ValueError(f"Untracked data dependency: {ref}")
    html = (directory / manifest["html"]).read_text()
    if "text/babel" in html or "cdn.tailwindcss.com" in html:
        raise ValueError("Browser compiler remains in release")
    return manifest


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("directory", nargs="?", default=".")
    args = parser.parse_args()
    manifest = validate_release(args.directory)
    print(f"Validated {len(manifest['files'])} release files, schema {manifest['schemaVersion']}")


if __name__ == "__main__":
    main()
