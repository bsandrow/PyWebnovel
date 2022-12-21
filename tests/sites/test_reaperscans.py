from unittest import TestCase

from webnovel.sites import reaperscans


class ReaperScansTestCase(TestCase):
    def test_validate_url(self):
        self.assertTrue(reaperscans.validate_url("https://reaperscans.com/novels/7145-max-talent-player"))
        self.assertTrue(reaperscans.validate_url("https://www.reaperscans.com/novels/7145-max-talent-player"))
        self.assertTrue(reaperscans.validate_url("http://www.reaperscans.com/novels/7145-max-talent-player"))
        self.assertTrue(reaperscans.validate_url("http://www.reaperscans.com/novels/7145-max-talent-player/"))
        self.assertFalse(reaperscans.validate_url("https://reaperscans.com/novels/max-talent-player/"))
