from unittest import TestCase, mock

from webnovel.cli import set_cover


class SetCoverTestCase(TestCase):
    @mock.patch("webnovel.actions.set_cover_image_for_epub")
    def test_run(self, action_mock):
        set_cover.run(["mybook.epub", "cover-image.tiff"])
        action_mock.assert_called_once_with(epub_file="mybook.epub", cover_image_path="cover-image.tiff")
