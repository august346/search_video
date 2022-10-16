from typing import Generator

from django.db import models
from storages.backends.s3boto3 import S3Boto3Storage

import api.utils
from api import utils
from api.utils import get_img_md5_and_content

KEY_FRAMES_BUCKET_NAME = "key-frames"
VIDEOS_BUCKET_NAME = "videos"

KEY_FRAME_EXTRACT_ALGO_VERSION = 0
COMPARE_ALGO_VERSION = 0


def get_s3_storage(bucket_name: str) -> S3Boto3Storage:
    storage: S3Boto3Storage = S3Boto3Storage()
    storage.bucket_name = bucket_name

    return storage


class User(models.Model):
    id = models.CharField(primary_key=True, max_length=128)


class Video(models.Model):
    hash = models.CharField(unique=True, max_length=32)
    created_at = models.DateTimeField(auto_now_add=True)
    file = models.FileField(storage=get_s3_storage(VIDEOS_BUCKET_NAME))
    is_key_frames_extracted = models.BooleanField(default=False)
    key_frames = models.ManyToManyField("KeyFrame")
    is_full = models.BooleanField()

    def extract_key_frames(self):
        for kf in KeyFrame.create_from_video(self):     # type: models.KeyFrame
            self.key_frames.add(kf)

        self.is_key_frames_extracted = True
        self.save(update_fields=["is_key_frames_extracted"])

    def compare_with_fulls(self):
        for v in Video.objects.filter(is_full=True).exclude(id=self.id):
            Compare.compare(v, self)


class KeyFrame(models.Model):
    hash = models.CharField(max_length=32)
    created_at = models.DateTimeField(auto_now_add=True)
    image = models.ImageField(storage=get_s3_storage(KEY_FRAMES_BUCKET_NAME))
    version = models.PositiveSmallIntegerField(default=KEY_FRAME_EXTRACT_ALGO_VERSION)

    class Meta:
        unique_together = ["hash", "version"]

    @staticmethod
    def create_from_video(video: Video) -> Generator["KeyFrame", None, None]:
        for img in api.utils.get_keyframes(video.file):
            md5, image = get_img_md5_and_content(img)
            kf, created = KeyFrame.objects.get_or_create(
                defaults=dict(image=image),
                hash=md5, version=KEY_FRAME_EXTRACT_ALGO_VERSION
            )
            yield kf


class Compare(models.Model):
    full = models.ForeignKey(Video, on_delete=models.CASCADE)
    short = models.ForeignKey(Video, on_delete=models.CASCADE, related_name="compare_results")
    score = models.PositiveIntegerField()
    version = models.PositiveSmallIntegerField(default=COMPARE_ALGO_VERSION)

    class Meta:
        unique_together = ["full_id", "short_id", "version"]

    @staticmethod
    def compare(full: Video, short: Video) -> "Compare":
        full_images, short_images = [
            [kf.image for kf in obj.key_frames.all()]
            for obj in [full, short]
        ]  # type: list[models.ImageField], list[models.ImageField]

        score, version = utils.compare_keyframes(full_images, short_images)  # type: int, int

        c, created = Compare.objects.get_or_create(
            defaults=dict(score=score),
            full=full, short=short, version=version
        )   # type: Compare, bool

        return c
