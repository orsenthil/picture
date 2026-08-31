"""
Processing utilities for Picture of the Day
"""
import re
import os
import time
import requests
from io import BytesIO
from PIL import Image
from django.conf import settings
from openai import OpenAI, RateLimitError


class ImageProcessor:
    """Handles image downloading, storage, and size calculation"""
    
    @staticmethod
    def get_image_metadata(url):
        """
        Get image metadata (width, height, size) from full resolution image URL
        
        Downloads the image to get dimensions, but doesn't save it.
        Uses Content-Length header for size if available, otherwise uses downloaded size.
        
        Returns:
            tuple: (width: int, height: int, size_bytes: int) or (None, None, None) on error
        """
        try:
            # Wikipedia and some sites require User-Agent header
            headers = {
                'User-Agent': 'PictureOfTheDay/1.0 (https://github.com/orsenthil/picture)'
            }
            # Download image to get dimensions (we need the image data for PIL)
            response = requests.get(url, headers=headers, timeout=60, stream=True)  # Increased timeout for large images
            response.raise_for_status()
            
            # Get size from Content-Length header if available
            if 'Content-Length' in response.headers:
                size_bytes = int(response.headers['Content-Length'])
            else:
                size_bytes = None
            
            # Download image data to get dimensions
            image_data = response.content
            
            # If we didn't get size from header, use downloaded size
            if size_bytes is None:
                size_bytes = len(image_data)
            
            # Get image dimensions using PIL
            try:
                img = Image.open(BytesIO(image_data))
                width, height = img.size
                # Verify image is valid
                img.verify()
            except Exception as img_error:
                # If PIL can't read it, try to get dimensions from EXIF or other methods
                # For now, return None for dimensions but keep size if we have it
                width, height = None, None
                # If we can't get dimensions, we still want to return size if available
                if size_bytes:
                    # Try one more time with a fresh image object (verify() consumes the data)
                    try:
                        img = Image.open(BytesIO(image_data))
                        width, height = img.size
                    except:
                        pass
            
            return width, height, size_bytes
            
        except requests.exceptions.RequestException as e:
            # Network error
            return None, None, None
        except Exception as e:
            # Other errors
            return None, None, None
    
    @staticmethod
    def download_image(url, save_path=None):
        """
        Download image from URL and optionally save to local path
        
        Returns:
            tuple: (image_data: bytes, width: int, height: int, size_bytes: int)
        """
        response = requests.get(url, timeout=30, stream=True)
        response.raise_for_status()
        
        image_data = response.content
        size_bytes = len(image_data)
        
        # Get image dimensions
        try:
            img = Image.open(BytesIO(image_data))
            width, height = img.size
        except Exception as e:
            # If we can't read the image, return None for dimensions
            width, height = None, None
        
        # Save to local path if provided
        if save_path:
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            with open(save_path, 'wb') as f:
                f.write(image_data)
        
        return image_data, width, height, size_bytes
    
    @staticmethod
    def get_image_path(source, date, filename=None):
        """
        Generate local path for storing image
        
        Args:
            source: Picture source (e.g., 'apod', 'wikipedia_pod')
            date: Date object
            filename: Optional filename, otherwise generated from date
        
        Returns:
            str: Path relative to MEDIA_ROOT
        """
        if filename is None:
            filename = f"{date.strftime('%Y-%m-%d')}.jpg"
        
        return os.path.join('pictures', source, date.strftime('%Y'), date.strftime('%m'), filename)


class TextProcessor:
    """Handles text processing with OpenRouter"""

    def __init__(self, api_key=None):
        self.client = OpenAI(api_key=api_key or settings.OPENROUTER_API_KEY,
                             base_url='https://openrouter.ai/api/v1')

    def process_picture_description(self, original_text, context="general"):
        """
        Process a picture description into a short, high-quality phrase
        (maximum 10 words) describing what the picture shows.

        This is the single unified processing function used for all picture
        sources. It is meant for dashboard display, so it deliberately avoids
        Wikipedia links or lengthy summaries - just a punchy phrase.

        Args:
            original_text: Original description text from the picture source
            context: Context for processing (e.g., 'astronomy', 'general')

        Returns:
            str: A phrase describing the picture, maximum 10 words
        """
        context_guidance = {
            'astronomy': "Focus on the most striking astronomical object or phenomenon shown.",
            'general': "Focus on the most striking subject or scene shown.",
        }
        guidance = context_guidance.get(context, context_guidance['general'])

        prompt = f"""Read the following picture description and write a single high-quality phrase, maximum 10 words, that describes what the picture shows.

{guidance}

Rules:
- Maximum 10 words
- No links, no citations, no Wikipedia references
- No trailing period
- Plain text only, no preamble or explanation

Original description:
{original_text}

Return ONLY the phrase:"""

        max_attempts = 4
        delay = 5
        result = None
        for attempt in range(1, max_attempts + 1):
            try:
                response = self.client.chat.completions.create(
                    model="openrouter/free",
                    messages=[
                        {"role": "system", "content": "You are an expert at distilling text into short, high-quality descriptive phrases."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    max_tokens=40
                )
                content = response.choices[0].message.content
                candidate = self._clean_candidate(content) if content else None
                if candidate and self._is_valid_caption(candidate):
                    result = candidate
                    break
            except RateLimitError:
                pass

            if attempt == max_attempts:
                raise ValueError(
                    f"OpenRouter returned no usable caption after {max_attempts} attempts "
                    f"for description: {original_text[:80]!r}..."
                )
            time.sleep(delay)
            delay *= 2

        return self._enforce_word_limit(result, max_words=10)

    @staticmethod
    def _clean_candidate(content):
        """Strip markdown code fences and surrounding quotes from a raw model response."""
        result = content.strip()
        result = re.sub(r'^```\w*\n', '', result)
        result = re.sub(r'\n```$', '', result)
        result = result.strip().strip('"').strip("'").strip()
        return result

    # Free-tier auto-routed models occasionally leak chain-of-thought
    # reasoning into the regular content field instead of a caption.
    _REASONING_LEAK_PATTERN = re.compile(
        r'^(we need|here\'?s|let\'?s|let me|i need|the user|first,|step \d|okay|sure|'
        r'analyz|input:|thinking process)',
        re.IGNORECASE
    )

    @classmethod
    def _is_valid_caption(cls, text):
        """
        Reject responses that look like leaked reasoning/instructions rather
        than an actual descriptive caption.
        """
        if not text:
            return False
        if cls._REASONING_LEAK_PATTERN.match(text):
            return False
        # Numbered-list / markdown structure ("1. **Analyze...") is a reasoning artifact
        if re.search(r'\d+\.\s*\*\*', text) or re.search(r'^\d+[.)]\s', text):
            return False
        return True

    @staticmethod
    def _enforce_word_limit(text, max_words=10):
        """Truncate text to at most max_words words."""
        if not text:
            return text

        words = text.split()
        if len(words) > max_words:
            text = ' '.join(words[:max_words])

        return text.rstrip('.')

