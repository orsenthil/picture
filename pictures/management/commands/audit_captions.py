"""
Audit stored processed_explanation captions and clear any that look like
leaked model reasoning/instructions instead of a real caption (a bug present
before caption validation was added to TextProcessor).
"""
from django.core.management.base import BaseCommand
from pictures.models import PictureOfTheDay
from pictures.processors import TextProcessor


class Command(BaseCommand):
    help = 'Clear processed_explanation values that fail caption validation'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Report what would be cleared without changing the database',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        pictures = PictureOfTheDay.objects.exclude(
            processed_explanation__isnull=True
        ).exclude(processed_explanation='')

        cleared = 0
        for picture in pictures:
            if TextProcessor._is_valid_caption(picture.processed_explanation):
                continue

            cleared += 1
            self.stdout.write(self.style.WARNING(
                f'[{picture.source} {picture.date}] {picture.title!r}: '
                f'{picture.processed_explanation!r}'
            ))

            if not dry_run:
                picture.processed_explanation = None
                picture.is_processed = False
                picture.processing_error = 'Cleared invalid/garbage caption on audit'
                picture.save()

        if dry_run:
            self.stdout.write(self.style.SUCCESS(
                f'Dry run: {cleared} invalid caption(s) found (not modified)'
            ))
        else:
            self.stdout.write(self.style.SUCCESS(
                f'Cleared {cleared} invalid caption(s); marked for reprocessing'
            ))
