from unittest import TestCase

from webnovel import data

from .helpers import get_test_data


class ImageTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.png = get_test_data("test-image.png", use_bytes=True)
        cls.jpg = get_test_data("test-image.jpg", use_bytes=True)

    def test_get_mimetype_from_image_data_handles_png(self):
        self.assertEqual(data.Image.get_mimetype_from_image_data(self.png), "image/png")

    def test_get_mimetype_from_image_data_handles_jpg(self):
        self.assertEqual(data.Image.get_mimetype_from_image_data(self.jpg), "image/jpeg")
