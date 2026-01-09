// NASA APOD API configuration
const NASA_API_KEY = 'HDin5BLUkoDRqGGDaJVQpOuF6NR26GXGlWV3jKkE'
const APOD_API_URL = 'https://api.nasa.gov/planetary/apod';

// Cache key for localStorage
const CACHE_KEY = 'picture_cache';
const CACHE_DATE_KEY = 'picture_cache_date';
const SOURCE_KEY = 'picture_source';  // Store selected source
const DIMENSIONS_VISIBLE_KEY = 'dimensions_overlay_visible';  // Store dimensions overlay visibility
const INFO_PANEL_VISIBLE_KEY = 'info_panel_visible';  // Store info panel visibility
const RANDOM_ON_NEW_TAB_KEY = 'random_on_new_tab';  // Store random on new tab preference

// API URL configuration - loaded from config.js
// config.js is set to localhost for development
// config.production.js is used for production builds
const BACKEND_API_URL = CONFIG.BACKEND_API_URL;
const PICTURES_API_URL = `${BACKEND_API_URL}/pictures`;

// Available sources - will be loaded dynamically from API
let AVAILABLE_SOURCES = ['apod', 'wikipedia', 'bing']; // Fallback if API fails
const SOURCES_CACHE_KEY = 'available_sources_cache';
const SOURCES_CACHE_DATE_KEY = 'available_sources_cache_date';

// Default source (will be randomly selected if not set)
const DEFAULT_SOURCE = 'apod';

// DOM elements
const apodImage = document.getElementById('apodImage');
const apodTitle = document.getElementById('apodTitle');
const apodDate = document.getElementById('apodDate');
const apodDescription = document.getElementById('apodDescription');
const apodCopyright = document.getElementById('apodCopyright');
const sourceLink = document.getElementById('sourceLink');
const infoPanel = document.getElementById('infoPanel');
const loading = document.getElementById('loading');
const loadingText = document.getElementById('loadingText');
const sourceSelect = document.getElementById('sourceSelect');
const viewportDimensions = document.getElementById('viewportDimensions');
const imageDimensions = document.getElementById('imageDimensions');
const scaleInfo = document.getElementById('scaleInfo');
const displayMode = document.getElementById('displayMode');
const dimensionsOverlay = document.getElementById('dimensionsOverlay');
const bingPictureSelect = document.getElementById('bingPictureSelect');
const BING_PICTURE_KEY = 'bing_picture_date';  // Store selected Bing picture date

// Settings panel elements
const settingsToggle = document.getElementById('settingsToggle');
const settingsPanel = document.getElementById('settingsPanel');
const settingsClose = document.getElementById('settingsClose');
const toggleDescription = document.getElementById('toggleDescription');
const toggleRandom = document.getElementById('toggleRandom');
const toggleDimensions = document.getElementById('toggleDimensions');

// Initialize source selector - will be updated when sources are loaded
// Temporary initialization to show loading state
if (sourceSelect) {
    sourceSelect.innerHTML = '<option value="">Loading sources...</option>';
    sourceSelect.disabled = true;
}

// Initialize dimensions overlay visibility
function getDimensionsOverlayVisible() {
    const stored = localStorage.getItem(DIMENSIONS_VISIBLE_KEY);
    return stored === null ? false : stored === 'true'; // Default to hidden
}

function setDimensionsOverlayVisible(visible) {
    localStorage.setItem(DIMENSIONS_VISIBLE_KEY, visible.toString());
    if (dimensionsOverlay) {
        if (visible) {
            dimensionsOverlay.classList.remove('hidden');
        } else {
            dimensionsOverlay.classList.add('hidden');
        }
    }
    // Update settings toggle checkbox
    if (toggleDimensions) {
        toggleDimensions.checked = visible;
    }
}

// Initialize settings panel
function initSettings() {
    // Initialize toggles from localStorage
    if (toggleDescription) {
        toggleDescription.checked = getInfoPanelVisible();
    }
    if (toggleRandom) {
        // Default to true if not set
        const stored = localStorage.getItem(RANDOM_ON_NEW_TAB_KEY);
        const randomEnabled = stored === null ? true : stored === 'true';
        toggleRandom.checked = randomEnabled;
        
        // Enable/disable source selector based on random setting
        if (sourceSelect) {
            sourceSelect.disabled = randomEnabled;
        }
    }
    if (toggleDimensions) {
        toggleDimensions.checked = getDimensionsOverlayVisible();
    }
    
    // Initialize dimensions overlay visibility
    if (dimensionsOverlay) {
        const isVisible = getDimensionsOverlayVisible();
        setDimensionsOverlayVisible(isVisible);
    }
}

// Initialize settings on page load
initSettings();

