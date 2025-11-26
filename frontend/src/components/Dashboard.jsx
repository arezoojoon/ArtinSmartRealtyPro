/**
 * ArtinSmartRealty V2 - Super Dashboard
 * Modern B2B SaaS Dashboard for Real Estate Agents
 * Dark Mode Theme with Luxury Aesthetics
 */

import React, { useState, useEffect, useCallback } from 'react';

// ==================== CONSTANTS ====================

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const COLORS = {
  navy: '#0f1729',
  navyLight: '#1a2744',
  navyLighter: '#243352',
  gold: '#D4AF37',
  goldLight: '#e6c84a',
  white: '#ffffff',
  gray: '#9ca3af',
  red: '#ef4444',
  green: '#22c55e',
  yellow: '#eab308',
};

const STATUS_COLORS = {
  new: '#ef4444',
  contacted: '#f97316',
  qualified: '#eab308',
  viewing_scheduled: '#22c55e',
  negotiating: '#3b82f6',
  closed_won: '#22c55e',
  closed_lost: '#6b7280',
};

const PURPOSE_LABELS = {
  investment: '📈 Investment',
  living: '🏡 Living',
  residency: '🛂 Residency/Visa',
};

const DAYS_OF_WEEK = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'];
const DAY_LABELS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];

// ==================== API HELPERS ====================

const api = {
  async get(endpoint) {
    const response = await fetch(`${API_BASE_URL}${endpoint}`);
    if (!response.ok) throw new Error(`API Error: ${response.statusText}`);
    return response.json();
  },
  
  async post(endpoint, data) {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!response.ok) throw new Error(`API Error: ${response.statusText}`);
    return response.json();
  },
  
  async delete(endpoint) {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, { method: 'DELETE' });
    if (!response.ok) throw new Error(`API Error: ${response.statusText}`);
    return response.json();
  },
};

// ==================== COMPONENTS ====================

// Sidebar Navigation
const Sidebar = ({ activeTab, setActiveTab }) => {
  const navItems = [
    { id: 'dashboard', icon: '📊', label: 'Dashboard' },
    { id: 'leads', icon: '👥', label: 'Lead Pipeline' },
    { id: 'calendar', icon: '📅', label: 'Calendar' },
    { id: 'properties', icon: '🏠', label: 'Properties' },
    { id: 'analytics', icon: '📈', label: 'Analytics' },
    { id: 'settings', icon: '⚙️', label: 'Settings' },
  ];

  return (
    <aside style={{
      width: '240px',
      backgroundColor: COLORS.navy,
      borderRight: `1px solid ${COLORS.navyLighter}`,
      padding: '20px 0',
      display: 'flex',
      flexDirection: 'column',
      height: '100vh',
    }}>
      {/* Logo */}
      <div style={{
        padding: '0 20px 30px',
        borderBottom: `1px solid ${COLORS.navyLighter}`,
        marginBottom: '20px',
      }}>
        <h1 style={{
          color: COLORS.gold,
          fontSize: '20px',
          fontWeight: '700',
          margin: 0,
        }}>
          ArtinSmartRealty
        </h1>
        <p style={{ color: COLORS.gray, fontSize: '12px', margin: '5px 0 0' }}>
          Real Estate SaaS v2.0
        </p>
      </div>

      {/* Navigation */}
      <nav style={{ flex: 1 }}>
        {navItems.map(item => (
          <button
            key={item.id}
            onClick={() => setActiveTab(item.id)}
            style={{
              display: 'flex',
              alignItems: 'center',
              width: '100%',
              padding: '14px 20px',
              backgroundColor: activeTab === item.id ? COLORS.navyLighter : 'transparent',
              border: 'none',
              borderLeft: activeTab === item.id ? `3px solid ${COLORS.gold}` : '3px solid transparent',
              cursor: 'pointer',
              transition: 'all 0.2s',
            }}
          >
            <span style={{ fontSize: '18px', marginRight: '12px' }}>{item.icon}</span>
            <span style={{
              color: activeTab === item.id ? COLORS.gold : COLORS.white,
              fontSize: '14px',
              fontWeight: activeTab === item.id ? '600' : '400',
            }}>
              {item.label}
            </span>
          </button>
        ))}
      </nav>

      {/* User section */}
      <div style={{
        padding: '20px',
        borderTop: `1px solid ${COLORS.navyLighter}`,
        display: 'flex',
        alignItems: 'center',
      }}>
        <div style={{
          width: '40px',
          height: '40px',
          borderRadius: '50%',
          backgroundColor: COLORS.gold,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          marginRight: '12px',
        }}>
          <span style={{ fontSize: '18px' }}>👤</span>
        </div>
        <div>
          <p style={{ color: COLORS.white, fontSize: '14px', margin: 0, fontWeight: '500' }}>Agent</p>
          <p style={{ color: COLORS.green, fontSize: '11px', margin: '2px 0 0' }}>● Online</p>
        </div>
      </div>
    </aside>
  );
};

