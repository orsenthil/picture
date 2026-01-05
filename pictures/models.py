from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone


class PictureSource(models.TextChoices):
    """Enum for different picture sources"""
    APOD = 'apod', 'Astronomy Picture of the Day (NASA)'
    WIKIPEDIA = 'wikipedia', 'Wikipedia Picture of the Day'
    BING = 'bing', 'Bing Picture of the Day'


class SourceConfiguration(models.Model):
    """Configuration for picture sources - enables/disables sources dynamically"""
    
    source = models.CharField(
        max_length=50,
        choices=PictureSource.choices,
        unique=True,
        db_index=True,
        help_text="Picture source identifier"
    )
    is_enabled = models.BooleanField(
        default=True,
        help_text="Whether this source is currently enabled and available to users"
    )
    display_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Custom display name (optional, defaults to source choice label)"
    )
    description = models.TextField(
        blank=True,
        null=True,
        help_text="Optional description of the source"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Source Configuration'
        verbose_name_plural = 'Source Configurations'
        ordering = ['source']
    
    def __str__(self):
        status = "Enabled" if self.is_enabled else "Disabled"
        return f"{self.get_source_display()} - {status}"
    
    @property
    def label(self):
        """Return display name or default label"""
        return self.display_name or self.get_source_display()
    
    @classmethod
    def get_enabled_sources(cls):
        """Get list of enabled source values"""
        return list(cls.objects.filter(is_enabled=True).values_list('source', flat=True))
    
    @classmethod
    def is_source_enabled(cls, source):
        """Check if a specific source is enabled"""
        try:
            config = cls.objects.get(source=source)
            return config.is_enabled
        except cls.DoesNotExist:
            # If no configuration exists, default to enabled for backward compatibility
            return True


class PictureOfTheDay(models.Model):
    """Base model for Picture of the Day from various sources"""
    
    # Source identification
    source = models.CharField(
        max_length=50,
        choices=PictureSource.choices,
        db_index=True,
        help_text="Source of the picture"
    )
    date = models.DateField(db_index=True)
    
    # Unique constraint: one picture per source per date
    class Meta:
        unique_together = [['source', 'date']]
        ordering = ['-date', 'source']
        indexes = [
            models.Index(fields=['-date', 'source']),
            models.Index(fields=['source', 'is_processed']),
        ]
        verbose_name = 'Picture of the Day'
        verbose_name_plural = 'Pictures of the Day'
    
    # Basic information
    title = models.CharField(max_length=255)
    original_explanation = models.TextField()
    media_type = models.CharField(max_length=20, default='image')
    
    # Image URLs
    image_url = models.URLField(max_length=500)
    hd_image_url = models.URLField(max_length=500, blank=True, null=True)
    thumbnail_url = models.URLField(max_length=500, blank=True, null=True)
    
    # Local storage
    local_image_path = models.CharField(max_length=500, blank=True, null=True)
    image_width = models.PositiveIntegerField(blank=True, null=True, validators=[MinValueValidator(1)])
    image_height = models.PositiveIntegerField(blank=True, null=True, validators=[MinValueValidator(1)])
    image_size_bytes = models.BigIntegerField(blank=True, null=True, validators=[MinValueValidator(0)])
    
    # Processed content
    simplified_explanation = models.TextField(blank=True, null=True)
    processed_explanation = models.TextField(
        blank=True, 
        null=True,
        help_text="Explanation with Wikipedia links embedded"
    )
    
    # Metadata
    copyright = models.CharField(max_length=255, blank=True, null=True)
    source_url = models.URLField(max_length=500, blank=True, null=True, help_text="Original source page URL")
    
    # Processing status
    is_processed = models.BooleanField(default=False)
    processing_error = models.TextField(blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.get_source_display()} - {self.date} - {self.title}"
    
    @property
    def display_explanation(self):
        """Return processed explanation if available, otherwise simplified, otherwise original"""
        return (
            self.processed_explanation or 
            self.simplified_explanation or 
            self.original_explanation
        )
    
    @property
    def display_image_url(self):
        """Return local path if available, otherwise HD URL, otherwise regular URL"""
        return self.local_image_path or self.hd_image_url or self.image_url
    
    @property
    def image_size_mb(self):
        """Return image size in megabytes"""
        if self.image_size_bytes:
            return round(self.image_size_bytes / (1024 * 1024), 2)
        return None
    
    @property
    def image_resolution(self):
        """Return image resolution as string"""
        if self.image_width and self.image_height:
            return f"{self.image_width}x{self.image_height}"
        return None

