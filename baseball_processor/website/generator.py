"""
Main website generator - orchestrates HTML creation from baseball data.
"""
import logging
from pathlib import Path
from .serializers import DataSerializer
from .templates import HTMLTemplate

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

        # Create the HTML content using template
        html_content = HTMLTemplate.create_full_page(json_data)

        # Create the JSON data file content
        data_json_content = HTMLTemplate.create_data_json(json_data)

        # Write HTML file
        output_file = Path(output_path)
        output_file.write_text(html_content, encoding='utf-8')

        # Write data.json alongside the HTML file
        data_file = output_file.parent / 'data.json'
        data_file.write_text(data_json_content, encoding='utf-8')

        html_size_mb = output_file.stat().st_size / (1024 * 1024)
        data_size_mb = data_file.stat().st_size / (1024 * 1024)

        logging.info(f"Website generated: {output_file.name} ({html_size_mb:.1f} MB) + data.json ({data_size_mb:.1f} MB)")
        logging.info(f"Location: {output_file.absolute()}")
        logging.info(f"Open in browser: file://{output_file.absolute()}")

        return output_file


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
