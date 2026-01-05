"""
Processing utilities for Picture of the Day
"""
import re
import os
import requests
from io import BytesIO
from PIL import Image
from django.conf import settings
from openai import OpenAI


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
    """Handles text processing with OpenAI"""
    
    def __init__(self, api_key=None):
        self.client = OpenAI(api_key=api_key or settings.OPENAI_API_KEY)
    
    def simplify_text(self, text, context="general"):
        """
        Simplify the explanation text
        
        Args:
            text: Original text to simplify
            context: Context for simplification (e.g., 'astronomy', 'general')
        
        Returns:
            str: Simplified text
        """
        prompt = f"""Please simplify the following explanation to make it more accessible to a general audience. 
Keep it informative but reduce technical jargon. Maintain the key facts and interesting details.
Keep the length similar to the original.

Original text:
{text}

Simplified version:"""

        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an expert at simplifying scientific text while maintaining accuracy."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1000
        )
        
        return response.choices[0].message.content.strip()
    
    def add_wikipedia_links(self, text, context="general"):
        """
        Add Wikipedia links to important concepts
        
        Args:
            text: Text to add links to
            context: Context for link identification (e.g., 'astronomy', 'general')
        
        Returns:
            str: Text with HTML anchor tags for Wikipedia links
        """
        # Context-specific focus areas
        focus_areas = {
            'astronomy': [
                '- Celestial objects (galaxies, nebulae, stars, planets, etc.)',
                '- Astronomical phenomena (eclipses, supernovae, etc.)',
                '- Scientific concepts (spectroscopy, redshift, etc.)',
                '- Space missions and telescopes'
            ],
            'general': [
                '- Important people, places, and events',
                '- Scientific concepts and terms',
                '- Historical events and figures',
                '- Cultural and artistic concepts'
            ]
        }
        
        focus_list = focus_areas.get(context, focus_areas['general'])
        focus_text = '\n'.join(focus_list)
        
        prompt = f"""Please identify important concepts, terms, people, places, and notable phenomena in the following text and add Wikipedia links to them.

Return the text with HTML anchor tags linking to relevant Wikipedia articles.
Format: <a href="https://en.wikipedia.org/wiki/Article_Name" target="_blank">term</a>

Only link the FIRST occurrence of each term. Don't over-link common words.
Focus on:
{focus_text}

Text:
{text}

Return ONLY the text with links added, no preamble or explanation:"""

        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an expert at identifying important concepts and linking them to Wikipedia."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=1500
        )
        
        result = response.choices[0].message.content.strip()
        
        # Clean up any markdown code blocks if present
        result = re.sub(r'^```html?\n', '', result)
        result = re.sub(r'\n```$', '', result)
        
        return result
    
    def process_text(self, text, context="general"):
        """
        Process text: simplify and add Wikipedia links
        
        Args:
            text: Original text
            context: Context for processing
        
        Returns:
            tuple: (simplified_text, processed_text_with_links)
        """
        simplified = self.simplify_text(text, context)
        processed = self.add_wikipedia_links(simplified, context)
        return simplified, processed

