from unittest import TestCase

from webnovel.data import Image
from webnovel.epub.files import EpubImages, EpubImage

from ...helpers import get_test_data


class EpubImageTestCase(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.test_png = Image(
            url="file:///test-image.png",
            data=get_test_data("test-image.png", use_bytes=True),
            mimetype="image/png",
            did_load=True,
        )
        cls.test_jpg = Image(
            url="file:///test-image.jpg",
            data=get_test_data("test-image.jpg", use_bytes=True),
            mimetype="image/jpg",
            did_load=True,
        )

    def test_from_image_handles_png(self):
        png = EpubImage.from_image(self.test_png, image_id="image0001")
        self.assertEqual(png.file_id, "image0001")
        self.assertEqual(png.filename, "OEBPS/image0001.png")
        self.assertEqual(png.mimetype, self.test_png.mimetype)
        self.assertEqual(png.data, self.test_png.data)

    def test_from_image_handles_jpg(self):
        jpg = EpubImage.from_image(self.test_jpg, image_id="image0001")
        self.assertEqual(jpg.file_id, "image0001")
        self.assertEqual(jpg.filename, "OEBPS/image0001.jpg")
        self.assertEqual(jpg.mimetype, self.test_jpg.mimetype)
        self.assertEqual(jpg.data, self.test_jpg.data)


class EpubImagesTestCase(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.test_png = Image(
            url="file:///test-image.png",
            data=get_test_data("test-image.png", use_bytes=True),
            mimetype="image/png",
            did_load=True,
        )
        cls.test_jpg = Image(
            url="file:///test-image.jpg",
            data=get_test_data("test-image.jpg", use_bytes=True),
            mimetype="image/jpg",
            did_load=True,
        )

    def test_add_cover_image(self):
        images = EpubImages()
        images.add(self.test_png, is_cover_image=True)

        self.assertEqual(images.cover_image, "image000")
        self.assertEqual(images.image_id_counter, 1)
        self.assertEqual(
            images["image000"],
            EpubImage(file_id="image000", filename="OEBPS/image000.png", mimetype="image/png", data=self.test_png.data)
        )
        self.assertEqual(list(images.keys()), ["image000"])

    def test_force_replace_image(self):
        images = EpubImages()
        images.add(self.test_png)

        self.assertEqual(
            images,
            {
                "image000": EpubImage(
                    file_id="image000", filename="OEBPS/image000.png", mimetype="image/png", data=self.test_png.data
                )
            }
        )

        new_image = EpubImage.from_image(self.test_jpg, image_id="image000")
        images.add(new_image, force=True)

        self.assertEqual(
            images,
            {
                "image000": EpubImage(
                    file_id="image000", filename="OEBPS/image000.jpg", mimetype="image/jpg", data=self.test_jpg.data
                )
            }
        )

    def test_handles_collision_without_force(self):
        images = EpubImages()
        images.add(self.test_png)

        self.assertEqual(
            images,
            {
                "image000": EpubImage(
                    file_id="image000", filename="OEBPS/image000.png", mimetype="image/png", data=self.test_png.data
                )
            }
        )

        new_image = EpubImage.from_image(self.test_jpg, image_id="image000")
        with self.assertRaises(ValueError):
            images.add(new_image, force=False)

    def test_generate_image_id(self):
        images = EpubImages()
        for i in range(5):
            self.assertEqual(f"image{i:03d}", images.generate_image_id())
        self.assertEqual(images.image_id_counter, 5)