// Handle source change
sourceSelect.addEventListener('change', async (e) => {
    // Don't allow changes if random on new tab is enabled
    const randomEnabled = localStorage.getItem(RANDOM_ON_NEW_TAB_KEY) === 'true';
    if (randomEnabled) {
        // Revert the change - random mode should ignore manual selection
        const randomSource = getRandomSource();
        if (randomSource) {
            e.target.value = randomSource;
        }
        return;
    }
    
    const newSource = e.target.value;
    
    // Validate the source is still enabled
    if (!AVAILABLE_SOURCES.includes(newSource)) {
        // Source was disabled - refresh sources and select first available
        await updateSourceSelector(true);
        if (AVAILABLE_SOURCES.length > 0) {
            e.target.value = AVAILABLE_SOURCES[0];
            setSelectedSource(AVAILABLE_SOURCES[0]);
        } else {
            showError('No picture sources are currently enabled.');
            return;
        }
        return;
    }
    
    setSelectedSource(newSource);
    
    // Show/hide Bing picture selector
    if (bingPictureSelect) {
        if (newSource === 'bing') {
            bingPictureSelect.classList.remove('hidden');
            await loadBingPictures();
        } else {
            bingPictureSelect.classList.add('hidden');
            bingPictureSelect.value = '';
        }
    }
    
    // Clear cache to force fetch of new source
    localStorage.removeItem(CACHE_KEY);
    localStorage.removeItem(CACHE_DATE_KEY);
    // Show loading screen
    loading.classList.remove('hidden');
    const sourceName = newSource === 'apod' ? 'NASA APOD' : newSource === 'wikipedia' ? 'Wikipedia POD' : 'Bing POD';
    loadingText.textContent = `Loading ${sourceName}...`;
    // Reload picture
    init();
});

// Handle Bing picture selection
if (bingPictureSelect) {
    bingPictureSelect.addEventListener('change', (e) => {
        const selectedDate = e.target.value;
        if (selectedDate) {
            localStorage.setItem(BING_PICTURE_KEY, selectedDate);
            // Clear cache to force fetch of selected picture
            localStorage.removeItem(CACHE_KEY);
            localStorage.removeItem(CACHE_DATE_KEY);
            // Show loading screen
            loading.classList.remove('hidden');
            loadingText.textContent = 'Loading Bing picture...';
            // Reload picture
            init();
        }
    });
}

// Initialize info panel visibility
function getInfoPanelVisible() {
    const stored = localStorage.getItem(INFO_PANEL_VISIBLE_KEY);
    return stored === null ? true : stored === 'true'; // Default to visible
}

function setInfoPanelVisible(visible) {
    localStorage.setItem(INFO_PANEL_VISIBLE_KEY, visible.toString());
    if (infoPanel) {
        if (visible) {
            infoPanel.classList.remove('hidden');
        } else {
            infoPanel.classList.add('hidden');
        }
    }
    // Update toggle checkbox
    if (toggleDescription) {
        toggleDescription.checked = visible;
    }
}

// Initialize info panel on page load
if (infoPanel) {
    const isVisible = getInfoPanelVisible();
    setInfoPanelVisible(isVisible);
}

// Settings panel handlers
if (settingsToggle) {
    settingsToggle.addEventListener('click', async (e) => {
        e.stopPropagation();
        if (settingsPanel) {
            const isOpening = !settingsPanel.classList.contains('visible');
            settingsPanel.classList.toggle('visible');
            
            // Refresh sources when opening settings panel to show latest enabled/disabled sources
            if (isOpening) {
                await updateSourceSelector(true);
            }
        }
    });
}

if (settingsClose) {
    settingsClose.addEventListener('click', (e) => {
        e.stopPropagation();
        if (settingsPanel) {
            settingsPanel.classList.remove('visible');
        }
    });
}

// Close settings panel when clicking outside
document.addEventListener('click', (e) => {
    if (settingsPanel && settingsPanel.classList.contains('visible')) {
        if (!settingsPanel.contains(e.target) && !settingsToggle.contains(e.target)) {
            settingsPanel.classList.remove('visible');
        }
    }
});

// Toggle description display
if (toggleDescription) {
    toggleDescription.addEventListener('change', (e) => {
        setInfoPanelVisible(e.target.checked);
    });
}

// Toggle random on new tab
if (toggleRandom) {
    toggleRandom.addEventListener('change', (e) => {
        const randomEnabled = e.target.checked;
        localStorage.setItem(RANDOM_ON_NEW_TAB_KEY, randomEnabled.toString());
        
        // Enable/disable source selector based on random setting
        if (sourceSelect) {
            sourceSelect.disabled = randomEnabled;
        }
        
        // If random is enabled, clear any stored source and Bing picture date
        // so it picks random on next tab
        if (randomEnabled) {
            clearSelectedSource();
            localStorage.removeItem(BING_PICTURE_KEY);
        }
        
        // Reload to apply the change
        init();
    });
}

// Toggle dimensions display
if (toggleDimensions) {
    toggleDimensions.addEventListener('change', (e) => {
        setDimensionsOverlayVisible(e.target.checked);
    });
}

