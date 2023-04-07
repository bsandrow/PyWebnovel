from unittest import TestCase, mock

from webnovel.cli import rebuild


class RebuildCommandTestCase(TestCase):
    @mock.patch("webnovel.actions.rebuild")
    def test_run(self, action_mock):
        rebuild.run(["mybook.epub"])
        action_mock.assert_called_once_with("mybook.epub")
