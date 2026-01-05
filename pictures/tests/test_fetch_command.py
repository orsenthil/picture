"""
Tests for the fetch_picture management command
"""
from django.test import TestCase
from django.core.management import call_command
from django.utils import timezone
from datetime import date
from io import StringIO
from unittest.mock import patch, MagicMock
from pictures.models import PictureOfTheDay, PictureSource


class FetchPictureCommandTest(TestCase):
    """Test cases for fetch_picture management command"""
    
    def setUp(self):
        """Set up test data"""
        pass
    
    @patch('pictures.management.commands.fetch_picture.get_fetcher')
    def test_fetch_picture_creates_new(self, mock_get_fetcher):
        """Test that fetch_picture creates a new picture"""
        # Mock the fetcher
        mock_fetcher = MagicMock()
        mock_get_fetcher.return_value = mock_fetcher
        
        # Mock fetch response
        today = date.today()
        mock_fetcher.fetch.return_value = {
            'date': today.strftime('%Y-%m-%d'),
            'title': 'Test Picture',
            'explanation': 'Test explanation',
            'image_url': 'https://example.com/image.jpg',
            'media_type': 'image'
        }
        
        # Count before
        count_before = PictureOfTheDay.objects.count()
        
        # Run command
        out = StringIO()
        call_command('fetch_picture', source='apod', stdout=out, stderr=out)
        
        # Count after
        count_after = PictureOfTheDay.objects.count()
        self.assertEqual(count_after, count_before + 1)
        
        # Verify picture was created
        picture = PictureOfTheDay.objects.get(source=PictureSource.APOD, date=today)
        self.assertEqual(picture.title, 'Test Picture')
        self.assertEqual(picture.original_explanation, 'Test explanation')
    
    @patch('pictures.management.commands.fetch_picture.get_fetcher')
    def test_fetch_picture_does_not_duplicate(self, mock_get_fetcher):
        """Test that fetch_picture doesn't create duplicates"""
        # Create existing picture
        today = date.today()
        PictureOfTheDay.objects.create(
            source=PictureSource.APOD,
            date=today,
            title='Existing Picture',
            original_explanation='Existing explanation',
            image_url='https://example.com/image.jpg'
        )
        
        # Mock the fetcher
        mock_fetcher = MagicMock()
        mock_get_fetcher.return_value = mock_fetcher
        mock_fetcher.fetch.return_value = {
            'date': today.strftime('%Y-%m-%d'),
            'title': 'New Picture',
            'explanation': 'New explanation',
            'image_url': 'https://example.com/image.jpg',
            'media_type': 'image'
        }
        
        # Count before
        count_before = PictureOfTheDay.objects.count()
        
        # Run command (without --force)
        out = StringIO()
        call_command('fetch_picture', source='apod', stdout=out, stderr=out)
        
        # Count should be unchanged
        count_after = PictureOfTheDay.objects.count()
        self.assertEqual(count_after, count_before)
        
        # Picture should still have original title
        picture = PictureOfTheDay.objects.get(source=PictureSource.APOD, date=today)
        self.assertEqual(picture.title, 'Existing Picture')
    
    @patch('pictures.management.commands.fetch_picture.get_fetcher')
    @patch('pictures.management.commands.fetch_picture.ImageProcessor')
    @patch('pictures.management.commands.fetch_picture.TextProcessor')
    def test_fetch_picture_force_update(self, mock_text_processor, mock_image_processor, mock_get_fetcher):
        """Test that --force updates existing picture and allows reprocessing"""
        # Create existing picture
        today = date.today()
        PictureOfTheDay.objects.create(
            source=PictureSource.APOD,
            date=today,
            title='Old Title',
            original_explanation='Old explanation',
            image_url='https://example.com/image.jpg',
            is_processed=True
        )
        
        # Mock the fetcher
        mock_fetcher = MagicMock()
        mock_get_fetcher.return_value = mock_fetcher
        mock_fetcher.fetch.return_value = {
            'date': today.strftime('%Y-%m-%d'),
            'title': 'New Title',
            'explanation': 'New explanation',
            'image_url': 'https://example.com/new-image.jpg',
            'media_type': 'image'
        }
        
        # Mock image processor
        mock_img_processor_instance = MagicMock()
        mock_image_processor.return_value = mock_img_processor_instance
        mock_img_processor_instance.get_image_metadata.return_value = (1920, 1080, 1024000)
        
        # Mock text processor to prevent actual API calls
        mock_txt_processor_instance = MagicMock()
        mock_text_processor.return_value = mock_txt_processor_instance
        mock_txt_processor_instance.simplify_text.return_value = 'Simplified text'
        mock_txt_processor_instance.add_wikipedia_links.return_value = 'Processed text with links'
        
        # Run command with --force
        out = StringIO()
        call_command('fetch_picture', source='apod', force=True, stdout=out, stderr=out)
        
        # Picture should be updated
        picture = PictureOfTheDay.objects.get(source=PictureSource.APOD, date=today)
        self.assertEqual(picture.title, 'New Title')
        self.assertEqual(picture.original_explanation, 'New explanation')
        # When force is used, is_processed is reset to False in save_picture,
        # then process_text runs and sets it back to True
        self.assertTrue(picture.is_processed)
        # Verify that processing was called (indicating the reset allowed reprocessing)
        mock_txt_processor_instance.simplify_text.assert_called_once()
        mock_txt_processor_instance.add_wikipedia_links.assert_called_once()
    
    @patch('pictures.management.commands.fetch_picture.get_fetcher')
    def test_fetch_picture_with_date(self, mock_get_fetcher):
        """Test fetching picture for specific date"""
        # Mock the fetcher
        mock_fetcher = MagicMock()
        mock_get_fetcher.return_value = mock_fetcher
        
        target_date = date(2024, 1, 15)
        mock_fetcher.fetch.return_value = {
            'date': target_date.strftime('%Y-%m-%d'),
            'title': 'Specific Date Picture',
            'explanation': 'Test explanation',
            'image_url': 'https://example.com/image.jpg',
            'media_type': 'image'
        }
        
        # Run command with date
        out = StringIO()
        call_command('fetch_picture', source='apod', date='2024-01-15', stdout=out, stderr=out)
        
        # Verify picture was created with correct date
        picture = PictureOfTheDay.objects.get(source=PictureSource.APOD, date=target_date)
        self.assertEqual(picture.title, 'Specific Date Picture')
    
    @patch('pictures.management.commands.fetch_picture.get_fetcher')
    def test_fetch_picture_invalid_date(self, mock_get_fetcher):
        """Test that invalid date format is handled"""
        # Mock the fetcher
        mock_fetcher = MagicMock()
        mock_get_fetcher.return_value = mock_fetcher
        
        # Run command with invalid date
        out = StringIO()
        call_command('fetch_picture', source='apod', date='invalid-date', stdout=out, stderr=out)
        
        # Should not create any picture
        count = PictureOfTheDay.objects.count()
        self.assertEqual(count, 0)
        
        # Output should contain error message
        output = out.getvalue()
        self.assertIn('Invalid date format', output)
    
    @patch('pictures.management.commands.fetch_picture.get_fetcher')
    @patch('pictures.management.commands.fetch_picture.ImageProcessor')
    def test_fetch_picture_get_metadata(self, mock_image_processor, mock_get_fetcher):
        """Test that image metadata is retrieved"""
        # Mock the fetcher
        mock_fetcher = MagicMock()
        mock_get_fetcher.return_value = mock_fetcher
        
        today = date.today()
        mock_fetcher.fetch.return_value = {
            'date': today.strftime('%Y-%m-%d'),
            'title': 'Test Picture',
            'explanation': 'Test explanation',
            'image_url': 'https://example.com/image.jpg',
            'media_type': 'image'
        }
        
        # Mock image processor
        mock_processor_instance = MagicMock()
        mock_image_processor.return_value = mock_processor_instance
        mock_processor_instance.get_image_metadata.return_value = (1920, 1080, 1024000)
        
        # Run command
        out = StringIO()
        call_command('fetch_picture', source='apod', stdout=out, stderr=out)
        
        # Verify metadata was set
        picture = PictureOfTheDay.objects.get(source=PictureSource.APOD, date=today)
        self.assertEqual(picture.image_width, 1920)
        self.assertEqual(picture.image_height, 1080)
        self.assertEqual(picture.image_size_bytes, 1024000)
    
    @patch('pictures.management.commands.fetch_picture.get_fetcher')
    def test_fetch_picture_all_sources(self, mock_get_fetcher):
        """Test fetching from different sources"""
        sources = ['apod', 'wikipedia', 'bing']
        today = date.today()
        
        for source in sources:
            # Mock the fetcher
            mock_fetcher = MagicMock()
            mock_get_fetcher.return_value = mock_fetcher
            mock_fetcher.fetch.return_value = {
                'date': today.strftime('%Y-%m-%d'),
                'title': f'{source} Picture',
                'explanation': 'Test explanation',
                'image_url': 'https://example.com/image.jpg',
                'media_type': 'image'
            }
            
            # Run command
            out = StringIO()
            call_command('fetch_picture', source=source, stdout=out, stderr=out)
            
            # Verify picture was created
            picture = PictureOfTheDay.objects.get(source=source, date=today)
            self.assertEqual(picture.title, f'{source} Picture')

