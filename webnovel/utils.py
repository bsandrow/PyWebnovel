import io
from typing import IO, Union


def normalize_io(file_or_io: Union[IO, str] = None, mode: str = "rb") -> IO:
    if file_or_io is None:
        return io.BytesIO()
    if isinstance(file_or_io, str):
        return open(file_or_io, mode=mode)
    return file_or_io

