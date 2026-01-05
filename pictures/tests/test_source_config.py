"""
Unit tests for SourceConfiguration model and functionality
"""
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from datetime import date
from pictures.models import PictureOfTheDay, PictureSource, SourceConfiguration


class SourceConfigurationModelTest(TestCase):
    """Test cases for SourceConfiguration model"""
    
    def setUp(self):
        """Set up test data"""
        self.apod_config = SourceConfiguration.objects.create(
            source=PictureSource.APOD,
            is_enabled=True
        )
        self.wiki_config = SourceConfiguration.objects.create(
            source=PictureSource.WIKIPEDIA,
            is_enabled=True
        )
        self.bing_config = SourceConfiguration.objects.create(
            source=PictureSource.BING,
            is_enabled=False  # Disabled
        )
    
    def test_source_configuration_str(self):
        """Test string representation"""
        self.assertIn('Enabled', str(self.apod_config))
        self.assertIn('Disabled', str(self.bing_config))
    
    def test_label_property(self):
        """Test label property returns display_name or default"""
        self.assertEqual(self.apod_config.label, 'Astronomy Picture of the Day (NASA)')
        
        self.apod_config.display_name = 'Custom APOD Name'
        self.apod_config.save()
        self.assertEqual(self.apod_config.label, 'Custom APOD Name')
    
    def test_get_enabled_sources(self):
        """Test get_enabled_sources class method"""
        enabled = SourceConfiguration.get_enabled_sources()
        self.assertIn('apod', enabled)
        self.assertIn('wikipedia', enabled)
        self.assertNotIn('bing', enabled)
    
    def test_is_source_enabled(self):
        """Test is_source_enabled class method"""
        self.assertTrue(SourceConfiguration.is_source_enabled('apod'))
        self.assertTrue(SourceConfiguration.is_source_enabled('wikipedia'))
        self.assertFalse(SourceConfiguration.is_source_enabled('bing'))
        
        # Test non-existent source (should default to enabled for backward compatibility)
        self.assertTrue(SourceConfiguration.is_source_enabled('nonexistent'))


class SourceConfigurationAPITest(TestCase):
    """Test cases for SourceConfiguration in API views"""
    
    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        
        # Create source configurations
        self.apod_config = SourceConfiguration.objects.create(
            source=PictureSource.APOD,
            is_enabled=True
        )
        self.wiki_config = SourceConfiguration.objects.create(
            source=PictureSource.WIKIPEDIA,
            is_enabled=True
        )
        self.bing_config = SourceConfiguration.objects.create(
            source=PictureSource.BING,
            is_enabled=False  # Disabled
        )
        
        # Create test pictures
        self.apod_picture = PictureOfTheDay.objects.create(
            source=PictureSource.APOD,
            date=date.today(),
            title='Today APOD',
            original_explanation='Today APOD explanation',
            image_url='https://example.com/apod.jpg',
            media_type='image'
        )
        
        self.bing_picture = PictureOfTheDay.objects.create(
            source=PictureSource.BING,
            date=date.today(),
            title='Today Bing',
            original_explanation='Today Bing explanation',
            image_url='https://example.com/bing.jpg',
            media_type='image'
        )
    
    def test_sources_endpoint_returns_only_enabled(self):
        """Test that sources endpoint returns only enabled sources"""
        url = reverse('pictures-sources')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        sources = response.json()
        
        # Should only return enabled sources
        source_values = [s['value'] for s in sources]
        self.assertIn('apod', source_values)
        self.assertIn('wikipedia', source_values)
        self.assertNotIn('bing', source_values)
        
        # Check that enabled flag is present
        for source in sources:
            self.assertTrue(source['enabled'])
    
    def test_today_endpoint_rejects_disabled_source(self):
        """Test that today endpoint rejects disabled sources"""
        url = reverse('pictures-today', kwargs={'source': 'bing'})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('disabled', response.json()['error'].lower())
    
    def test_today_endpoint_accepts_enabled_source(self):
        """Test that today endpoint accepts enabled sources"""
        url = reverse('pictures-today', kwargs={'source': 'apod'})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['source'], 'apod')
    
    def test_by_date_endpoint_rejects_disabled_source(self):
        """Test that by_date endpoint rejects disabled sources"""
        url = reverse('pictures-by-date', kwargs={
            'date_str': date.today().isoformat(),
            'source': 'bing'
        })
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('disabled', response.json()['error'].lower())
    
    def test_latest_endpoint_rejects_disabled_source(self):
        """Test that latest endpoint rejects disabled sources"""
        url = reverse('pictures-latest', kwargs={'source': 'bing'})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('disabled', response.json()['error'].lower())
    
    def test_list_by_source_endpoint_rejects_disabled_source(self):
        """Test that list_by_source endpoint rejects disabled sources"""
        url = reverse('pictures-list-by-source', kwargs={'source': 'bing'})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('disabled', response.json()['error'].lower())
    
    def test_sources_endpoint_backward_compatibility(self):
        """Test that sources endpoint works when no configurations exist"""
        # Delete all configurations
        SourceConfiguration.objects.all().delete()
        
        url = reverse('pictures-sources')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        sources = response.json()
        
        # Should return all sources as enabled (backward compatibility)
        source_values = [s['value'] for s in sources]
        self.assertIn('apod', source_values)
        self.assertIn('wikipedia', source_values)
        self.assertIn('bing', source_values)
        
        # All should be marked as enabled
        for source in sources:
            self.assertTrue(source['enabled'])

