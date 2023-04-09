from contextlib import contextmanager
import pathlib
import shutil
import tempfile
from typing import Iterable, Optional, Union
from unittest import TestCase as TestCase_orig
from zipfile import ZipFile

from freezegun import freeze_time
from requests_mock import Mocker as RequestsMocker

from webnovel import data, epub

TEST_DATA_DIR = pathlib.Path(__file__).parent / "data"


def get_test_data(filename, use_bytes: bool = False) -> Union[str, bytes]:
    with (TEST_DATA_DIR / filename).open(mode="rb" if use_bytes else "r") as fh:
        return fh.read()


class TestCase(TestCase_orig):
    TEST_DIR: str
    req_mock: RequestsMocker

    # A mapping of URL / Path to file contents
    mocked_requests: dict[str, Union[str, bytes]] = None

    def setUp(self):
        super().setUp()
        self.requests_mock = RequestsMocker()
        self.requests_mock.start()
        if self.mocked_requests:
            for url, content in self.mocked_requests.items():
                kwargs = {"content": content} if isinstance(content, bytes) else {"text": content}
                self.requests_mock.get(url, **kwargs)

    def tearDown(self):
        self.requests_mock.stop()
        super().setUp()

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.TEST_DIR = tempfile.mkdtemp(suffix=".pywn-test")

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(cls.TEST_DIR)

    @classmethod
    def create_epub(cls, jpg: bytes = None, timestamp: str = "2001-01-01 12:15", chapters: list[data.Chapter] = None):
        """Create an epub file for testing purposes."""
        _, epubfile = tempfile.mkstemp(prefix=f"pywn_{cls.__name__}_", suffix=".epub", dir=cls.TEST_DIR)
        pkg = epub.EpubPackage(
            file_or_io=epubfile,
            options={
                "include_title_page": True,
                "include_toc_page": True,
                "include_images": True,
            },
            metadata={
                "novel_url": "https://example.com/novel/creepy-story-club",
                "site_id": "Example.com",
                "novel_id": "creepy-story-club",
                "title": "Creepy Story Club",
                "status": data.NovelStatus.ONGOING.value,
                "summary": "A\nB\nC",
                "summary_type": epub.SummaryType.text.value,
                "author": {"name": "John Smythe"},
                "cover_image_url": "https://example.com/imgs/creepy-story-club.jpg",
            },
        )

        if jpg:
            pkg.add_image(
                image=data.Image(url="", data=jpg, mimetype="image/jpeg", did_load=True),
                content=jpg,
                is_cover_image=True,
            )

        for chapter in chapters or []:
            pkg.add_chapter(chapter)

        with freeze_time(timestamp):
            pkg.save()

        return epubfile

    @contextmanager
    def assert_files_changed(
        self,
        epub_file: str,
        expected_changed_files: Iterable,
        expected_new_files: Optional[Iterable] = None,
        expected_initial_files: Optional[Iterable] = None,
        expected_final_files: Optional[Iterable] = None,
    ):
        """Assert Before/After Changes on the contents of an EPUB file."""

        # NOTE: The explicit test for None when choosing to do assertions is a
        # speicfic choice, which allows empty iterables to be passed when the
        # expected set of files is an empty set.

        expected_changed_files = set(expected_changed_files) if expected_changed_files is not None else None
        expected_new_files = set(expected_new_files) if expected_new_files is not None else None
        expected_initial_files = set(expected_initial_files) if expected_initial_files is not None else None
        expected_final_files = set(expected_final_files) if expected_final_files is not None else None

        with ZipFile(epub_file) as zfh:
            pre_file_map = {fname: zfh.read(fname) for fname in zfh.namelist()}
            pre_files = set(pre_file_map.keys())

        #
        # If expected_initial_files was provided, assert it.
        #
        if expected_initial_files is not None:
            self.assertEqual(pre_files, expected_initial_files)

        yield

        with ZipFile(epub_file) as zfh:
            post_file_map = {fname: zfh.read(fname) for fname in zfh.namelist()}
            post_files = set(post_file_map.keys())

        #
        # If expected_final_files was provided, assert that the full list of
        # files in post_file_map looks like it.
        #
        if expected_final_files is not None:
            self.assertEqual(post_files, expected_final_files)

        #
        # If expected_new_files was provided, assert that these files are only
        # present in post_files.
        #
        if expected_new_files is not None:
            actual_new_files = post_files - pre_files
            self.assertEqual(actual_new_files, expected_new_files)

        common_files = pre_files & post_files

        #
        # Make sure that all files we expect to have changes were present both
        # before _and_ after the change. expected_new_files should be used to
        # assert files that were expected to only be present in the
        # post_file_map.
        #
        self.assertEqual(
            expected_changed_files - common_files,
            set(),
            (
                f"Files that were expected to change where not present either in "
                f"the package before or after the change: {expected_changed_files - common_files}"
            ),
        )

        #
        # Assert that all files expected to change did _not_ remain the same.
        #
        for filename in common_files - expected_changed_files:
            self.assertEqual(
                pre_file_map[filename],
                post_file_map[filename],
                (
                    f"\n"
                    f"File {filename} unexpectedly had changes to content.\n\n"
                    f"==[ Before ]==\n\n"
                    f"{pre_file_map[filename]!r}\n\n"
                    f"==[ After  ]==\n\n"
                    f"{post_file_map[filename]!r}\n\n"
                    f"==============\n"
                ),
            )

        #
        # Assert that all files that were _not_ expected to change actually
        # remained the same.
        #
        for filename in expected_changed_files:
            self.assertNotEqual(
                pre_file_map[filename],
                post_file_map[filename],
                (
                    f"\n"
                    f"File {filename} was expected to change, but didn't\n\n"
                    f"==[ Contents ]==\n\n"
                    f"{pre_file_map[filename]!r}\n\n"
                    f"==============\n"
                ),
            )