// Header
const Header = () => {
  return (
    <header style={{
      backgroundColor: COLORS.navy,
      padding: '16px 24px',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      borderBottom: `1px solid ${COLORS.navyLighter}`,
    }}>
      {/* Search */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        backgroundColor: COLORS.navyLight,
        borderRadius: '8px',
        padding: '10px 16px',
        width: '300px',
      }}>
        <span style={{ color: COLORS.gray, marginRight: '10px' }}>🔍</span>
        <input
          type="text"
          placeholder="Search leads, properties..."
          style={{
            backgroundColor: 'transparent',
            border: 'none',
            outline: 'none',
            color: COLORS.white,
            fontSize: '14px',
            width: '100%',
          }}
        />
      </div>

      {/* Actions */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
        <button style={{
          backgroundColor: 'transparent',
          border: 'none',
          cursor: 'pointer',
          position: 'relative',
        }}>
          <span style={{ fontSize: '22px' }}>🔔</span>
          <span style={{
            position: 'absolute',
            top: '-5px',
            right: '-5px',
            backgroundColor: COLORS.red,
            color: COLORS.white,
            fontSize: '10px',
            padding: '2px 6px',
            borderRadius: '10px',
            fontWeight: '600',
          }}>3</span>
        </button>
        
        <div style={{
          width: '40px',
          height: '40px',
          borderRadius: '50%',
          border: `2px solid ${COLORS.gold}`,
          overflow: 'hidden',
        }}>
          <img
            src="https://ui-avatars.com/api/?name=Agent&background=D4AF37&color=0f1729&bold=true"
            alt="Profile"
            style={{ width: '100%', height: '100%' }}
          />
        </div>
      </div>
    </header>
  );
};

// KPI Card with glassmorphism effect
const KPICard = ({ title, value, icon, trend, trendUp }) => {
  return (
    <div style={{
      backgroundColor: 'rgba(26, 39, 68, 0.8)',
      backdropFilter: 'blur(10px)',
      borderRadius: '12px',
      padding: '24px',
      border: `1px solid ${COLORS.navyLighter}`,
      position: 'relative',
      overflow: 'hidden',
    }}>
      {/* Gradient accent */}
      <div style={{
        position: 'absolute',
        top: 0,
        left: 0,
        right: 0,
        height: '3px',
        background: `linear-gradient(90deg, ${COLORS.gold}, ${COLORS.goldLight})`,
      }} />
      
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <p style={{ color: COLORS.gray, fontSize: '14px', margin: '0 0 8px' }}>{title}</p>
          <h2 style={{ color: COLORS.white, fontSize: '32px', fontWeight: '700', margin: 0 }}>{value}</h2>
          {trend && (
            <p style={{
              color: trendUp ? COLORS.green : COLORS.red,
              fontSize: '12px',
              margin: '8px 0 0',
            }}>
              {trendUp ? '↑' : '↓'} {trend}
            </p>
          )}
        </div>
        <span style={{
          fontSize: '36px',
          opacity: 0.8,
        }}>{icon}</span>
      </div>
    </div>
  );
};

