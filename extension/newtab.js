const CACHE_KEY = 'picture_cache';
const CACHE_DATE_KEY = 'picture_cache_date';
const SOURCE_KEY = 'picture_source';  // Store selected source
const DIMENSIONS_VISIBLE_KEY = 'dimensions_overlay_visible';  // Store dimensions overlay visibility
const INFO_PANEL_VISIBLE_KEY = 'info_panel_visible';  // Store info panel visibility
const RANDOM_ON_NEW_TAB_KEY = 'random_on_new_tab';  // Store random on new tab preference

const BACKEND_API_URL = CONFIG.BACKEND_API_URL;
const PICTURES_API_URL = `${BACKEND_API_URL}/pictures`;

let AVAILABLE_SOURCES = ['apod', 'wikipedia', 'bing'];
const SOURCES_CACHE_KEY = 'available_sources_cache';
const SOURCES_CACHE_DATE_KEY = 'available_sources_cache_date';

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

const settingsToggle = document.getElementById('settingsToggle');
const settingsPanel = document.getElementById('settingsPanel');
const settingsClose = document.getElementById('settingsClose');
const toggleDescription = document.getElementById('toggleDescription');
const toggleRandom = document.getElementById('toggleRandom');
const toggleDimensions = document.getElementById('toggleDimensions');

if (sourceSelect) {
    sourceSelect.innerHTML = '<option value="">Loading sources...</option>';
    sourceSelect.disabled = true;
}

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
        const randomSource = getRandomSource();
        if (randomSource) {
            e.target.value = randomSource;
        }
        return;
    }
    
    const newSource = e.target.value;
    
    if (!AVAILABLE_SOURCES.includes(newSource)) {
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
    const sourceName = newSource === 'apod' ? 'NASA picture of day' : newSource === 'wikipedia' ? 'Wikipedia picture of day' : 'Bing picture of day';
    loadingText.textContent = `Loading ${sourceName}...`;
    init();
});

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
    if (toggleDescription) {
        toggleDescription.checked = visible;
    }
}

if (infoPanel) {
    const isVisible = getInfoPanelVisible();
    setInfoPanelVisible(isVisible);
}

