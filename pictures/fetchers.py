"""
Base fetcher interface and implementations for different picture sources
"""
import re
import os
from abc import ABC, abstractmethod
from datetime import date
from typing import Dict, Any
import requests
from django.conf import settings


class BasePictureFetcher(ABC):
    """Abstract base class for fetching pictures from different sources"""
    
    source_name: str = None
    
    @abstractmethod
    def fetch(self, target_date: date) -> Dict[str, Any]:
        """
        Fetch picture data for a given date
        
        Args:
            target_date: Date to fetch picture for
        
        Returns:
            dict: Picture data with keys:
                - title: str
                - date: str (YYYY-MM-DD)
                - explanation: str
                - image_url: str
                - hd_image_url: str (optional)
                - thumbnail_url: str (optional)
                - media_type: str (default: 'image')
                - copyright: str (optional)
                - source_url: str (optional)
        """
        pass
    
    @abstractmethod
    def get_source_url(self, picture_date: date) -> str:
        """Get the URL to the original source page"""
        pass


class APODFetcher(BasePictureFetcher):
    """Fetcher for NASA Astronomy Picture of the Day"""
    
    source_name = 'apod'
    
    def fetch(self, target_date: date) -> Dict[str, Any]:
        """Fetch APOD from NASA API"""
        api_key = settings.NASA_API_KEY
        url = 'https://api.nasa.gov/planetary/apod'
        
        params = {
            'api_key': api_key,
            'date': target_date.strftime('%Y-%m-%d')
        }
        
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        date_str = data['date'].replace('-', '')[2:]
        nasa_url = f"https://apod.nasa.gov/apod/ap{date_str}.html"
        
        return {
            'title': data['title'],
            'date': data['date'],
            'explanation': data['explanation'],
            'image_url': data.get('url', ''),
            'hd_image_url': data.get('hdurl'),
            'thumbnail_url': data.get('thumbnail_url'),
            'media_type': data.get('media_type', 'image'),
            'copyright': data.get('copyright'),
            'source_url': nasa_url,
        }
    
    def get_source_url(self, picture_date: date) -> str:
        """Get NASA APOD URL for a date"""
        date_str = picture_date.strftime('%y%m%d')
        return f"https://apod.nasa.gov/apod/ap{date_str}.html"


