from unittest import TestCase, mock

from webnovel.cli import create


class CreateCommandTestCase(TestCase):
    @mock.patch("webnovel.actions.create_epub")
    def test_minimum_call(self, action_mock):
        create.run(["--novel-url=https://example.com/novel/1"])
        action_mock.assert_called_once_with(
            "https://example.com/novel/1", None, cover_image_url=None, chapter_limit=None
        )

    @mock.patch("webnovel.actions.create_epub")
    def test_handles_filename(self, action_mock):
        create.run(["--novel-url=https://example.com/novel/1", "--filename=test.epub"])
        action_mock.assert_called_once_with(
            "https://example.com/novel/1", "test.epub", cover_image_url=None, chapter_limit=None
        )

    @mock.patch("webnovel.actions.create_epub")
    def test_handles_cover_image_url(self, action_mock):
        create.run(
            ["--novel-url=https://example.com/novel/1", "--cover-image-url=https://example.com/imgs/cover-image.png"]
        )
        action_mock.assert_called_once_with(
            "https://example.com/novel/1",
            None,
            cover_image_url="https://example.com/imgs/cover-image.png",
            chapter_limit=None,
        )

    @mock.patch("webnovel.actions.create_epub")
    def tesat_handles_chapter_limit(self, action_mock):
        create.run(["--novel-url=https://example.com/novel/1", "--chapter-limit=40"])
        action_mock.assert_called_once_with(
            "https://example.com/novel/1",
            None,
            cover_image_url=None,
            chapter_limit=40,
        )
