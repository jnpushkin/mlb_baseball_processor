"""Ordered React source chunks for the generated website."""

from .core_foundation import CODE as CORE_FOUNDATION_CODE
from .core import CODE as CORE_CODE
from .game_details import CODE as GAME_DETAILS_CODE
from .journeys import CODE as JOURNEYS_CODE
from .tables import CODE as TABLES_CODE
from .dashboard import CODE as DASHBOARD_CODE
from .badges import CODE as BADGES_CODE
from .special import CODE as SPECIAL_CODE
from .player_views import CODE as PLAYER_VIEWS_CODE

REACT_CHUNKS = [
    CORE_FOUNDATION_CODE,
    CORE_CODE,
    GAME_DETAILS_CODE,
    JOURNEYS_CODE,
    TABLES_CODE,
    DASHBOARD_CODE,
    BADGES_CODE,
    SPECIAL_CODE,
    PLAYER_VIEWS_CODE,
]

__all__ = ['REACT_CHUNKS']
