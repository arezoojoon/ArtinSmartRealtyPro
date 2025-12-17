// Background Service Worker for Manifest V3
console.log('AI Lead Scraper & Personalizer - Background Service Worker Loaded');

// Handle extension installation
chrome.runtime.onInstalled.addListener(() => {
  console.log('Extension installed successfully');
  
  // ✅ Initialize default settings - Use production URL!
  chrome.storage.local.get(['productDescription', 'apiEndpoint', 'tenantId'], (result) => {
    if (!result.apiEndpoint) {
      chrome.storage.local.set({
        apiEndpoint: 'https://api.artinsmartagent.com',  // ✅ Production URL
        tenantId: 1  // ✅ Default tenant (can be changed in settings)
      });
    }
  });
});

// Listen for messages from content script or popup
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'openSidePanel') {
    chrome.sidePanel.open({ windowId: sender.tab.windowId });
    sendResponse({ success: true });
    return true; // Keep message channel open
  }
  
  if (request.action === 'scrapeProfile') {
    // Forward scraping request to the active tab's content script
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      if (tabs[0]) {
        chrome.tabs.sendMessage(tabs[0].id, { action: 'extractProfileData' }, (response) => {
          sendResponse(response);
        });
      }
    });
    return true; // Keep the message channel open for async response
  }
  
  if (request.action === 'generateMessage') {
    // Send data to backend API
    handleMessageGeneration(request.data)
      .then(result => sendResponse(result))
      .catch(error => sendResponse({ error: error.message }));
    return true; // Keep the message channel open for async response
  }
});

// Generate personalized message via backend API
async function handleMessageGeneration(data) {
  // Check rate limit
  if (!checkRateLimit()) {
    return { success: false, error: 'Rate limit exceeded. Please wait a minute and try again.' };
  }
  
  try {
    const { apiEndpoint, tenantId } = await chrome.storage.local.get(['apiEndpoint', 'tenantId']);
    const endpoint = apiEndpoint || 'https://api.artinsmartagent.com';  // ✅ Production URL
    
    // ✅ Add tenantId to request for multi-tenant support
    const requestData = {
      ...data,
      tenantId: tenantId || 1
    };
    
    // Add timeout to fetch
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 30000); // 30 second timeout
    
    // ✅ Use NEW unified LinkedIn endpoint
    const response = await fetch(`${endpoint}/api/linkedin/generate-message`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(requestData),
      signal: controller.signal
    });
    
    clearTimeout(timeoutId);
    
    if (!response.ok) {
      throw new Error(`API Error: ${response.status} ${response.statusText}`);
    }
    
    const result = await response.json();
    return { success: true, message: result.message, leadId: result.leadId };
  } catch (error) {
    console.error('Message generation failed:', error);
    if (error.name === 'AbortError') {
      return { success: false, error: 'Request timeout. Please check your backend connection.' };
    }
    return { success: false, error: error.message };
  }
}

// Rate limiting to prevent LinkedIn detection
const requestTimes = [];
const MAX_REQUESTS_PER_MINUTE = 10;

function checkRateLimit() {
  const now = Date.now();
  const oneMinuteAgo = now - 60000;
  
  // Remove old timestamps
  while (requestTimes.length > 0 && requestTimes[0] < oneMinuteAgo) {
    requestTimes.shift();
  }
  
  if (requestTimes.length >= MAX_REQUESTS_PER_MINUTE) {
    return false;
  }
  
  requestTimes.push(now);
  return true;
}
