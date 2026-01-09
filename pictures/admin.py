from django.contrib import admin
from django.core.management import call_command
from io import StringIO
import logging
from .models import PictureOfTheDay, SourceConfiguration

logger = logging.getLogger(__name__)


@admin.register(PictureOfTheDay)
class PictureOfTheDayAdmin(admin.ModelAdmin):
    list_display = ['source', 'date', 'title', 'is_processed', 'image_resolution', 'image_size_mb', 'created_at']
    list_filter = ['source', 'is_processed', 'media_type', 'date']
    search_fields = ['title', 'original_explanation']
    readonly_fields = ['created_at', 'updated_at', 'display_explanation', 'display_image_url', 'image_size_mb', 'image_resolution']
    date_hierarchy = 'date'
    actions = ['fetch_today_for_source', 'refetch_selected']
    
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
    
    def fetch_today_for_source(self, request, queryset):
        """Fetch today's picture for the source of selected pictures"""
        # Get unique sources from selected pictures
        sources = queryset.values_list('source', flat=True).distinct()
        
        if not sources:
            self.message_user(request, "No pictures selected.", level='warning')
            return
        
        success_count = 0
        error_count = 0
        errors = []
        
        for source in sources:
            # Check if source is enabled
            if not SourceConfiguration.is_source_enabled(source):
                errors.append(f"{source}: Source is disabled")
                error_count += 1
                continue
            
            out = StringIO()
            err = StringIO()
            
            try:
                # Use fetch-all for Bing, regular fetch for others
                if source == 'bing':
                    call_command('fetch_picture', source=source, fetch_all=True, stdout=out, stderr=err)
                else:
                    call_command('fetch_picture', source=source, stdout=out, stderr=err)
                
                output = out.getvalue()
                error_output = err.getvalue()
                
                if error_output:
                    errors.append(f"{source}: {error_output}")
                    error_count += 1
                    logger.error(f"Error fetching {source}: {error_output}")
                else:
                    success_count += 1
                    logger.info(f"Successfully fetched {source}: {output}")
                    
            except Exception as e:
                error_msg = str(e)
                errors.append(f"{source}: {error_msg}")
                error_count += 1
                logger.exception(f"Exception fetching {source}: {error_msg}")
        
        # Build message
        messages = []
        if success_count > 0:
            messages.append(f"Successfully fetched today's pictures for {success_count} source(s).")
        if error_count > 0:
            messages.append(f"Failed to fetch pictures for {error_count} source(s).")
            for error in errors:
                messages.append(f"  - {error}")
        
        self.message_user(request, "\n".join(messages) if messages else "No sources processed.")
    
    fetch_today_for_source.short_description = "Fetch today's picture for selected picture sources"
    
    def refetch_selected(self, request, queryset):
        """Re-fetch and re-process selected pictures (with --force flag)"""
        success_count = 0
        error_count = 0
        errors = []
        
        # Group by source and date to avoid duplicate fetches
        source_date_pairs = queryset.values_list('source', 'date').distinct()
        
        for source, picture_date in source_date_pairs:
            # Check if source is enabled
            if not SourceConfiguration.is_source_enabled(source):
                errors.append(f"{source} ({picture_date}): Source is disabled")
                error_count += 1
                continue
            
            out = StringIO()
            err = StringIO()
            
            try:
                date_str = picture_date.strftime('%Y-%m-%d')
                
                # Use fetch-all for Bing, regular fetch for others
                if source == 'bing':
                    call_command('fetch_picture', source=source, date=date_str, force=True, fetch_all=True, stdout=out, stderr=err)
                else:
                    call_command('fetch_picture', source=source, date=date_str, force=True, stdout=out, stderr=err)
                
                output = out.getvalue()
                error_output = err.getvalue()
                
                if error_output:
                    errors.append(f"{source} ({picture_date}): {error_output}")
                    error_count += 1
                    logger.error(f"Error refetching {source} for {picture_date}: {error_output}")
                else:
                    success_count += 1
                    logger.info(f"Successfully refetched {source} for {picture_date}: {output}")
                    
            except Exception as e:
                error_msg = str(e)
                errors.append(f"{source} ({picture_date}): {error_msg}")
                error_count += 1
                logger.exception(f"Exception refetching {source} for {picture_date}: {error_msg}")
        
        # Build message
        messages = []
        if success_count > 0:
            messages.append(f"Successfully refetched {success_count} picture(s).")
        if error_count > 0:
            messages.append(f"Failed to refetch {error_count} picture(s).")
            for error in errors:
                messages.append(f"  - {error}")
        
        self.message_user(request, "\n".join(messages) if messages else "No pictures processed.")
    
    refetch_selected.short_description = "Re-fetch and re-process selected pictures"


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
    
    actions = ['enable_sources', 'disable_sources', 'fetch_selected_sources', 'fetch_all_enabled_sources']
    
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
    
    def fetch_selected_sources(self, request, queryset):
        """Fetch pictures for selected sources"""
        success_count = 0
        error_count = 0
        errors = []
        
        for source_config in queryset:
            if not source_config.is_enabled:
                errors.append(f"{source_config.label}: Source is disabled")
                error_count += 1
                continue
            
            source = source_config.source
            out = StringIO()
            err = StringIO()
            
            try:
                # Use fetch-all for Bing, regular fetch for others
                if source == 'bing':
                    call_command('fetch_picture', source=source, fetch_all=True, stdout=out, stderr=err)
                else:
                    call_command('fetch_picture', source=source, stdout=out, stderr=err)
                
                output = out.getvalue()
                error_output = err.getvalue()
                
                if error_output:
                    errors.append(f"{source_config.label}: {error_output}")
                    error_count += 1
                    logger.error(f"Error fetching {source}: {error_output}")
                else:
                    success_count += 1
                    logger.info(f"Successfully fetched {source}: {output}")
                    
            except Exception as e:
                error_msg = str(e)
                errors.append(f"{source_config.label}: {error_msg}")
                error_count += 1
                logger.exception(f"Exception fetching {source}: {error_msg}")
        
        # Build message
        messages = []
        if success_count > 0:
            messages.append(f"Successfully fetched pictures for {success_count} source(s).")
        if error_count > 0:
            messages.append(f"Failed to fetch pictures for {error_count} source(s).")
            for error in errors:
                messages.append(f"  - {error}")
        
        self.message_user(request, "\n".join(messages) if messages else "No sources processed.")
    
    fetch_selected_sources.short_description = "Fetch pictures for selected sources"
    
    def fetch_all_enabled_sources(self, request, queryset):
        """Fetch pictures for all enabled sources"""
        enabled_sources = SourceConfiguration.objects.filter(is_enabled=True)
        
        if not enabled_sources.exists():
            self.message_user(request, "No enabled sources found.", level='warning')
            return
        
        success_count = 0
        error_count = 0
        errors = []
        
        for source_config in enabled_sources:
            source = source_config.source
            out = StringIO()
            err = StringIO()
            
            try:
                # Use fetch-all for Bing, regular fetch for others
                if source == 'bing':
                    call_command('fetch_picture', source=source, fetch_all=True, stdout=out, stderr=err)
                else:
                    call_command('fetch_picture', source=source, stdout=out, stderr=err)
                
                output = out.getvalue()
                error_output = err.getvalue()
                
                if error_output:
                    errors.append(f"{source_config.label}: {error_output}")
                    error_count += 1
                    logger.error(f"Error fetching {source}: {error_output}")
                else:
                    success_count += 1
                    logger.info(f"Successfully fetched {source}: {output}")
                    
            except Exception as e:
                error_msg = str(e)
                errors.append(f"{source_config.label}: {error_msg}")
                error_count += 1
                logger.exception(f"Exception fetching {source}: {error_msg}")
        
        # Build message
        messages = []
        if success_count > 0:
            messages.append(f"Successfully fetched pictures for {success_count} enabled source(s).")
        if error_count > 0:
            messages.append(f"Failed to fetch pictures for {error_count} source(s).")
            for error in errors:
                messages.append(f"  - {error}")
        
        self.message_user(request, "\n".join(messages) if messages else "No sources processed.")
    
    fetch_all_enabled_sources.short_description = "Fetch pictures for all enabled sources"


