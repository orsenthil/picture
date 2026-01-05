"""
Tests for the cleanup_old_pictures management command
"""
from django.test import TestCase
from django.core.management import call_command
from django.utils import timezone
from datetime import date, timedelta
from io import StringIO
from pictures.models import PictureOfTheDay, PictureSource


class CleanupOldPicturesCommandTest(TestCase):
    """Test cases for cleanup_old_pictures management command"""
    
    def setUp(self):
        """Set up test data"""
        # Create pictures with various dates
        today = timezone.now().date()
        
        # Recent pictures (within last 90 days)
        for i in range(5):
            PictureOfTheDay.objects.create(
                source=PictureSource.APOD,
                date=today - timedelta(days=i),
                title=f'Recent APOD {i}',
                original_explanation='Test explanation',
                image_url='https://example.com/image.jpg'
            )
        
        # Old pictures (older than 90 days)
        for i in range(10):
            PictureOfTheDay.objects.create(
                source=PictureSource.APOD,
                date=today - timedelta(days=95 + i),
                title=f'Old APOD {i}',
                original_explanation='Test explanation',
                image_url='https://example.com/image.jpg'
            )
        
        # Wikipedia pictures
        for i in range(3):
            PictureOfTheDay.objects.create(
                source=PictureSource.WIKIPEDIA,
                date=today - timedelta(days=i),
                title=f'Recent Wikipedia {i}',
                original_explanation='Test explanation',
                image_url='https://example.com/image.jpg'
            )
        
        # Old Wikipedia pictures
        for i in range(5):
            PictureOfTheDay.objects.create(
                source=PictureSource.WIKIPEDIA,
                date=today - timedelta(days=95 + i),
                title=f'Old Wikipedia {i}',
                original_explanation='Test explanation',
                image_url='https://example.com/image.jpg'
            )
    
    def test_cleanup_removes_old_pictures(self):
        """Test that old pictures are removed"""
        # Count before cleanup
        apod_count_before = PictureOfTheDay.objects.filter(source=PictureSource.APOD).count()
        self.assertEqual(apod_count_before, 15)  # 5 recent + 10 old
        
        # Run cleanup with default settings (90 days, keep 10)
        call_command('cleanup_old_pictures', days=90, keep_min=10)
        
        # Count after cleanup
        apod_count_after = PictureOfTheDay.objects.filter(source=PictureSource.APOD).count()
        # Should keep 10 (5 recent + 5 old to meet minimum)
        self.assertEqual(apod_count_after, 10)
        
        # Verify recent pictures are still there
        today = timezone.now().date()
        recent_count = PictureOfTheDay.objects.filter(
            source=PictureSource.APOD,
            date__gte=today - timedelta(days=90)
        ).count()
        self.assertEqual(recent_count, 5)
    
    def test_cleanup_respects_keep_min(self):
        """Test that minimum number of pictures is kept"""
        # Run cleanup with keep_min=15
        call_command('cleanup_old_pictures', days=90, keep_min=15)
        
        # Should keep at least 15 APOD pictures
        apod_count = PictureOfTheDay.objects.filter(source=PictureSource.APOD).count()
        self.assertGreaterEqual(apod_count, 15)
    
    def test_cleanup_dry_run(self):
        """Test dry run doesn't actually delete"""
        count_before = PictureOfTheDay.objects.count()
        
        # Run dry run
        out = StringIO()
        call_command('cleanup_old_pictures', days=90, keep_min=10, dry_run=True, stdout=out)
        
        # Count should be unchanged
        count_after = PictureOfTheDay.objects.count()
        self.assertEqual(count_before, count_after)
        
        # Output should contain "DRY RUN"
        output = out.getvalue()
        self.assertIn('DRY RUN', output)
        self.assertIn('Would delete', output)
    
    def test_cleanup_source_filter(self):
        """Test cleanup with source filter"""
        # Clean up only APOD
        call_command('cleanup_old_pictures', days=90, keep_min=10, source='apod')
        
        # APOD should be cleaned
        apod_count = PictureOfTheDay.objects.filter(source=PictureSource.APOD).count()
        self.assertLessEqual(apod_count, 15)
        
        # Wikipedia should be unchanged
        wikipedia_count = PictureOfTheDay.objects.filter(source=PictureSource.WIKIPEDIA).count()
        self.assertEqual(wikipedia_count, 8)  # 3 recent + 5 old
    
    def test_cleanup_all_sources(self):
        """Test cleanup processes all sources"""
        # Run cleanup
        call_command('cleanup_old_pictures', days=90, keep_min=10)
        
        # Both sources should be processed
        apod_count = PictureOfTheDay.objects.filter(source=PictureSource.APOD).count()
        wikipedia_count = PictureOfTheDay.objects.filter(source=PictureSource.WIKIPEDIA).count()
        
        # APOD: 15 total, should keep 10
        self.assertEqual(apod_count, 10)
        
        # Wikipedia: 8 total, but only 3 recent, so should keep 10 (all of them)
        self.assertEqual(wikipedia_count, 8)
    
    def test_cleanup_no_old_pictures(self):
        """Test cleanup when no old pictures exist"""
        # Delete all old pictures first
        today = timezone.now().date()
        PictureOfTheDay.objects.filter(date__lt=today - timedelta(days=90)).delete()
        
        count_before = PictureOfTheDay.objects.count()
        
        # Run cleanup
        out = StringIO()
        call_command('cleanup_old_pictures', days=90, keep_min=10, stdout=out)
        
        # Count should be unchanged
        count_after = PictureOfTheDay.objects.count()
        self.assertEqual(count_before, count_after)
        
        # Output should indicate no cleanup needed
        output = out.getvalue()
        self.assertIn('No cleanup needed', output)
    
    def test_cleanup_custom_days(self):
        """Test cleanup with custom retention period"""
        # Use 5 days retention
        call_command('cleanup_old_pictures', days=5, keep_min=10)
        
        # Should keep more pictures since cutoff is more recent
        apod_count = PictureOfTheDay.objects.filter(source=PictureSource.APOD).count()
        # With 5 days, only the most recent 5 are within retention, so we keep 10 minimum
        self.assertGreaterEqual(apod_count, 10)