// Load available sources from API
// forceRefresh: if true, bypasses cache and fetches fresh data
async function loadAvailableSources(forceRefresh = false) {
    const now = Date.now();
    // Reduced cache time to 30 seconds for faster detection of admin changes
    // In development (localhost), use even shorter cache (10 seconds) for immediate updates
    const isLocalhost = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
    const cacheTime = isLocalhost ? 10 * 1000 : 30 * 1000; // 10 seconds for localhost, 30 seconds for production
    
    // Check cache first (unless forcing refresh)
    if (!forceRefresh) {
        const cachedDate = localStorage.getItem(SOURCES_CACHE_DATE_KEY);
        const cachedSources = localStorage.getItem(SOURCES_CACHE_KEY);
        
        if (cachedDate && cachedSources && (now - parseInt(cachedDate)) < cacheTime) {
            try {
                const sources = JSON.parse(cachedSources);
                // Only include enabled sources
                const enabledSources = sources.filter(s => s.enabled !== false);
                AVAILABLE_SOURCES = enabledSources.map(s => s.value);
                
                // Validate current selection is still available (even with cache)
                // Check stored source directly to avoid recursion
                const storedSource = localStorage.getItem(SOURCE_KEY);
                if (storedSource && !AVAILABLE_SOURCES.includes(storedSource)) {
                    // Current source was disabled - force refresh to get latest state
                    console.log('Current source disabled, refreshing sources...');
                    return await loadAvailableSources(true);
                }
                
                return enabledSources;
            } catch (e) {
                // Cache corrupted, continue to fetch
            }
        }
    }
    
    try {
        const response = await fetch(`${PICTURES_API_URL}/sources/`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const sources = await response.json();
        // Only include enabled sources
        const enabledSources = sources.filter(s => s.enabled !== false);
        AVAILABLE_SOURCES = enabledSources.map(s => s.value);
        
        // Cache the sources (including disabled ones for reference)
        localStorage.setItem(SOURCES_CACHE_KEY, JSON.stringify(sources));
        localStorage.setItem(SOURCES_CACHE_DATE_KEY, now.toString());
        
        return enabledSources;
    } catch (error) {
        console.error('Failed to load sources from API:', error);
        // Use cached sources if available (even if expired)
        const cachedSources = localStorage.getItem(SOURCES_CACHE_KEY);
        if (cachedSources) {
            try {
                const sources = JSON.parse(cachedSources);
                const enabledSources = sources.filter(s => s.enabled !== false);
                AVAILABLE_SOURCES = enabledSources.map(s => s.value);
                console.log('Using cached sources (API unavailable)');
                return enabledSources;
            } catch (e) {
                // Cache corrupted
            }
        }
        
        // Last resort: return empty array - extension will show error
        console.error('No sources available - API failed and no cache');
        AVAILABLE_SOURCES = [];
        return [];
    }
}

// Update source selector dropdown with available sources
async function updateSourceSelector(forceRefresh = false) {
    const sources = await loadAvailableSources(forceRefresh);
    
    if (!sourceSelect) return;
    
    // Store current selection
    const currentValue = sourceSelect.value;
    
    // Clear existing options
    sourceSelect.innerHTML = '';
    
    // Check if we have any sources
    if (sources.length === 0) {
        sourceSelect.innerHTML = '<option value="">No sources available</option>';
        sourceSelect.disabled = true;
        return;
    }
    
    sourceSelect.disabled = false;
    
    // Add options for each enabled source
    sources.forEach(source => {
        if (source.enabled !== false) {
            const option = document.createElement('option');
            option.value = source.value;
            option.textContent = source.label || source.value;
            sourceSelect.appendChild(option);
        }
    });
    
    // Restore selection if it's still valid, otherwise select first available
    if (currentValue && AVAILABLE_SOURCES.includes(currentValue)) {
        sourceSelect.value = currentValue;
    } else if (AVAILABLE_SOURCES.length > 0) {
        sourceSelect.value = AVAILABLE_SOURCES[0];
        // Clear stored source if it's no longer available
        if (currentValue && !AVAILABLE_SOURCES.includes(currentValue)) {
            localStorage.removeItem(SOURCE_KEY);
            // Also clear Bing picture selection if Bing was disabled
            if (currentValue === 'bing') {
                localStorage.removeItem(BING_PICTURE_KEY);
            }
        }
    }
}

// Get selected source from localStorage (if user has manually selected)
// Returns null if no manual selection has been made
// Validates that the source is still enabled
function getSelectedSource() {
    const stored = localStorage.getItem(SOURCE_KEY);
    if (!stored) {
        return null;
    }
    
    // Validate that the stored source is still available
    if (AVAILABLE_SOURCES.length > 0 && !AVAILABLE_SOURCES.includes(stored)) {
        // Source is no longer enabled - clear it
        localStorage.removeItem(SOURCE_KEY);
        if (stored === 'bing') {
            localStorage.removeItem(BING_PICTURE_KEY);
        }
        return null;
    }
    
    return stored;
}

// Get a random source from available sources
function getRandomSource() {
    if (AVAILABLE_SOURCES.length === 0) {
        // No sources available - return null to trigger error handling
        return null;
    }
    const randomIndex = Math.floor(Math.random() * AVAILABLE_SOURCES.length);
    return AVAILABLE_SOURCES[randomIndex];
}

// Set selected source (saves to localStorage - used when user manually selects)
function setSelectedSource(source) {
    localStorage.setItem(SOURCE_KEY, source);
}

// Clear selected source (for random selection on each new tab)
function clearSelectedSource() {
    localStorage.removeItem(SOURCE_KEY);
}

// Calculate optimal display settings based on viewport and image dimensions
// General algorithm that considers multiple display strategies
function calculateOptimalDisplay(viewportWidth, viewportHeight, imageWidth, imageHeight) {
    if (!imageWidth || !imageHeight) {
        return {
            objectFit: 'cover',
            objectPosition: 'center',
            scale: 1,
            mode: 'Default (no dimensions)',
            displayWidth: viewportWidth,
            displayHeight: viewportHeight
        };
    }
    
    // Calculate aspect ratios
    const viewportAspect = viewportWidth / viewportHeight;
    const imageAspect = imageWidth / imageHeight;
    const aspectRatioDiff = Math.abs(imageAspect - viewportAspect);
    
    // Strategy 1: Square crop (center crop to square, then scale to fit)
    // This works well for images that are much wider or taller than viewport
    const viewportIsWide = viewportAspect > 1;
    const imageIsWide = imageAspect > 1;
    
    // Calculate square dimensions based on viewport
    const squareSize = Math.min(viewportWidth, viewportHeight);
    const squareAspect = 1; // 1:1
    
    // Strategy 2: Smart crop - crop to match viewport aspect ratio more closely
    // Strategy 3: Contain - show full image with letterboxing
    
    let objectFit = 'cover';
    let objectPosition = 'center';
    let mode = 'Cover';
    let scale = 1;
    let displayWidth = viewportWidth;
    let displayHeight = viewportHeight;
    
    // Calculate scaling factors
    const scaleToFitWidth = viewportWidth / imageWidth;
    const scaleToFitHeight = viewportHeight / imageHeight;
    const scaleToFill = Math.max(scaleToFitWidth, scaleToFitHeight); // For cover
    const scaleToContain = Math.min(scaleToFitWidth, scaleToFitHeight); // For contain
    
    // Decision algorithm:
    // 1. If viewport is roughly square and image is very wide/tall, use square crop
    if (viewportAspect >= 0.9 && viewportAspect <= 1.1) {
        // Viewport is roughly square
        if (imageAspect > 1.5 || imageAspect < 0.67) {
            // Image is very wide or very tall - use square crop
            objectFit = 'cover';
            objectPosition = 'center';
            mode = 'Square Crop';
            scale = scaleToFill;
            displayWidth = squareSize;
            displayHeight = squareSize;
        } else {
            // Image aspect is closer to square - use cover
            objectFit = 'cover';
            mode = 'Cover (Square Viewport)';
            scale = scaleToFill;
        }
    }
    // 2. If viewport is wide and image is tall (or vice versa), use contain to show full image
    else if ((viewportIsWide && !imageIsWide) || (!viewportIsWide && imageIsWide)) {
        // Portrait image in landscape viewport (or vice versa) - use contain to show full image
        objectFit = 'contain';
        objectPosition = 'center';
        scale = scaleToContain;
        if (viewportIsWide && !imageIsWide) {
            // Landscape viewport, portrait image - show full image with black bars on sides
            mode = 'Contain (Portrait in Landscape)';
            displayWidth = imageWidth * scaleToContain;
            displayHeight = imageHeight * scaleToContain;
        } else {
            // Portrait viewport, landscape image - show full image with black bars on top/bottom
            mode = 'Contain (Landscape in Portrait)';
            displayWidth = imageWidth * scaleToContain;
            displayHeight = imageHeight * scaleToContain;
        }
    }
    // 3. If image is much smaller than viewport, use contain to avoid upscaling
    else if (scaleToContain > 1.5) {
        objectFit = 'contain';
        mode = 'Contain (Upscale)';
        scale = scaleToContain;
        displayWidth = imageWidth * scaleToContain;
        displayHeight = imageHeight * scaleToContain;
    }
    // 4. If aspect ratios are very similar, cover works perfectly
    else if (aspectRatioDiff < 0.1) {
        objectFit = 'cover';
        mode = 'Cover (Perfect Match)';
        scale = scaleToFill;
    }
    // 5. Default: smart cover with minimal cropping
    else {
        // Calculate crop percentage
        let cropPercent = 0;
        if (imageAspect > viewportAspect) {
            const scaledHeight = viewportWidth / imageAspect;
            cropPercent = ((viewportHeight - scaledHeight) / viewportHeight) * 100;
        } else {
            const scaledWidth = viewportHeight * imageAspect;
            cropPercent = ((viewportWidth - scaledWidth) / viewportWidth) * 100;
        }
        
        if (cropPercent > 25) {
            // Significant cropping - use contain
            objectFit = 'contain';
            mode = `Contain (${cropPercent.toFixed(0)}% crop avoided)`;
            scale = scaleToContain;
        } else {
            // Minimal cropping - use cover
            objectFit = 'cover';
            mode = `Cover (${cropPercent.toFixed(0)}% cropped)`;
            scale = scaleToFill;
        }
    }
    
    return {
        objectFit,
        objectPosition,
        scale: scale.toFixed(2),
        mode,
        displayWidth: Math.round(displayWidth),
        displayHeight: Math.round(displayHeight)
    };
}

// Apply image display settings to the image element
function applyImageDisplaySettings(settings, viewportWidth, viewportHeight, imageWidth, imageHeight) {
    // Explicitly set dimensions to ensure object-fit works correctly
    apodImage.style.width = viewportWidth + 'px';
    apodImage.style.height = viewportHeight + 'px';
    apodImage.style.objectFit = settings.objectFit;
    apodImage.style.objectPosition = settings.objectPosition;
    
    // Update dimension overlay
    updateDimensionsOverlay(viewportWidth, viewportHeight, imageWidth, imageHeight, settings);
}

// Update dimensions overlay with current information
function updateDimensionsOverlay(viewportWidth, viewportHeight, imageWidth, imageHeight, settings) {
    if (viewportDimensions) {
        viewportDimensions.textContent = `${viewportWidth} × ${viewportHeight}`;
    }
    
    if (imageDimensions) {
        if (imageWidth && imageHeight) {
            imageDimensions.textContent = `${imageWidth} × ${imageHeight}`;
        } else {
            imageDimensions.textContent = 'Unknown';
        }
    }
    
    if (scaleInfo) {
        if (settings && settings.scale) {
            const scalePercent = (parseFloat(settings.scale) * 100).toFixed(0);
            scaleInfo.textContent = `${settings.scale}x (${scalePercent}%)`;
        } else {
            scaleInfo.textContent = '-';
        }
    }
    
    if (displayMode) {
        if (settings && settings.mode) {
            displayMode.textContent = settings.mode;
        } else {
            displayMode.textContent = '-';
        }
    }
}

// Handle window resize to recalculate display settings
let resizeTimeout;
window.addEventListener('resize', () => {
    clearTimeout(resizeTimeout);
    resizeTimeout = setTimeout(() => {
        // Get current picture data
        const cached = localStorage.getItem(CACHE_KEY);
        if (cached) {
            const data = JSON.parse(cached);
            const viewportWidth = window.innerWidth;
            const viewportHeight = window.innerHeight;
            
            if (data.image_width && data.image_height) {
                const displaySettings = calculateOptimalDisplay(
                    viewportWidth,
                    viewportHeight,
                    data.image_width,
                    data.image_height
                );
                applyImageDisplaySettings(displaySettings, viewportWidth, viewportHeight, data.image_width, data.image_height);
            } else {
                // Update viewport dimensions even if image dimensions aren't available
                updateDimensionsOverlay(viewportWidth, viewportHeight, null, null, null);
            }
        }
    }, 250); // Debounce resize events
});

// Fetch all available Bing pictures
async function loadBingPictures(pickRandom = false) {
    if (!bingPictureSelect) return;
    
    try {
        const response = await fetch(`${PICTURES_API_URL}/list/bing/`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const pictures = await response.json();
        
        // Clear existing options except the first one
        bingPictureSelect.innerHTML = '<option value="">Select a Bing picture...</option>';
        
        // Add all available Bing pictures
        pictures.forEach(picture => {
            const option = document.createElement('option');
            option.value = picture.date;
            option.textContent = `${picture.date} - ${picture.title}`;
            bingPictureSelect.appendChild(option);
        });
        
        // Set selected value
        const storedDate = localStorage.getItem(BING_PICTURE_KEY);
        if (pickRandom && pictures.length > 0) {
            // Random mode: pick a random picture from all available
            const randomIndex = Math.floor(Math.random() * pictures.length);
            const randomDate = pictures[randomIndex].date;
            bingPictureSelect.value = randomDate;
            // Don't save it to localStorage in random mode (so next tab gets a different random one)
        } else if (storedDate) {
            // Use stored date if available
            bingPictureSelect.value = storedDate;
        } else if (pictures.length > 0) {
            // Default to most recent (first in list)
            bingPictureSelect.value = pictures[0].date;
            localStorage.setItem(BING_PICTURE_KEY, pictures[0].date);
        }
    } catch (error) {
        console.error('Failed to load Bing pictures:', error);
        let errorMessage = 'Error loading pictures';
        
        // Provide more specific error messages
        if (error.message && error.message.includes('Failed to fetch')) {
            errorMessage = 'Backend not accessible. Is the server running?';
        } else if (error.message && error.message.includes('HTTP error')) {
            errorMessage = `Server error: ${error.message}`;
        } else if (error.message) {
            errorMessage = `Error: ${error.message}`;
        }
        
        bingPictureSelect.innerHTML = `<option value="">${errorMessage}</option>`;
    }
}

// Fetch picture data from backend API with fallback
async function fetchPicture(source = null) {
    let selectedSource = source || getSelectedSource();
    
    // Validate that the source is still enabled
    if (selectedSource && !AVAILABLE_SOURCES.includes(selectedSource)) {
        // Source is no longer enabled - switch to first available source
        if (AVAILABLE_SOURCES.length > 0) {
            selectedSource = AVAILABLE_SOURCES[0];
            setSelectedSource(selectedSource);
            if (sourceSelect) {
                sourceSelect.value = selectedSource;
            }
        } else {
            throw new Error('No picture sources are currently enabled. Please enable sources in the admin panel.');
        }
    }
    
    if (!selectedSource) {
        // No source selected and none available
        if (AVAILABLE_SOURCES.length === 0) {
            throw new Error('No picture sources are currently enabled. Please enable sources in the admin panel.');
        }
        selectedSource = AVAILABLE_SOURCES[0];
    }
    
    // For Bing, check if a specific date is selected
    let url;
    if (selectedSource === 'bing') {
        // Check localStorage first, then check the dropdown (for random mode)
        let selectedDate = localStorage.getItem(BING_PICTURE_KEY);
        if (!selectedDate && bingPictureSelect && bingPictureSelect.value) {
            // Use the dropdown value (e.g., when random mode selected a random picture)
            selectedDate = bingPictureSelect.value;
        }
        if (selectedDate) {
            // Fetch specific date
            url = `${PICTURES_API_URL}/date/${selectedDate}/bing/`;
        } else {
            // Fetch today's picture
            url = `${PICTURES_API_URL}/today/${selectedSource}/`;
        }
    } else {
        // Use path-based routing: /api/pictures/today/{source}
        url = `${PICTURES_API_URL}/today/${selectedSource}/`;
    }
    
    // Try new unified API first
    try {
        const response = await fetch(url);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        // Check if backend returned an error message
        if (data.error) {
            throw new Error(data.error);
        }
        
        // Check if we got valid data
        if (data && data.title) {
            // Normalize data format
            return normalizePictureData(data, selectedSource);
        } else {
            throw new Error('Invalid data from backend');
        }
    } catch (error) {
        
        // Fallback to direct source API (only for APOD)
        if (selectedSource === 'apod') {
            try {
                const response = await fetch(`${APOD_API_URL}?api_key=${NASA_API_KEY}`);
                
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                
                const data = await response.json();
                
                // Transform NASA API response to match backend format
                return normalizePictureData({
                    title: data.title,
                    date: data.date,
                    display_explanation: data.explanation,
                    original_explanation: data.explanation,
                    media_type: data.media_type,
                    image_url: data.url,
                    hd_image_url: data.hdurl,
                    display_image_url: data.hdurl || data.url,
                    copyright: data.copyright,
                    source_url: `https://apod.nasa.gov/apod/ap${data.date.replace(/-/g, '').substring(2)}.html`
                }, 'apod');
            } catch (nasaError) {
                console.error('Both APIs failed:', nasaError);
                throw nasaError;
            }
        } else {
            // For other sources, just throw the error
            throw error;
        }
    }
}

// Normalize picture data to consistent format
function normalizePictureData(data, source) {
    return {
        source: source,
        title: data.title,
        date: data.date,
        processed_explanation: data.processed_explanation,
        display_explanation: data.display_explanation || data.processed_explanation || data.original_explanation || data.explanation,
        original_explanation: data.original_explanation || data.explanation,
        simplified_explanation: data.simplified_explanation,
        is_processed: data.is_processed || false,
        media_type: data.media_type || 'image',
        image_url: data.image_url || data.url,
        hd_image_url: data.hd_image_url || data.hdurl,
        display_image_url: data.display_image_url || data.hd_image_url || data.hdurl || data.image_url || data.url,
        thumbnail_url: data.thumbnail_url,
        copyright: data.copyright,
        source_url: data.source_url || data.nasa_url,
        image_width: data.image_width,
        image_height: data.image_height,
        image_size_mb: data.image_size_mb,
        image_resolution: data.image_resolution,
    };
}

// Check if cached data is still valid (same day and same source)
function isCacheValid(source) {
    const cachedDate = localStorage.getItem(CACHE_DATE_KEY);
    const cachedSource = localStorage.getItem(SOURCE_KEY);
    const today = new Date().toDateString();
    return cachedDate === today && cachedSource === source;
}

// Get cached picture data
function getCachedPicture(source) {
    if (!isCacheValid(source)) {
        return null;
    }
    
    const cached = localStorage.getItem(CACHE_KEY);
    return cached ? JSON.parse(cached) : null;
}

// Cache picture data
function cachePicture(data) {
    localStorage.setItem(CACHE_KEY, JSON.stringify(data));
    localStorage.setItem(CACHE_DATE_KEY, new Date().toDateString());
    if (data.source) {
        setSelectedSource(data.source);
    }
}

// Display picture data
function displayPicture(data) {
    // Validate data
    if (!data) {
        throw new Error('No data received');
    }
    
    // Set title and date
    if (data.title) {
        apodTitle.textContent = data.title;
    } else {
        apodTitle.textContent = 'Astronomy Picture of the Day';
    }
    
    if (data.date) {
        apodDate.textContent = data.date;
    }
    
    // Display processed explanation with Wikipedia links (HTML format)
    // Prefer processed_explanation (with Wikipedia links) if available
    if (data.processed_explanation) {
        // Processed explanation with Wikipedia links - always render as HTML
        apodDescription.innerHTML = data.processed_explanation;
    } else if (data.display_explanation) {
        // display_explanation from backend (falls back to simplified or original if processed not available)
        // If is_processed is true but processed_explanation is null, display_explanation might be simplified
        // If is_processed is false, display_explanation is original
        if (data.is_processed && data.simplified_explanation) {
            // Has simplified but not processed - use simplified
            apodDescription.textContent = data.simplified_explanation;
        } else if (data.hasOwnProperty('is_processed')) {
            // This is from backend - check if it contains HTML links
            if (data.display_explanation.includes('<a ') || data.display_explanation.includes('<a>') || 
                data.display_explanation.includes('href=')) {
                apodDescription.innerHTML = data.display_explanation;
            } else {
                apodDescription.textContent = data.display_explanation;
            }
        } else {
            // This is from NASA API fallback
            apodDescription.textContent = data.display_explanation;
        }
    } else if (data.original_explanation) {
        apodDescription.textContent = data.original_explanation;
    } else if (data.explanation) {
        // Fallback for NASA API format
        apodDescription.textContent = data.explanation;
    } else {
        apodDescription.textContent = 'No explanation available.';
    }
    
    // Set copyright if available
    if (data.copyright) {
        apodCopyright.textContent = `© ${data.copyright}`;
    } else {
        apodCopyright.textContent = '';
    }
    
    // Set link to source page (in top-right corner)
    if (sourceLink) {
        const sourceNames = {
            'apod': 'NASA APOD',
            'wikipedia': 'Wikipedia POD',
            'bing': 'Bing POD'
        };
        
        if (data.source === 'wikipedia') {
            // Always use the Wikipedia POD page URL for Wikipedia source
            sourceLink.href = 'https://en.wikipedia.org/wiki/Wikipedia:Picture_of_the_day';
            sourceLink.title = `Visit ${sourceNames[data.source]}`;
        } else if (data.source === 'apod') {
            if (data.source_url) {
                sourceLink.href = data.source_url;
            } else if (data.nasa_url) {
                sourceLink.href = data.nasa_url;
            } else if (data.date) {
                // Fallback to constructing URL from date for APOD
                sourceLink.href = `https://apod.nasa.gov/apod/ap${data.date.replace(/-/g, '').substring(2)}.html`;
            } else {
                sourceLink.href = 'https://apod.nasa.gov/';
            }
            sourceLink.title = `Visit ${sourceNames[data.source]}`;
        } else if (data.source === 'bing') {
            if (data.source_url) {
                sourceLink.href = data.source_url;
            } else {
                sourceLink.href = 'https://www.bing.com';
            }
            sourceLink.title = `Visit ${sourceNames[data.source]}`;
        } else if (data.source_url) {
            sourceLink.href = data.source_url;
            sourceLink.title = `Visit ${sourceNames[data.source] || 'Source'}`;
        } else {
            sourceLink.href = '#';
            sourceLink.title = 'Visit Source';
        }
    }
    
    // Handle media type (image or video)
    const mediaType = data.media_type || 'image';
    
    if (mediaType === 'image') {
        // Use display_image_url from backend (prioritizes local, then HD, then regular)
        const imageUrl = data.display_image_url || data.hd_image_url || data.image_url || data.hdurl || data.url;
        
        if (!imageUrl) {
            throw new Error('No image URL available');
        }
        
        // Get viewport dimensions
        const viewportWidth = window.innerWidth;
        const viewportHeight = window.innerHeight;
        
        // Get image dimensions from API or calculate from loaded image
        const imageWidth = data.image_width;
        const imageHeight = data.image_height;
        
        // Calculate optimal display settings
        const displaySettings = calculateOptimalDisplay(
            viewportWidth,
            viewportHeight,
            imageWidth,
            imageHeight
        );
        
        // Apply display settings
        applyImageDisplaySettings(displaySettings, viewportWidth, viewportHeight, imageWidth, imageHeight);
        
        // Preload image
        const img = new Image();
        img.onload = () => {
            // If we don't have dimensions from API, get them from loaded image
            if (!imageWidth || !imageHeight) {
                const loadedWidth = img.naturalWidth;
                const loadedHeight = img.naturalHeight;
                const newDisplaySettings = calculateOptimalDisplay(
                    viewportWidth,
                    viewportHeight,
                    loadedWidth,
                    loadedHeight
                );
                applyImageDisplaySettings(newDisplaySettings, viewportWidth, viewportHeight, loadedWidth, loadedHeight);
            }
            
            apodImage.src = imageUrl;
            apodImage.classList.add('loaded');
            hideLoading();
        };
        img.onerror = () => {
            // Fallback to regular URL if HD fails
            const fallbackUrl = data.image_url || data.url || imageUrl;
            if (fallbackUrl && fallbackUrl !== imageUrl) {
                apodImage.src = fallbackUrl;
            } else {
                apodImage.src = imageUrl;
            }
            apodImage.classList.add('loaded');
            hideLoading();
        };
        img.src = imageUrl;
    } else if (mediaType === 'video') {
        // For videos, show a thumbnail or the video embed
        // Using thumbnail_url if available, otherwise show a message
        if (data.thumbnail_url) {
            apodImage.src = data.thumbnail_url;
            apodImage.classList.add('loaded');
        } else {
            apodImage.style.display = 'none';
            document.querySelector('.background-container').style.background = 
                'linear-gradient(to bottom, #000428, #004e92)';
        }
        hideLoading();
        
        // Update description to include video link
        const explanation = data.display_explanation || data.original_explanation || data.explanation || '';
        const videoUrl = data.image_url || data.url;
        if (videoUrl) {
            apodDescription.innerHTML = `
                ${explanation}<br><br>
                <a href="${videoUrl}" target="_blank" style="color: #4a9eff;">Watch Video</a>
            `;
        }
    } else {
        // Unknown media type, try to show as image
        const imageUrl = data.display_image_url || data.hd_image_url || data.image_url || data.hdurl || data.url;
        if (imageUrl) {
            apodImage.src = imageUrl;
            apodImage.classList.add('loaded');
        }
        hideLoading();
    }
}

// Hide loading screen
function hideLoading() {
    setTimeout(() => {
        loading.classList.add('hidden');
    }, 300);
}

// Show error message
function showError(message) {
    console.error('Picture Error:', message);
    apodTitle.textContent = 'Error Loading Picture';
    apodDescription.textContent = message;
    hideLoading();
    
    // Make sure info panel is visible so user can see the error
    setInfoPanelVisible(true);
}

// Main initialization
async function init() {
    try {
        // Load available sources first and update selector
        // Force refresh on localhost (development) to immediately pick up admin changes
        // In production, use normal caching (30 seconds)
        const isLocalhost = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
        await updateSourceSelector(isLocalhost);
        
        // Check if we have any sources available
        if (AVAILABLE_SOURCES.length === 0) {
            showError('No picture sources are currently enabled. Please enable sources in the admin panel.');
            return;
        }
        
        // Check if random on new tab is enabled (default to true if not set)
        const stored = localStorage.getItem(RANDOM_ON_NEW_TAB_KEY);
        const randomEnabled = stored === null ? true : stored === 'true';
        let source;
        
        // When random is enabled, always pick a random source (ignore any stored source)
        if (randomEnabled) {
            // Random mode: always pick a random source for this new tab
            source = getRandomSource();
            if (!source) {
                // No sources available (shouldn't happen due to check above, but handle gracefully)
                showError('No picture sources are currently enabled.');
                return;
            }
            // Update the dropdown to show the random selection (but don't save it)
            if (sourceSelect) {
                sourceSelect.value = source;
            }
        } else {
            // Normal mode: use stored source or pick a random one and save it
            source = getSelectedSource();
            if (!source) {
                // No source saved - pick a random one and save it
                source = getRandomSource();
                if (!source) {
                    showError('No picture sources are currently enabled.');
                    return;
                }
                if (sourceSelect) {
                    sourceSelect.value = source;
                }
                setSelectedSource(source);
            } else {
                // User has manually selected a source - validate it's still enabled
                if (!AVAILABLE_SOURCES.includes(source)) {
                    // Source was disabled - switch to first available
                    source = AVAILABLE_SOURCES[0];
                    setSelectedSource(source);
                }
                if (sourceSelect) {
                    sourceSelect.value = source;
                }
            }
        }
        
        // Show/hide Bing picture selector
        if (bingPictureSelect) {
            if (source === 'bing') {
                bingPictureSelect.classList.remove('hidden');
                // Pass pickRandom=true when random mode is enabled
                await loadBingPictures(randomEnabled);
            } else {
                bingPictureSelect.classList.add('hidden');
            }
        }
        
        // Update viewport dimensions immediately
        const viewportWidth = window.innerWidth;
        const viewportHeight = window.innerHeight;
        updateDimensionsOverlay(viewportWidth, viewportHeight, null, null, null);
        
        // Update loading text based on source
        const sourceNames = {
            'apod': 'NASA APOD',
            'wikipedia': 'Wikipedia POD',
            'bing': 'Bing POD'
        };
        const sourceName = sourceNames[source] || 'Picture';
        loadingText.textContent = `Loading ${sourceName}...`;
        
        // Check cache first (but only if it's for the same source)
        let pictureData = getCachedPicture(source);
        
        if (!pictureData) {
            // Fetch fresh data
            pictureData = await fetchPicture(source);
            cachePicture(pictureData);
        }
        
        displayPicture(pictureData);
    } catch (error) {
        console.error('Initialization error:', error);
        const errorMessage = error.message || 'Failed to load Picture of the Day. Please check your internet connection and try again.';
        showError(errorMessage);
    }
}

// Start the extension
init();