// Lead Pipeline Kanban Column
const PipelineColumn = ({ title, leads, color, onLeadClick }) => {
  return (
    <div style={{
      flex: 1,
      backgroundColor: COLORS.navyLight,
      borderRadius: '12px',
      padding: '16px',
      minWidth: '250px',
    }}>
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        marginBottom: '16px',
      }}>
        <h3 style={{ color: COLORS.white, fontSize: '14px', margin: 0, fontWeight: '600' }}>
          {title}
        </h3>
        <span style={{
          backgroundColor: color,
          color: COLORS.white,
          fontSize: '12px',
          padding: '4px 10px',
          borderRadius: '12px',
          fontWeight: '600',
        }}>
          {leads.length}
        </span>
      </div>
      
      <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', maxHeight: '400px', overflowY: 'auto' }}>
        {leads.map(lead => (
          <div
            key={lead.id}
            onClick={() => onLeadClick(lead)}
            style={{
              backgroundColor: COLORS.navy,
              borderRadius: '8px',
              padding: '14px',
              cursor: 'pointer',
              border: `1px solid ${COLORS.navyLighter}`,
              transition: 'transform 0.2s',
            }}
            onMouseEnter={e => e.currentTarget.style.transform = 'translateY(-2px)'}
            onMouseLeave={e => e.currentTarget.style.transform = 'translateY(0)'}
          >
            <p style={{ color: COLORS.white, fontSize: '14px', margin: '0 0 8px', fontWeight: '500' }}>
              {lead.name || 'Anonymous'}
            </p>
            <p style={{ color: COLORS.gray, fontSize: '12px', margin: '0 0 8px' }}>
              {lead.phone || 'No phone'}
            </p>
            {lead.budget_max && (
              <p style={{ color: COLORS.gold, fontSize: '12px', margin: '0 0 8px' }}>
                💰 Up to AED {(lead.budget_max / 1000000).toFixed(1)}M
              </p>
            )}
            {lead.purpose && (
              <span style={{
                backgroundColor: COLORS.navyLighter,
                color: COLORS.white,
                fontSize: '11px',
                padding: '4px 8px',
                borderRadius: '4px',
              }}>
                {PURPOSE_LABELS[lead.purpose] || lead.purpose}
              </span>
            )}
          </div>
        ))}
        
        {leads.length === 0 && (
          <p style={{ color: COLORS.gray, fontSize: '13px', textAlign: 'center', padding: '20px' }}>
            No leads in this stage
          </p>
        )}
      </div>
    </div>
  );
};

