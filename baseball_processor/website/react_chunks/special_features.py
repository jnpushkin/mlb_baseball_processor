"""Highlights, record exploration, and witnessed career moments."""
from pathlib import Path

CODE = Path(__file__).with_suffix('.jsx').read_text(encoding='utf-8')

CODE += Path(__file__).with_name("record_book.jsx").read_text(encoding="utf-8")
