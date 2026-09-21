import unittest

from baseball_processor.website.react_chunks.badges import CODE as BADGES_CODE
from baseball_processor.website.react_chunks.journeys import CODE as JOURNEYS_CODE
from baseball_processor.website.react_chunks.special import CODE as SPECIAL_CODE


class VisualTabImprovementTests(unittest.TestCase):
    def test_generic_data_tables_have_a_default_mobile_card(self):
        self.assertIn("const defaultMobileCard", JOURNEYS_CODE)
        self.assertIn("const renderMobileCard = mobileCard || defaultMobileCard", JOURNEYS_CODE)
        self.assertIn('className="hidden sm:block overflow-x-auto relative"', JOURNEYS_CODE)

    def test_players_navigation_is_grouped(self):
        self.assertIn("const playerGroups", SPECIAL_CODE)
        self.assertIn("label: 'Stats'", SPECIAL_CODE)
        self.assertIn("label: 'Recognition'", SPECIAL_CODE)
        self.assertIn("label: 'Background'", SPECIAL_CODE)
        self.assertIn("label: 'Tools'", SPECIAL_CODE)

    def test_milestones_use_compact_primary_and_advanced_filters(self):
        self.assertIn("showMilestoneFilters", JOURNEYS_CODE)
        self.assertIn("More filters", JOURNEYS_CODE)
        self.assertIn('id="milestone-type-filter"', JOURNEYS_CODE)
        self.assertIn('id="timeline-filter"', JOURNEYS_CODE)

    def test_special_bookends_and_collection_gaps_have_story_views(self):
        self.assertIn("const CareerBookendsView", BADGES_CODE)
        self.assertIn("Personal Record Book", BADGES_CODE)
        self.assertIn("MLB Debuts Witnessed", BADGES_CODE)
        self.assertIn("Final MLB Games Witnessed", BADGES_CODE)
        self.assertIn("Missing ({missingNumbers.length})", BADGES_CODE)
        self.assertIn("Missing ({missingCells.length})", BADGES_CODE)


if __name__ == "__main__":
    unittest.main()
