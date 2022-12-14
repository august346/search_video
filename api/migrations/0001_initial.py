# Generated by Django 4.1.1 on 2022-10-18 22:14

from django.db import migrations, models
import django.db.models.deletion
import storages.backends.s3boto3


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='KeyFrame',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('hash', models.CharField(max_length=32)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('image', models.ImageField(storage=storages.backends.s3boto3.S3Boto3Storage(), upload_to='')),
                ('version', models.PositiveSmallIntegerField()),
            ],
            options={
                'unique_together': {('hash', 'version')},
            },
        ),
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.CharField(max_length=128, primary_key=True, serialize=False)),
            ],
        ),
        migrations.CreateModel(
            name='Video',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('hash', models.CharField(max_length=32, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('file', models.FileField(storage=storages.backends.s3boto3.S3Boto3Storage(), upload_to='')),
                ('is_key_frames_extracted', models.BooleanField(default=False)),
                ('is_full', models.BooleanField()),
                ('meta', models.JSONField(null=True)),
                ('key_frames', models.ManyToManyField(to='api.keyframe')),
            ],
        ),
        migrations.CreateModel(
            name='Compare',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('score', models.PositiveIntegerField()),
                ('version', models.PositiveSmallIntegerField()),
                ('full', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='compared_with', to='api.video')),
                ('short', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='compare_results', to='api.video')),
            ],
            options={
                'ordering': ['version', '-score', 'pk'],
                'unique_together': {('full_id', 'short_id', 'version')},
                'index_together': {('short_id', 'version')},
            },
        ),
    ]
