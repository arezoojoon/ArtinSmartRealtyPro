// Side Panel Script - Main UI Logic
console.log('Side Panel loaded');

let currentProfileData = null;

const scrapeBtn = document.getElementById('scrapeBtn');
const generateBtn = document.getElementById('generateBtn');
const copyBtn = document.getElementById('copyBtn');
const manualToggle = document.getElementById('manualToggle');
const manualInputSection = document.getElementById('manualInputSection');
const manualPostInput = document.getElementById('manualPostInput');

const emptyState = document.getElementById('emptyState');
const profileDataSection = document.getElementById('profileData');
const profileInfo = document.getElementById('profileInfo');
const loading = document.getElementById('loading');
const error = document.getElementById('error');
const result = document.getElementById('result');
const generatedMessage = document.getElementById('generatedMessage');

// Scrape profile data
scrapeBtn.addEventListener('click', async () => {
  scrapeBtn.disabled = true;
  scrapeBtn.textContent = '⏳ Scraping...';
  hideError();
  hideResult();
  
  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    
    if (!tab.url.includes('linkedin.com/in/')) {
      showError('Please navigate to a LinkedIn profile page first.');
      return;
    }
    
    chrome.tabs.sendMessage(tab.id, { action: 'extractProfileData' }, (response) => {
      if (chrome.runtime.lastError) {
        showError('Failed to communicate with content script. Try refreshing the page.');
        return;
      }
      
      if (chrome.runtime.lastError) {
        showError('Failed to communicate with content script. Try refreshing the page.');
        scrapeBtn.disabled = false;
        scrapeBtn.textContent = '🔍 Scrape Profile';
        return;
      }
      
      if (response && response.success) {
        currentProfileData = response.data;
        displayProfileData(response.data);
        emptyState.style.display = 'none';
        profileDataSection.style.display = 'block';
        
        // Save lead to CRM database
        saveLeadToCRM(response.data);
      } else {
        showError(response?.error || 'Failed to extract profile data. Try the manual input option.');
      }
      
      scrapeBtn.disabled = false;
      scrapeBtn.textContent = '🔍 Scrape Profile';
    });
  } catch (err) {
    showError(err.message);
    scrapeBtn.disabled = false;
    scrapeBtn.textContent = '🔍 Scrape Profile';
  }
});

// Display scraped profile data
function displayProfileData(data) {
  // Use textContent for safety, then build HTML safely
  const safeName = (data.name || 'Unknown').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  let html = `<strong>Name:</strong> ${safeName}<br>`;
  
  if (data.about) {
    const safeAbout = data.about.substring(0, 150).replace(/</g, '&lt;').replace(/>/g, '&gt;');
    html += `<strong>About:</strong> ${safeAbout}${data.about.length > 150 ? '...' : ''}<br>`;
  }
  
  if (data.experience && data.experience.length > 0) {
    const exp = data.experience[0];
    const title = (exp.title || '').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    const company = (exp.company || '').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    if (title || company) {
      html += `<strong>Current Position:</strong> ${title}${title && company ? ' at ' : ''}${company}<br>`;
    }
  }
  
  if (data.recentPosts && data.recentPosts.length > 0) {
    html += `<strong>Recent Posts Found:</strong> ${data.recentPosts.length}<br>`;
    data.recentPosts.forEach((post, index) => {
      const safeText = post.text.substring(0, 100).replace(/</g, '&lt;').replace(/>/g, '&gt;');
      html += `<div class="post-preview"><strong>Post ${index + 1}:</strong><br>${safeText}...</div>`;
    });
  } else {
    html += `<div class="post-preview" style="border-left-color: #ff9800;">⚠️ No recent posts found. Consider using manual input.</div>`;
  }
  
  profileInfo.innerHTML = html;
}

// Toggle manual input
manualToggle.addEventListener('click', () => {
  const isVisible = manualInputSection.style.display !== 'none';
  manualInputSection.style.display = isVisible ? 'none' : 'block';
  manualToggle.textContent = isVisible ? '✏️ Manual Input (Fallback)' : '❌ Hide Manual Input';
});

// Generate personalized message
generateBtn.addEventListener('click', async () => {
  hideError();
  hideResult();
  
  if (!currentProfileData) {
    showError('Please scrape a profile first.');
    return;
  }
  
  // Get product description from storage
  const { productDescription } = await chrome.storage.local.get('productDescription');
  
  if (!productDescription) {
    showError('Please set your product description in the extension settings first.');
    return;
  }
  
  // Check if manual input is provided
  const manualPost = manualPostInput.value.trim();
  if (manualPost) {
    currentProfileData.recentPosts = [{ text: manualPost, timestamp: '' }];
  }
  
  if (!currentProfileData.recentPosts || currentProfileData.recentPosts.length === 0) {
    showError('No recent posts available. Please use manual input to paste a recent post.');
    return;
  }
  
  generateBtn.disabled = true;
  loading.style.display = 'block';
  
  try {
    const response = await chrome.runtime.sendMessage({
      action: 'generateMessage',
      data: {
        profileData: currentProfileData,
        productDescription: productDescription
      }
    });
    
    if (!response) {
      showError('No response from background script. Try reloading the extension.');
      return;
    }
    
    if (response.success) {
      displayGeneratedMessage(response.message);
      // ✅ Message already saved in unified system via generate-message API
    } else {
      showError(response.error || 'Failed to generate message. Make sure the backend API is running.');
    }
  } catch (err) {
    showError('Error communicating with backend: ' + err.message);
  } finally {
    generateBtn.disabled = false;
    loading.style.display = 'none';
  }
});

// Display generated message
function displayGeneratedMessage(message) {
  generatedMessage.textContent = message;
  result.style.display = 'block';
}

// Copy to clipboard
copyBtn.addEventListener('click', () => {
  const text = generatedMessage.textContent;
  navigator.clipboard.writeText(text).then(() => {
    copyBtn.textContent = '✅ Copied!';
    setTimeout(() => {
      copyBtn.textContent = '📋 Copy to Clipboard';
    }, 2000);
  });
});

// Helper functions
function showError(message) {
  error.textContent = message;
  error.style.display = 'block';
}

function hideError() {
  error.style.display = 'none';
}

function hideResult() {
  result.style.display = 'none';
}

// ✅ Save lead to UNIFIED CRM database
async function saveLeadToCRM(profileData) {
  try {
    // ✅ Use unified system API (not localhost!)
    const { apiEndpoint, tenantId } = await chrome.storage.local.get(['apiEndpoint', 'tenantId']);
    const baseUrl = apiEndpoint || 'https://api.artinsmartagent.com';  // ✅ Production URL
    
    // ✅ NEW: Use unified LinkedIn endpoint
    const response = await fetch(`${baseUrl}/api/linkedin/add-lead`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        profileData: profileData,
        tenantId: tenantId || 1  // ✅ Multi-tenant support
      })
    });
    
    const result = await response.json();
    
    if (result.duplicate) {
      console.log('✅ Lead already exists in unified database');
    } else if (result.success) {
      console.log('✅ Lead saved to unified CRM - Follow-up will be scheduled!');
    }
  } catch (err) {
    console.error('❌ Error saving lead to unified CRM:', err);
  }
}

// ✅ Message is now saved automatically in generate-message endpoint
// No need for separate update call

