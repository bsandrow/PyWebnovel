import functools
import json
from pathlib import Path
from shutil import rmtree
from tempfile import mkdtemp
from unittest import TestCase

from webnovel import dir


class create_test_directory:
    directory: Path

    def __call__(self, func):
        @functools.wraps(func)
        def wrapped(*args, **kwargs):
            with self as test_directory:
                return func(*args, test_directory, **kwargs)

        return wrapped

    def __enter__(self):
        self.directory = Path(mkdtemp(prefix="pywebnovel.tests"))
        return self.directory

    def __exit__(self, *exc_info):
        rmtree(self.directory)


class WebNovelDirectoryTestCase(TestCase):
    def test_handles_bad_directory(self):
        with self.assertRaises(ValueError) as cm:
            dir.WebNovelDirectory.from_path("/does-not-exist")
        self.assertEqual(cm.exception.args[0], "Not a directory: /does-not-exist")

    @create_test_directory()
    def test_handles_empty_directory(self, testdir):
        wnd = dir.WebNovelDirectory.from_path(testdir)
        self.assertEqual(wnd.path, testdir)

    @create_test_directory()
    def test_overrides_mismatched_path(self, testdir):
        wndfile = testdir / "status.json"
        with wndfile.open("w") as fh:
            fh.write('{"path": "/tmp/other-dir"}')
        wnd = dir.WebNovelDirectory.from_path(testdir)
        self.assertEqual(wnd.path, testdir)


class WNDItemTestCase(TestCase):
    def test_normalize_path(self):
        actual = dir.WNDItem.normalize_path(
            Path("~/Dropbox/Webnovels/Test Book.epub").expanduser(), Path("~/Dropbox/Webnovels").expanduser()
        )
        expected = Path("Test Book.epub")
        self.assertEqual(actual, expected)

        actual = dir.WNDItem.normalize_path(
            Path("~/Dropbox/Webnovels/Test Book.epub").expanduser(), Path("~/Downloads").expanduser()
        )
        expected = Path("../Dropbox/Webnovels/Test Book.epub")
        self.assertEqual(actual, expected)

        actual = dir.WNDItem.normalize_path(
            Path("~/Dropbox/Webnovels/Dropped/Test Book.epub").expanduser(), Path("~/Dropbox/Webnovels").expanduser()
        )
        expected = Path("Dropped/Test Book.epub")
        self.assertEqual(actual, expected)

        actual = dir.WNDItem.normalize_path(
            Path("Test Book.epub").expanduser(), Path("~/Dropbox/Webnovels").expanduser()
        )
        expected = Path("Test Book.epub")
        self.assertEqual(actual, expected)

    def get_bucket_path(self):
        item = dir.WNDItem(path="Test Book.epub", status=dir.WebNovelStatus.DROPPED)
        actual = item.get_bucket_path()
        expected = Path("Dropped")
        self.assertEqual(actual, expected)

    def get_bucket_path(self):
        item = dir.WNDItem(path="Test Book.epub", status=dir.WebNovelStatus.DROPPED)
        actual = item.get_bucket_path()
        expected = Path("Dropped")
        self.assertEqual(actual, expected)

    @create_test_directory()
    def test_update_bucket(self, testdir: Path):
        filename = "Test Book.epub"
        dropped_dir = testdir / "dropped"
        ongoing_dir = testdir / "ongoing"
        item = dir.WNDItem(path=Path(filename), status=dir.WebNovelStatus.ONGOING)
        (testdir / filename).touch()  # Create empty file for test

        # Move from not in a bucket to being in a bucket.
        item.update_bucket(basedir=testdir)
        self.assertEqual(item.path, (ongoing_dir / filename).relative_to(testdir))
        self.assertTrue((testdir / "ongoing" / filename).exists())
        self.assertFalse((testdir / "dropped" / filename).exists())
        self.assertFalse((testdir / filename).exists())

        item.status = dir.WebNovelStatus.DROPPED
        item.update_bucket(basedir=testdir)
        self.assertEqual(item.path, (dropped_dir / filename).relative_to(testdir))
        self.assertFalse((testdir / "ongoing" / filename).exists())
        self.assertTrue((testdir / "dropped" / filename).exists())
        self.assertFalse((testdir / filename).exists())


class WNDControllerTestCase(TestCase):
    @create_test_directory()
    def test_clean(self, testdir):
        filename = "Test Book.epub"
        ongoing_dir = testdir / "ongoing"
        item = dir.WNDItem(path=Path(filename), status=dir.WebNovelStatus.ONGOING)
        (testdir / filename).touch()  # Create empty file for test
        status_content = {"path": str(testdir), "webnovels": [item.to_dict()]}
        with (testdir / "status.json").open("w") as fh:
            fh.write(json.dumps(status_content))

        controller = dir.WNDController.from_path(testdir)

        self.assertEqual(controller.directory.path, testdir)

        controller.clean()

        self.assertFalse((testdir / filename).exists())
        self.assertTrue((ongoing_dir / filename).exists())
        self.assertTrue((testdir / "status.json").exists())
        self.assertTrue((testdir / "status.json").is_file())

        with (testdir / "status.json").open("r") as fh:
            data_raw = fh.read()

        webnovel_dir = dir.WebNovelDirectory.from_json(data_raw)
        self.assertEqual(webnovel_dir.path, testdir)
        self.assertEqual(
            webnovel_dir.webnovels, [dir.WNDItem(path=Path("ongoing") / filename, status=dir.WebNovelStatus.ONGOING)]
        )
