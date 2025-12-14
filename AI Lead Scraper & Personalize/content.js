// Content Script - Artin Lead Scraper & Personalizer by ArtinSmartAgent
console.log('Artin Lead Scraper - Content Script Loaded');

// Configuration constants
const CONFIG = {
  DELAYS: {
    MIN: 500,
    MAX: 1500,
    POST_SCROLL: 1000,
    POST_SCROLL_MAX: 2000,
    BUTTON_REINJECT: 1000
  },
  LIMITS: {
    MAX_ABOUT_LENGTH: 500,
    MAX_POST_LENGTH: 300,
    MAX_POSTS: 3,
    MAX_EXPERIENCE: 2
  }
};

// Human-like delay function to avoid detection
const humanDelay = (min = CONFIG.DELAYS.MIN, max = CONFIG.DELAYS.MAX) => {
  return new Promise(resolve => {
    setTimeout(resolve, Math.random() * (max - min) + min);
  });
};

// Check if we're on a LinkedIn profile page
function isLinkedInProfile() {
  const url = window.location.href;
  return url.includes('linkedin.com/in/') && !url.includes('/edit/');
}

// Extract profile name
function extractName() {
  try {
    // Try multiple selectors for robustness
    const selectors = [
      'h1.text-heading-xlarge',
      'h1[class*="top-card-layout__title"]',
      '.pv-text-details__left-panel h1',
      '[data-generated-suggestion-target] h1'
    ];
    
    for (const selector of selectors) {
      const element = document.querySelector(selector);
      if (element && element.textContent.trim()) {
        return element.textContent.trim();
      }
    }
    
    return 'Unknown';
  } catch (error) {
    console.error('Error extracting name:', error);
    return 'Unknown';
  }
}

// Extract About section
function extractAbout() {
  try {
    // LinkedIn's About section has various structures
    const aboutSection = document.querySelector('[id*="about"]')?.closest('section');
    
    if (aboutSection) {
      // Try to find the actual about text
      const aboutText = aboutSection.querySelector('.inline-show-more-text, .pv-about__summary-text, [class*="about"] .visually-hidden');
      
      if (aboutText) {
        return aboutText.textContent.trim().substring(0, CONFIG.LIMITS.MAX_ABOUT_LENGTH);
      }
      
      // Fallback: get all paragraph text in the section
      const paragraphs = aboutSection.querySelectorAll('p, span[aria-hidden="true"]');
      let text = '';
      paragraphs.forEach(p => {
        const content = p.textContent.trim();
        if (content && content.length > 20) {
          text += content + ' ';
        }
      });
      
      return text.trim().substring(0, CONFIG.LIMITS.MAX_ABOUT_LENGTH);
    }
    
    return '';
  } catch (error) {
    console.error('Error extracting about:', error);
    return '';
  }
}

// Extract Experience (current position)
function extractExperience() {
  try {
    const experiences = [];
    
    // Find experience section
    const experienceSection = document.querySelector('[id*="experience"]')?.closest('section');
    
    if (experienceSection) {
      // Get the first experience entry (current/most recent)
      const experienceItems = experienceSection.querySelectorAll('li[class*="profile-section-card"]');
      
      for (let i = 0; i < Math.min(CONFIG.LIMITS.MAX_EXPERIENCE, experienceItems.length); i++) {
        const item = experienceItems[i];
        const title = item.querySelector('[class*="profile-section-card__title"]')?.textContent.trim();
        const company = item.querySelector('[class*="profile-section-card__subtitle"]')?.textContent.trim();
        const duration = item.querySelector('[class*="date-range"]')?.textContent.trim();
        
        if (title || company) {
          experiences.push({
            title: title || '',
            company: company || '',
            duration: duration || ''
          });
        }
      }
    }
    
    return experiences;
  } catch (error) {
    console.error('Error extracting experience:', error);
    return [];
  }
}

