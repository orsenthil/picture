const NASA_API_KEY = 'HDin5BLUkoDRqGGDaJVQpOuF6NR26GXGlWV3jKkE'
const APOD_API_URL = 'https://api.nasa.gov/planetary/apod';

const CACHE_KEY = 'picture_cache';
const CACHE_DATE_KEY = 'picture_cache_date';
const SOURCE_KEY = 'picture_source';  // Store selected source
const DIMENSIONS_VISIBLE_KEY = 'dimensions_overlay_visible';  // Store dimensions overlay visibility
const INFO_PANEL_VISIBLE_KEY = 'info_panel_visible';  // Store info panel visibility
const RANDOM_ON_NEW_TAB_KEY = 'random_on_new_tab';  // Store random on new tab preference

const BACKEND_API_URL = window.location.origin + '/api';
const PICTURES_API_URL = `${BACKEND_API_URL}/pictures`;

// Available sources - will be loaded dynamically from API
let AVAILABLE_SOURCES = ['apod', 'wikipedia', 'bing']; // Fallback if API fails
const SOURCES_CACHE_KEY = 'available_sources_cache';
const SOURCES_CACHE_DATE_KEY = 'available_sources_cache_date';

// Default source (will be randomly selected if not set)
const DEFAULT_SOURCE = 'apod';

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
const BING_PICTURE_KEY = 'bing_picture_date';

const settingsToggle = document.getElementById('settingsToggle');
const settingsPanel = document.getElementById('settingsPanel');
const settingsClose = document.getElementById('settingsClose');
const toggleDescription = document.getElementById('toggleDescription');
const toggleRandom = document.getElementById('toggleRandom');
const toggleDimensions = document.getElementById('toggleDimensions');

// Initialize source selector - will be updated when sources are loaded
// Temporary initialization to avoid errors
if (sourceSelect) {
    sourceSelect.innerHTML = '<option value="apod">NASA APOD</option><option value="wikipedia">Wikipedia POD</option><option value="bing">Bing POD</option>';
}

function getDimensionsOverlayVisible() {
    const stored = localStorage.getItem(DIMENSIONS_VISIBLE_KEY);
    return stored === null ? false : stored === 'true';
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
    if (toggleDimensions) {
        toggleDimensions.checked = visible;
    }
}

function initSettings() {
    if (toggleDescription) {
        toggleDescription.checked = getInfoPanelVisible();
    }
    if (toggleRandom) {
        const stored = localStorage.getItem(RANDOM_ON_NEW_TAB_KEY);
        const randomEnabled = stored === null ? true : stored === 'true';
        toggleRandom.checked = randomEnabled;
        
        if (sourceSelect) {
            sourceSelect.disabled = randomEnabled;
        }
    }
    if (toggleDimensions) {
        toggleDimensions.checked = getDimensionsOverlayVisible();
    }
    
    if (dimensionsOverlay) {
        const isVisible = getDimensionsOverlayVisible();
        setDimensionsOverlayVisible(isVisible);
    }
}

initSettings();

sourceSelect.addEventListener('change', async (e) => {
    const randomEnabled = localStorage.getItem(RANDOM_ON_NEW_TAB_KEY) === 'true';
    if (randomEnabled) {
        e.target.value = getRandomSource();
        return;
    }
    
    const newSource = e.target.value;
    setSelectedSource(newSource);
    
    if (bingPictureSelect) {
        if (newSource === 'bing') {
            bingPictureSelect.classList.remove('hidden');
            await loadBingPictures();
        } else {
            bingPictureSelect.classList.add('hidden');
            bingPictureSelect.value = '';
        }
    }
    
    localStorage.removeItem(CACHE_KEY);
    localStorage.removeItem(CACHE_DATE_KEY);
    loading.classList.remove('hidden');
    const sourceName = newSource === 'apod' ? 'NASA APOD' : newSource === 'wikipedia' ? 'Wikipedia POD' : 'Bing POD';
    loadingText.textContent = `Loading ${sourceName}...`;
    init();
});

if (bingPictureSelect) {
    bingPictureSelect.addEventListener('change', (e) => {
        const selectedDate = e.target.value;
        if (selectedDate) {
            localStorage.setItem(BING_PICTURE_KEY, selectedDate);
            localStorage.removeItem(CACHE_KEY);
            localStorage.removeItem(CACHE_DATE_KEY);
            loading.classList.remove('hidden');
            loadingText.textContent = 'Loading Bing picture...';
            init();
        }
    });
}

