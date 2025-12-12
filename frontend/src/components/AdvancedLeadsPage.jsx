/**
 * Advanced Leads Management Page
 * Features: Drag & Drop Kanban, Search, Filters, Pagination, Temperature Categorization
 * Based on New Folder UI/UX with Glassmorphism Design
 */

import React, { useState, useEffect } from 'react';
import {
  Plus,
  Search,
  Filter,
  Download,
  Phone,
  Mail,
  Calendar,
  MapPin,
  Edit,
  Trash2,
  GripVertical,
  X,
  Clock,
  DollarSign,
  Flame,
  Thermometer,
  Snowflake,
  Sun,
  ChevronLeft,
  ChevronRight,
  TrendingUp
} from 'lucide-react';
import { DragDropContext, Droppable, Draggable } from 'react-beautiful-dnd';

// ==================== CONSTANTS ====================

const API_BASE_URL = import.meta.env.VITE_API_URL || '';

const LEAD_STATUSES = {
  new: { label: 'New', color: 'bg-red-500', icon: '🆕' },
  contacted: { label: 'Contacted', color: 'bg-orange-500', icon: '📞' },
  qualified: { label: 'Qualified', color: 'bg-yellow-500', icon: '⭐' },
  viewing_scheduled: { label: 'Viewing Scheduled', color: 'bg-green-500', icon: '📅' },
  negotiating: { label: 'Negotiating', color: 'bg-blue-500', icon: '💰' },
  closed_won: { label: 'Closed Won', color: 'bg-green-600', icon: '🎉' },
  closed_lost: { label: 'Closed Lost', color: 'bg-gray-500', icon: '❌' },
};

const TEMPERATURE_CONFIG = {
  burning: { emoji: '🔥', color: 'bg-red-500/20 text-red-400 border-red-500/30', label: 'BURNING', icon: Flame },
  hot: { emoji: '🌶️', color: 'bg-orange-500/20 text-orange-400 border-orange-500/30', label: 'HOT', icon: Thermometer },
  warm: { emoji: '☀️', color: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30', label: 'WARM', icon: Sun },
  cold: { emoji: '❄️', color: 'bg-blue-500/20 text-blue-400 border-blue-500/30', label: 'COLD', icon: Snowflake },
};

const PURPOSE_LABELS = {
  investment: '📈 Investment',
  living: '🏡 Living',
  residency: '🛂 Residency/Visa',
};

// ==================== API HELPERS ====================

const getAuthHeaders = () => {
  const token = localStorage.getItem('token');
  return token ? { 'Authorization': `Bearer ${token}` } : {};
};

const api = {
  async get(endpoint) {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      headers: getAuthHeaders(),
    });
    if (!response.ok) throw new Error(`API Error: ${response.statusText}`);
    return response.json();
  },
  async patch(endpoint, data) {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: 'PATCH',
      headers: { ...getAuthHeaders(), 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!response.ok) throw new Error(`API Error: ${response.statusText}`);
    return response.json();
  },
  async post(endpoint, data) {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: 'POST',
      headers: { ...getAuthHeaders(), 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!response.ok) throw new Error(`API Error: ${response.statusText}`);
    return response.json();
  },
  async delete(endpoint) {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: 'DELETE',
      headers: getAuthHeaders(),
    });
    if (!response.ok) throw new Error(`API Error: ${response.statusText}`);
    return response.json();
  },
};

// ==================== LEAD CARD COMPONENT ====================