if (settingsToggle) {
    settingsToggle.addEventListener('click', async (e) => {
        e.stopPropagation();
        if (settingsPanel) {
            const isOpening = !settingsPanel.classList.contains('visible');
            settingsPanel.classList.toggle('visible');
            
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

async function loadAvailableSources(forceRefresh = false) {
    const now = Date.now();
    const isLocalhost = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
    const cacheTime = isLocalhost ? 10 * 1000 : 30 * 1000;
    
    if (!forceRefresh) {
        const cachedDate = localStorage.getItem(SOURCES_CACHE_DATE_KEY);
        const cachedSources = localStorage.getItem(SOURCES_CACHE_KEY);
        
        if (cachedDate && cachedSources && (now - parseInt(cachedDate)) < cacheTime) {
            try {
                const sources = JSON.parse(cachedSources);
                const enabledSources = sources.filter(s => s.enabled !== false);
                AVAILABLE_SOURCES = enabledSources.map(s => s.value);
                
                const storedSource = localStorage.getItem(SOURCE_KEY);
                if (storedSource && !AVAILABLE_SOURCES.includes(storedSource)) {
                    console.log('Current source disabled, refreshing sources...');
                    return await loadAvailableSources(true);
                }
                
                return enabledSources;
            } catch (e) {
            }
        }
    }
    
    try {
        const response = await fetch(`${PICTURES_API_URL}/sources/`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const sources = await response.json();
        const enabledSources = sources.filter(s => s.enabled !== false);
        AVAILABLE_SOURCES = enabledSources.map(s => s.value);
        
        localStorage.setItem(SOURCES_CACHE_KEY, JSON.stringify(sources));
        localStorage.setItem(SOURCES_CACHE_DATE_KEY, now.toString());
        
        return enabledSources;
    } catch (error) {
        console.error('Failed to load sources from API:', error);
        const cachedSources = localStorage.getItem(SOURCES_CACHE_KEY);
        if (cachedSources) {
            try {
                const sources = JSON.parse(cachedSources);
                const enabledSources = sources.filter(s => s.enabled !== false);
                AVAILABLE_SOURCES = enabledSources.map(s => s.value);
                console.log('Using cached sources (API unavailable)');
                return enabledSources;
            } catch (e) {
            }
        }
        
        console.error('No sources available - API failed and no cache');
        AVAILABLE_SOURCES = [];
        return [];
    }
}

async function updateSourceSelector(forceRefresh = false) {
    const sources = await loadAvailableSources(forceRefresh);
    
    if (!sourceSelect) return;
    
    const currentValue = sourceSelect.value;
    
    sourceSelect.innerHTML = '';
    
    if (sources.length === 0) {
        sourceSelect.innerHTML = '<option value="">No sources available</option>';
        sourceSelect.disabled = true;
        return;
    }
    
    sourceSelect.disabled = false;
    
    sources.forEach(source => {
        if (source.enabled !== false) {
            const option = document.createElement('option');
            option.value = source.value;
            option.textContent = source.label || source.value;
            sourceSelect.appendChild(option);
        }
    });
    
    if (currentValue && AVAILABLE_SOURCES.includes(currentValue)) {
        sourceSelect.value = currentValue;
    } else if (AVAILABLE_SOURCES.length > 0) {
        sourceSelect.value = AVAILABLE_SOURCES[0];
        if (currentValue && !AVAILABLE_SOURCES.includes(currentValue)) {
            localStorage.removeItem(SOURCE_KEY);
            if (currentValue === 'bing') {
                localStorage.removeItem(BING_PICTURE_KEY);
            }
        }
    }
}

function getSelectedSource() {
    const stored = localStorage.getItem(SOURCE_KEY);
    if (!stored) {
        return null;
    }
    
    if (AVAILABLE_SOURCES.length > 0 && !AVAILABLE_SOURCES.includes(stored)) {
        localStorage.removeItem(SOURCE_KEY);
        if (stored === 'bing') {
            localStorage.removeItem(BING_PICTURE_KEY);
        }
        return null;
    }
    
    return stored;
}

function getRandomSource() {
    if (AVAILABLE_SOURCES.length === 0) {
        return null;
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

// Calculate simple display settings based on viewport and image dimensions
function calculateOptimalDisplay(viewportWidth, viewportHeight, imageWidth, imageHeight) {
    if (!imageWidth || !imageHeight) {
        return {
            objectFit: 'cover',
            objectPosition: 'center',
            scale: 1,
            mode: 'Cover',
            displayWidth: viewportWidth,
            displayHeight: viewportHeight
        };
    }
    
    // Simple cover strategy with basic scaling calculation
    const scaleToFitWidth = viewportWidth / imageWidth;
    const scaleToFitHeight = viewportHeight / imageHeight;
    const scale = Math.max(scaleToFitWidth, scaleToFitHeight);
    
    return {
        objectFit: 'cover',
        objectPosition: 'center',
        scale: scale.toFixed(2),
        mode: 'Cover',
        displayWidth: viewportWidth,
        displayHeight: viewportHeight
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
    let selectedSource = source || getSelectedSource();
    
    if (selectedSource && !AVAILABLE_SOURCES.includes(selectedSource)) {
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
        if (AVAILABLE_SOURCES.length === 0) {
            throw new Error('No picture sources are currently enabled. Please enable sources in the admin panel.');
        }
        selectedSource = AVAILABLE_SOURCES[0];
    }
    
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
}

function sanitizeHtmlEntities(text) {
    if (!text || typeof text !== 'string') {
        return text;
    }
    
    const textarea = document.createElement('textarea');
    textarea.innerHTML = text;
    let sanitized = textarea.value;
    
    sanitized = sanitized.replace(/\u00A0/g, ' ');
    
    return sanitized;
}

function normalizePictureData(data, source) {
    // Backend provides standardized fields - trust them
    return {
        source: source,
        title: data.title,  // Backend already sanitizes
        date: data.date,
        processed_explanation: data.processed_explanation,
        display_explanation: data.display_explanation,  // Backend handles fallbacks
        original_explanation: data.original_explanation,
        simplified_explanation: data.simplified_explanation,
        is_processed: data.is_processed || false,
        media_type: data.media_type || 'image',
        image_url: data.image_url,
        hd_image_url: data.hd_image_url,
        display_image_url: data.display_image_url,
        thumbnail_url: data.thumbnail_url,
        copyright: data.copyright,  // Backend already sanitizes
        source_url: data.source_url,
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
    
    // Sanitize cached data for backward compatibility with old cache entries
    const data = JSON.parse(cached);
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
    
    if (data.title) {
        apodTitle.textContent = data.title;
    } else {
        apodTitle.textContent = 'Astronomy Picture of the Day';
    }
    
    if (data.date) {
        apodDate.textContent = data.date;
    }
    
    // Backend provides processed_explanation or display_explanation
    if (data.processed_explanation) {
        apodDescription.innerHTML = data.processed_explanation;
    } else if (data.display_explanation) {
        // Check if it contains HTML links
        if (data.display_explanation.includes('<a ') || data.display_explanation.includes('href=')) {
            apodDescription.innerHTML = data.display_explanation;
        } else {
            apodDescription.textContent = data.display_explanation;
        }
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
            'apod': 'NASA Picture of the Day',
            'wikipedia': 'Wikipedia Picture of the Day',
            'bing': 'Bing Picture of the Day'
        };
        
        if (data.source === 'wikipedia') {
            sourceLink.href = 'https://en.wikipedia.org/wiki/Wikipedia:Picture_of_the_day';
            sourceLink.title = `Visit ${sourceNames[data.source]}`;
        } else if (data.source === 'apod') {
        if (data.source_url) {
            sourceLink.href = data.source_url;
        } else if (data.date) {
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
        const imageUrl = data.display_image_url;
        
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
            apodImage.classList.add('loaded');
            hideLoading();
            showError('Failed to load image');
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
        
        const explanation = data.display_explanation || '';
        const videoUrl = data.image_url;
        if (videoUrl) {
            apodDescription.innerHTML = `
                ${explanation}<br><br>
                <a href="${videoUrl}" target="_blank" style="color: #4a9eff;">Watch Video</a>
            `;
        }
    } else {
        const imageUrl = data.display_image_url;
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
        const isLocalhost = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
        await updateSourceSelector(isLocalhost);
        
        if (AVAILABLE_SOURCES.length === 0) {
            showError('No picture sources are currently enabled. Please enable sources in the admin panel.');
            return;
        }
        
        const stored = localStorage.getItem(RANDOM_ON_NEW_TAB_KEY);
        const randomEnabled = stored === null ? true : stored === 'true';
        let source;
        
        if (randomEnabled) {
            source = getRandomSource();
            if (!source) {
                showError('No picture sources are currently enabled.');
                return;
            }
            if (sourceSelect) {
                sourceSelect.value = source;
            }
        } else {
            source = getSelectedSource();
            if (!source) {
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
                if (!AVAILABLE_SOURCES.includes(source)) {
                    source = AVAILABLE_SOURCES[0];
                    setSelectedSource(source);
                }
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
            'apod': 'NASA Picture of the Day',
            'wikipedia': 'Wikipedia Picture of the Day',
            'bing': 'Bing Picture of the Day'
        };
        const sourceName = sourceNames[source] || 'Picture';
        loadingText.textContent = `Loading ${sourceName}...`;
        
        let pictureData = getCachedPicture(source);
        
        if (!pictureData) {
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

init();