// Extract Recent Activity/Posts (MOST CRITICAL)
async function extractRecentPosts() {
  try {
    const posts = [];
    
    // Scroll to activity section to trigger lazy loading
    const activitySection = document.querySelector('[id*="activity"]')?.closest('section');
    
    if (activitySection) {
      activitySection.scrollIntoView({ behavior: 'smooth', block: 'center' });
      await humanDelay(CONFIG.DELAYS.POST_SCROLL, CONFIG.DELAYS.POST_SCROLL_MAX);
      
      // Find "Show all activity" link and extract posts from there
      const activityLink = activitySection.querySelector('a[href*="/recent-activity/"]');
      
      if (activityLink) {
        // Get posts from the preview shown on profile
        const postElements = activitySection.querySelectorAll('[class*="profile-creator-shared-feed-update"]');
        
        for (let i = 0; i < Math.min(CONFIG.LIMITS.MAX_POSTS, postElements.length); i++) {
          const postElement = postElements[i];
          
          // Extract post text
          const postText = postElement.querySelector('[class*="break-words"]')?.textContent.trim() || 
                          postElement.querySelector('.feed-shared-text')?.textContent.trim() || '';
          
          if (postText && postText.length > 20) {
            posts.push({
              text: postText.substring(0, CONFIG.LIMITS.MAX_POST_LENGTH),
              timestamp: postElement.querySelector('time')?.getAttribute('datetime') || ''
            });
          }
        }
      }
    }
    
    // Fallback: Try to find posts in feed updates
    if (posts.length === 0) {
      const feedUpdates = document.querySelectorAll('[data-urn*="activity"]');
      
      for (let i = 0; i < Math.min(CONFIG.LIMITS.MAX_POSTS, feedUpdates.length); i++) {
        const update = feedUpdates[i];
        const text = update.querySelector('[class*="break-words"]')?.textContent.trim();
        
        if (text && text.length > 20) {
          posts.push({
            text: text.substring(0, CONFIG.LIMITS.MAX_POST_LENGTH),
            timestamp: ''
          });
        }
      }
    }
    
    // ✨ NEW: If no posts found, create dummy post so backend knows to use About section
    if (posts.length === 0) {
      posts.push({
        text: '[NO_POSTS_FOUND_USE_ABOUT]',
        timestamp: ''
      });
    }
    
    return posts;
  } catch (error) {
    console.error('Error extracting posts:', error);
    return [];
  }
}

// Main extraction function
async function extractProfileData() {
  if (!isLinkedInProfile()) {
    return {
      success: false,
      error: 'Not on a LinkedIn profile page'
    };
  }
  
  try {
    console.log('Starting profile data extraction...');
    
    // Add human-like delays between extractions
    const name = extractName();
    await humanDelay();
    
    const about = extractAbout();
    await humanDelay();
    
    const experience = extractExperience();
    await humanDelay();
    
    const recentPosts = await extractRecentPosts();
    
    const profileData = {
      success: true,
      data: {
        name,
        about,
        experience,
        recentPosts,
        profileUrl: window.location.href
      }
    };
    
    console.log('Profile data extracted:', profileData);
    return profileData;
  } catch (error) {
    console.error('Extraction error:', error);
    return {
      success: false,
      error: error.message
    };
  }
}

// Listen for messages from background or popup
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'extractProfileData') {
    extractProfileData().then(result => {
      sendResponse(result);
    });
    return true; // Keep message channel open for async response
  }
});

// Inject floating button on LinkedIn profile pages
function injectFloatingButton() {
  if (!isLinkedInProfile()) return;
  
  // Check if button already exists
  if (document.getElementById('ai-scraper-floating-btn')) return;
  
  const button = document.createElement('button');
  button.id = 'ai-scraper-floating-btn';
  button.innerHTML = '🤖 Generate Icebreaker';
  button.style.cssText = `
    position: fixed;
    bottom: 20px;
    right: 20px;
    z-index: 9999;
    padding: 12px 24px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border: none;
    border-radius: 25px;
    font-size: 14px;
    font-weight: 600;
    cursor: pointer;
    box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
    transition: all 0.3s ease;
  `;
  
  button.addEventListener('mouseenter', () => {
    button.style.transform = 'translateY(-2px)';
    button.style.boxShadow = '0 6px 20px rgba(102, 126, 234, 0.6)';
  });
  
  button.addEventListener('mouseleave', () => {
    button.style.transform = 'translateY(0)';
    button.style.boxShadow = '0 4px 15px rgba(102, 126, 234, 0.4)';
  });
  
  button.addEventListener('click', () => {
    chrome.runtime.sendMessage({ action: 'openSidePanel' });
  });
  
  document.body.appendChild(button);
}

// Initialize on page load
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', injectFloatingButton);
} else {
  injectFloatingButton();
}

// Re-inject button on navigation (LinkedIn is a SPA)
let lastUrl = location.href;
let navigationObserver = null;

function setupNavigationObserver() {
  // Disconnect previous observer if exists
  if (navigationObserver) {
    navigationObserver.disconnect();
  }
  
  navigationObserver = new MutationObserver(() => {
    const url = location.href;
    if (url !== lastUrl) {
      lastUrl = url;
      setTimeout(injectFloatingButton, 1000); // Delay for page to load
    }
  });
  
  navigationObserver.observe(document, { subtree: true, childList: true });
}

setupNavigationObserver();

// Cleanup on page unload
window.addEventListener('unload', () => {
  if (navigationObserver) {
    navigationObserver.disconnect();
  }
});