class WikipediaPODFetcher(BasePictureFetcher):
    """Fetcher for Wikipedia Picture of the Day"""
    
    source_name = 'wikipedia'
    
    def fetch(self, target_date: date) -> Dict[str, Any]:
        """Fetch Wikipedia Picture of the Day using MediaWiki API"""
        endpoint = "https://en.wikipedia.org/w/api.php"
        date_iso = target_date.isoformat()
        template_title = f"Template:POTD protected/{date_iso}"
        potd_template_title = f"Template:POTD/{date_iso}"
        
        headers = {
            'User-Agent': 'PictureOfTheDay/1.0 (https://github.com/yourusername/picture)'
        }
        
        params = {
            "action": "query",
            "format": "json",
            "formatversion": "2",
            "prop": "images",
            "titles": template_title
        }
        
        response = requests.get(endpoint, params=params, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        pages = data.get('query', {}).get('pages', [])
        if not pages or 'images' not in pages[0] or not pages[0]['images']:
            raise ValueError(f"No POTD found for {date_iso}")
        
        filename = pages[0]['images'][0]['title']
        
        image_url = self._fetch_image_url(filename, endpoint, headers)
        
        explanation, title = self._fetch_potd_description(potd_template_title, endpoint, headers)
        
        if not title:
            clean_filename = filename
            if clean_filename.startswith('File:'):
                clean_filename = clean_filename[5:]
            title = self._clean_filename_title(clean_filename)
        
        source_url = f"https://en.wikipedia.org/wiki/Wikipedia:Picture_of_the_day/{target_date.strftime('%B_%d,_%Y')}"
        
        return {
            'title': title or 'Wikipedia Picture of the Day',
            'date': target_date.strftime('%Y-%m-%d'),
            'explanation': explanation or 'No description available.',
            'image_url': image_url,
            'hd_image_url': image_url,
            'thumbnail_url': image_url,
            'media_type': 'image',
            'copyright': None,
            'source_url': source_url,
        }
    
    def _fetch_image_url(self, filename: str, endpoint: str, headers: dict) -> str:
        """Fetch the full resolution image URL from MediaWiki API"""
        params = {
            "action": "query",
            "format": "json",
            "formatversion": "2",
            "prop": "imageinfo",
            "iiprop": "url",
            "titles": filename
        }
        
        response = requests.get(endpoint, params=params, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        pages = data.get('query', {}).get('pages', [])
        if not pages or 'imageinfo' not in pages[0] or not pages[0]['imageinfo']:
            raise ValueError(f"Could not fetch image URL for {filename}")
        
        return pages[0]['imageinfo'][0]['url']
    
    def _fetch_potd_description(self, template_title: str, endpoint: str, headers: dict) -> tuple:
        """Fetch the description and title from Template:POTD/{date}"""
        params = {
            "action": "query",
            "format": "json",
            "formatversion": "2",
            "prop": "revisions",
            "rvprop": "content",
            "rvslots": "main",
            "titles": template_title
        }
        
        try:
            response = requests.get(endpoint, params=params, headers=headers, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            pages = data.get('query', {}).get('pages', [])
            if pages and 'revisions' in pages[0] and pages[0]['revisions']:
                content = pages[0]['revisions'][0].get('slots', {}).get('main', {}).get('content', '')
                if not content:
                    content = pages[0]['revisions'][0].get('content', '')
                
                if content:
                    explanation, title = self._parse_potd_wikitext(content)
                    return explanation, title
        except Exception as e:
            pass
        
        try:
            params = {
                "action": "parse",
                "format": "json",
                "page": template_title,
                "prop": "text",
                "section": "0"
            }
            response = requests.get(endpoint, params=params, headers=headers, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            if 'parse' in data and 'text' in data['parse']:
                html_content = data['parse']['text']['*']
                explanation, title = self._extract_description_from_html(html_content)
                if explanation:
                    return explanation, title
        except Exception as e:
            pass
        
        return None, None
    
    def _parse_potd_wikitext(self, wikitext: str) -> tuple:
        """Parse POTD wikitext to extract caption and title"""
        
        explanation = None
        title = None
        
        title_match = re.search(r'\|\s*texttitle\s*=\s*(.+?)(?:\n|$)', wikitext)
        if not title_match:
            title_match = re.search(r'\|\s*title\s*=\s*\[\[([^\]]+)\|([^\]]+)\]\]', wikitext)
            if title_match:
                title = title_match.group(2)
            else:
                title_match = re.search(r'\|\s*title\s*=\s*\[\[([^\]]+)\]\]', wikitext)
                if title_match:
                    title = title_match.group(1)
        
        if title_match and not title:
            title = title_match.group(1).strip()
        
        caption_match = re.search(r'\|\s*caption\s*=\s*(.+?)(?:\n\s*\||$)', wikitext, re.DOTALL)
        if caption_match:
            explanation = caption_match.group(1).strip()
            explanation = self._clean_wikitext(explanation)
        
        return explanation, title
    
    def _clean_wikitext(self, text: str) -> str:
        """Clean wikitext markup to plain text"""
        
        text = re.sub(r'\[\[([^\]]+)\|([^\]]+)\]\]', r'\2', text)
        text = re.sub(r'\[\[([^\]]+)\]\]', r'\1', text)
        
        text = re.sub(r"'''([^']+)'''", r'\1', text)
        text = re.sub(r"''([^']+)''", r'\1', text)
        
        text = text.replace('&nbsp;', ' ')
        text = text.replace('&amp;', '&')
        text = text.replace('&lt;', '<')
        text = text.replace('&gt;', '>')
        
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        return text
    
    def _extract_description_from_html(self, html: str) -> tuple:
        """Extract description text from parsed HTML"""
        import re
        import html as html_module
        
        match = re.search(r'<div style="padding-top: 0\.3em;">(.+?)</div>', html, re.DOTALL)
        if match:
            description_html = match.group(1)
            text = re.sub(r'<[^>]+>', '', description_html)
            text = re.sub(r'Photograph credit:.*$', '', text, flags=re.DOTALL)
            text = re.sub(r'Archive.*$', '', text, flags=re.DOTALL)
            text = html_module.unescape(text.strip())
            
            title_match = re.search(r'^([^\.]+)', text)
            title = title_match.group(1).strip() if title_match else None
            
            return text, title
        
        return None, None
    
    
    def _clean_filename_title(self, filename: str) -> str:
        """Clean a filename to create a readable title"""
        
        if filename.startswith('File:'):
            filename = filename[5:]
        
        filename = os.path.splitext(filename)[0]
        
        filename = filename.replace('_', ' ')
        
        filename = re.sub(r',?\s*\d{4}[-_]\d{2}[-_]\d{2}\s*,?', ' ', filename)
        filename = re.sub(r',?\s*\d{8}\s*,?', ' ', filename)
        
        filename = re.sub(r',?\s+[A-Z]{2,}(\s+[0-9-]+)?\s*$', '', filename)
        filename = re.sub(r',?\s+DD\s+\d+-\d+\s*', ' ', filename)
        filename = re.sub(r',?\s+[A-Z]\s+[A-Z]-\w\s*', ' ', filename)
        
        filename = re.sub(r'^\d+\s+', '', filename)
        
        filename = re.sub(r',?\s+[A-Z]{3}\s*$', '', filename)
        
        filename = re.sub(r',+\s*$', '', filename)  # Remove trailing commas
        filename = re.sub(r'\s+', ' ', filename)  # Multiple spaces to single
        filename = re.sub(r',\s*,', ',', filename)  # Multiple commas to single
        filename = re.sub(r'\s*,\s*', ', ', filename)  # Normalize comma spacing
        
        filename = filename.strip()
        if filename:
            filename = filename.strip(',').strip()
            if filename:
                filename = filename[0].upper() + filename[1:] if len(filename) > 1 else filename.upper()
        
        return filename
    
    def get_source_url(self, picture_date: date) -> str:
        """Get Wikipedia POD page URL for a date"""
        return f"https://en.wikipedia.org/wiki/Wikipedia:Picture_of_the_day/{picture_date.strftime('%B_%d,_%Y')}"


class BingPODFetcher(BasePictureFetcher):
    """Fetcher for Bing Picture of the Day"""
    
    source_name = 'bing'
    
    def fetch(self, target_date: date) -> Dict[str, Any]:
        """Fetch Bing Picture of the Day"""
        # Bing HPImageArchive API
        # idx=0 means today, idx=1 means yesterday, etc.
        # n=8 gets last 8 days (to find the one matching target_date)
        # We'll fetch multiple days and find the one matching our target date
        
        # Calculate days offset from today
        from datetime import date as date_class
        today = date_class.today()
        days_offset = (today - target_date).days
        
        if days_offset < 0:
            # Future date - not available
            raise ValueError(f"Bing POD not available for future dates")
        if days_offset > 7:
            # Too far in the past - fetch more days
            n = min(days_offset + 1, 15)  # Bing typically has last 15 days
        else:
            n = 8  # Default to 8 days
        
        api_url = f"https://www.bing.com/HPImageArchive.aspx?format=js&idx=0&n={n}&mkt=en-US"
        
        headers = {
            'User-Agent': 'PictureOfTheDay/1.0 (https://github.com/yourusername/picture)'
        }
        response = requests.get(api_url, headers=headers, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        images = data.get('images', [])
        
        if not images:
            raise ValueError("No Bing images available")
        
        # Find image matching target date
        matching_image = None
        for img in images:
            img_date_str = img.get('startdate', '')
            if img_date_str:
                try:
                    img_date = date_class(
                        int(img_date_str[:4]),   # year
                        int(img_date_str[4:6]),  # month
                        int(img_date_str[6:8])   # day
                    )
                    if img_date == target_date:
                        matching_image = img
                        break
                except (ValueError, IndexError):
                    continue
        
        # If no exact match, use the first image (today's)
        if not matching_image:
            if days_offset == 0:
                matching_image = images[0]
            else:
                # Try to get image at the offset position
                if days_offset < len(images):
                    matching_image = images[days_offset]
                else:
                    matching_image = images[0]  # Fallback to today's
        
        # Extract image data
        # Bing provides relative URLs, need to prepend domain
        image_path = matching_image.get('url', '')
        if image_path.startswith('/'):
            image_url = f"https://www.bing.com{image_path}"
        else:
            image_url = image_path
        
        # Get full resolution URL (Bing provides UHD versions)
        # Bing URL format: /th?id=OHR.ImageName_1920x1080.jpg&rf=LaDigue_1920x1080.jpg&pid=hp
        # UHD format: /th?id=OHR.ImageName_UHD.jpg&rf=LaDigue_UHD.jpg&pid=hp
        hd_url = image_url
        # Try to construct UHD URL
        if '_' in image_url:
            # Replace resolution with UHD
            # Pattern: ..._1920x1080.jpg -> ..._UHD.jpg
            import re
            # Replace any resolution pattern (e.g., 1920x1080, 1366x768) with UHD
            hd_url = re.sub(r'_\d+x\d+\.jpg', '_UHD.jpg', image_url)
            # Also replace in rf parameter if present
            hd_url = re.sub(r'rf=LaDigue_\d+x\d+\.jpg', 'rf=LaDigue_UHD.jpg', hd_url)
        
        # Get title and description
        title = matching_image.get('title', 'Bing Picture of the Day')
        description = matching_image.get('copyright', '')
        
        # Get full description from copyright field (Bing puts description there)
        explanation = matching_image.get('copyright', '')
        if not explanation:
            explanation = matching_image.get('title', 'No description available.')
        
        # Get source URL
        source_url = "https://www.bing.com"
        
        return {
            'title': title,
            'date': target_date.strftime('%Y-%m-%d'),
            'explanation': explanation,
            'image_url': image_url,
            'hd_image_url': hd_url,  # Bing images are already high resolution
            'thumbnail_url': image_url,  # Bing doesn't provide separate thumbnails
            'media_type': 'image',
            'copyright': matching_image.get('copyright', ''),
            'source_url': source_url,
        }
    
    def get_source_url(self, picture_date: date) -> str:
        """Get Bing homepage URL"""
        return "https://www.bing.com"
    
    def fetch_all_available(self, max_days: int = 8) -> list:
        """
        Fetch all available Bing Pictures of the Day
        
        Args:
            max_days: Maximum number of days to fetch (default 8, max 15)
        
        Returns:
            list: List of picture data dictionaries
        """
        n = min(max_days, 15)  # Bing API limit
        api_url = f"https://www.bing.com/HPImageArchive.aspx?format=js&idx=0&n={n}&mkt=en-US"
        
        headers = {
            'User-Agent': 'PictureOfTheDay/1.0 (https://github.com/yourusername/picture)'
        }
        response = requests.get(api_url, headers=headers, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        images = data.get('images', [])
        
        results = []
        from datetime import date as date_class
        
        for img in images:
            img_date_str = img.get('startdate', '')
            if img_date_str:
                try:
                    img_date = date_class(
                        int(img_date_str[:4]),
                        int(img_date_str[4:6]),
                        int(img_date_str[6:8])
                    )
                    
                    image_path = img.get('url', '')
                    if image_path.startswith('/'):
                        image_url = f"https://www.bing.com{image_path}"
                    else:
                        image_url = image_path
                    
                    # Get UHD version
                    hd_url = image_url
                    if '_' in image_url:
                        import re
                        hd_url = re.sub(r'_\d+x\d+\.jpg', '_UHD.jpg', image_url)
                        hd_url = re.sub(r'rf=LaDigue_\d+x\d+\.jpg', 'rf=LaDigue_UHD.jpg', hd_url)
                    
                    results.append({
                        'title': img.get('title', 'Bing Picture of the Day'),
                        'date': img_date.strftime('%Y-%m-%d'),
                        'explanation': img.get('copyright', ''),
                        'image_url': image_url,
                        'hd_image_url': hd_url,
                        'thumbnail_url': image_url,
                        'media_type': 'image',
                        'copyright': img.get('copyright', ''),
                        'source_url': 'https://www.bing.com',
                    })
                except (ValueError, IndexError):
                    continue
        
        return results


def get_fetcher(source: str) -> BasePictureFetcher:
    """Factory function to get the appropriate fetcher"""
    fetchers = {
        'apod': APODFetcher(),
        'wikipedia': WikipediaPODFetcher(),
        'bing': BingPODFetcher(),
    }
    
    if source not in fetchers:
        raise ValueError(f"Unknown source: {source}. Available: {list(fetchers.keys())}")
    
    return fetchers[source]

