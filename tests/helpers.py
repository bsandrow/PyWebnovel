import pathlib
from typing import Union

TEST_DATA_DIR = pathlib.Path(__file__).parent / "data"


def get_test_data(filename, use_bytes: bool = False) -> Union[str, bytes]:
    with (TEST_DATA_DIR / filename).open(mode="rb" if use_bytes else "r") as fh:
        return fh.read()
