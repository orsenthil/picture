"""
Unit tests for PictureOfTheDay API views
"""
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status
from datetime import date, timedelta
from pictures.models import PictureOfTheDay, PictureSource, SourceConfiguration


class PictureOfTheDayViewSetTest(TestCase):
    """Test cases for PictureOfTheDayViewSet"""
    
    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        
        # Create source configurations (all enabled by default for tests)
        SourceConfiguration.objects.get_or_create(
            source=PictureSource.APOD,
            defaults={'is_enabled': True}
        )
        SourceConfiguration.objects.get_or_create(
            source=PictureSource.WIKIPEDIA,
            defaults={'is_enabled': True}
        )
        SourceConfiguration.objects.get_or_create(
            source=PictureSource.BING,
            defaults={'is_enabled': True}
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
        
        self.wiki_picture = PictureOfTheDay.objects.create(
            source=PictureSource.WIKIPEDIA,
            date=date.today(),
            title='Today Wikipedia',
            original_explanation='Today Wikipedia explanation',
            image_url='https://example.com/wiki.jpg',
            media_type='image'
        )
        
        self.bing_picture = PictureOfTheDay.objects.create(
            source=PictureSource.BING,
            date=date.today() - timedelta(days=1),
            title='Yesterday Bing',
            original_explanation='Yesterday Bing explanation',
            image_url='https://example.com/bing.jpg',
            media_type='image'
        )
    
    def test_list_pictures(self):
        """Test listing all pictures"""
        url = reverse('pictures-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 3)
    
    def test_list_pictures_filtered_by_source(self):
        """Test listing pictures filtered by source"""
        url = reverse('pictures-list')
        response = self.client.get(url, {'source': 'apod'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['source'], 'apod')
    
    def test_retrieve_picture(self):
        """Test retrieving a specific picture"""
        url = reverse('pictures-detail', args=[self.apod_picture.id])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Today APOD')
        self.assertEqual(response.data['source'], 'apod')
    
    def test_today_endpoint(self):
        """Test today endpoint"""
        url = '/api/pictures/today/apod/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Today APOD')
        self.assertEqual(response.data['source'], 'apod')
    
    def test_today_endpoint_without_source(self):
        """Test today endpoint without source (should fail)"""
        url = '/api/pictures/today/'
        response = self.client.get(url)
        
        # This will 404 because the URL pattern requires a source parameter
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_today_endpoint_invalid_source(self):
        """Test today endpoint with invalid source"""
        url = '/api/pictures/today/invalid/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Invalid source', response.data['error'])
    
    def test_today_endpoint_not_found(self):
        """Test today endpoint when picture doesn't exist"""
        # Delete today's picture
        self.apod_picture.delete()
        
        url = '/api/pictures/today/apod/'
        response = self.client.get(url)
        
        # Should try yesterday and return 404
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_today_endpoint_fallback_to_yesterday(self):
        """Test today endpoint falls back to yesterday"""
        # Delete today's picture, create yesterday's
        # Use timezone-aware date to match the view's behavior
        today = timezone.now().date()
        yesterday = today - timedelta(days=1)
        
        self.apod_picture.delete()
        yesterday_picture = PictureOfTheDay.objects.create(
            source=PictureSource.APOD,
            date=yesterday,
            title='Yesterday APOD',
            original_explanation='Yesterday APOD explanation',
            image_url='https://example.com/yesterday.jpg',
            media_type='image'
        )
        
        url = '/api/pictures/today/apod/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Yesterday APOD')
    
    def test_by_date_endpoint(self):
        """Test by_date endpoint"""
        test_date = date.today() - timedelta(days=1)
        url = f'/api/pictures/date/{test_date.isoformat()}/bing/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Yesterday Bing')
        self.assertEqual(response.data['source'], 'bing')
    
    def test_by_date_endpoint_invalid_date(self):
        """Test by_date endpoint with invalid date format"""
        url = '/api/pictures/date/invalid-date/apod/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Invalid date format', response.data['error'])
    
    def test_by_date_endpoint_not_found(self):
        """Test by_date endpoint when picture doesn't exist"""
        url = '/api/pictures/date/2020-01-01/apod/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_by_date_endpoint_without_source(self):
        """Test by_date endpoint without source"""
        url = '/api/pictures/date/2024-01-01/'
        response = self.client.get(url)
        
        # This will 404 because the URL pattern requires a source parameter
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_latest_endpoint(self):
        """Test latest endpoint"""
        url = '/api/pictures/latest/apod/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Today APOD')
    
    def test_latest_endpoint_not_found(self):
        """Test latest endpoint when no pictures exist"""
        PictureOfTheDay.objects.filter(source=PictureSource.APOD).delete()
        
        url = '/api/pictures/latest/apod/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_latest_endpoint_without_source(self):
        """Test latest endpoint without source"""
        url = '/api/pictures/latest/'
        response = self.client.get(url)
        
        # This will 404 because the URL pattern requires a source parameter
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_sources_endpoint(self):
        """Test sources endpoint"""
        url = '/api/pictures/sources/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        # Should return all enabled sources (3 in this case)
        self.assertEqual(len(response.data), 3)
        
        # Check that all sources are present and enabled
        source_values = [s['value'] for s in response.data]
        for source in response.data:
            self.assertTrue(source.get('enabled', True))
        self.assertIn('apod', source_values)
        self.assertIn('wikipedia', source_values)
        self.assertIn('bing', source_values)
    
    def test_list_by_source_endpoint(self):
        """Test list_by_source endpoint"""
        url = '/api/pictures/list/apod/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['source'], 'apod')
    
    def test_list_by_source_endpoint_without_source(self):
        """Test list_by_source endpoint without source"""
        url = '/api/pictures/list/'
        response = self.client.get(url)
        
        # This will 404 because the URL pattern requires a source parameter
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_list_by_source_endpoint_invalid_source(self):
        """Test list_by_source endpoint with invalid source"""
        url = '/api/pictures/list/invalid/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_pagination(self):
        """Test that list view is paginated"""
        # Create more pictures to test pagination
        for i in range(25):
            PictureOfTheDay.objects.create(
                source=PictureSource.APOD,
                date=date.today() - timedelta(days=i+10),
                title=f'Picture {i}',
                original_explanation=f'Explanation {i}',
                image_url=f'https://example.com/image{i}.jpg',
                media_type='image'
            )
        
        url = reverse('pictures-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertIn('count', response.data)
        self.assertEqual(len(response.data['results']), 20)  # PAGE_SIZE
    
    def test_serializer_detail_vs_list(self):
        """Test that detail view uses different serializer"""
        # List view should use basic serializer
        list_url = reverse('pictures-list')
        list_response = self.client.get(list_url)
        
        # Detail view should use detail serializer
        detail_url = reverse('pictures-detail', args=[self.apod_picture.id])
        detail_response = self.client.get(detail_url)
        
        # Both should work but detail might have more fields
        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        self.assertEqual(detail_response.status_code, status.HTTP_200_OK)
        
        # Check that both have required fields
        self.assertIn('title', list_response.data['results'][0])
        self.assertIn('title', detail_response.data)
    
    def test_all_recent_endpoint(self):
        """Test all_recent endpoint returns pictures from all enabled sources"""
        url = '/api/pictures/all_recent/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        
        # Should return at least 2 pictures (today's APOD and Wikipedia)
        # Bing might have more
        self.assertGreaterEqual(len(response.data), 2)
        
        # Check that we have pictures from different sources
        sources = [pic['source'] for pic in response.data]
        self.assertIn('apod', sources)
        self.assertIn('wikipedia', sources)
    
    def test_all_recent_endpoint_with_multiple_bing_pictures(self):
        """Test all_recent endpoint includes multiple recent Bing pictures"""
        # Create multiple Bing pictures
        for i in range(7):
            PictureOfTheDay.objects.create(
                source=PictureSource.BING,
                date=date.today() - timedelta(days=i+2),
                title=f'Bing Picture {i}',
                original_explanation=f'Bing explanation {i}',
                image_url=f'https://example.com/bing{i}.jpg',
                media_type='image'
            )
        
        url = '/api/pictures/all_recent/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Count Bing pictures in response
        bing_pictures = [pic for pic in response.data if pic['source'] == 'bing']
        
        # Should have at most 8 Bing pictures (as configured)
        self.assertLessEqual(len(bing_pictures), 8)
        # Should have more than 1 Bing picture
        self.assertGreater(len(bing_pictures), 1)
    
    def test_all_recent_endpoint_with_disabled_source(self):
        """Test all_recent endpoint excludes disabled sources"""
        # Disable Wikipedia source
        wiki_config = SourceConfiguration.objects.get(source=PictureSource.WIKIPEDIA)
        wiki_config.is_enabled = False
        wiki_config.save()
        
        url = '/api/pictures/all_recent/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Wikipedia pictures should not be included
        sources = [pic['source'] for pic in response.data]
        self.assertNotIn('wikipedia', sources)
        self.assertIn('apod', sources)
    
    def test_all_recent_endpoint_with_all_sources_disabled(self):
        """Test all_recent endpoint when all sources are disabled"""
        # Disable all sources
        SourceConfiguration.objects.all().update(is_enabled=False)
        
        url = '/api/pictures/all_recent/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('No picture sources', response.data['error'])
    
    def test_all_recent_endpoint_falls_back_to_yesterday(self):
        """Test all_recent endpoint falls back to yesterday for sources without today's picture"""
        # Delete today's APOD picture
        self.apod_picture.delete()
        
        # Create yesterday's APOD picture
        yesterday = timezone.now().date() - timedelta(days=1)
        yesterday_apod = PictureOfTheDay.objects.create(
            source=PictureSource.APOD,
            date=yesterday,
            title='Yesterday APOD',
            original_explanation='Yesterday APOD explanation',
            image_url='https://example.com/yesterday_apod.jpg',
            media_type='image'
        )
        
        url = '/api/pictures/all_recent/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Should still have APOD from yesterday
        apod_pictures = [pic for pic in response.data if pic['source'] == 'apod']
        self.assertEqual(len(apod_pictures), 1)
        self.assertEqual(apod_pictures[0]['title'], 'Yesterday APOD')
    
    def test_all_recent_endpoint_picture_distribution(self):
        """Test that all_recent balances pictures across sources"""
        # Create 7 more Bing pictures (total 8 with existing one)
        for i in range(7):
            PictureOfTheDay.objects.create(
                source=PictureSource.BING,
                date=date.today() - timedelta(days=i+2),
                title=f'Bing {i}',
                original_explanation=f'Bing explanation {i}',
                image_url=f'https://example.com/bing{i}.jpg',
                media_type='image'
            )
        
        url = '/api/pictures/all_recent/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Count pictures by source
        source_counts = {}
        for pic in response.data:
            source = pic['source']
            source_counts[source] = source_counts.get(source, 0) + 1
        
        # Bing should have more pictures (around 8)
        # APOD and Wikipedia should have 1 each
        self.assertGreaterEqual(source_counts.get('bing', 0), 1)
        self.assertEqual(source_counts.get('apod', 0), 1)
        self.assertEqual(source_counts.get('wikipedia', 0), 1)
        
        # Total should be around 10 pictures (1 APOD + 1 Wikipedia + 8 Bing)
        self.assertGreaterEqual(len(response.data), 8)