function getInfoPanelVisible() {
    const stored = localStorage.getItem(INFO_PANEL_VISIBLE_KEY);
    return stored === null ? true : stored === 'true';
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
    if (toggleDescription) {
        toggleDescription.checked = visible;
    }
}

if (infoPanel) {
    const isVisible = getInfoPanelVisible();
    setInfoPanelVisible(isVisible);
}

if (settingsToggle) {
    settingsToggle.addEventListener('click', (e) => {
        e.stopPropagation();
        if (settingsPanel) {
            settingsPanel.classList.toggle('visible');
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

document.addEventListener('click', (e) => {
    if (settingsPanel && settingsPanel.classList.contains('visible')) {
        if (!settingsPanel.contains(e.target) && !settingsToggle.contains(e.target)) {
            settingsPanel.classList.remove('visible');
        }
    }
});

if (toggleDescription) {
    toggleDescription.addEventListener('change', (e) => {
        setInfoPanelVisible(e.target.checked);
    });
}

if (toggleRandom) {
    toggleRandom.addEventListener('change', (e) => {
        const randomEnabled = e.target.checked;
        localStorage.setItem(RANDOM_ON_NEW_TAB_KEY, randomEnabled.toString());
        
        if (sourceSelect) {
            sourceSelect.disabled = randomEnabled;
        }
        
        if (randomEnabled) {
            clearSelectedSource();
            localStorage.removeItem(BING_PICTURE_KEY);
        }
        
        init();
    });
}

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
        console.log('Fetching sources from API (forceRefresh:', forceRefresh, ')');
        const response = await fetch(`${PICTURES_API_URL}/sources/`, { cache: forceRefresh ? 'no-cache' : 'default' });
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const sources = await response.json();
        console.log('API returned sources:', sources);
        // Only include enabled sources
        const enabledSources = sources.filter(s => s.enabled !== false);
        console.log('Filtered enabled sources:', enabledSources);
        AVAILABLE_SOURCES = enabledSources.map(s => s.value);
        console.log('AVAILABLE_SOURCES set to:', AVAILABLE_SOURCES);
        
        // Cache the sources (including disabled ones for reference)
        localStorage.setItem(SOURCES_CACHE_KEY, JSON.stringify(sources));
        localStorage.setItem(SOURCES_CACHE_DATE_KEY, now.toString());
        console.log('Sources cached at:', new Date(now).toISOString());
        
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
        
        // Last resort: return empty array - website will show error
        console.error('No sources available - API failed and no cache');
        AVAILABLE_SOURCES = [];
        return [];
    }
}

// Update source selector dropdown with available sources
async function updateSourceSelector(forceRefresh = false) {
    console.log('updateSourceSelector called with forceRefresh:', forceRefresh);
    const sources = await loadAvailableSources(forceRefresh);
    console.log('Loaded sources:', sources);
    
    if (!sourceSelect) {
        console.warn('sourceSelect element not found');
        return;
    }
    
    // Store current selection
    const currentValue = sourceSelect.value;
    
    // Clear existing options
    sourceSelect.innerHTML = '';
    
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
        }
    }
}

function getSelectedSource() {
    return localStorage.getItem(SOURCE_KEY);
}

