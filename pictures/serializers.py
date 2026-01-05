from rest_framework import serializers
from .models import PictureOfTheDay


class PictureOfTheDaySerializer(serializers.ModelSerializer):
    """Serializer for Picture of the Day model"""
    
    display_explanation = serializers.ReadOnlyField()
    display_image_url = serializers.ReadOnlyField()
    image_size_mb = serializers.ReadOnlyField()
    image_resolution = serializers.ReadOnlyField()
    source_display = serializers.CharField(source='get_source_display', read_only=True)
    
    class Meta:
        model = PictureOfTheDay
        fields = [
            'id',
            'source',
            'source_display',
            'date',
            'title',
            'display_explanation',
            'display_image_url',
            'media_type',
            'copyright',
            'source_url',
            'is_processed',
            'image_width',
            'image_height',
            'image_size_mb',
            'image_resolution',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']


class PictureOfTheDayDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer with all fields"""
    
    display_explanation = serializers.ReadOnlyField()
    display_image_url = serializers.ReadOnlyField()
    image_size_mb = serializers.ReadOnlyField()
    image_resolution = serializers.ReadOnlyField()
    source_display = serializers.CharField(source='get_source_display', read_only=True)
    
    class Meta:
        model = PictureOfTheDay
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


