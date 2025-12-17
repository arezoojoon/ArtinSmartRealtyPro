// Automation Dashboard JavaScript

const API_ENDPOINT = 'http://localhost:8000';
let productDescription = '';

// Load stats on page load
window.addEventListener('DOMContentLoaded', async () => {
  // Load product description from storage
  const result = await chrome.storage.local.get(['productDescription']);
  productDescription = result.productDescription || '';
  
  if (!productDescription) {
    showStatus('emailStatus', 'Please set Product Description in Extension Settings first', 'error');
    return;
  }
  
  // Load stats
  loadStats();
});

// Load campaign stats
async function loadStats() {
  try {
    const response = await fetch(`${API_ENDPOINT}/api/auto/campaign-stats`);
    const stats = await response.json();
    
    document.getElementById('totalLeads').textContent = stats.total_leads;
    document.getElementById('withEmail').textContent = stats.with_email;
    document.getElementById('withPhone').textContent = stats.with_phone;
    document.getElementById('linkedinToday').textContent = 
      `${stats.linkedin_sent_today}/${stats.linkedin_remaining_today + stats.linkedin_sent_today}`;
    
  } catch (error) {
    console.error('Failed to load stats:', error);
  }
}

// Send daily LinkedIn messages
document.getElementById('sendDailyLinkedIn').addEventListener('click', async () => {
  const btn = document.getElementById('sendDailyLinkedIn');
  const statusDiv = document.getElementById('linkedinStatus');
  
  btn.disabled = true;
  btn.textContent = 'Sending messages...';
  
  try {
    const response = await fetch(`${API_ENDPOINT}/api/auto/send-daily-linkedin`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ product_description: productDescription })
    });
    
    const result = await response.json();
    
    if (result.status === 'success') {
      showStatus('linkedinStatus', `✅ ${result.sent} LinkedIn messages sent successfully!`, 'success');
      
      // Display messages
      const resultsDiv = document.getElementById('results');
      resultsDiv.innerHTML = '<h3>Messages Sent:</h3>';
      
      result.messages.forEach(msg => {
        resultsDiv.innerHTML += `
          <div class="list-item">
            <strong>${msg.name}</strong>
            <p>${msg.message}</p>
            <a href="${msg.linkedin_url}" target="_blank">Open Profile</a>
          </div>
        `;
      });
      
      loadStats();
    } else {
      showStatus('linkedinStatus', result.message, 'info');
    }
    
  } catch (error) {
    showStatus('linkedinStatus', 'Error sending messages: ' + error.message, 'error');
  } finally {
    btn.disabled = false;
    btn.textContent = 'Send 10 LinkedIn Messages Today';
  }
});

// Prepare email campaign
document.getElementById('prepareEmail').addEventListener('click', async () => {
  const btn = document.getElementById('prepareEmail');
  const statusDiv = document.getElementById('emailStatus');
  const downloadBtn = document.getElementById('downloadEmailCSV');
  
  btn.disabled = true;
  btn.textContent = 'Preparing campaign...';
  
  try {
    const response = await fetch(
      `${API_ENDPOINT}/api/auto/prepare-email-campaign?product_desc=${encodeURIComponent(productDescription)}`
    );
    
    const result = await response.json();
    
    showStatus('emailStatus', `✅ ${result.count} emails prepared!`, 'success');
    
    // Display email list
    const resultsDiv = document.getElementById('results');
    resultsDiv.innerHTML = '<h3>Email List:</h3>';
    
    result.emails.slice(0, 10).forEach(email => {
      resultsDiv.innerHTML += `
        <div class="list-item">
          <strong>${email.name} - ${email.job_title}</strong>
          <p>📧 ${email.email}</p>
          <p style="margin-top:8px; opacity:0.9;">${email.message.substring(0, 100)}...</p>
        </div>
      `;
    });
    
    if (result.count > 10) {
      resultsDiv.innerHTML += `<p style="margin-top:16px; opacity:0.8;">... and ${result.count - 10} more emails</p>`;
    }
    
    // Store data for CSV download
    window.emailData = result.emails;
    downloadBtn.style.display = 'block';
    
  } catch (error) {
    showStatus('emailStatus', 'Error: ' + error.message, 'error');
  } finally {
    btn.disabled = false;
    btn.textContent = 'Prepare Email Campaign';
  }
});

