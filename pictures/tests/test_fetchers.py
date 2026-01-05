"""
Unit tests for picture fetchers
"""
from django.test import TestCase
from unittest.mock import patch, MagicMock
from datetime import date, timedelta
from pictures.fetchers import (
    APODFetcher,
    WikipediaPODFetcher,
    BingPODFetcher,
    get_fetcher
)


class APODFetcherTest(TestCase):
    """Test cases for APODFetcher"""
    
    def setUp(self):
        """Set up test data"""
        self.fetcher = APODFetcher()
        self.test_date = date(2024, 1, 15)
    
    def test_source_name(self):
        """Test that source_name is set correctly"""
        self.assertEqual(self.fetcher.source_name, 'apod')
    
    @patch('pictures.fetchers.requests.get')
    @patch('pictures.fetchers.settings')
    def test_fetch_success(self, mock_settings, mock_get):
        """Test successful fetch from NASA API"""
        mock_settings.NASA_API_KEY = 'test_key'
        
        # Mock API response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'title': 'Test APOD',
            'date': '2024-01-15',
            'explanation': 'Test explanation',
            'url': 'https://apod.nasa.gov/image.jpg',
            'hdurl': 'https://apod.nasa.gov/image_hd.jpg',
            'media_type': 'image',
            'copyright': 'Test Copyright'
        }
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response
        
        result = self.fetcher.fetch(self.test_date)
        
        self.assertEqual(result['title'], 'Test APOD')
        self.assertEqual(result['date'], '2024-01-15')
        self.assertEqual(result['explanation'], 'Test explanation')
        self.assertEqual(result['image_url'], 'https://apod.nasa.gov/image.jpg')
        self.assertEqual(result['hd_image_url'], 'https://apod.nasa.gov/image_hd.jpg')
        self.assertEqual(result['media_type'], 'image')
        self.assertEqual(result['copyright'], 'Test Copyright')
        self.assertIn('source_url', result)
        self.assertIn('ap240115', result['source_url'])
        
        # Verify API was called correctly
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        self.assertEqual(call_args[0][0], 'https://api.nasa.gov/planetary/apod')
        self.assertIn('api_key', call_args[1]['params'])
        self.assertEqual(call_args[1]['params']['date'], '2024-01-15')
    
    def test_get_source_url(self):
        """Test get_source_url method"""
        url = self.fetcher.get_source_url(self.test_date)
        self.assertEqual(url, 'https://apod.nasa.gov/apod/ap240115.html')
    
    @patch('pictures.fetchers.requests.get')
    @patch('pictures.fetchers.settings')
    def test_fetch_without_hdurl(self, mock_settings, mock_get):
        """Test fetch when hdurl is not available"""
        mock_settings.NASA_API_KEY = 'test_key'
        
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'title': 'Test APOD',
            'date': '2024-01-15',
            'explanation': 'Test explanation',
            'url': 'https://apod.nasa.gov/image.jpg',
            'media_type': 'image'
        }
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response
        
        result = self.fetcher.fetch(self.test_date)
        
        self.assertIsNone(result.get('hd_image_url'))


class WikipediaPODFetcherTest(TestCase):
    """Test cases for WikipediaPODFetcher"""
    
    def setUp(self):
        """Set up test data"""
        self.fetcher = WikipediaPODFetcher()
        self.test_date = date(2024, 1, 15)
    
    def test_source_name(self):
        """Test that source_name is set correctly"""
        self.assertEqual(self.fetcher.source_name, 'wikipedia')
    
    @patch('pictures.fetchers.requests.get')
    def test_fetch_success(self, mock_get):
        """Test successful fetch from Wikipedia"""
        # Mock first API call (get images)
        mock_response1 = MagicMock()
        mock_response1.json.return_value = {
            'query': {
                'pages': [{
                    'images': [{
                        'title': 'File:Test_image.jpg'
                    }]
                }]
            }
        }
        mock_response1.raise_for_status = MagicMock()
        
        # Mock second API call (get image URL)
        mock_response2 = MagicMock()
        mock_response2.json.return_value = {
            'query': {
                'pages': [{
                    'imageinfo': [{
                        'url': 'https://upload.wikimedia.org/test_image.jpg'
                    }]
                }]
            }
        }
        mock_response2.raise_for_status = MagicMock()
        
        # Mock third API call (get description)
        mock_response3 = MagicMock()
        mock_response3.json.return_value = {
            'query': {
                'pages': [{
                    'revisions': [{
                        'slots': {
                            'main': {
                                'content': '|title=[[Test Title]]|caption=Test caption'
                            }
                        }
                    }]
                }]
            }
        }
        mock_response3.raise_for_status = MagicMock()
        
        mock_get.side_effect = [mock_response1, mock_response2, mock_response3]
        
        result = self.fetcher.fetch(self.test_date)
        
        self.assertEqual(result['date'], '2024-01-15')
        self.assertEqual(result['image_url'], 'https://upload.wikimedia.org/test_image.jpg')
        self.assertEqual(result['media_type'], 'image')
        self.assertIn('source_url', result)
        self.assertIn('wikipedia.org', result['source_url'])
    
    def test_get_source_url(self):
        """Test get_source_url method"""
        url = self.fetcher.get_source_url(self.test_date)
        expected = 'https://en.wikipedia.org/wiki/Wikipedia:Picture_of_the_day/January_15,_2024'
        self.assertEqual(url, expected)
    
    def test_clean_wikitext(self):
        """Test wikitext cleaning"""
        text = "'''Bold''' and ''italic'' [[Link|text]] [[AnotherLink]]"
        cleaned = self.fetcher._clean_wikitext(text)
        self.assertNotIn("'''", cleaned)
        self.assertNotIn("''", cleaned)
        self.assertNotIn("[[", cleaned)
        self.assertNotIn("]]", cleaned)
    
    def test_clean_filename_title(self):
        """Test filename to title conversion"""
        filename = "File:Test_Image_2024-01-15.jpg"
        title = self.fetcher._clean_filename_title(filename)
        self.assertNotIn("File:", title)
        self.assertNotIn(".jpg", title)
        self.assertNotIn("2024-01-15", title)
        self.assertIn("Test Image", title)


