"""
Management command to initialize source configurations
"""
from django.core.management.base import BaseCommand
from pictures.models import PictureSource, SourceConfiguration


class Command(BaseCommand):
    help = 'Initialize source configurations for all available picture sources'

    def add_arguments(self, parser):
        parser.add_argument(
            '--disable',
            nargs='+',
            type=str,
            help='List of sources to disable during initialization (e.g., --disable apod)',
            default=[],
        )

    def handle(self, *args, **options):
        sources_to_disable = options.get('disable', [])
        
        created_count = 0
        updated_count = 0
        
        for source_value, source_label in PictureSource.choices:
            is_enabled = source_value not in sources_to_disable
            
            config, created = SourceConfiguration.objects.get_or_create(
                source=source_value,
                defaults={
                    'is_enabled': is_enabled,
                    'display_name': None,  # Use default label
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Created configuration for {source_value} ({source_label}) - '
                        f'{"Enabled" if is_enabled else "Disabled"}'
                    )
                )
            else:
                # Update if it was created but status changed
                if config.is_enabled != is_enabled:
                    config.is_enabled = is_enabled
                    config.save()
                    updated_count += 1
                    self.stdout.write(
                        self.style.WARNING(
                            f'Updated configuration for {source_value} - '
                            f'{"Enabled" if is_enabled else "Disabled"}'
                        )
                    )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\nInitialization complete: {created_count} created, {updated_count} updated'
            )
        )

