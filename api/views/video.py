from functools import cached_property
from typing import Optional

from django import forms
from django.core.files.uploadedfile import TemporaryUploadedFile
from django.core.validators import BaseValidator
from django.utils.deconstruct import deconstructible
from django.utils.translation import gettext_lazy as _
from rest_framework import viewsets, serializers, status, exceptions
from rest_framework.decorators import api_view
from rest_framework.response import Response

from api import models, utils
from api.some import extractor


class CR(serializers.ModelSerializer):
    class Meta:
        model = models.Compare
        fields = '__all__'


class KF(serializers.ModelSerializer):
    class Meta:
        model = models.KeyFrame
        fields = '__all__'


class VideoSerializer(serializers.ModelSerializer):
    key_frames = KF(many=True)
    compare_results = CR(many=True)

    class Meta:
        model = models.Video
        fields = '__all__'


@deconstructible
class VideoFormatValidator(BaseValidator):
    message = _("Ensure this format in %(limit_value)s (it is %(show_value)s).")
    code = "format"

    def __init__(self):
        super(VideoFormatValidator, self).__init__(["mp4"], None)

    def compare(self, a, b):
        return a not in b

    def clean(self, x: TemporaryUploadedFile) -> Optional[str]:
        return (
            isinstance(x.content_type, str)
            and len(ct_split := x.content_type.split("/")) == 2
            and ct_split[1].lower()
            or None
        )


@deconstructible
class IsVideoValidator(BaseValidator):
    code = "video"

    def __init__(self):
        super(IsVideoValidator, self).__init__("video", None)

    def compare(self, a, b):
        return a != b

    def clean(self, x: TemporaryUploadedFile) -> Optional[str]:
        return (
            isinstance(x.content_type, str)
            and len(ct_split := x.content_type.split("/")) == 2
            and ct_split[0].lower()
            or None
        )


class VideoForm(forms.ModelForm):
    file = forms.FileField(validators=[VideoFormatValidator(), IsVideoValidator()])
    is_full = forms.BooleanField()

    class Meta:
        model = models.Video
        fields = ["file", "is_full"]

    def get_is_full(self):
        return

    def save(self, commit=True):
        super(VideoForm, self).save(False)
        if not commit:
            return self.instance

        self.instance.hash = self.file_hash

        self.instance, created = models.Video.objects.get_or_create(
            defaults=dict(is_full=self.instance.is_full),
            hash=self.file_hash,
            file=self.instance.file
        )   # type: models.Video, bool

        if not self.instance.is_key_frames_extracted:
            self.instance.extract_key_frames()

        return self.instance

    save.alters_data = True

    @cached_property
    def file_hash(self) -> str:
        return utils.get_hash(self.cleaned_data["file"])


class Video(viewsets.ModelViewSet):
    queryset = models.Video.objects.all()
    serializer_class = VideoSerializer

    def create(self, *args, **kwargs):
        video_form: VideoForm = VideoForm(self.request.POST, self.request.FILES)
        if not video_form.is_valid():
            raise exceptions.ValidationError

        instance: models.Video = video_form.save()
        if self.request.query_params.get("is_need_compare") == "1":
            instance.compare_with_fulls()

        data = self.serializer_class(instance=instance).data
        return Response(data, status=status.HTTP_201_CREATED, headers=self.get_success_headers(data))
