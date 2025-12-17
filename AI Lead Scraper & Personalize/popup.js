// Popup Script - Settings Management
console.log('Popup loaded');

const productInput = document.getElementById('productDescription');
const apiEndpointInput = document.getElementById('apiEndpoint');
const saveBtn = document.getElementById('saveSettings');
const sidePanelBtn = document.getElementById('openSidePanel');
const crmBtn = document.getElementById('openCRM');
const statusDiv = document.getElementById('status');

// Load saved settings on popup open
chrome.storage.local.get(['productDescription', 'apiEndpoint'], (result) => {
  if (chrome.runtime.lastError) {
    console.error('Failed to load settings:', chrome.runtime.lastError);
    apiEndpointInput.value = 'http://localhost:8000';
    return;
  }
  
  if (result.productDescription) {
    productInput.value = result.productDescription;
  }
  if (result.apiEndpoint) {
    apiEndpointInput.value = result.apiEndpoint;
  } else {
    apiEndpointInput.value = 'http://localhost:8000';
  }
});

// Save settings
saveBtn.addEventListener('click', () => {
  const productDescription = productInput.value.trim();
  const apiEndpoint = apiEndpointInput.value.trim() || 'http://localhost:8000';
  
  if (!productDescription) {
    showStatus('Please describe your product/service', 'error');
    return;
  }
  
  // Validate API endpoint URL
  try {
    new URL(apiEndpoint);
  } catch (e) {
    showStatus('Invalid API endpoint URL', 'error');
    return;
  }
  
  chrome.storage.local.set({
    productDescription,
    apiEndpoint
  }, () => {
    showStatus('Settings saved successfully!', 'success');
  });
});

// Open side panel
sidePanelBtn.addEventListener('click', () => {
  chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
    if (chrome.runtime.lastError) {
      console.error('Failed to query tabs:', chrome.runtime.lastError);
      showStatus('Failed to open side panel', 'error');
      return;
    }
    if (tabs && tabs[0]) {
      chrome.sidePanel.open({ windowId: tabs[0].windowId });
    }
  });
});

// Open CRM Manager
crmBtn.addEventListener('click', () => {
  chrome.tabs.create({ url: chrome.runtime.getURL('crm.html') });
});

// Open Automation Dashboard
const automationBtn = document.getElementById('openAutomation');
automationBtn.addEventListener('click', () => {
  chrome.tabs.create({ url: chrome.runtime.getURL('automation.html') });
});

// Show status message
function showStatus(message, type) {
  statusDiv.textContent = message;
  statusDiv.className = `status ${type}`;
  statusDiv.style.display = 'block';
  
  setTimeout(() => {
    statusDiv.style.display = 'none';
  }, 3000);
}
