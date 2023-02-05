from typing import Union

from webnovel.epub.files.base import EpubFile
from webnovel.data import Image


class EpubImage(EpubFile):
    @classmethod
    def from_image(cls, image: Image, image_id: str) -> "EpubImage":
        return EpubImage(
            file_id=image_id,
            filename=f"OEBPS/{image_id}{image.extension}",
            mimetype=image.mimetype,
            data=image.data,
        )


class EpubImages(dict):
    image_id_counter: int
    cover_image: str = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.image_id_counter = 0

    def validate(self) -> bool:
        return (
            len(self) <= self.image_id_counter
            and (self.cover_image is None or self.cover_image in self)
        )

    def get_cover_image(self) -> EpubImage:
        return self[self.cover_image] if self.cover_image and self.cover_image in self else None

    def generate_image_id(self):
        image_id = None
        while image_id is None or image_id in self:
            image_id = f"image{self.image_id_counter:03d}"
            self.image_id_counter += 1
        return image_id

    def add(self, image: Union[EpubImage, Image], is_cover_image: bool = False, force: bool = False) -> None:
        """
        Add an image to the image list.

        :param image: An EpubImage or Image instance to add to this list.
        :param is_cover_image: (optional) Should this image be set as the cover image. Default: False
        :param force: (optional) Control how to handle an image_id collision. Default: False
        """
        if isinstance(image, Image):
            image = EpubImage.from_image(image, image_id=self.generate_image_id())
        if image.file_id in self and not force:
            raise ValueError(f"EpubImageList: collision on key {image.file_id!r}")
        self[image.file_id] = image
        if is_cover_image:
            self.cover_image = image.file_id