const LeadCard = ({ lead, index, isDragging }) => {
  const tempConfig = TEMPERATURE_CONFIG[lead?.temperature] || TEMPERATURE_CONFIG.cold;

  return (
    <div className={`glass-card rounded-xl p-4 cursor-move hover:shadow-gold transition-all ${
      isDragging ? 'opacity-50 rotate-2' : ''
    }`}>
      {/* Drag Handle */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-2">
          <GripVertical size={16} className="text-white/30" />
          <h4 className="text-white font-semibold text-sm">{lead?.name || lead?.full_name || 'Anonymous'}</h4>
        </div>
        {/* Temperature Badge */}
        <span className={`${tempConfig.color} px-2 py-1 rounded-md text-xs font-bold border flex items-center gap-1`}>
          {tempConfig.emoji} {tempConfig.label}
        </span>
      </div>

      {/* Lead Info */}
      <div className="space-y-2 text-xs text-white/70">
        {lead.phone && (
          <div className="flex items-center gap-2">
            <Phone size={14} className="text-gold-500" />
            <span>{lead.phone}</span>
          </div>
        )}
        {lead.email && (
          <div className="flex items-center gap-2">
            <Mail size={14} className="text-gold-500" />
            <span className="truncate">{lead.email}</span>
          </div>
        )}
        {(lead?.budget_min || lead?.budget_max) && (
          <div className="flex items-center gap-2">
            <DollarSign size={14} className="text-gold-500" />
            <span className="text-gold-400 font-semibold">
              {lead.budget_min ? `${(Number(lead.budget_min)/1000000).toFixed(1)}M` : ''} 
              {lead.budget_min && lead.budget_max ? ' - ' : ''}
              {lead.budget_max ? `${(Number(lead.budget_max)/1000000).toFixed(1)}M` : ''}
            </span>
          </div>
        )}
        {lead.purpose && (
          <div className="flex items-center gap-2">
            <span>{PURPOSE_LABELS[lead.purpose] || lead.purpose}</span>
          </div>
        )}
      </div>

      {/* Lead Score & Interactions */}
      <div className="flex items-center justify-between mt-3 pt-3 border-t border-white/10">
        <div className="flex items-center gap-2">
          <TrendingUp size={14} className="text-green-400" />
          <span className="text-white/60 text-xs">Score: <strong className="text-green-400">{lead.lead_score || 0}</strong></span>
        </div>
        <div className="flex items-center gap-2 text-white/40 text-xs">
          {(lead?.total_interactions || 0) > 0 && (
            <span>💬 {lead.total_interactions}</span>
          )}
        </div>
      </div>

      {/* Quick Actions */}
      <div className="flex gap-2 mt-3">
        <button className="flex-1 px-3 py-1.5 rounded-lg bg-gold-500/10 text-gold-500 text-xs font-semibold hover:bg-gold-500/20 transition-colors">
          <Edit size={12} className="inline mr-1" />
          Edit
        </button>
        <button className="px-3 py-1.5 rounded-lg bg-red-500/10 text-red-400 text-xs font-semibold hover:bg-red-500/20 transition-colors">
          <Trash2 size={12} />
        </button>
      </div>
    </div>
  );
};

// ==================== KANBAN COLUMN COMPONENT ====================

const KanbanColumn = ({ status, statusConfig, leads, provided, snapshot }) => (
  <div className="flex-1 min-w-[300px]">
    <div className="glass-card rounded-2xl p-5">
      {/* Column Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <span className="text-2xl">{statusConfig.icon}</span>
          <h3 className="text-white font-semibold">{statusConfig.label}</h3>
        </div>
        <span className={`${statusConfig.color} text-white text-xs px-3 py-1.5 rounded-full font-bold`}>
          {leads.length}
        </span>
      </div>

      {/* Droppable Area */}
      <div
        ref={provided.innerRef}
        {...provided.droppableProps}
        className={`space-y-3 min-h-[400px] max-h-[600px] overflow-y-auto pr-2 ${
          snapshot.isDraggingOver ? 'bg-white/5 rounded-xl' : ''
        }`}
      >
        {leads.map((lead, index) => (
          <Draggable key={lead.id} draggableId={String(lead.id)} index={index}>
            {(provided, snapshot) => (
              <div
                ref={provided.innerRef}
                {...provided.draggableProps}
                {...provided.dragHandleProps}
              >
                <LeadCard lead={lead} index={index} isDragging={snapshot.isDragging} />
              </div>
            )}
          </Draggable>
        ))}
        {provided.placeholder}
        
        {leads.length === 0 && (
          <div className="text-center py-12 text-white/30">
            <p>No leads in this stage</p>
            <p className="text-xs mt-2">Drag leads here</p>
          </div>
        )}
      </div>
    </div>
  </div>
);

// ==================== MAIN COMPONENT ====================

const AdvancedLeadsPage = () => {
  const [leads, setLeads] = useState([]);
  const [filteredLeads, setFilteredLeads] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterStatus, setFilterStatus] = useState('all');
  const [filterTemperature, setFilterTemperature] = useState('all');
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage] = useState(50);
  const [viewMode, setViewMode] = useState('kanban'); // 'kanban' or 'table'

  useEffect(() => {
    fetchLeads();
  }, []);

  useEffect(() => {
    filterLeads();
  }, [leads, searchQuery, filterStatus, filterTemperature]);

  const fetchLeads = async () => {
    try {
      const response = await api.get('/api/leads?limit=1000');
      const leadsData = Array.isArray(response) ? response : (response.leads || []);
      setLeads(leadsData);
    } catch (error) {
      console.error('Failed to fetch leads:', error);
      // Set empty array on error to prevent crashes
      setLeads([]);
    } finally {
      setLoading(false);
    }
  };

  const filterLeads = () => {
    let filtered = [...leads];

    // Status filter
    if (filterStatus !== 'all') {
      filtered = filtered.filter(lead => lead.status === filterStatus);
    }

    // Temperature filter
    if (filterTemperature !== 'all') {
      filtered = filtered.filter(lead => lead.temperature === filterTemperature);
    }

    // Search filter
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(lead =>
        lead?.name?.toLowerCase().includes(query) ||
        lead?.full_name?.toLowerCase().includes(query) ||
        lead?.phone?.toLowerCase().includes(query) ||
        lead?.email?.toLowerCase().includes(query) ||
        lead?.company_name?.toLowerCase().includes(query)
      );
    }

    setFilteredLeads(filtered);
  };

  const handleDragEnd = async (result) => {
    if (!result.destination) return;

    const { source, destination, draggableId } = result;
    
    // If dropped in same column, no change needed
    if (source.droppableId === destination.droppableId) return;

    const leadId = parseInt(draggableId);
    const newStatus = destination.droppableId;

    // Optimistically update UI
    const updatedLeads = leads.map(lead =>
      lead.id === leadId ? { ...lead, status: newStatus } : lead
    );
    setLeads(updatedLeads);

    // Update backend
    try {
      await api.patch(`/api/leads/${leadId}`, { status: newStatus });
      console.log(`✅ Lead ${leadId} moved to ${newStatus}`);
    } catch (error) {
      console.error('Failed to update lead status:', error);
      // Revert on error
      fetchLeads();
    }
  };

  const exportToExcel = () => {
    // CSV export functionality
    const csvContent = [
      ['Name', 'Phone', 'Email', 'Budget Min', 'Budget Max', 'Purpose', 'Status', 'Temperature', 'Lead Score'],
      ...filteredLeads.map(lead => [
        lead.name || '',
        lead.phone || '',
        lead.email || '',
        lead.budget_min || '',
        lead.budget_max || '',
        lead.purpose || '',
        lead.status || '',
        lead.temperature || '',
        lead.lead_score || 0
      ])
    ].map(row => row.join(',')).join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `leads_export_${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
  };

  // Group leads by status for Kanban view
  const leadsByStatus = Object.keys(LEAD_STATUSES).reduce((acc, status) => {
    acc[status] = filteredLeads.filter(lead => lead.status === status);
    return acc;
  }, {});

  // Pagination
  const totalPages = Math.ceil(filteredLeads.length / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const paginatedLeads = filteredLeads.slice(startIndex, startIndex + itemsPerPage);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="animate-spin rounded-full h-16 w-16 border-t-2 border-b-2 border-gold-500"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen p-6 space-y-6">
      {/* Header Section */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-4xl font-bold text-white mb-2">Lead Management</h1>
          <p className="text-white/60">
            Total: <strong className="text-gold-500">{filteredLeads.length}</strong> leads
          </p>
        </div>
        <div className="flex gap-3">
          <button
            onClick={exportToExcel}
            className="btn-gold flex items-center gap-2"
          >
            <Download size={18} />
            Export to Excel
          </button>
          <button className="btn-gold flex items-center gap-2">
            <Plus size={18} />
            Add Lead
          </button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {Object.entries(TEMPERATURE_CONFIG).map(([key, config]) => {
          const count = filteredLeads.filter(l => l.temperature === key).length;
          const Icon = config.icon;
          return (
            <div
              key={key}
              className="glass-card rounded-xl p-5 cursor-pointer hover:shadow-gold transition-all"
              onClick={() => setFilterTemperature(filterTemperature === key ? 'all' : key)}
            >
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-white/60 text-sm mb-1">{config.label} Leads</p>
                  <p className="text-3xl font-bold text-white">{count}</p>
                </div>
                <div className={`${config.color} p-4 rounded-xl border`}>
                  <Icon size={28} />
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Filters Bar */}
      <div className="glass-card rounded-xl p-4">
        <div className="flex flex-wrap gap-4">
          {/* Search */}
          <div className="flex-1 min-w-[300px]">
            <div className="relative">
              <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 text-white/40" size={20} />
              <input
                type="text"
                placeholder="Search leads by name, phone, email..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full bg-navy-800/50 text-white pl-12 pr-4 py-3 rounded-xl border border-white/10 focus:border-gold-500 focus:outline-none transition-colors"
              />
              {searchQuery && (
                <button
                  onClick={() => setSearchQuery('')}
                  className="absolute right-4 top-1/2 transform -translate-y-1/2 text-white/40 hover:text-white"
                >
                  <X size={18} />
                </button>
              )}
            </div>
          </div>

          {/* Status Filter */}
          <select
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
            className="bg-navy-800/50 text-white px-4 py-3 rounded-xl border border-white/10 focus:border-gold-500 focus:outline-none cursor-pointer"
          >
            <option value="all">All Statuses</option>
            {Object.entries(LEAD_STATUSES).map(([key, config]) => (
              <option key={key} value={key}>{config.icon} {config.label}</option>
            ))}
          </select>

          {/* View Toggle */}
          <div className="flex gap-2 bg-navy-800/50 p-1 rounded-xl border border-white/10">
            <button
              onClick={() => setViewMode('kanban')}
              className={`px-4 py-2 rounded-lg text-sm font-semibold transition-colors ${
                viewMode === 'kanban' ? 'bg-gold-500 text-navy-900' : 'text-white/60 hover:text-white'
              }`}
            >
              📋 Kanban
            </button>
            <button
              onClick={() => setViewMode('table')}
              className={`px-4 py-2 rounded-lg text-sm font-semibold transition-colors ${
                viewMode === 'table' ? 'bg-gold-500 text-navy-900' : 'text-white/60 hover:text-white'
              }`}
            >
              📊 Table
            </button>
          </div>
        </div>
      </div>

      {/* Kanban View */}
      {viewMode === 'kanban' && (
        <DragDropContext onDragEnd={handleDragEnd}>
          <div className="flex gap-4 overflow-x-auto pb-4">
            {Object.entries(LEAD_STATUSES).map(([status, statusConfig]) => (
              <Droppable key={status} droppableId={status}>
                {(provided, snapshot) => (
                  <KanbanColumn
                    status={status}
                    statusConfig={statusConfig}
                    leads={leadsByStatus[status] || []}
                    provided={provided}
                    snapshot={snapshot}
                  />
                )}
              </Droppable>
            ))}
          </div>
        </DragDropContext>
      )}

      {/* Table View */}
      {viewMode === 'table' && (
        <div className="glass-card rounded-2xl overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="bg-navy-900/50">
                  {['Name', 'Phone', 'Email', 'Budget', 'Purpose', 'Status', 'Temperature', 'Score'].map(header => (
                    <th key={header} className="text-gold-500 text-left px-6 py-4 text-sm font-bold border-b border-white/10 uppercase tracking-wide">
                      {header}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {paginatedLeads.map(lead => {
                  const tempConfig = TEMPERATURE_CONFIG[lead.temperature] || TEMPERATURE_CONFIG.cold;
                  const statusConfig = LEAD_STATUSES[lead.status] || LEAD_STATUSES.new;
                  
                  return (
                    <tr key={lead.id} className="border-b border-white/5 hover:bg-white/5 transition-colors cursor-pointer">
                      <td className="text-white px-6 py-4 text-sm font-medium">{lead?.name || lead?.full_name || 'Anonymous'}</td>
                      <td className="text-white px-6 py-4 text-sm">{lead?.phone || '-'}</td>
                      <td className="text-white px-6 py-4 text-sm">{lead?.email || '-'}</td>
                      <td className="text-gold-500 px-6 py-4 text-sm font-semibold">
                        {lead?.budget_min || lead?.budget_max
                          ? `${lead.budget_min ? `${(Number(lead.budget_min)/1000000).toFixed(1)}M` : ''} ${lead.budget_min && lead.budget_max ? '-' : ''} ${lead.budget_max ? `${(Number(lead.budget_max)/1000000).toFixed(1)}M` : ''}`
                          : '-'}
                      </td>
                      <td className="px-6 py-4">
                        <span className="badge-gold text-xs">
                          {PURPOSE_LABELS[lead?.purpose] || lead?.purpose || '-'}
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        <span className={`${statusConfig.color} text-white text-xs px-3 py-1.5 rounded-full font-bold`}>
                          {statusConfig.icon} {statusConfig.label}
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        <span className={`${tempConfig.color} px-2 py-1 rounded-md text-xs font-bold border`}>
                          {tempConfig.emoji} {tempConfig.label}
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-2">
                          <TrendingUp size={16} className="text-green-400" />
                          <span className="text-white font-semibold">{lead?.lead_score || 0}</span>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between px-6 py-4 border-t border-white/10">
              <p className="text-white/60 text-sm">
                Showing {startIndex + 1} to {Math.min(startIndex + itemsPerPage, filteredLeads.length)} of {filteredLeads.length} leads
              </p>
              <div className="flex gap-2">
                <button
                  onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                  disabled={currentPage === 1}
                  className="px-4 py-2 rounded-lg bg-navy-800/50 text-white disabled:opacity-30 disabled:cursor-not-allowed hover:bg-navy-700 transition-colors"
                >
                  <ChevronLeft size={18} />
                </button>
                <span className="px-4 py-2 text-white">
                  Page {currentPage} of {totalPages}
                </span>
                <button
                  onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                  disabled={currentPage === totalPages}
                  className="px-4 py-2 rounded-lg bg-navy-800/50 text-white disabled:opacity-30 disabled:cursor-not-allowed hover:bg-navy-700 transition-colors"
                >
                  <ChevronRight size={18} />
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default AdvancedLeadsPage;
