"""
Django management command to clean up old pictures from the database.

This command removes pictures older than a specified number of days,
with options to keep a minimum number of recent pictures per source.
"""
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from datetime import timedelta
from pictures.models import PictureOfTheDay, PictureSource


class Command(BaseCommand):
    help = 'Remove old pictures from the database for cleanup and garbage collection'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=90,
            help='Number of days to keep pictures (default: 90)',
        )
        parser.add_argument(
            '--keep-min',
            type=int,
            default=10,
            help='Minimum number of recent pictures to keep per source (default: 10)',
        )
        parser.add_argument(
            '--source',
            type=str,
            choices=[choice[0] for choice in PictureSource.choices],
            help='Only clean up pictures from a specific source (optional)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting',
        )

    def handle(self, *args, **options):
        days = options['days']
        keep_min = options['keep_min']
        source_filter = options.get('source')
        dry_run = options['dry_run']

        cutoff_date = timezone.now().date() - timedelta(days=days)
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n=== Picture Cleanup {"(DRY RUN)" if dry_run else ""} ===\n'
            )
        )
        self.stdout.write(f'Cutoff date: {cutoff_date} (keeping pictures from last {days} days)')
        self.stdout.write(f'Minimum to keep per source: {keep_min}')
        if source_filter:
            self.stdout.write(f'Source filter: {source_filter}')
        self.stdout.write('')

        sources = [source_filter] if source_filter else [choice[0] for choice in PictureSource.choices]
        
        total_deleted = 0
        total_kept = 0
        
        for source in sources:
            queryset = PictureOfTheDay.objects.filter(source=source).order_by('-date')
            total_count = queryset.count()
            
            old_pictures = queryset.filter(date__lt=cutoff_date)
            old_count = old_pictures.count()
            
            recent_pictures = queryset.filter(date__gte=cutoff_date)
            recent_count = recent_pictures.count()
            
            if recent_count < keep_min:
                pictures_to_keep = queryset[:keep_min]
                keep_ids = set(pictures_to_keep.values_list('id', flat=True))
                pictures_to_delete = queryset.exclude(id__in=keep_ids)
                delete_count = pictures_to_delete.count()
            else:
                pictures_to_delete = old_pictures
                delete_count = old_count
            
            if delete_count > 0:
                if dry_run:
                    self.stdout.write(
                        self.style.WARNING(
                            f'[{source.upper()}] Would delete {delete_count} pictures '
                            f'(keeping {total_count - delete_count} recent ones)'
                        )
                    )
                    examples = pictures_to_delete[:5]
                    for pic in examples:
                        self.stdout.write(f'  - Would delete: {pic.date} - {pic.title[:50]}...')
                    if delete_count > 5:
                        self.stdout.write(f'  ... and {delete_count - 5} more')
                else:
                    deleted = pictures_to_delete.delete()[0]
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'[{source.upper()}] Deleted {deleted} pictures '
                            f'(kept {total_count - deleted} recent ones)'
                        )
                    )
                    total_deleted += deleted
            else:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'[{source.upper()}] No cleanup needed ({total_count} pictures, all within retention period)'
                    )
                )
            
            total_kept += (total_count - delete_count)
            self.stdout.write('')
        
        self.stdout.write('=' * 50)
        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f'\nDRY RUN: Would delete {total_deleted} pictures, keeping {total_kept}'
                )
            )
            self.stdout.write('Run without --dry-run to perform the actual cleanup.')
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f'\nCleanup complete: Deleted {total_deleted} pictures, kept {total_kept}'
                )
            )
        self.stdout.write('')