async function loadAllRecentPictures() {
    try {
        const response = await fetch(`${PICTURES_API_URL}/all_recent/`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const pictures = await response.json();
        return pictures;
    } catch (error) {
        console.error('Failed to load recent pictures:', error);
        return [];
    }
}

async function getRandomPicture() {
    const pictures = await loadAllRecentPictures();
    
    if (pictures.length === 0) {
        return null;
    }
    
    const randomIndex = Math.floor(Math.random() * pictures.length);
    return pictures[randomIndex];
}

function getRandomSource() {
    if (AVAILABLE_SOURCES.length === 0) {
        return DEFAULT_SOURCE;
    }
    const randomIndex = Math.floor(Math.random() * AVAILABLE_SOURCES.length);
    return AVAILABLE_SOURCES[randomIndex];
}

function setSelectedSource(source) {
    localStorage.setItem(SOURCE_KEY, source);
}

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
    
    const viewportAspect = viewportWidth / viewportHeight;
    const imageAspect = imageWidth / imageHeight;
    const aspectRatioDiff = Math.abs(imageAspect - viewportAspect);
    
    const viewportIsWide = viewportAspect > 1;
    const imageIsWide = imageAspect > 1;
    
    const squareSize = Math.min(viewportWidth, viewportHeight);
    const squareAspect = 1;
    
    let objectFit = 'cover';
    let objectPosition = 'center';
    let mode = 'Cover';
    let scale = 1;
    let displayWidth = viewportWidth;
    let displayHeight = viewportHeight;
    
    const scaleToFitWidth = viewportWidth / imageWidth;
    const scaleToFitHeight = viewportHeight / imageHeight;
    const scaleToFill = Math.max(scaleToFitWidth, scaleToFitHeight); // For cover
    const scaleToContain = Math.min(scaleToFitWidth, scaleToFitHeight); // For contain
    
    if (viewportAspect >= 0.9 && viewportAspect <= 1.1) {
        if (imageAspect > 1.5 || imageAspect < 0.67) {
            objectFit = 'cover';
            objectPosition = 'center';
            mode = 'Square Crop';
            scale = scaleToFill;
            displayWidth = squareSize;
            displayHeight = squareSize;
        } else {
            objectFit = 'cover';
            mode = 'Cover (Square Viewport)';
            scale = scaleToFill;
        }
    }
    else if ((viewportIsWide && !imageIsWide) || (!viewportIsWide && imageIsWide)) {
        objectFit = 'contain';
        objectPosition = 'center';
        scale = scaleToContain;
        if (viewportIsWide && !imageIsWide) {
            mode = 'Contain (Portrait in Landscape)';
            displayWidth = imageWidth * scaleToContain;
            displayHeight = imageHeight * scaleToContain;
        } else {
            mode = 'Contain (Landscape in Portrait)';
            displayWidth = imageWidth * scaleToContain;
            displayHeight = imageHeight * scaleToContain;
        }
    }
    else if (scaleToContain > 1.5) {
        objectFit = 'contain';
        mode = 'Contain (Upscale)';
        scale = scaleToContain;
        displayWidth = imageWidth * scaleToContain;
        displayHeight = imageHeight * scaleToContain;
    }
    else if (aspectRatioDiff < 0.1) {
        objectFit = 'cover';
        mode = 'Cover (Perfect Match)';
        scale = scaleToFill;
    }
    else {
        let cropPercent = 0;
        if (imageAspect > viewportAspect) {
            const scaledHeight = viewportWidth / imageAspect;
            cropPercent = ((viewportHeight - scaledHeight) / viewportHeight) * 100;
        } else {
            const scaledWidth = viewportHeight * imageAspect;
            cropPercent = ((viewportWidth - scaledWidth) / viewportWidth) * 100;
        }
        
        if (cropPercent > 25) {
            objectFit = 'contain';
            mode = `Contain (${cropPercent.toFixed(0)}% crop avoided)`;
            scale = scaleToContain;
        } else {
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

function applyImageDisplaySettings(settings, viewportWidth, viewportHeight, imageWidth, imageHeight) {
    apodImage.style.width = viewportWidth + 'px';
    apodImage.style.height = viewportHeight + 'px';
    apodImage.style.objectFit = settings.objectFit;
    apodImage.style.objectPosition = settings.objectPosition;
    
    updateDimensionsOverlay(viewportWidth, viewportHeight, imageWidth, imageHeight, settings);
}

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

let resizeTimeout;
window.addEventListener('resize', () => {
    clearTimeout(resizeTimeout);
    resizeTimeout = setTimeout(() => {
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
                updateDimensionsOverlay(viewportWidth, viewportHeight, null, null, null);
            }
        }
    }, 250);
});

async function loadBingPictures(pickRandom = false) {
    if (!bingPictureSelect) return;
    
    try {
        const response = await fetch(`${PICTURES_API_URL}/list/bing/`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const pictures = await response.json();
        
        bingPictureSelect.innerHTML = '<option value="">Select a Bing picture...</option>';
        
        pictures.forEach(picture => {
            const option = document.createElement('option');
            option.value = picture.date;
            option.textContent = `${picture.date} - ${sanitizeHtmlEntities(picture.title)}`;
            bingPictureSelect.appendChild(option);
        });
        
        const storedDate = localStorage.getItem(BING_PICTURE_KEY);
        if (pickRandom && pictures.length > 0) {
            const randomIndex = Math.floor(Math.random() * pictures.length);
            const randomDate = pictures[randomIndex].date;
            bingPictureSelect.value = randomDate;
        } else if (storedDate) {
            bingPictureSelect.value = storedDate;
        } else if (pictures.length > 0) {
            bingPictureSelect.value = pictures[0].date;
            localStorage.setItem(BING_PICTURE_KEY, pictures[0].date);
        }
    } catch (error) {
        console.error('Failed to load Bing pictures:', error);
        bingPictureSelect.innerHTML = '<option value="">Error loading pictures</option>';
    }
}

async function fetchPicture(source = null) {
    const selectedSource = source || getSelectedSource();
    
    let url;
    if (selectedSource === 'bing') {
        let selectedDate = localStorage.getItem(BING_PICTURE_KEY);
        if (!selectedDate && bingPictureSelect && bingPictureSelect.value) {
            selectedDate = bingPictureSelect.value;
        }
        if (selectedDate) {
            url = `${PICTURES_API_URL}/date/${selectedDate}/bing/`;
        } else {
            url = `${PICTURES_API_URL}/today/${selectedSource}/`;
        }
    } else {
        url = `${PICTURES_API_URL}/today/${selectedSource}/`;
    }
    
    try {
        const response = await fetch(url);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (data.error) {
            throw new Error(data.error);
        }
        
        if (data && data.title) {
            return normalizePictureData(data, selectedSource);
        } else {
            throw new Error('Invalid data from backend');
        }
    } catch (error) {
        
        if (selectedSource === 'apod') {
            try {
                const response = await fetch(`${APOD_API_URL}?api_key=${NASA_API_KEY}`);
                
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                
                const data = await response.json();
                
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
            throw error;
        }
    }
}

// Sanitize HTML entities in text
function sanitizeHtmlEntities(text) {
    if (!text || typeof text !== 'string') {
        return text;
    }
    
    // Create a temporary DOM element to decode HTML entities
    const textarea = document.createElement('textarea');
    textarea.innerHTML = text;
    let sanitized = textarea.value;
    
    // Replace non-breaking spaces (U+00A0) with regular spaces
    sanitized = sanitized.replace(/\u00A0/g, ' ');
    
    return sanitized;
}

function normalizePictureData(data, source) {
    // Don't sanitize processed_explanation - it contains HTML links that must be preserved
    // Only sanitize plain text fields
    return {
        source: source,
        title: sanitizeHtmlEntities(data.title),
        date: data.date,
        processed_explanation: data.processed_explanation,  // Keep HTML links intact
        display_explanation: data.display_explanation || data.processed_explanation || sanitizeHtmlEntities(data.original_explanation || data.explanation),
        original_explanation: sanitizeHtmlEntities(data.original_explanation || data.explanation),
        simplified_explanation: sanitizeHtmlEntities(data.simplified_explanation),
        is_processed: data.is_processed || false,
        media_type: data.media_type || 'image',
        image_url: data.image_url || data.url,
        hd_image_url: data.hd_image_url || data.hdurl,
        display_image_url: data.display_image_url || data.hd_image_url || data.hdurl || data.image_url || data.url,
        thumbnail_url: data.thumbnail_url,
        copyright: sanitizeHtmlEntities(data.copyright),
        source_url: data.source_url || data.nasa_url,
        image_width: data.image_width,
        image_height: data.image_height,
        image_size_mb: data.image_size_mb,
        image_resolution: data.image_resolution,
    };
}

function isCacheValid(source) {
    const cachedDate = localStorage.getItem(CACHE_DATE_KEY);
    const cachedSource = localStorage.getItem(SOURCE_KEY);
    const today = new Date().toDateString();
    return cachedDate === today && cachedSource === source;
}

function getCachedPicture(source) {
    if (!isCacheValid(source)) {
        return null;
    }
    
    const cached = localStorage.getItem(CACHE_KEY);
    if (!cached) {
        return null;
    }
    
    const data = JSON.parse(cached);
    // Sanitize cached data to handle old cached data with HTML entities
    // Don't sanitize processed_explanation if it contains HTML links
    return {
        ...data,
        title: sanitizeHtmlEntities(data.title),
        display_explanation: data.display_explanation ? (data.display_explanation.includes('<a ') ? data.display_explanation : sanitizeHtmlEntities(data.display_explanation)) : null,
        processed_explanation: data.processed_explanation,  // Keep HTML links intact
        original_explanation: sanitizeHtmlEntities(data.original_explanation),
        simplified_explanation: sanitizeHtmlEntities(data.simplified_explanation),
        copyright: sanitizeHtmlEntities(data.copyright),
    };
}

function cachePicture(data) {
    localStorage.setItem(CACHE_KEY, JSON.stringify(data));
    localStorage.setItem(CACHE_DATE_KEY, new Date().toDateString());
    if (data.source) {
        setSelectedSource(data.source);
    }
}

function displayPicture(data) {
    if (!data) {
        throw new Error('No data received');
    }
    
    // Debug logging
    console.log('displayPicture called with data:', {
        has_processed_explanation: !!data.processed_explanation,
        has_display_explanation: !!data.display_explanation,
        is_processed: data.is_processed,
        source: data.source
    });
    
    if (data.title) {
        apodTitle.textContent = data.title;
    } else {
        apodTitle.textContent = 'Astronomy Picture of the Day';
    }
    
    if (data.date) {
        apodDate.textContent = data.date;
    }
    
    if (data.processed_explanation) {
        // Processed explanation with Wikipedia links - render as HTML
        const linkCount = (data.processed_explanation.match(/<a\s+href/g) || []).length;
        console.log('Displaying processed_explanation with', linkCount, 'Wikipedia links');
        console.log('processed_explanation length:', data.processed_explanation.length);
        apodDescription.innerHTML = data.processed_explanation;
    } else if (data.display_explanation) {
        if (data.is_processed && data.simplified_explanation) {
            apodDescription.textContent = data.simplified_explanation;
        } else if (data.hasOwnProperty('is_processed')) {
            if (data.display_explanation.includes('<a ') || data.display_explanation.includes('<a>') || 
                data.display_explanation.includes('href=')) {
                apodDescription.innerHTML = data.display_explanation;
            } else {
                apodDescription.textContent = data.display_explanation;
            }
        } else {
            apodDescription.textContent = data.display_explanation;
        }
    } else if (data.original_explanation) {
        apodDescription.textContent = data.original_explanation;
    } else if (data.explanation) {
        apodDescription.textContent = data.explanation;
    } else {
        apodDescription.textContent = 'No explanation available.';
    }
    
    if (data.copyright) {
        apodCopyright.textContent = `© ${data.copyright}`;
    } else {
        apodCopyright.textContent = '';
    }
    
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
    
    const mediaType = data.media_type || 'image';
    
    if (mediaType === 'image') {
        const imageUrl = data.display_image_url || data.hd_image_url || data.image_url || data.hdurl || data.url;
        
        if (!imageUrl) {
            throw new Error('No image URL available');
        }
        
        const viewportWidth = window.innerWidth;
        const viewportHeight = window.innerHeight;
        
        const imageWidth = data.image_width;
        const imageHeight = data.image_height;
        
        const displaySettings = calculateOptimalDisplay(
            viewportWidth,
            viewportHeight,
            imageWidth,
            imageHeight
        );
        
        applyImageDisplaySettings(displaySettings, viewportWidth, viewportHeight, imageWidth, imageHeight);
        
        const img = new Image();
        img.onload = () => {
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
        if (data.thumbnail_url) {
            apodImage.src = data.thumbnail_url;
            apodImage.classList.add('loaded');
        } else {
            apodImage.style.display = 'none';
            document.querySelector('.background-container').style.background = 
                'linear-gradient(to bottom, #000428, #004e92)';
        }
        hideLoading();
        
        const explanation = data.display_explanation || data.original_explanation || data.explanation || '';
        const videoUrl = data.image_url || data.url;
        if (videoUrl) {
            apodDescription.innerHTML = `
                ${explanation}<br><br>
                <a href="${videoUrl}" target="_blank" style="color: #4a9eff;">Watch Video</a>
            `;
        }
    } else {
        const imageUrl = data.display_image_url || data.hd_image_url || data.image_url || data.hdurl || data.url;
        if (imageUrl) {
            apodImage.src = imageUrl;
            apodImage.classList.add('loaded');
        }
        hideLoading();
    }
}

function hideLoading() {
    setTimeout(() => {
        loading.classList.add('hidden');
    }, 300);
}

function showError(message) {
    console.error('Picture Error:', message);
    apodTitle.textContent = 'Error Loading Picture';
    apodDescription.textContent = message;
    hideLoading();
    
    setInfoPanelVisible(true);
}

async function init() {
    try {
        // Load available sources first and update selector
        // Force refresh on localhost (development) to immediately pick up admin changes
        // In production, use normal caching (30 seconds)
        const isLocalhost = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
        console.log('Initializing sources, isLocalhost:', isLocalhost, 'forceRefresh:', isLocalhost);
        await updateSourceSelector(isLocalhost);
        
        const stored = localStorage.getItem(RANDOM_ON_NEW_TAB_KEY);
        const randomEnabled = stored === null ? true : stored === 'true';
        let source;
        
        if (randomEnabled) {
            // New approach: pick a random picture from all available pictures
            const randomPicture = await getRandomPicture();
            if (!randomPicture) {
                showError('No pictures are currently available.');
                return;
            }
            
            // Set the source based on the random picture
            source = randomPicture.source;
            if (sourceSelect) {
                sourceSelect.value = source;
            }
            
            // If it's a Bing picture with a specific date, store that date
            if (source === 'bing' && randomPicture.date) {
                localStorage.setItem(BING_PICTURE_KEY, randomPicture.date);
            }
        } else {
            source = getSelectedSource();
            if (!source) {
                source = getRandomSource();
                if (sourceSelect) {
                    sourceSelect.value = source;
                }
                setSelectedSource(source);
            } else {
                if (sourceSelect) {
                    sourceSelect.value = source;
                }
            }
        }
        
        if (bingPictureSelect) {
            if (source === 'bing') {
                bingPictureSelect.classList.remove('hidden');
                await loadBingPictures(randomEnabled);
            } else {
                bingPictureSelect.classList.add('hidden');
            }
        }
        
        const viewportWidth = window.innerWidth;
        const viewportHeight = window.innerHeight;
        updateDimensionsOverlay(viewportWidth, viewportHeight, null, null, null);
        
        const sourceNames = {
            'apod': 'NASA APOD',
            'wikipedia': 'Wikipedia POD',
            'bing': 'Bing POD'
        };
        const sourceName = sourceNames[source] || 'Picture';
        loadingText.textContent = `Loading ${sourceName}...`;
        
        let pictureData = getCachedPicture(source);
        
        // Always fetch fresh data if cached data is missing processed_explanation
        // This ensures we get the latest processed version from the API
        if (pictureData && pictureData.is_processed && !pictureData.processed_explanation) {
            console.log('Cached data missing processed_explanation, clearing cache and fetching fresh data...');
            // Clear the cache to force fresh fetch
            localStorage.removeItem(CACHE_KEY);
            localStorage.removeItem(CACHE_DATE_KEY);
            pictureData = null;
        }
        
        // For Wikipedia, always check API if cache doesn't have processed_explanation
        // This handles the case where a picture was processed after being cached
        if (pictureData && source === 'wikipedia' && !pictureData.processed_explanation) {
            console.log('Wikipedia picture in cache without processed_explanation, checking API...');
            try {
                const freshData = await fetchPicture(source);
                if (freshData.is_processed && freshData.processed_explanation) {
                    console.log('Found processed version in API, using it and updating cache');
                    pictureData = freshData;
                    cachePicture(freshData);
                }
            } catch (error) {
                console.warn('Failed to check for processed version, using cache:', error);
            }
        }
        
        if (!pictureData) {
            console.log('Fetching fresh picture data from API...');
            pictureData = await fetchPicture(source);
            console.log('Fetched data:', {
                has_processed_explanation: !!pictureData.processed_explanation,
                is_processed: pictureData.is_processed,
                source: pictureData.source
            });
            cachePicture(pictureData);
        } else {
            console.log('Using cached picture data:', {
                has_processed_explanation: !!pictureData.processed_explanation,
                is_processed: pictureData.is_processed,
                source: pictureData.source
            });
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
