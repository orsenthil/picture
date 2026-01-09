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
    
    def process_picture_description(self, original_text, context="general"):
        """
        Process picture description: create a highly representative summary (max 300 words)
        with exactly 3 high-value Wikipedia links.
        
        This is the unified processing function used for all picture sources.
        It creates a concise, informative summary and links only the 3 most important terms.
        
        Args:
            original_text: Original description text from the picture source
            context: Context for processing (e.g., 'astronomy', 'general')
        
        Returns:
            str: Processed text with summary (max 300 words) and exactly 3 Wikipedia links
        """
        # Context-specific guidance for selecting high-value terms
        context_guidance = {
            'astronomy': """Focus on the most significant astronomical concepts, objects, or phenomena mentioned. 
Prioritize: major celestial objects, important scientific discoveries, key astronomical phenomena, or notable space missions.""",
            'general': """Focus on the most significant people, places, events, or concepts mentioned.
Prioritize: notable historical figures, important locations, significant events, or key scientific/cultural concepts."""
        }
        
        guidance = context_guidance.get(context, context_guidance['general'])
        
        prompt = f"""Create a highly representative summary of the following picture description. The summary should:
1. Be concise and informative (maximum 300 words)
2. Capture the essential information and key points about the picture
3. Be accessible to a general audience while maintaining accuracy
4. Include exactly 3 high-value Wikipedia links to the most important terms/concepts

Select the 3 most important terms/concepts that would benefit readers most from Wikipedia links.
These should be the highest-value terms that add significant context or understanding.

{guidance}

Format the Wikipedia links as HTML anchor tags:
<a href="https://en.wikipedia.org/wiki/Article_Name" target="_blank">term</a>

Original description:
{original_text}

Return ONLY the processed summary text with exactly 3 Wikipedia links embedded, no preamble or explanation:"""

        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an expert at creating concise, informative summaries and identifying the most valuable terms for Wikipedia linking."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=800  # Enough for ~300 words plus HTML links
        )
        
        result = response.choices[0].message.content.strip()
        
        # Clean up any markdown code blocks if present
        result = re.sub(r'^```html?\n', '', result)
        result = re.sub(r'\n```$', '', result)
        
        # Validate and fix if needed
        result = self._validate_and_fix_processed_text(result)
        
        return result
    
    def _validate_and_fix_processed_text(self, text):
        """
        Validate processed text meets requirements:
        - Maximum 300 words
        - Exactly 3 Wikipedia links
        
        If not, attempt to fix by truncating or adjusting links.
        """
        if not text:
            return text
        
        # Count Wikipedia links first (before any truncation)
        link_pattern = r'<a\s+href=["\']https?://en\.wikipedia\.org/wiki/[^"\']+["\'][^>]*>.*?</a>'
        all_links = re.findall(link_pattern, text, re.IGNORECASE | re.DOTALL)
        link_count = len(all_links)
        
        # Count words (excluding HTML tags for accurate count)
        text_for_word_count = re.sub(r'<[^>]+>', '', text)  # Remove HTML tags for word counting
        words = text_for_word_count.split()
        word_count = len(words)
        
        # If word count exceeds 300, truncate carefully to preserve links
        if word_count > 300:
            # Find positions of all links
            link_matches = list(re.finditer(link_pattern, text, re.IGNORECASE | re.DOTALL))
            
            # Try to truncate while preserving at least 3 links
            if link_count >= 3:
                # Find where the 3rd link ends
                if len(link_matches) >= 3:
                    third_link_end = link_matches[2].end()
                    # Truncate to preserve first 3 links
                    truncated = text[:third_link_end]
                    # Count words in truncated version
                    truncated_text_for_count = re.sub(r'<[^>]+>', '', truncated)
                    truncated_word_count = len(truncated_text_for_count.split())
                    
                    # If still over 300 words, truncate by words but try to preserve links
                    if truncated_word_count > 300:
                        # Truncate by words, but keep complete links
                        words_list = text_for_word_count.split()[:300]
                        # Find the position of the 300th word in original text
                        word_pos = len(' '.join(words_list))
                        # Find the nearest complete link before this position
                        for link_match in reversed(link_matches[:3]):
                            if link_match.end() <= len(text[:word_pos + 100]):  # Add buffer
                                text = text[:link_match.end()]
                                break
                    else:
                        text = truncated
                else:
                    # Fallback: truncate by words
                    words_list = text_for_word_count.split()[:300]
                    text = ' '.join(words_list)
            else:
                # Not enough links, just truncate by words
                words_list = text_for_word_count.split()[:300]
                text = ' '.join(words_list)
            
            # Re-count after truncation
            links = re.findall(link_pattern, text, re.IGNORECASE | re.DOTALL)
            link_count = len(links)
        
        # If link count is not 3, try to fix
        if link_count != 3:
            if link_count > 3:
                # Remove excess links, keeping first 3
                link_matches = list(re.finditer(link_pattern, text, re.IGNORECASE | re.DOTALL))
                if len(link_matches) > 3:
                    # Keep text up to end of 3rd link
                    text = text[:link_matches[2].end()]
                    # Re-count to verify
                    links = re.findall(link_pattern, text, re.IGNORECASE | re.DOTALL)
                    link_count = len(links)
            # If link_count < 3, we can't automatically add links - return as is
            # The prompt should have ensured 3 links, but we handle edge cases
        
        return text
    
    # Legacy methods kept for backward compatibility but deprecated
    def simplify_text(self, text, context="general"):
        """
        DEPRECATED: Use process_picture_description instead.
        Simplify the explanation text
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
        DEPRECATED: Use process_picture_description instead.
        Add Wikipedia links to important concepts
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
        DEPRECATED: Use process_picture_description instead.
        Process text: simplify and add Wikipedia links
        """
        simplified = self.simplify_text(text, context)
        processed = self.add_wikipedia_links(simplified, context)
        return simplified, processed