// Weekly Calendar for Scheduling
const WeeklyCalendar = ({ slots, onAddSlot, onDeleteSlot }) => {
  const [showModal, setShowModal] = useState(false);
  const [selectedDay, setSelectedDay] = useState(null);
  const [newSlot, setNewSlot] = useState({ start_time: '09:00', end_time: '10:00' });

  const handleAddSlot = () => {
    if (selectedDay) {
      onAddSlot({
        day_of_week: selectedDay,
        start_time: newSlot.start_time,
        end_time: newSlot.end_time,
      });
      setShowModal(false);
      setNewSlot({ start_time: '09:00', end_time: '10:00' });
    }
  };

  return (
    <div style={{
      backgroundColor: COLORS.navyLight,
      borderRadius: '12px',
      padding: '20px',
    }}>
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: '20px',
      }}>
        <h3 style={{ color: COLORS.white, fontSize: '16px', margin: 0 }}>📅 Weekly Availability</h3>
        <button
          onClick={() => { setShowModal(true); setSelectedDay(DAYS_OF_WEEK[0]); }}
          style={{
            backgroundColor: COLORS.gold,
            color: COLORS.navy,
            border: 'none',
            padding: '10px 16px',
            borderRadius: '8px',
            cursor: 'pointer',
            fontWeight: '600',
            fontSize: '13px',
          }}
        >
          + Set Availability
        </button>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(7, 1fr)', gap: '10px' }}>
        {DAYS_OF_WEEK.map((day, index) => {
          const daySlots = slots.filter(s => s.day_of_week === day);
          
          return (
            <div key={day} style={{
              backgroundColor: COLORS.navy,
              borderRadius: '8px',
              padding: '12px',
              minHeight: '120px',
            }}>
              <p style={{
                color: COLORS.gold,
                fontSize: '12px',
                fontWeight: '600',
                margin: '0 0 10px',
                textAlign: 'center',
              }}>
                {DAY_LABELS[index]}
              </p>
              
              {daySlots.map(slot => (
                <div
                  key={slot.id}
                  style={{
                    backgroundColor: slot.is_booked ? COLORS.red : COLORS.gold,
                    color: slot.is_booked ? COLORS.white : COLORS.navy,
                    borderRadius: '4px',
                    padding: '6px',
                    fontSize: '11px',
                    marginBottom: '6px',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                  }}
                >
                  <span>{slot.start_time} - {slot.end_time}</span>
                  {!slot.is_booked && (
                    <button
                      onClick={() => onDeleteSlot(slot.id)}
                      style={{
                        backgroundColor: 'transparent',
                        border: 'none',
                        cursor: 'pointer',
                        padding: '0 4px',
                        fontSize: '10px',
                      }}
                    >
                      ✕
                    </button>
                  )}
                </div>
              ))}
              
              {daySlots.length === 0 && (
                <p style={{ color: COLORS.gray, fontSize: '10px', textAlign: 'center' }}>
                  No slots
                </p>
              )}
            </div>
          );
        })}
      </div>

      {/* Add Slot Modal */}
      {showModal && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0,0,0,0.7)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1000,
        }}>
          <div style={{
            backgroundColor: COLORS.navy,
            borderRadius: '12px',
            padding: '24px',
            width: '320px',
            border: `1px solid ${COLORS.gold}`,
          }}>
            <h3 style={{ color: COLORS.white, margin: '0 0 20px' }}>Add Available Slot</h3>
            
            <label style={{ color: COLORS.gray, fontSize: '13px', display: 'block', marginBottom: '6px' }}>
              Day of Week
            </label>
            <select
              value={selectedDay}
              onChange={e => setSelectedDay(e.target.value)}
              style={{
                width: '100%',
                padding: '10px',
                borderRadius: '6px',
                border: `1px solid ${COLORS.navyLighter}`,
                backgroundColor: COLORS.navyLight,
                color: COLORS.white,
                marginBottom: '16px',
              }}
            >
              {DAYS_OF_WEEK.map((day, i) => (
                <option key={day} value={day}>{DAY_LABELS[i]}</option>
              ))}
            </select>
            
            <div style={{ display: 'flex', gap: '12px', marginBottom: '20px' }}>
              <div style={{ flex: 1 }}>
                <label style={{ color: COLORS.gray, fontSize: '13px', display: 'block', marginBottom: '6px' }}>
                  Start Time
                </label>
                <input
                  type="time"
                  value={newSlot.start_time}
                  onChange={e => setNewSlot({ ...newSlot, start_time: e.target.value })}
                  style={{
                    width: '100%',
                    padding: '10px',
                    borderRadius: '6px',
                    border: `1px solid ${COLORS.navyLighter}`,
                    backgroundColor: COLORS.navyLight,
                    color: COLORS.white,
                  }}
                />
              </div>
              <div style={{ flex: 1 }}>
                <label style={{ color: COLORS.gray, fontSize: '13px', display: 'block', marginBottom: '6px' }}>
                  End Time
                </label>
                <input
                  type="time"
                  value={newSlot.end_time}
                  onChange={e => setNewSlot({ ...newSlot, end_time: e.target.value })}
                  style={{
                    width: '100%',
                    padding: '10px',
                    borderRadius: '6px',
                    border: `1px solid ${COLORS.navyLighter}`,
                    backgroundColor: COLORS.navyLight,
                    color: COLORS.white,
                  }}
                />
              </div>
            </div>
            
            <div style={{ display: 'flex', gap: '12px' }}>
              <button
                onClick={() => setShowModal(false)}
                style={{
                  flex: 1,
                  padding: '12px',
                  borderRadius: '6px',
                  border: `1px solid ${COLORS.navyLighter}`,
                  backgroundColor: 'transparent',
                  color: COLORS.white,
                  cursor: 'pointer',
                }}
              >
                Cancel
              </button>
              <button
                onClick={handleAddSlot}
                style={{
                  flex: 1,
                  padding: '12px',
                  borderRadius: '6px',
                  border: 'none',
                  backgroundColor: COLORS.gold,
                  color: COLORS.navy,
                  fontWeight: '600',
                  cursor: 'pointer',
                }}
              >
                Add Slot
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// Lead Table
const LeadTable = ({ leads, onExport }) => {
  return (
    <div style={{
      backgroundColor: COLORS.navyLight,
      borderRadius: '12px',
      overflow: 'hidden',
    }}>
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        padding: '16px 20px',
        borderBottom: `1px solid ${COLORS.navyLighter}`,
      }}>
        <h3 style={{ color: COLORS.white, fontSize: '16px', margin: 0 }}>Lead Manager</h3>
        <button
          onClick={onExport}
          style={{
            backgroundColor: COLORS.green,
            color: COLORS.white,
            border: 'none',
            padding: '10px 16px',
            borderRadius: '8px',
            cursor: 'pointer',
            fontWeight: '600',
            fontSize: '13px',
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
          }}
        >
          📥 Export to Excel
        </button>
      </div>
      
      <div style={{ overflowX: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ backgroundColor: COLORS.navy }}>
              {['Name', 'Phone', 'Budget', 'Purpose', 'Payment', 'Status', 'Voice Transcript'].map(header => (
                <th key={header} style={{
                  color: COLORS.gold,
                  padding: '14px 16px',
                  textAlign: 'left',
                  fontSize: '13px',
                  fontWeight: '600',
                  borderBottom: `1px solid ${COLORS.navyLighter}`,
                }}>
                  {header}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {leads.map(lead => (
              <tr key={lead.id} style={{
                borderBottom: `1px solid ${COLORS.navyLighter}`,
              }}>
                <td style={{ color: COLORS.white, padding: '14px 16px', fontSize: '13px' }}>
                  {lead.name || 'Anonymous'}
                </td>
                <td style={{ color: COLORS.white, padding: '14px 16px', fontSize: '13px' }}>
                  {lead.phone || '-'}
                </td>
                <td style={{ color: COLORS.gold, padding: '14px 16px', fontSize: '13px' }}>
                  {lead.budget_min || lead.budget_max 
                    ? `${lead.budget_min ? `${(lead.budget_min/1000000).toFixed(1)}M` : ''} - ${lead.budget_max ? `${(lead.budget_max/1000000).toFixed(1)}M` : ''}`
                    : '-'}
                </td>
                <td style={{ padding: '14px 16px' }}>
                  <span style={{
                    backgroundColor: lead.purpose === 'residency' ? COLORS.gold : COLORS.navyLighter,
                    color: lead.purpose === 'residency' ? COLORS.navy : COLORS.white,
                    padding: '4px 10px',
                    borderRadius: '12px',
                    fontSize: '11px',
                    fontWeight: '500',
                  }}>
                    {PURPOSE_LABELS[lead.purpose] || lead.purpose || '-'}
                  </span>
                </td>
                <td style={{ color: COLORS.white, padding: '14px 16px', fontSize: '13px', textTransform: 'capitalize' }}>
                  {lead.payment_method || '-'}
                </td>
                <td style={{ padding: '14px 16px' }}>
                  <span style={{
                    backgroundColor: STATUS_COLORS[lead.status] || COLORS.gray,
                    color: COLORS.white,
                    padding: '4px 10px',
                    borderRadius: '12px',
                    fontSize: '11px',
                    fontWeight: '500',
                    textTransform: 'capitalize',
                  }}>
                    {lead.status?.replace('_', ' ') || 'new'}
                  </span>
                </td>
                <td style={{ color: COLORS.gray, padding: '14px 16px', fontSize: '12px', maxWidth: '200px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {lead.voice_transcript || '-'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        
        {leads.length === 0 && (
          <div style={{ padding: '40px', textAlign: 'center' }}>
            <p style={{ color: COLORS.gray }}>No leads yet. Start your Telegram bot to capture leads!</p>
          </div>
        )}
      </div>
    </div>
  );
};

// ==================== MAIN DASHBOARD COMPONENT ====================

const Dashboard = () => {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [tenantId, setTenantId] = useState(1); // Default tenant
  const [stats, setStats] = useState(null);
  const [leads, setLeads] = useState([]);
  const [slots, setSlots] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Fetch dashboard data
  const fetchDashboardData = useCallback(async () => {
    try {
      setLoading(true);
      const [statsData, leadsData, slotsData] = await Promise.all([
        api.get(`/api/tenants/${tenantId}/dashboard/stats`),
        api.get(`/api/tenants/${tenantId}/leads`),
        api.get(`/api/tenants/${tenantId}/schedule`),
      ]);
      
      setStats(statsData);
      setLeads(leadsData);
      setSlots(slotsData);
      setError(null);
    } catch (err) {
      console.error('Failed to fetch dashboard data:', err);
      setError('Failed to load dashboard data. Please try again.');
    } finally {
      setLoading(false);
    }
  }, [tenantId]);

  useEffect(() => {
    fetchDashboardData();
  }, [fetchDashboardData]);

  // Add schedule slot
  const handleAddSlot = async (slotData) => {
    try {
      await api.post(`/api/tenants/${tenantId}/schedule`, slotData);
      fetchDashboardData();
    } catch (err) {
      console.error('Failed to add slot:', err);
      alert('Failed to add slot. Check for time conflicts.');
    }
  };

  // Delete schedule slot
  const handleDeleteSlot = async (slotId) => {
    try {
      await api.delete(`/api/tenants/${tenantId}/schedule/${slotId}`);
      fetchDashboardData();
    } catch (err) {
      console.error('Failed to delete slot:', err);
      alert('Failed to delete slot.');
    }
  };

  // Export leads to Excel
  const handleExportLeads = () => {
    window.open(`${API_BASE_URL}/api/tenants/${tenantId}/leads/export`, '_blank');
  };

  // Group leads by status for Kanban view
  const leadsByStatus = {
    new: leads.filter(l => l.status === 'new' || !l.status),
    qualified: leads.filter(l => l.status === 'qualified'),
    viewing_scheduled: leads.filter(l => l.status === 'viewing_scheduled'),
    closed: leads.filter(l => l.status === 'closed_won' || l.status === 'closed_lost'),
  };

  if (loading) {
    return (
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        height: '100vh',
        backgroundColor: COLORS.navy,
      }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{
            width: '50px',
            height: '50px',
            border: `3px solid ${COLORS.navyLighter}`,
            borderTopColor: COLORS.gold,
            borderRadius: '50%',
            animation: 'spin 1s linear infinite',
            margin: '0 auto 20px',
          }} />
          <p style={{ color: COLORS.gray }}>Loading dashboard...</p>
        </div>
        <style>{`
          @keyframes spin {
            to { transform: rotate(360deg); }
          }
        `}</style>
      </div>
    );
  }

  return (
    <div style={{
      display: 'flex',
      minHeight: '100vh',
      backgroundColor: COLORS.navy,
      fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
    }}>
      {/* Sidebar */}
      <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} />
      
      {/* Main Content */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
        <Header />
        
        <main style={{ flex: 1, padding: '24px', overflowY: 'auto' }}>
          {error && (
            <div style={{
              backgroundColor: 'rgba(239, 68, 68, 0.2)',
              border: `1px solid ${COLORS.red}`,
              borderRadius: '8px',
              padding: '12px 16px',
              marginBottom: '20px',
              color: COLORS.red,
            }}>
              {error}
            </div>
          )}

          {/* Dashboard Tab */}
          {activeTab === 'dashboard' && stats && (
            <>
              {/* KPI Cards */}
              <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(4, 1fr)',
                gap: '20px',
                marginBottom: '30px',
              }}>
                <KPICard
                  title="Total Leads"
                  value={stats.total_leads}
                  icon="👥"
                  trend="+12% from last month"
                  trendUp={true}
                />
                <KPICard
                  title="Active Deals"
                  value={stats.active_deals}
                  icon="🎯"
                  trend="+5% from last week"
                  trendUp={true}
                />
                <KPICard
                  title="Conversion Rate"
                  value={`${stats.conversion_rate}%`}
                  icon="📈"
                  trend="+2.3% improvement"
                  trendUp={true}
                />
                <KPICard
                  title="Scheduled Viewings"
                  value={stats.scheduled_viewings}
                  icon="🏠"
                />
              </div>

              {/* Pipeline View */}
              <h2 style={{ color: COLORS.white, fontSize: '18px', margin: '0 0 16px' }}>Lead Pipeline</h2>
              <div style={{
                display: 'flex',
                gap: '16px',
                marginBottom: '30px',
                overflowX: 'auto',
                paddingBottom: '10px',
              }}>
                <PipelineColumn
                  title="New Leads"
                  leads={leadsByStatus.new}
                  color={STATUS_COLORS.new}
                  onLeadClick={() => {}}
                />
                <PipelineColumn
                  title="Qualified"
                  leads={leadsByStatus.qualified}
                  color={STATUS_COLORS.qualified}
                  onLeadClick={() => {}}
                />
                <PipelineColumn
                  title="Viewing Scheduled"
                  leads={leadsByStatus.viewing_scheduled}
                  color={STATUS_COLORS.viewing_scheduled}
                  onLeadClick={() => {}}
                />
                <PipelineColumn
                  title="Closed"
                  leads={leadsByStatus.closed}
                  color={COLORS.gray}
                  onLeadClick={() => {}}
                />
              </div>

              {/* Calendar Widget */}
              <WeeklyCalendar
                slots={slots}
                onAddSlot={handleAddSlot}
                onDeleteSlot={handleDeleteSlot}
              />
            </>
          )}

          {/* Leads Tab */}
          {activeTab === 'leads' && (
            <LeadTable leads={leads} onExport={handleExportLeads} />
          )}

          {/* Calendar Tab */}
          {activeTab === 'calendar' && (
            <WeeklyCalendar
              slots={slots}
              onAddSlot={handleAddSlot}
              onDeleteSlot={handleDeleteSlot}
            />
          )}

          {/* Placeholder for other tabs */}
          {['properties', 'analytics', 'settings'].includes(activeTab) && (
            <div style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              height: '400px',
              backgroundColor: COLORS.navyLight,
              borderRadius: '12px',
            }}>
              <div style={{ textAlign: 'center' }}>
                <span style={{ fontSize: '48px', display: 'block', marginBottom: '16px' }}>🚧</span>
                <p style={{ color: COLORS.gray, fontSize: '16px' }}>
                  {activeTab.charAt(0).toUpperCase() + activeTab.slice(1)} module coming soon!
                </p>
              </div>
            </div>
          )}
        </main>
      </div>
    </div>
  );
};

export default Dashboard;
