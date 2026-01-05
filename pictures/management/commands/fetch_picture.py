"""
Unified command to fetch and process pictures from any source
"""
import os
from datetime import date, datetime
from django.core.management.base import BaseCommand
from django.conf import settings
from pictures.models import PictureOfTheDay, PictureSource
from pictures.fetchers import get_fetcher
from pictures.processors import ImageProcessor, TextProcessor


class Command(BaseCommand):
    help = 'Fetch and process Picture of the Day from various sources'

    def add_arguments(self, parser):
        parser.add_argument(
            '--source',
            type=str,
            choices=[choice[0] for choice in PictureSource.choices],
            default='apod',
            help='Source to fetch from (default: apod)',
        )
        parser.add_argument(
            '--date',
            type=str,
            help='Fetch picture for specific date (YYYY-MM-DD)',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force re-processing even if already processed',
        )
        parser.add_argument(
            '--download-image',
            action='store_true',
            help='Download and store image locally',
        )
        parser.add_argument(
            '--process-text',
            action='store_true',
            default=True,
            help='Process text with OpenAI (default: True)',
        )
        parser.add_argument(
            '--fetch-all',
            action='store_true',
            help='Fetch all available pictures (for sources that support multiple images like Bing)',
        )

    def handle(self, *args, **options):
        source = options.get('source', 'apod')
        target_date = options.get('date')
        force = options.get('force', False)
        download_image = options.get('download_image', False)
        process_text = options.get('process_text', True)
        fetch_all = options.get('fetch_all', False)
        
        try:
            fetcher = get_fetcher(source)
            
            if fetch_all and hasattr(fetcher, 'fetch_all_available'):
                self.stdout.write(f'Fetching all available {source.upper()} pictures...')
                all_pictures = fetcher.fetch_all_available()
                
                self.stdout.write(f'Found {len(all_pictures)} pictures')
                
                for picture_data in all_pictures:
                    picture_date = datetime.strptime(picture_data['date'], '%Y-%m-%d').date()
                    self.stdout.write(f'Processing {source.upper()} for {picture_date}...')
                    
                    picture, created = self.save_picture(source, picture_data, force)
                    
                    if created:
                        self.stdout.write(self.style.SUCCESS(f'Created: {picture.title}'))
                    else:
                        self.stdout.write(self.style.WARNING(f'Exists: {picture.title}'))
                    
                    if picture.media_type == 'image':
                        self.get_image_metadata(picture)
                    
                    if download_image and picture.media_type == 'image':
                        self.download_and_store_image(picture)
                    
                    if process_text and (not picture.is_processed or force):
                        self.process_text(picture, source)
                
                self.stdout.write(self.style.SUCCESS(f'Successfully processed {len(all_pictures)} pictures!'))
                return
            
            if target_date:
                try:
                    picture_date = datetime.strptime(target_date, '%Y-%m-%d').date()
                except ValueError:
                    self.stdout.write(self.style.ERROR('Invalid date format. Use YYYY-MM-DD'))
                    return
            else:
                picture_date = date.today()
            
            self.stdout.write(f'Fetching {source.upper()} for {picture_date}...')
            
            picture_data = fetcher.fetch(picture_date)
            
            picture, created = self.save_picture(source, picture_data, force)
            
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created new picture: {picture.title}'))
            else:
                self.stdout.write(self.style.WARNING(f'Picture already exists: {picture.title}'))
            
            if picture.media_type == 'image':
                self.stdout.write('Getting image metadata...')
                self.get_image_metadata(picture)
                self.stdout.write(self.style.SUCCESS('Image metadata retrieved ✓'))
            
            if download_image and picture.media_type == 'image':
                self.stdout.write('Downloading image...')
                self.download_and_store_image(picture)
                self.stdout.write(self.style.SUCCESS('Image downloaded ✓'))
            
            if process_text and (not picture.is_processed or force):
                self.stdout.write('Processing text with OpenAI...')
                self.process_text(picture, source)
                self.stdout.write(self.style.SUCCESS('Processing complete!'))
            elif picture.is_processed and not force:
                self.stdout.write('Picture already processed. Use --force to reprocess.')
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {str(e)}'))
            import traceback
            self.stdout.write(traceback.format_exc())

    def save_picture(self, source, picture_data, force=False):
        """Save picture data to database"""
        picture_date = datetime.strptime(picture_data['date'], '%Y-%m-%d').date()
        
        defaults = {
            'title': picture_data['title'],
            'original_explanation': picture_data['explanation'],
            'media_type': picture_data.get('media_type', 'image'),
            'image_url': picture_data.get('image_url', ''),
            'hd_image_url': picture_data.get('hd_image_url'),
            'thumbnail_url': picture_data.get('thumbnail_url'),
            'copyright': picture_data.get('copyright'),
            'source_url': picture_data.get('source_url'),
        }
        
        if force:
            picture, created = PictureOfTheDay.objects.update_or_create(
                source=source,
                date=picture_date,
                defaults=defaults
            )
            if not created:
                picture.is_processed = False
                picture.processing_error = None
                picture.save()
        else:
            picture, created = PictureOfTheDay.objects.get_or_create(
                source=source,
                date=picture_date,
                defaults=defaults
            )
        
        return picture, created

    def get_image_metadata(self, picture):
        """Get image metadata (width, height, size) from full resolution URL"""
        try:
            image_processor = ImageProcessor()
            
            image_url = picture.hd_image_url or picture.image_url
            
            if not image_url:
                self.stdout.write(self.style.WARNING('No image URL available'))
                return
            
            width, height, size_bytes = image_processor.get_image_metadata(image_url)
            
            if width and height and size_bytes:
                picture.image_width = width
                picture.image_height = height
                picture.image_size_bytes = size_bytes
                picture.save()
                self.stdout.write(f'  Dimensions: {width}x{height}, Size: {size_bytes / (1024*1024):.2f} MB')
            else:
                self.stdout.write(self.style.WARNING('  Could not retrieve image metadata'))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error getting image metadata: {str(e)}'))

    def download_and_store_image(self, picture):
        """Download image and store locally with size information"""
        try:
            image_processor = ImageProcessor()
            
            image_url = picture.hd_image_url or picture.image_url
            
            if not image_url:
                self.stdout.write(self.style.WARNING('No image URL available'))
                return
            
            local_path = image_processor.get_image_path(
                picture.source,
                picture.date
            )
            
            from django.conf import settings
            full_path = os.path.join(settings.MEDIA_ROOT, local_path)
            
            _, width, height, size_bytes = image_processor.download_image(
                image_url,
                full_path
            )
            
            picture.local_image_path = local_path
            picture.image_width = width
            picture.image_height = height
            picture.image_size_bytes = size_bytes
            picture.save()
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error downloading image: {str(e)}'))
            picture.processing_error = f"Image download error: {str(e)}"
            picture.save()
            raise

    def process_text(self, picture, source):
        """Process picture explanation with OpenAI"""
        try:
            text_processor = TextProcessor()
            
            context_map = {
                'apod': 'astronomy',
                'wikipedia': 'general',
                'bing': 'general',
            }
            context = context_map.get(source, 'general')
            
            simplified_text = text_processor.simplify_text(picture.original_explanation, context)
            picture.simplified_explanation = simplified_text
            picture.save()
            
            self.stdout.write('Text simplified ✓')
            
            processed_text = text_processor.add_wikipedia_links(simplified_text, context)
            picture.processed_explanation = processed_text
            picture.is_processed = True
            picture.processing_error = None
            picture.save()
            
            self.stdout.write('Wikipedia links added ✓')
            
        except Exception as e:
            picture.processing_error = str(e)
            picture.save()
            raise