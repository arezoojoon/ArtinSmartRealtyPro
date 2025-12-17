// CRM Manager Script
console.log('CRM Manager loaded');

let allLeads = [];
let filteredLeads = [];

const searchInput = document.getElementById('searchInput');
const refreshBtn = document.getElementById('refreshBtn');
const exportBtn = document.getElementById('exportBtn');
const clearFiltersBtn = document.getElementById('clearFiltersBtn');
const leadsTable = document.getElementById('leadsTable');
const leadsTableBody = document.getElementById('leadsTableBody');
const emptyState = document.getElementById('emptyState');
const loading = document.getElementById('loading');

// Stats elements
const totalLeadsEl = document.getElementById('totalLeads');
const messagesSentEl = document.getElementById('messagesSent');
const withEmailEl = document.getElementById('withEmail');
const withPhoneEl = document.getElementById('withPhone');

// Load data on page load
document.addEventListener('DOMContentLoaded', () => {
  loadStats();
  loadLeads();
});

// Refresh button
refreshBtn.addEventListener('click', () => {
  loadStats();
  loadLeads();
});

// Export button
exportBtn.addEventListener('click', async () => {
  exportBtn.disabled = true;
  exportBtn.textContent = '⏳ Exporting...';
  
  try {
    const { apiEndpoint } = await chrome.storage.local.get('apiEndpoint');
    const baseUrl = apiEndpoint || 'http://localhost:8000';
    
    // Open export URL in new tab (browser will download file)
    window.open(`${baseUrl}/api/export-excel`, '_blank');
    
    exportBtn.textContent = '✅ Downloaded!';
    setTimeout(() => {
      exportBtn.textContent = '📥 Export to Excel';
      exportBtn.disabled = false;
    }, 2000);
    
  } catch (err) {
    alert('Error exporting: ' + err.message);
    exportBtn.textContent = '📥 Export to Excel';
    exportBtn.disabled = false;
  }
});

// Clear filters
clearFiltersBtn.addEventListener('click', () => {
  searchInput.value = '';
  filteredLeads = [...allLeads];
  renderTable();
});

// Search functionality
searchInput.addEventListener('input', (e) => {
  const query = e.target.value.toLowerCase();
  
  if (!query) {
    filteredLeads = [...allLeads];
  } else {
    filteredLeads = allLeads.filter(lead => {
      const name = (lead.name || '').toLowerCase();
      const email = (lead.email || '').toLowerCase();
      const company = (lead.company || '').toLowerCase();
      const jobTitle = (lead.job_title || '').toLowerCase();
      
      return name.includes(query) || 
             email.includes(query) || 
             company.includes(query) ||
             jobTitle.includes(query);
    });
  }
  
  renderTable();
});

// Load statistics
async function loadStats() {
  try {
    const { apiEndpoint } = await chrome.storage.local.get('apiEndpoint');
    const baseUrl = apiEndpoint || 'http://localhost:8000';
    
    const response = await fetch(`${baseUrl}/api/stats`);
    const stats = await response.json();
    
    totalLeadsEl.textContent = stats.total_leads || 0;
    messagesSentEl.textContent = stats.messages_sent || 0;
    withEmailEl.textContent = stats.with_email || 0;
    withPhoneEl.textContent = stats.with_phone || 0;
    
  } catch (err) {
    console.error('Error loading stats:', err);
  }
}

// Load all leads
async function loadLeads() {
  loading.style.display = 'block';
  leadsTable.style.display = 'none';
  emptyState.style.display = 'none';
  
  try {
    const { apiEndpoint } = await chrome.storage.local.get('apiEndpoint');
    const baseUrl = apiEndpoint || 'http://localhost:8000';
    
    const response = await fetch(`${baseUrl}/api/leads`);
    const data = await response.json();
    
    allLeads = data.leads || [];
    filteredLeads = [...allLeads];
    
    if (allLeads.length === 0) {
      emptyState.style.display = 'block';
    } else {
      renderTable();
    }
    
  } catch (err) {
    console.error('Error loading leads:', err);
    alert('Failed to load leads. Make sure backend is running.');
  } finally {
    loading.style.display = 'none';
  }
}

// Render table
function renderTable() {
  if (filteredLeads.length === 0) {
    leadsTable.style.display = 'none';
    emptyState.style.display = 'block';
    return;
  }
  
  leadsTable.style.display = 'table';
  emptyState.style.display = 'none';
  
  leadsTableBody.innerHTML = '';
  
  filteredLeads.forEach(lead => {
    const row = document.createElement('tr');
    
    // Format date
    const addedDate = new Date(lead.created_at).toLocaleDateString();
    
    // Status badge
    const statusBadge = lead.message_sent 
      ? '<span class="badge badge-success">Sent</span>'
      : '<span class="badge badge-warning">Pending</span>';
    
    // LinkedIn link
    const linkedinLink = lead.linkedin_url 
      ? `<a href="${lead.linkedin_url}" target="_blank" class="linkedin-link">View Profile</a>`
      : '-';
    
    row.innerHTML = `
      <td><strong>${escapeHtml(lead.name)}</strong></td>
      <td>${escapeHtml(lead.job_title || '-')}</td>
      <td>${escapeHtml(lead.company || '-')}</td>
      <td>${escapeHtml(lead.email || '-')}</td>
      <td>${escapeHtml(lead.phone || '-')}</td>
      <td>${linkedinLink}</td>
      <td>${statusBadge}</td>
      <td>${addedDate}</td>
    `;
    
    leadsTableBody.appendChild(row);
  });
}

// Escape HTML to prevent XSS
function escapeHtml(text) {
  if (!text) return '';
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}
