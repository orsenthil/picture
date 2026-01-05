"""
Unit tests for PictureOfTheDay model
"""
from django.test import TestCase
from django.core.exceptions import ValidationError
from datetime import date
from pictures.models import PictureOfTheDay, PictureSource


class PictureOfTheDayModelTest(TestCase):
    """Test cases for PictureOfTheDay model"""
    
    def setUp(self):
        """Set up test data"""
        self.picture_data = {
            'source': PictureSource.APOD,
            'date': date(2024, 1, 15),
            'title': 'Test Picture',
            'original_explanation': 'Test explanation',
            'image_url': 'https://example.com/image.jpg',
            'media_type': 'image'
        }
    
    def test_create_picture(self):
        """Test creating a picture"""
        picture = PictureOfTheDay.objects.create(**self.picture_data)
        
        self.assertEqual(picture.source, PictureSource.APOD)
        self.assertEqual(picture.date, date(2024, 1, 15))
        self.assertEqual(picture.title, 'Test Picture')
        self.assertFalse(picture.is_processed)
    
    def test_str_representation(self):
        """Test string representation"""
        picture = PictureOfTheDay.objects.create(**self.picture_data)
        str_repr = str(picture)
        
        self.assertIn('Astronomy Picture of the Day', str_repr)
        self.assertIn('2024-01-15', str_repr)
        self.assertIn('Test Picture', str_repr)
    
    def test_unique_constraint(self):
        """Test that source+date combination is unique"""
        PictureOfTheDay.objects.create(**self.picture_data)
        
        # Try to create duplicate
        with self.assertRaises(Exception):  # IntegrityError
            PictureOfTheDay.objects.create(**self.picture_data)
    
    def test_display_explanation_property(self):
        """Test display_explanation property priority"""
        # Test with processed_explanation
        picture = PictureOfTheDay.objects.create(
            **self.picture_data,
            processed_explanation='Processed explanation'
        )
        self.assertEqual(picture.display_explanation, 'Processed explanation')
        
        # Test with simplified_explanation (no processed)
        picture2 = PictureOfTheDay.objects.create(
            **{**self.picture_data, 'date': date(2024, 1, 16)},
            simplified_explanation='Simplified explanation'
        )
        self.assertEqual(picture2.display_explanation, 'Simplified explanation')
        
        # Test with original_explanation only
        picture3 = PictureOfTheDay.objects.create(
            **{**self.picture_data, 'date': date(2024, 1, 17)}
        )
        self.assertEqual(picture3.display_explanation, 'Test explanation')
    
    def test_display_image_url_property(self):
        """Test display_image_url property priority"""
        # Test with local_image_path
        picture = PictureOfTheDay.objects.create(
            **self.picture_data,
            local_image_path='/local/path/image.jpg',
            hd_image_url='https://example.com/hd.jpg'
        )
        self.assertEqual(picture.display_image_url, '/local/path/image.jpg')
        
        # Test with hd_image_url (no local)
        picture2 = PictureOfTheDay.objects.create(
            **{**self.picture_data, 'date': date(2024, 1, 16)},
            hd_image_url='https://example.com/hd.jpg'
        )
        self.assertEqual(picture2.display_image_url, 'https://example.com/hd.jpg')
        
        # Test with image_url only
        picture3 = PictureOfTheDay.objects.create(
            **{**self.picture_data, 'date': date(2024, 1, 17)}
        )
        self.assertEqual(picture3.display_image_url, 'https://example.com/image.jpg')
    
    def test_image_size_mb_property(self):
        """Test image_size_mb property"""
        # Test with size
        picture = PictureOfTheDay.objects.create(
            **self.picture_data,
            image_size_bytes=2097152  # 2 MB
        )
        self.assertEqual(picture.image_size_mb, 2.0)
        
        # Test without size
        picture2 = PictureOfTheDay.objects.create(
            **{**self.picture_data, 'date': date(2024, 1, 16)}
        )
        self.assertIsNone(picture2.image_size_mb)
    
    def test_image_resolution_property(self):
        """Test image_resolution property"""
        # Test with dimensions
        picture = PictureOfTheDay.objects.create(
            **self.picture_data,
            image_width=1920,
            image_height=1080
        )
        self.assertEqual(picture.image_resolution, '1920x1080')
        
        # Test without dimensions
        picture2 = PictureOfTheDay.objects.create(
            **{**self.picture_data, 'date': date(2024, 1, 16)}
        )
        self.assertIsNone(picture2.image_resolution)
    
    def test_ordering(self):
        """Test default ordering"""
        PictureOfTheDay.objects.create(
            **{**self.picture_data, 'date': date(2024, 1, 10)}
        )
        PictureOfTheDay.objects.create(
            **{**self.picture_data, 'date': date(2024, 1, 15)}
        )
        PictureOfTheDay.objects.create(
            **{**self.picture_data, 'date': date(2024, 1, 20)}
        )
        
        pictures = list(PictureOfTheDay.objects.all())
        # Should be ordered by -date (newest first)
        self.assertEqual(pictures[0].date, date(2024, 1, 20))
        self.assertEqual(pictures[1].date, date(2024, 1, 15))
        self.assertEqual(pictures[2].date, date(2024, 1, 10))
    
    def test_multiple_sources_same_date(self):
        """Test that different sources can have same date"""
        PictureOfTheDay.objects.create(**self.picture_data)
        
        # Create with different source, same date
        picture2 = PictureOfTheDay.objects.create(
            source=PictureSource.WIKIPEDIA,
            date=date(2024, 1, 15),
            title='Wikipedia Picture',
            original_explanation='Wikipedia explanation',
            image_url='https://example.com/wikipedia.jpg',
            media_type='image'
        )
        
        self.assertEqual(PictureOfTheDay.objects.count(), 2)
        self.assertEqual(picture2.source, PictureSource.WIKIPEDIA)
    
    def test_is_processed_default(self):
        """Test that is_processed defaults to False"""
        picture = PictureOfTheDay.objects.create(**self.picture_data)
        self.assertFalse(picture.is_processed)
    
    def test_processing_error_field(self):
        """Test processing_error field"""
        picture = PictureOfTheDay.objects.create(
            **self.picture_data,
            processing_error='Test error message'
        )
        self.assertEqual(picture.processing_error, 'Test error message')
    
    def test_timestamps(self):
        """Test created_at and updated_at timestamps"""
        picture = PictureOfTheDay.objects.create(**self.picture_data)
        
        self.assertIsNotNone(picture.created_at)
        self.assertIsNotNone(picture.updated_at)
        
        # Update and check updated_at changes
        original_updated = picture.updated_at
        picture.title = 'Updated Title'
        picture.save()
        
        picture.refresh_from_db()
        self.assertGreater(picture.updated_at, original_updated)

