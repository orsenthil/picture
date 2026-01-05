from django.contrib import admin
from .models import PictureOfTheDay, SourceConfiguration


@admin.register(PictureOfTheDay)
class PictureOfTheDayAdmin(admin.ModelAdmin):
    list_display = ['source', 'date', 'title', 'is_processed', 'image_resolution', 'image_size_mb', 'created_at']
    list_filter = ['source', 'is_processed', 'media_type', 'date']
    search_fields = ['title', 'original_explanation']
    readonly_fields = ['created_at', 'updated_at', 'display_explanation', 'display_image_url', 'image_size_mb', 'image_resolution']
    date_hierarchy = 'date'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('source', 'date', 'title', 'media_type')
        }),
        ('Content', {
            'fields': ('original_explanation', 'simplified_explanation', 'processed_explanation', 'display_explanation')
        }),
        ('Images', {
            'fields': ('image_url', 'hd_image_url', 'thumbnail_url', 'local_image_path', 
                      'image_width', 'image_height', 'image_size_bytes', 'image_size_mb', 'image_resolution', 'display_image_url')
        }),
        ('Metadata', {
            'fields': ('copyright', 'source_url')
        }),
        ('Processing', {
            'fields': ('is_processed', 'processing_error')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(SourceConfiguration)
class SourceConfigurationAdmin(admin.ModelAdmin):
    list_display = ['source', 'is_enabled', 'label', 'updated_at']
    list_filter = ['is_enabled', 'source']
    search_fields = ['source', 'display_name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Source Information', {
            'fields': ('source', 'is_enabled', 'display_name', 'description')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    actions = ['enable_sources', 'disable_sources']
    
    def enable_sources(self, request, queryset):
        """Enable selected sources"""
        queryset.update(is_enabled=True)
        self.message_user(request, f"{queryset.count()} source(s) enabled.")
    enable_sources.short_description = "Enable selected sources"
    
    def disable_sources(self, request, queryset):
        """Disable selected sources"""
        queryset.update(is_enabled=False)
        self.message_user(request, f"{queryset.count()} source(s) disabled.")
    disable_sources.short_description = "Disable selected sources"


