from unittest import TestCase, mock

from click.testing import CliRunner

from webnovel import cli


class SetCoverTestCase(TestCase):
    @mock.patch("webnovel.actions.set_cover_image_for_epub")
    def test_run(self, action_mock):
        runner = CliRunner()
        result = runner.invoke(cli.pywn, ["set-cover", "mybook.epub", "cover-image.tiff"])
        self.assertEqual(result.exit_code, 0)
        action_mock.assert_called_once_with("mybook.epub", "cover-image.tiff")


class RebuildCommandTestCase(TestCase):
    @mock.patch("webnovel.actions.rebuild")
    def test_run(self, action_mock):
        runner = CliRunner()
        result = runner.invoke(cli.pywn, ["rebuild", "mybook.epub"])
        self.assertEqual(result.exit_code, 0)
        action_mock.assert_called_once_with("mybook.epub", reload_chapters=tuple())

    @mock.patch("webnovel.actions.rebuild")
    def test_reload_chapters(self, action_mock):
        runner = CliRunner()
        result = runner.invoke(
            cli.pywn, ["rebuild", "mybook.epub", "--reload-chapter=chapter-1-slug", "--reload-chapter=chapter-33-slug"]
        )
        self.assertEqual(result.exit_code, 0)
        action_mock.assert_called_once_with("mybook.epub", reload_chapters=("chapter-1-slug", "chapter-33-slug"))


class CreateCommandTestCase(TestCase):
    @mock.patch("webnovel.actions.create_epub")
    def test_minimum_call(self, action_mock):
        runner = CliRunner()
        result = runner.invoke(cli.pywn, ["create", "https://example.com/novel/1"])
        self.assertEqual(result.exit_code, 0)
        action_mock.assert_called_once_with(
            "https://example.com/novel/1", None, cover_image_url=None, chapter_limit=None
        )

    @mock.patch("webnovel.actions.create_epub")
    def test_handles_filename(self, action_mock):
        runner = CliRunner()
        result = runner.invoke(cli.pywn, ["create", "https://example.com/novel/1", "--filename=test.epub"])
        self.assertEqual(result.exit_code, 0)
        action_mock.assert_called_once_with(
            "https://example.com/novel/1", "test.epub", cover_image_url=None, chapter_limit=None
        )

    @mock.patch("webnovel.actions.create_epub")
    def test_handles_cover_image_url(self, action_mock):
        runner = CliRunner()
        result = runner.invoke(
            cli.pywn,
            ["create", "https://example.com/novel/1", "--cover-image=https://example.com/imgs/cover-image.png"],
        )
        self.assertEqual(result.exit_code, 0)
        action_mock.assert_called_once_with(
            "https://example.com/novel/1",
            None,
            cover_image_url="https://example.com/imgs/cover-image.png",
            chapter_limit=None,
        )

    @mock.patch("webnovel.actions.create_epub")
    def test_handles_chapter_limit(self, action_mock):
        runner = CliRunner()
        result = runner.invoke(cli.pywn, ["create", "https://example.com/novel/1", "--chapter-limit=40"])
        self.assertEqual(result.exit_code, 0)
        action_mock.assert_called_once_with(
            "https://example.com/novel/1",
            None,
            cover_image_url=None,
            chapter_limit=40,
        )
