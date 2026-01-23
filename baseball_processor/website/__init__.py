"""
Website generation module for baseball statistics.
Generates interactive HTML/React websites from processed game data.
"""

from .generator import WebsiteGenerator, generate_website_from_data

__all__ = ['WebsiteGenerator', 'generate_website_from_data']