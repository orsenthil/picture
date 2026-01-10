from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from django.shortcuts import render
from datetime import date, timedelta
from .models import PictureOfTheDay, PictureSource, SourceConfiguration
from .serializers import PictureOfTheDaySerializer, PictureOfTheDayDetailSerializer


class PictureOfTheDayViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for Picture of the Day data from various sources
    
    list: Get all pictures (optionally filtered by source)
    retrieve: Get specific picture by ID
    today: Get today's picture (optionally filtered by source)
    by_date: Get picture for specific date (optionally filtered by source)
    """
    
    queryset = PictureOfTheDay.objects.all()
    serializer_class = PictureOfTheDaySerializer
    
    def get_serializer_class(self):
        if self.action == 'retrieve' or self.action == 'today':
            return PictureOfTheDayDetailSerializer
        return PictureOfTheDaySerializer
    
    def _get_enabled_sources(self):
        """Get list of enabled source values"""
        return SourceConfiguration.get_enabled_sources()
    
    def _is_source_enabled(self, source):
        """Check if a source is enabled"""
        return SourceConfiguration.is_source_enabled(source)
    
    def _validate_source(self, source):
        """Validate that source exists and is enabled"""
        # First check if it's a valid source choice
        valid_sources = [choice[0] for choice in PictureSource.choices]
        if source not in valid_sources:
            return False, f'Invalid source: {source}. Valid sources: {", ".join(valid_sources)}'
        
        # Then check if it's enabled
        if not self._is_source_enabled(source):
            return False, f'Source {source} is currently disabled'
        
        return True, None
    
    def get_queryset(self):
        """Filter by source if provided in query params (for list view)"""
        queryset = super().get_queryset()
        source = self.request.query_params.get('source', None)
        if source:
            queryset = queryset.filter(source=source)
        return queryset
    
    @action(detail=False, methods=['get'], url_path='today/(?P<source>[^/.]+)')
    def today(self, request, source=None):
        """Get today's picture for a specific source"""
        # Use local timezone-aware date
        today = timezone.now().date()
        
        if not source:
            return Response(
                {'error': 'Source is required. Use /api/pictures/today/{source}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate source exists and is enabled
        is_valid, error_message = self._validate_source(source)
        if not is_valid:
            return Response(
                {'error': error_message},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            picture = PictureOfTheDay.objects.get(source=source, date=today)
        except PictureOfTheDay.DoesNotExist:
            # Try yesterday if today's not available
            yesterday = today - timedelta(days=1)
            try:
                picture = PictureOfTheDay.objects.get(source=source, date=yesterday)
            except PictureOfTheDay.DoesNotExist:
                return Response(
                    {'error': f'No {source} picture available. Please run the fetch command.'},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        serializer = self.get_serializer(picture)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], url_path='date/(?P<date_str>[^/.]+)/(?P<source>[^/.]+)')
    def by_date(self, request, date_str=None, source=None):
        """Get picture for specific date and source (format: YYYY-MM-DD)"""
        if not source:
            return Response(
                {'error': 'Source is required. Use /api/pictures/date/{date}/{source}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate source exists and is enabled
        is_valid, error_message = self._validate_source(source)
        if not is_valid:
            return Response(
                {'error': error_message},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            picture_date = date.fromisoformat(date_str)
            picture = PictureOfTheDay.objects.get(source=source, date=picture_date)
        except ValueError:
            return Response(
                {'error': 'Invalid date format. Use YYYY-MM-DD'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except PictureOfTheDay.DoesNotExist:
            return Response(
                {'error': f'No {source} picture found for {date_str}'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = self.get_serializer(picture)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], url_path='latest/(?P<source>[^/.]+)')
    def latest(self, request, source=None):
        """Get the most recent picture for a specific source"""
        if not source:
            return Response(
                {'error': 'Source is required. Use /api/pictures/latest/{source}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate source exists and is enabled
        is_valid, error_message = self._validate_source(source)
        if not is_valid:
            return Response(
                {'error': error_message},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            picture = PictureOfTheDay.objects.filter(source=source).order_by('-date').first()
        except PictureOfTheDay.DoesNotExist:
            return Response(
                {'error': f'No {source} picture available'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        if not picture:
            return Response(
                {'error': f'No {source} picture available'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = self.get_serializer(picture)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def sources(self, request):
        """Get list of available (enabled) sources"""
        # Get all source configurations
        configs = SourceConfiguration.objects.all()
        
        # Build response with enabled sources
        sources = []
        for config in configs:
            if config.is_enabled:
                sources.append({
                    'value': config.source,
                    'label': config.label,
                    'enabled': True
                })
        
        # If no configurations exist, return all sources as enabled (backward compatibility)
        if not configs.exists():
            sources = [
                {
                    'value': choice[0],
                    'label': choice[1],
                    'enabled': True
                }
                for choice in PictureSource.choices
            ]
        
        return Response(sources)
    
    @action(detail=False, methods=['get'])
    def all_recent(self, request):
        """Get all recent pictures from all enabled sources for random selection
        
        Returns a pool of pictures that gives each individual picture equal probability:
        - For sources like Wikipedia and APOD: returns today's (or yesterday's) picture
        - For Bing: returns multiple recent pictures (last 8 days) to balance the pool
        """
        enabled_sources = self._get_enabled_sources()
        
        if not enabled_sources:
            return Response(
                {'error': 'No picture sources are currently enabled'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        today = timezone.now().date()
        pictures = []
        
        # Get today's (or yesterday's) picture for non-Bing enabled sources
        for source in enabled_sources:
            if source == 'bing':
                continue  # Handle Bing separately to get multiple pictures
            
            try:
                picture = PictureOfTheDay.objects.get(source=source, date=today)
                pictures.append(picture)
            except PictureOfTheDay.DoesNotExist:
                # Try yesterday if today's not available
                yesterday = today - timedelta(days=1)
                try:
                    picture = PictureOfTheDay.objects.get(source=source, date=yesterday)
                    pictures.append(picture)
                except PictureOfTheDay.DoesNotExist:
                    pass
        
        # For Bing, include recent historical pictures (last 8 days) to balance the pool
        if 'bing' in enabled_sources:
            recent_bing = PictureOfTheDay.objects.filter(
                source='bing'
            ).order_by('-date')[:8]  # Get 8 recent Bing pictures
            
            pictures.extend(recent_bing)
        
        serializer = PictureOfTheDaySerializer(pictures, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], url_path='list/(?P<source>[^/.]+)')
    def list_by_source(self, request, source=None):
        """Get all available pictures for a specific source, ordered by date (newest first)"""
        if not source:
            return Response(
                {'error': 'Source is required. Use /api/pictures/list/{source}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate source exists and is enabled
        is_valid, error_message = self._validate_source(source)
        if not is_valid:
            return Response(
                {'error': error_message},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        pictures = PictureOfTheDay.objects.filter(source=source).order_by('-date')
        serializer = PictureOfTheDaySerializer(pictures, many=True)
        return Response(serializer.data)


def picture_of_the_day_view(request):
    """Render the Picture of the Day page"""
    return render(request, 'pictures/picture_of_the_day.html')


def privacy_policy_view(request):
    """Render the Privacy Policy page"""
    return render(request, 'pictures/privacy.html')
