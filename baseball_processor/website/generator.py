"""
Main website generator - orchestrates HTML creation from baseball data.
"""
import logging
from pathlib import Path
import re
from .serializers import DataSerializer
from .templates import HTMLTemplate
from .parity import collect_website_data_parity_issues

DATA_SIDECAR_THRESHOLD_BYTES = 128 * 1024
DATA_SIDECAR_MAX_BYTES = 1_800_000

class WebsiteGenerator:
    """Generate an interactive HTML website from processed game data."""

    def __init__(self, data):
        """
        Initialize with processed data dictionary containing:
        - summary_rows: List of summary statistics
        - milestones: Dict of milestone DataFrames
        - hitters: DataFrame of hitter statistics
        - pitchers: DataFrame of pitcher statistics
        - team_records: DataFrame of team records
        - game_log: DataFrame of games
        - stadiums: DataFrame of stadium records (optional)
        """
        self.data = data
        self.serializer = DataSerializer()

    def generate(self, output_path):
        """Generate the HTML file and separate data JSON file."""
        logging.info("Generating interactive website...")

        # Convert data to JSON-serializable format
        json_data = self.serializer.serialize_all_data(self.data)
        parity_issues = collect_website_data_parity_issues(
            self.data,
            json_data,
            excluded_milestone_types=self.serializer.EXCLUDED_MILESTONE_TYPES,
        )
        self._log_parity_issues(parity_issues)

        output_file = Path(output_path)
        output_dir = output_file.parent

        from .bundle import build_site
        return build_site(json_data, output_file)

    def _write_data_sidecars(self, data_payload, output_dir):
        """Move large top-level list payloads into smaller sidecar JSON files."""
        return self._write_payload_sidecars(
            data_payload,
            output_dir,
            file_prefix='data',
            stale_pattern='data-*.json',
            skip_keys={'awardChecklists'},
        )

    def _write_award_sidecars(self, award_payload, output_dir):
        """Move large award checklist payloads into smaller sidecar JSON files."""
        return self._write_payload_sidecars(
            award_payload,
            output_dir,
            file_prefix='award-sidecar',
            stale_pattern='award-sidecar-*.json',
        )

    def _write_payload_sidecars(self, payload, output_dir, file_prefix, stale_pattern, skip_keys=None):
        """Move large top-level dict/list payloads into smaller sidecar JSON files."""
        skip_keys = skip_keys or set()
        sidecars = []
        slim_payload = dict(payload)

        for stale_sidecar in output_dir.glob(stale_pattern):
            stale_sidecar.unlink()

        for key, value in list(payload.items()):
            if key.startswith("__") or key in skip_keys:
                continue
            if not isinstance(value, (dict, list)):
                continue
            if self._json_size(value) < DATA_SIDECAR_THRESHOLD_BYTES:
                continue

            safe_key = re.sub(r'[^a-zA-Z0-9_-]+', '-', key).strip('-') or 'payload'
            if isinstance(value, list):
                chunks = self._chunk_list_sidecar(key, value)
                slim_payload[key] = []
                for idx, chunk in enumerate(chunks, start=1):
                    filename = f"{file_prefix}-{safe_key}-{idx}.json"
                    sidecar_payload = {
                        "key": key,
                        "mode": "append",
                        "items": chunk,
                    }
                    (output_dir / filename).write_text(HTMLTemplate.create_data_json(sidecar_payload), encoding='utf-8')
                    sidecars.append({"path": filename, "key": key, "mode": "append"})
            else:
                filename = f"{file_prefix}-{safe_key}-1.json"
                sidecar_payload = {
                    "key": key,
                    "mode": "replace",
                    "value": value,
                }
                (output_dir / filename).write_text(HTMLTemplate.create_data_json(sidecar_payload), encoding='utf-8')
                slim_payload[key] = {}
                sidecars.append({"path": filename, "key": key, "mode": "replace"})

        if sidecars:
            slim_payload["__dataSidecars"] = sidecars
        else:
            slim_payload.pop("__dataSidecars", None)
        return slim_payload, sidecars

    def _chunk_list_sidecar(self, key, rows):
        """Split one list into sidecar chunks below the configured byte budget."""
        if self._json_size({"key": key, "mode": "append", "items": rows}) <= DATA_SIDECAR_MAX_BYTES:
            return [rows]

        chunks = []
        current = []
        for row in rows:
            current.append(row)
            payload = {"key": key, "mode": "append", "items": current}
            if len(current) > 1 and self._json_size(payload) > DATA_SIDECAR_MAX_BYTES:
                last = current.pop()
                chunks.append(current)
                current = [last]
        if current:
            chunks.append(current)
        return chunks

    def _json_size(self, value):
        return len(HTMLTemplate.create_data_json(value).encode('utf-8'))

    def _log_parity_issues(self, issues):
        if not issues:
            return

        warnings = [issue for issue in issues if issue["severity"] == "warning"]
        feature_gaps = [issue for issue in issues if issue["severity"] != "warning"]

        for issue in warnings:
            logging.warning("Website data parity warning: %s", issue["message"])

        if feature_gaps:
            labels = ", ".join(issue["dataset"] for issue in feature_gaps[:6])
            extra = len(feature_gaps) - 6
            if extra > 0:
                labels = f"{labels}, +{extra} more"
            logging.info("Website feature parity gaps detected: %s", labels)


def generate_website_from_data(processed_data, output_path="baseball_stats.html"):
    """
    Convenience function to generate website from processed baseball data.

    Args:
        processed_data: Dictionary containing all processed DataFrames
        output_path: Path where HTML file should be saved

    Returns:
        Path to generated HTML file

    Example:
        >>> from baseball_processor.website import generate_website_from_data
        >>>
        >>> website_data = {
        >>>     'summary_rows': summary_rows,
        >>>     'milestones': milestone_dfs,
        >>>     'hitters': hitters_df,
        >>>     'pitchers': pitchers_df,
        >>>     'team_records': team_records_df,
        >>>     'game_log': game_log_df,
        >>>     'stadiums': stadiums_df  # optional
        >>> }
        >>>
        >>> html_path = output_file.replace('.xlsx', '.html')
        >>> generate_website_from_data(website_data, html_path)
    """
    generator = WebsiteGenerator(processed_data)
    return generator.generate(output_path)
