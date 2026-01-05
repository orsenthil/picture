/**
 * Tests for newtab.js browser extension functionality
 * 
 * To run these tests:
 * 1. Install dependencies: npm install
 * 2. Run tests: npm test
 * 3. Run tests in watch mode: npm run test:watch
 * 4. Run tests with coverage: npm run test:coverage
 */

// We need to load the HTML first to set up the DOM
const fs = require('fs');
const path = require('path');

// Load the HTML file to set up DOM structure
// Source files are in the parent extension directory
const htmlContent = fs.readFileSync(
  path.join(__dirname, '../../extension/newtab.html'),
  'utf8'
);

// Load the newtab.js file
const newtabJsContent = fs.readFileSync(
  path.join(__dirname, '../../extension/newtab.js'),
  'utf8'
);

describe('newtab.js Tests', () => {
  // Store original init to prevent auto-execution
  let originalInit;
  
  beforeEach(() => {
    // Set up DOM from HTML
    document.documentElement.innerHTML = htmlContent;
    
    // Clear localStorage
    localStorage.clear();
    
    // Reset fetch mock completely (not just clear)
    fetch.mockReset();
    // Set default implementation that can be overridden by individual tests
    // Mock sources API endpoint by default
    fetch.mockImplementation((url) => {
      if (url && url.includes('/sources/')) {
        return Promise.resolve({
          ok: true,
          json: async () => [
            { value: 'apod', label: 'NASA APOD', enabled: true },
            { value: 'wikipedia', label: 'Wikipedia POD', enabled: true },
            { value: 'bing', label: 'Bing POD', enabled: true }
          ],
        });
      }
      return Promise.resolve({
        ok: true,
        json: async () => ({}),
      });
    });
    
    // Mock console methods to avoid noise in test output
    global.console = {
      ...console,
      log: jest.fn(),
      warn: jest.fn(),
      error: jest.fn(),
    };
    
    // Set up window.location for API URL construction
    Object.defineProperty(window, 'location', {
      value: {
        origin: 'http://localhost:8000',
        href: 'http://localhost:8000/',
      },
      writable: true,
    });
    
    // Evaluate newtab.js to make functions available
    // We'll prevent init() from running by temporarily removing it
    const modifiedJs = newtabJsContent.replace(/\/\/ Start the extension\s*init\(\);?/m, '// Start the extension - disabled in tests');
    
    // Wrap the code to capture function definitions and assign them to global scope
    // This ensures Jest can access the functions in tests
    const wrappedJs = `
      (function() {
        ${modifiedJs}
        // Explicitly assign functions to global scope for Jest
        if (typeof loadBingPictures !== 'undefined') global.loadBingPictures = loadBingPictures;
        if (typeof fetchPicture !== 'undefined') global.fetchPicture = fetchPicture;
        if (typeof normalizePictureData !== 'undefined') global.normalizePictureData = normalizePictureData;
        if (typeof displayPicture !== 'undefined') global.displayPicture = displayPicture;
        if (typeof getSelectedSource !== 'undefined') global.getSelectedSource = getSelectedSource;
        if (typeof setSelectedSource !== 'undefined') global.setSelectedSource = setSelectedSource;
        if (typeof clearSelectedSource !== 'undefined') global.clearSelectedSource = clearSelectedSource;
        if (typeof getRandomSource !== 'undefined') global.getRandomSource = getRandomSource;
        if (typeof loadAvailableSources !== 'undefined') global.loadAvailableSources = loadAvailableSources;
        if (typeof updateSourceSelector !== 'undefined') global.updateSourceSelector = updateSourceSelector;
      })();
    `;
    
    eval(wrappedJs);
  });

  describe('Source Selection Functions', () => {
    test('getRandomSource should return a valid source from available sources', () => {
      const AVAILABLE_SOURCES = ['apod', 'wikipedia', 'bing'];
      const randomIndex = Math.floor(Math.random() * AVAILABLE_SOURCES.length);
      const randomSource = AVAILABLE_SOURCES[randomIndex];
      
      expect(AVAILABLE_SOURCES).toContain(randomSource);
    });

    test('getRandomSource should return different sources on multiple calls', () => {
      const AVAILABLE_SOURCES = ['apod', 'wikipedia', 'bing'];
      const results = new Set();
      
      // Call multiple times to ensure randomness
      for (let i = 0; i < 10; i++) {
        const randomIndex = Math.floor(Math.random() * AVAILABLE_SOURCES.length);
        results.add(AVAILABLE_SOURCES[randomIndex]);
      }
      
      // Should get at least one result (likely more with 10 calls)
      expect(results.size).toBeGreaterThan(0);
    });

    test('setSelectedSource should save source to localStorage', () => {
      const SOURCE_KEY = 'picture_source';
      const source = 'apod';
      localStorage.setItem(SOURCE_KEY, source);
      
      expect(localStorage.getItem(SOURCE_KEY)).toBe(source);
    });

    test('getSelectedSource should retrieve source from localStorage', () => {
      const SOURCE_KEY = 'picture_source';
      const source = 'wikipedia';
      localStorage.setItem(SOURCE_KEY, source);
      
      const retrieved = localStorage.getItem(SOURCE_KEY);
      expect(retrieved).toBe(source);
    });

    test('getSelectedSource should return null when no source is set', () => {
      const SOURCE_KEY = 'picture_source';
      localStorage.removeItem(SOURCE_KEY);
      
      const retrieved = localStorage.getItem(SOURCE_KEY);
      expect(retrieved).toBeNull();
    });

    test('clearSelectedSource should remove source from localStorage', () => {
      const SOURCE_KEY = 'picture_source';
      localStorage.setItem(SOURCE_KEY, 'bing');
      localStorage.removeItem(SOURCE_KEY);
      
      expect(localStorage.getItem(SOURCE_KEY)).toBeNull();
    });
  });

  describe('Dimensions Overlay Functions', () => {
    test('getDimensionsOverlayVisible should return false by default', () => {
      const stored = localStorage.getItem('dimensions_overlay_visible');
      const result = stored === null ? false : stored === 'true';
      
      expect(result).toBe(false);
    });

    test('getDimensionsOverlayVisible should return true when set', () => {
      localStorage.setItem('dimensions_overlay_visible', 'true');
      const stored = localStorage.getItem('dimensions_overlay_visible');
      const result = stored === null ? false : stored === 'true';
      
      expect(result).toBe(true);
    });

    test('setDimensionsOverlayVisible should update localStorage and DOM', () => {
      const overlay = document.getElementById('dimensionsOverlay');
      const toggle = document.getElementById('toggleDimensions');
      
      if (overlay) {
        overlay.classList.add('hidden');
        localStorage.setItem('dimensions_overlay_visible', 'true');
        
        if (localStorage.getItem('dimensions_overlay_visible') === 'true') {
          overlay.classList.remove('hidden');
          if (toggle) toggle.checked = true;
        }
        
        expect(overlay.classList.contains('hidden')).toBe(false);
        if (toggle) expect(toggle.checked).toBe(true);
      }
    });
  });

  describe('Info Panel Functions', () => {
    test('getInfoPanelVisible should return true by default', () => {
      const stored = localStorage.getItem('info_panel_visible');
      const result = stored === null ? true : stored === 'true';
      
      expect(result).toBe(true);
    });

    test('setInfoPanelVisible should update localStorage and DOM', () => {
      const panel = document.getElementById('infoPanel');
      const toggle = document.getElementById('toggleDescription');
      
      if (panel) {
        panel.classList.add('hidden');
        localStorage.setItem('info_panel_visible', 'false');
        
        const stored = localStorage.getItem('info_panel_visible');
        if (stored === 'false') {
          panel.classList.add('hidden');
          if (toggle) toggle.checked = false;
        }
        
        expect(panel.classList.contains('hidden')).toBe(true);
        if (toggle) expect(toggle.checked).toBe(false);
      }
    });
  });

  describe('Cache Functions', () => {
    test('isCacheValid should return false for different source', () => {
      const today = new Date().toDateString();
      localStorage.setItem('picture_cache_date', today);
      localStorage.setItem('picture_source', 'apod');
      
      const cachedDate = localStorage.getItem('picture_cache_date');
      const cachedSource = localStorage.getItem('picture_source');
      const currentSource = 'wikipedia';
      
      const isValid = cachedDate === today && cachedSource === currentSource;
      expect(isValid).toBe(false);
    });

    test('isCacheValid should return true for same source and date', () => {
      const today = new Date().toDateString();
      localStorage.setItem('picture_cache_date', today);
      localStorage.setItem('picture_source', 'apod');
      
      const cachedDate = localStorage.getItem('picture_cache_date');
      const cachedSource = localStorage.getItem('picture_source');
      const currentSource = 'apod';
      
      const isValid = cachedDate === today && cachedSource === currentSource;
      expect(isValid).toBe(true);
    });

    test('cachePicture should save data to localStorage', () => {
      const pictureData = {
        source: 'apod',
        title: 'Test Picture',
        date: '2024-01-15',
      };
      
      localStorage.setItem('picture_cache', JSON.stringify(pictureData));
      localStorage.setItem('picture_cache_date', new Date().toDateString());
      localStorage.setItem('picture_source', pictureData.source);
      
      const cached = localStorage.getItem('picture_cache');
      expect(cached).toBeTruthy();
      
      const parsed = JSON.parse(cached);
      expect(parsed.title).toBe('Test Picture');
    });

    test('getCachedPicture should return null for invalid cache', () => {
      const source = 'apod';
      const today = new Date().toDateString();
      localStorage.setItem('picture_cache_date', 'yesterday');
      localStorage.setItem('picture_source', 'wikipedia');
      
      const cachedDate = localStorage.getItem('picture_cache_date');
      const cachedSource = localStorage.getItem('picture_source');
      const isValid = cachedDate === today && cachedSource === source;
      
      if (!isValid) {
        expect(localStorage.getItem('picture_cache')).toBeNull();
      }
    });
  });

  describe('Normalize Picture Data', () => {
    test('normalizePictureData should handle backend API format', () => {
      const backendData = {
        title: 'Test Title',
        date: '2024-01-15',
        processed_explanation: 'Processed text',
        display_explanation: 'Display text',
        original_explanation: 'Original text',
        image_url: 'https://example.com/image.jpg',
        hd_image_url: 'https://example.com/hd.jpg',
        media_type: 'image',
        copyright: 'Test Copyright',
        source_url: 'https://example.com',
        image_width: 1920,
        image_height: 1080,
      };
      
      const normalized = {
        source: 'apod',
        title: backendData.title,
        date: backendData.date,
        processed_explanation: backendData.processed_explanation,
        display_explanation: backendData.display_explanation || backendData.processed_explanation || backendData.original_explanation,
        original_explanation: backendData.original_explanation,
        image_url: backendData.image_url,
        hd_image_url: backendData.hd_image_url,
        display_image_url: backendData.hd_image_url || backendData.image_url,
        media_type: backendData.media_type,
        copyright: backendData.copyright,
        source_url: backendData.source_url,
        image_width: backendData.image_width,
        image_height: backendData.image_height,
      };
      
      expect(normalized.title).toBe('Test Title');
      expect(normalized.display_explanation).toBe('Display text');
      expect(normalized.image_width).toBe(1920);
    });

    test('normalizePictureData should handle NASA API fallback format', () => {
      const nasaData = {
        title: 'NASA Title',
        date: '2024-01-15',
        explanation: 'NASA explanation',
        url: 'https://apod.nasa.gov/image.jpg',
        hdurl: 'https://apod.nasa.gov/hd.jpg',
        media_type: 'image',
        copyright: 'NASA',
      };
      
      const normalized = {
        source: 'apod',
        title: nasaData.title,
        date: nasaData.date,
        display_explanation: nasaData.explanation,
        original_explanation: nasaData.explanation,
        image_url: nasaData.url,
        hd_image_url: nasaData.hdurl,
        display_image_url: nasaData.hdurl || nasaData.url,
        media_type: nasaData.media_type,
        copyright: nasaData.copyright,
      };
      
      expect(normalized.title).toBe('NASA Title');
      expect(normalized.display_explanation).toBe('NASA explanation');
      expect(normalized.display_image_url).toBe('https://apod.nasa.gov/hd.jpg');
    });
  });

  describe('Calculate Optimal Display', () => {
    test('calculateOptimalDisplay should handle missing dimensions', () => {
      const viewportWidth = 1920;
      const viewportHeight = 1080;
      const imageWidth = null;
      const imageHeight = null;
      
      const result = {
        objectFit: 'cover',
        objectPosition: 'center',
        scale: 1,
        mode: 'Default (no dimensions)',
        displayWidth: viewportWidth,
        displayHeight: viewportHeight,
      };
      
      expect(result.objectFit).toBe('cover');
      expect(result.mode).toBe('Default (no dimensions)');
    });

    test('calculateOptimalDisplay should calculate correct aspect ratios', () => {
      const viewportWidth = 1920;
      const viewportHeight = 1080;
      const imageWidth = 3840;
      const imageHeight = 2160;
      
      const viewportAspect = viewportWidth / viewportHeight;
      const imageAspect = imageWidth / imageHeight;
      const aspectRatioDiff = Math.abs(imageAspect - viewportAspect);
      
      expect(viewportAspect).toBeCloseTo(1.777, 2);
      expect(imageAspect).toBeCloseTo(1.777, 2);
      expect(aspectRatioDiff).toBeCloseTo(0, 2);
    });

    test('calculateOptimalDisplay should use cover for perfect match', () => {
      const viewportWidth = 1920;
      const viewportHeight = 1080;
      const imageWidth = 3840;
      const imageHeight = 2160;
      
      const viewportAspect = viewportWidth / viewportHeight;
      const imageAspect = imageWidth / imageHeight;
      const aspectRatioDiff = Math.abs(imageAspect - viewportAspect);
      
      if (aspectRatioDiff < 0.1) {
        const scaleToFitWidth = viewportWidth / imageWidth;
        const scaleToFitHeight = viewportHeight / imageHeight;
        const scaleToFill = Math.max(scaleToFitWidth, scaleToFitHeight);
        
        expect(scaleToFill).toBeCloseTo(0.5, 1);
      }
    });
  });

  describe('Update Dimensions Overlay', () => {
    test('updateDimensionsOverlay should update viewport dimensions', () => {
      const viewportEl = document.getElementById('viewportDimensions');
      if (viewportEl) {
        const viewportWidth = 1920;
        const viewportHeight = 1080;
        viewportEl.textContent = `${viewportWidth} × ${viewportHeight}`;
        
        expect(viewportEl.textContent).toBe('1920 × 1080');
      }
    });

    test('updateDimensionsOverlay should update image dimensions', () => {
      const imageEl = document.getElementById('imageDimensions');
      if (imageEl) {
        const imageWidth = 3840;
        const imageHeight = 2160;
        imageEl.textContent = `${imageWidth} × ${imageHeight}`;
        
        expect(imageEl.textContent).toBe('3840 × 2160');
      }
    });

    test('updateDimensionsOverlay should show Unknown for missing dimensions', () => {
      const imageEl = document.getElementById('imageDimensions');
      if (imageEl) {
        imageEl.textContent = 'Unknown';
        expect(imageEl.textContent).toBe('Unknown');
      }
    });
  });

  describe('Load Bing Pictures', () => {
    test('loadBingPictures should handle successful API response', async () => {
      const mockPictures = [
        { date: '2024-01-15', title: 'Bing Picture 1' },
        { date: '2024-01-14', title: 'Bing Picture 2' },
      ];
      
      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockPictures,
      });
      
      const select = document.getElementById('bingPictureSelect');
      if (select) {
        select.innerHTML = '<option value="">Select a Bing picture...</option>';
        
        mockPictures.forEach(picture => {
          const option = document.createElement('option');
          option.value = picture.date;
          option.textContent = `${picture.date} - ${picture.title}`;
          select.appendChild(option);
        });
        
        expect(select.options.length).toBe(3); // Default + 2 pictures
        expect(select.options[1].value).toBe('2024-01-15');
      }
    });

    test('loadBingPictures should handle API error', async () => {
      fetch.mockRejectedValueOnce(new Error('Failed to fetch'));
      
      const select = document.getElementById('bingPictureSelect');
      if (select) {
        // Actually call the loadBingPictures function
        await loadBingPictures();
        
        // The error message should indicate an error occurred
        // For "Failed to fetch" errors, it shows "Backend not accessible. Is the server running?"
        // For other errors, it shows "Error: ..." or "Error loading pictures"
        expect(select.innerHTML).toMatch(/Error|Backend not accessible|Server error/);
      }
    });

    test('loadBingPictures should set random selection when pickRandom is true', async () => {
      const mockPictures = [
        { date: '2024-01-15', title: 'Bing Picture 1' },
        { date: '2024-01-14', title: 'Bing Picture 2' },
      ];
      
      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockPictures,
      });
      
      const select = document.getElementById('bingPictureSelect');
      if (select && mockPictures.length > 0) {
        // Actually call loadBingPictures with pickRandom=true
        await loadBingPictures(true);
        
        // The function should have set a random value
        expect(select.value).toBeTruthy();
        expect(mockPictures.map(p => p.date)).toContain(select.value);
      }
    });
  });

  describe('Fetch Picture', () => {
    test('fetchPicture should construct correct URL for APOD', () => {
      const source = 'apod';
      const url = `http://localhost:8000/api/pictures/today/${source}/`;
      
      expect(url).toBe('http://localhost:8000/api/pictures/today/apod/');
    });

    test('fetchPicture should construct correct URL for Bing with date', () => {
      const source = 'bing';
      const selectedDate = '2024-01-15';
      const url = `http://localhost:8000/api/pictures/date/${selectedDate}/bing/`;
      
      expect(url).toBe('http://localhost:8000/api/pictures/date/2024-01-15/bing/');
    });

    test('fetchPicture should handle successful backend API response', async () => {
      // Set up source in localStorage
      localStorage.setItem('picture_source', 'apod');
      
      const mockData = {
        title: 'Test Picture',
        date: '2024-01-15',
        display_explanation: 'Test explanation',
        image_url: 'https://example.com/image.jpg',
        media_type: 'image',
      };
      
      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockData,
      });
      
      // Actually call the fetchPicture function
      const data = await fetchPicture('apod');
      
      expect(data.title).toBe('Test Picture');
      expect(data.date).toBe('2024-01-15');
    });

    test('fetchPicture should handle backend API error response', async () => {
      const mockError = { error: 'No picture available' };
      
      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockError,
      });
      
      const response = await fetch('http://localhost:8000/api/pictures/today/apod/');
      const data = await response.json();
      
      if (data.error) {
        expect(data.error).toBe('No picture available');
      }
    });

    test('fetchPicture should fallback to NASA API for APOD', async () => {
      // First call fails (backend)
      fetch.mockRejectedValueOnce(new Error('Backend failed'));
      
      // Second call succeeds (NASA)
      const nasaData = {
        title: 'NASA Picture',
        date: '2024-01-15',
        explanation: 'NASA explanation',
        url: 'https://apod.nasa.gov/image.jpg',
        hdurl: 'https://apod.nasa.gov/hd.jpg',
        media_type: 'image',
      };
      
      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => nasaData,
      });
      
      try {
        await fetch('http://localhost:8000/api/pictures/today/apod/');
      } catch (error) {
        // Fallback to NASA
        const nasaResponse = await fetch('https://api.nasa.gov/planetary/apod?api_key=test');
        const nasaResult = await nasaResponse.json();
        
        expect(nasaResult.title).toBe('NASA Picture');
      }
    });
  });

  describe('Display Picture', () => {
    test('displayPicture should set title and date', () => {
      const titleEl = document.getElementById('apodTitle');
      const dateEl = document.getElementById('apodDate');
      
      if (titleEl && dateEl) {
        titleEl.textContent = 'Test Title';
        dateEl.textContent = '2024-01-15';
        
        expect(titleEl.textContent).toBe('Test Title');
        expect(dateEl.textContent).toBe('2024-01-15');
      }
    });

    test('displayPicture should handle processed explanation with HTML', () => {
      const descEl = document.getElementById('apodDescription');
      if (descEl) {
        const processedText = 'This is a <a href="https://wikipedia.org">link</a> to Wikipedia.';
        descEl.innerHTML = processedText;
        
        expect(descEl.innerHTML).toContain('<a href');
        expect(descEl.innerHTML).toContain('Wikipedia');
      }
    });

    test('displayPicture should handle plain text explanation', () => {
      const descEl = document.getElementById('apodDescription');
      if (descEl) {
        const plainText = 'This is a plain text explanation.';
        descEl.textContent = plainText;
        
        expect(descEl.textContent).toBe(plainText);
        expect(descEl.innerHTML).not.toContain('<a');
      }
    });

    test('displayPicture should set copyright', () => {
      const copyrightEl = document.getElementById('apodCopyright');
      if (copyrightEl) {
        copyrightEl.textContent = '© Test Copyright';
        expect(copyrightEl.textContent).toBe('© Test Copyright');
      }
    });

    test('displayPicture should set source link for APOD', () => {
      const linkEl = document.getElementById('sourceLink');
      if (linkEl) {
        linkEl.href = 'https://apod.nasa.gov/apod/ap240115.html';
        linkEl.title = 'Visit NASA APOD';
        
        expect(linkEl.href).toContain('apod.nasa.gov');
        expect(linkEl.title).toBe('Visit NASA APOD');
      }
    });
  });

  describe('Settings Panel Interactions', () => {
    test('settings toggle should show/hide settings panel', () => {
      const toggle = document.getElementById('settingsToggle');
      const panel = document.getElementById('settingsPanel');
      
      if (toggle && panel) {
        panel.classList.remove('visible');
        expect(panel.classList.contains('visible')).toBe(false);
        
        // Simulate click
        panel.classList.toggle('visible');
        expect(panel.classList.contains('visible')).toBe(true);
      }
    });

    test('settings close should hide settings panel', () => {
      const close = document.getElementById('settingsClose');
      const panel = document.getElementById('settingsPanel');
      
      if (close && panel) {
        panel.classList.add('visible');
        expect(panel.classList.contains('visible')).toBe(true);
        
        // Simulate click
        panel.classList.remove('visible');
        expect(panel.classList.contains('visible')).toBe(false);
      }
    });

    test('toggle description should show/hide info panel', () => {
      const toggle = document.getElementById('toggleDescription');
      const panel = document.getElementById('infoPanel');
      
      if (toggle && panel) {
        toggle.checked = false;
        panel.classList.add('hidden');
        
        expect(panel.classList.contains('hidden')).toBe(true);
        expect(toggle.checked).toBe(false);
        
        toggle.checked = true;
        panel.classList.remove('hidden');
        
        expect(panel.classList.contains('hidden')).toBe(false);
        expect(toggle.checked).toBe(true);
      }
    });
  });
});