class BingPODFetcherTest(TestCase):
    """Test cases for BingPODFetcher"""
    
    def setUp(self):
        """Set up test data"""
        self.fetcher = BingPODFetcher()
        self.test_date = date(2024, 1, 15)
    
    def test_source_name(self):
        """Test that source_name is set correctly"""
        self.assertEqual(self.fetcher.source_name, 'bing')
    
    @patch('pictures.fetchers.requests.get')
    @patch('pictures.fetchers.date')
    def test_fetch_success(self, mock_date, mock_get):
        """Test successful fetch from Bing"""
        # Mock today's date
        mock_date.today.return_value = date(2024, 1, 15)
        mock_date_class = MagicMock()
        mock_date_class.today.return_value = date(2024, 1, 15)
        mock_date.side_effect = lambda *args, **kwargs: date(*args, **kwargs) if args else mock_date_class
        
        # Mock API response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'images': [{
                'startdate': '20240115',
                'url': '/th?id=OHR.TestImage_1920x1080.jpg',
                'title': 'Test Bing Image',
                'copyright': 'Test Copyright'
            }]
        }
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response
        
        result = self.fetcher.fetch(self.test_date)
        
        self.assertEqual(result['title'], 'Test Bing Image')
        self.assertEqual(result['date'], '2024-01-15')
        self.assertEqual(result['explanation'], 'Test Copyright')
        self.assertIn('bing.com', result['image_url'])
        self.assertEqual(result['media_type'], 'image')
        self.assertEqual(result['copyright'], 'Test Copyright')
        self.assertEqual(result['source_url'], 'https://www.bing.com')
    
    def test_get_source_url(self):
        """Test get_source_url method"""
        url = self.fetcher.get_source_url(self.test_date)
        self.assertEqual(url, 'https://www.bing.com')
    
    @patch('pictures.fetchers.requests.get')
    @patch('pictures.fetchers.date')
    def test_fetch_all_available(self, mock_date, mock_get):
        """Test fetch_all_available method"""
        mock_date_class = MagicMock()
        mock_date_class.today.return_value = date(2024, 1, 15)
        
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'images': [
                {
                    'startdate': '20240115',
                    'url': '/th?id=OHR.Test1_1920x1080.jpg',
                    'title': 'Test 1',
                    'copyright': 'Copyright 1'
                },
                {
                    'startdate': '20240114',
                    'url': '/th?id=OHR.Test2_1920x1080.jpg',
                    'title': 'Test 2',
                    'copyright': 'Copyright 2'
                }
            ]
        }
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response
        
        results = self.fetcher.fetch_all_available(max_days=8)
        
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]['title'], 'Test 1')
        self.assertEqual(results[1]['title'], 'Test 2')
    
    @patch('pictures.fetchers.requests.get')
    def test_fetch_future_date_error(self, mock_get):
        """Test that fetching future dates raises an error"""
        from datetime import date as date_class
        
        # Use a future date relative to today
        future_date = date_class.today() + timedelta(days=1)
        
        with self.assertRaises(ValueError) as context:
            self.fetcher.fetch(future_date)
        
        self.assertIn('future', str(context.exception).lower())


class GetFetcherTest(TestCase):
    """Test cases for get_fetcher factory function"""
    
    def test_get_apod_fetcher(self):
        """Test getting APOD fetcher"""
        fetcher = get_fetcher('apod')
        self.assertIsInstance(fetcher, APODFetcher)
    
    def test_get_wikipedia_fetcher(self):
        """Test getting Wikipedia fetcher"""
        fetcher = get_fetcher('wikipedia')
        self.assertIsInstance(fetcher, WikipediaPODFetcher)
    
    def test_get_bing_fetcher(self):
        """Test getting Bing fetcher"""
        fetcher = get_fetcher('bing')
        self.assertIsInstance(fetcher, BingPODFetcher)
    
    def test_get_invalid_fetcher(self):
        """Test getting invalid fetcher raises error"""
        with self.assertRaises(ValueError) as context:
            get_fetcher('invalid')
        
        self.assertIn('Unknown source', str(context.exception))