// Download email CSV
document.getElementById('downloadEmailCSV').addEventListener('click', () => {
  if (!window.emailData) return;
  
  // Create CSV content
  let csv = 'Name,Email,Job Title,Company,Message\n';
  
  window.emailData.forEach(email => {
    csv += `"${email.name}","${email.email}","${email.job_title || ''}","${email.company || ''}","${email.message.replace(/"/g, '""')}"\n`;
  });
  
  // Download
  const blob = new Blob([csv], { type: 'text/csv' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `email_campaign_${new Date().toISOString().split('T')[0]}.csv`;
  a.click();
  URL.revokeObjectURL(url);
});

// Prepare WhatsApp campaign
document.getElementById('prepareWhatsApp').addEventListener('click', async () => {
  const btn = document.getElementById('prepareWhatsApp');
  const statusDiv = document.getElementById('whatsappStatus');
  const downloadBtn = document.getElementById('downloadWhatsAppCSV');
  
  btn.disabled = true;
  btn.textContent = 'Preparing campaign...';
  
  try {
    const response = await fetch(
      `${API_ENDPOINT}/api/auto/prepare-whatsapp-campaign?product_desc=${encodeURIComponent(productDescription)}`
    );
    
    const result = await response.json();
    
    showStatus('whatsappStatus', `✅ ${result.count} WhatsApp contacts prepared!`, 'success');
    
    // Display WhatsApp list
    const resultsDiv = document.getElementById('results');
    resultsDiv.innerHTML = '<h3>WhatsApp List:</h3>';
    
    result.contacts.slice(0, 10).forEach(contact => {
      resultsDiv.innerHTML += `
        <div class="list-item">
          <strong>${contact.name}</strong>
          <p>📱 ${contact.phone}</p>
          <a href="${contact.whatsapp_link}" target="_blank" style="color:#25D366; text-decoration:none;">
            💚 Open WhatsApp Chat
          </a>
        </div>
      `;
    });
    
    if (result.count > 10) {
      resultsDiv.innerHTML += `<p style="margin-top:16px; opacity:0.8;">... and ${result.count - 10} more contacts</p>`;
    }
    
    // Store data for CSV download
    window.whatsappData = result.contacts;
    downloadBtn.style.display = 'block';
    
  } catch (error) {
    showStatus('whatsappStatus', 'Error: ' + error.message, 'error');
  } finally {
    btn.disabled = false;
    btn.textContent = 'Prepare WhatsApp Campaign';
  }
});

// Download WhatsApp CSV
document.getElementById('downloadWhatsAppCSV').addEventListener('click', () => {
  if (!window.whatsappData) return;
  
  // Create CSV content
  let csv = 'Name,Phone,WhatsApp Link,Message\n';
  
  window.whatsappData.forEach(contact => {
    csv += `"${contact.name}","${contact.phone}","${contact.whatsapp_link}","${contact.message.replace(/"/g, '""')}"\n`;
  });
  
  // Download
  const blob = new Blob([csv], { type: 'text/csv' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `whatsapp_campaign_${new Date().toISOString().split('T')[0]}.csv`;
  a.click();
  URL.revokeObjectURL(url);
});

// Helper function to show status
function showStatus(elementId, message, type) {
  const statusDiv = document.getElementById(elementId);
  statusDiv.textContent = message;
  statusDiv.className = `status ${type}`;
  statusDiv.style.display = 'block';
  
  if (type === 'success') {
    setTimeout(() => {
      statusDiv.style.display = 'none';
    }, 5000);
  }
}
