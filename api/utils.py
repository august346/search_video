import hashlib
import os
import subprocess
import tempfile
from io import BytesIO
from typing import Generator

from PIL import Image
from django.core.files.base import ContentFile
from django.db.models.fields.files import FieldFile

_RUN_CMD_TEMPLATE = "ffmpeg -skip_frame nokey -i {} -vsync 2 -s 10x10 -r 30 -f image2 {}/thumbnails-%02d.jpeg"


def get_hash(file: BytesIO) -> str:
    chunk_size = 65536
    md5 = hashlib.md5()

    while data := file.read(chunk_size):
        md5.update(data)

    file.seek(0)

    return md5.hexdigest()


def get_key_frames(file) -> Generator[Image.Image, None, None]:
    for _ in range(10):
        yield Image.new('RGB', (10, 10))


def compare_keyframes(set_0: list[Image], set_1: list[Image]) -> tuple[int, int]:
    return 1, 0


def get_img_md5_and_content(img: Image.Image) -> tuple[str, ContentFile]:
    with BytesIO() as f:
        img.save(f, format='PNG', quality=100)
        f.seek(0)
        md5: str = get_hash(f)
        img_content = ContentFile(f.getvalue(), f'{md5}.png')
        return md5, img_content


def get_keyframes(video_file: FieldFile) -> Generator[Image.Image, None, None]:
    with tempfile.TemporaryDirectory() as temp_dir:
        src_path: str = os.path.join(temp_dir, "src")
        dst_path: str = os.path.join(temp_dir, "dst")
        os.mkdir(src_path)
        os.mkdir(dst_path)
        with tempfile.NamedTemporaryFile(dir=src_path, suffix=f".{video_file.name.rsplit('.', 1)[-1]}") as temp_file:
            for line in video_file:
                temp_file.write(line)

            temp_file.seek(0)

            yield from _extract(temp_file.name, dst_path)


def _extract(src_fp: str, dst_path: str) -> Generator[Image.Image, None, None]:
    subprocess.run(_RUN_CMD_TEMPLATE.format(src_fp, dst_path).split(" "))

    for file_name in os.listdir(dst_path):
        with Image.open(os.path.join(dst_path, file_name)) as im:
            yield im