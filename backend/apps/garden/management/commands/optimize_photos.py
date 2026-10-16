"""One-off: optimize all stored garden photos in place.

Photos uploaded before server-side optimization live on in MEDIA_ROOT.
This command re-processes every stored photo through `optimize_image_file`
and atomically replaces the file under the same name, so database rows and
URLs stay untouched. Safe to run repeatedly (idempotent).
"""
import os
import tempfile

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db.models import Q

from PIL import UnidentifiedImageError

from apps.garden.images import optimize_image_file
from apps.garden.models import GardenItem


class Command(BaseCommand):
    help = 'Optimize all stored garden photos in place (idempotent)'

    def handle(self, *args, **options):
        items = GardenItem.objects.exclude(
            Q(photo='') | Q(photo__isnull=True)
        ).iterator()

        optimized = untouched = failed = 0
        for item in items:
            path = item.photo.path
            try:
                with item.photo.open('rb') as stored:
                    before = os.path.getsize(path)
                    result = optimize_image_file(stored)
            except (UnidentifiedImageError, OSError) as e:
                failed += 1
                self.stderr.write(f'Skipped {path}: {e}')
                continue

            if result is stored:  # already small enough, leave the file alone
                untouched += 1
                continue

            data = result.read()

            # Atomic replace: write a temp file in the same directory, then
            # rename over the original so a crash never leaves a half file.
            directory = os.path.dirname(path)
            fd, tmp_path = tempfile.mkstemp(prefix='.optimize-', dir=directory)
            try:
                with os.fdopen(fd, 'wb') as tmp:
                    tmp.write(data)
                os.replace(tmp_path, path)
            except BaseException:
                os.unlink(tmp_path)
                raise

            optimized += 1
            after = len(data)
            self.stdout.write(
                f'{os.path.relpath(path, settings.MEDIA_ROOT)}: '
                f'{before // 1024} KB -> {after // 1024} KB'
            )

        self.stdout.write(
            f'Done: {optimized} optimized, {untouched} already small, {failed} failed.'
        )
