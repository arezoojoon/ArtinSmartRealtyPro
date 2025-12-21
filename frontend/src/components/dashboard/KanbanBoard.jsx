/**
 * Artin Smart Realty - Enhanced Kanban Board
 * CRM Pipeline with drag-and-drop, hotness scoring, and lead actions
 */

import React, { useState, useEffect, useCallback } from 'react';
import { DragDropContext, Droppable, Draggable } from 'react-beautiful-dnd';
import {
  Phone,
  Mail,
  DollarSign,
  TrendingUp,
  MoreVertical,
  MessageSquare,
  FileText,
  Calendar,
  User,
  X,
  Edit,
  Trash2,
  ExternalLink,
} from 'lucide-react';

const API_BASE_URL = import.meta.env.VITE_API_URL || '';

// Pipeline columns configuration
const COLUMNS = [
  { id: 'new', title: 'New Leads', color: 'bg-blue-500' },
  { id: 'qualified', title: 'Qualified', color: 'bg-yellow-500' },
  { id: 'viewing_scheduled', title: 'Viewing Scheduled', color: 'bg-orange-500' },
  { id: 'negotiating', title: 'Negotiation', color: 'bg-purple-500' },
  { id: 'closed_won', title: 'Closed Won', color: 'bg-green-500' },
];

// Calculate hotness score based on lead data
const getHotnessScore = (lead) => {
  let score = 0;

  // Budget factor (0-30 points)
  if (lead.budget_max >= 5000000) score += 30;
  else if (lead.budget_max >= 2000000) score += 25;
  else if (lead.budget_max >= 1000000) score += 20;
  else if (lead.budget_max >= 500000) score += 15;
  else score += 10;

  // Engagement factor (0-30 points)
  if (lead.messages_count > 20) score += 30;
  else if (lead.messages_count > 10) score += 20;
  else if (lead.messages_count > 5) score += 15;
  else score += 5;

  // Response time factor (0-20 points)
  if (lead.last_message_at) {
    const hoursSinceLastMessage = (Date.now() - new Date(lead.last_message_at)) / (1000 * 60 * 60);
    if (hoursSinceLastMessage < 1) score += 20;
    else if (hoursSinceLastMessage < 24) score += 15;
    else if (hoursSinceLastMessage < 72) score += 10;
    else score += 5;
  }

  // Contact info factor (0-20 points)
  if (lead.phone_number || lead.phone) score += 10;
  if (lead.email) score += 10;

  return Math.min(100, score);
};

// Hotness indicator component
const HotnessIndicator = ({ score }) => {
  const getConfig = () => {
    if (score >= 80) return { color: 'text-red-500', bg: 'bg-red-500/20', label: 'Hot' };
    if (score >= 60) return { color: 'text-orange-500', bg: 'bg-orange-500/20', label: 'Warm' };
    if (score >= 40) return { color: 'text-yellow-500', bg: 'bg-yellow-500/20', label: 'Cool' };
    return { color: 'text-blue-500', bg: 'bg-blue-500/20', label: 'Cold' };
  };

  const config = getConfig();

  return (
    <div className={`flex items-center gap-1.5 px-2 py-0.5 rounded-full ${config.bg}`}>
      <TrendingUp className={`w-3 h-3 ${config.color}`} />
      <span className={`text-xs font-bold ${config.color}`}>{score}°</span>
    </div>
  );
};

// Lead action menu component
const LeadActionMenu = ({ lead, onClose, onAction }) => {
  return (
    <div
      className="absolute right-0 top-full mt-1 w-48 glass-card p-2 z-50 animate-slide-up"
      onClick={(e) => e.stopPropagation()}
    >
      <button
        onClick={() => { onAction('whatsapp', lead); onClose(); }}
        className="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-gray-300 hover:bg-navy-700 hover:text-white transition-all"
      >
        <MessageSquare className="w-4 h-4 text-green-400" />
        <span className="text-sm">Send WhatsApp</span>
      </button>
      <button
        onClick={() => { onAction('call', lead); onClose(); }}
        className="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-gray-300 hover:bg-navy-700 hover:text-white transition-all"
      >
        <Phone className="w-4 h-4 text-blue-400" />
        <span className="text-sm">Call</span>
      </button>
      <button
        onClick={() => { onAction('pdf', lead); onClose(); }}
        className="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-gray-300 hover:bg-navy-700 hover:text-white transition-all"
      >
        <FileText className="w-4 h-4 text-purple-400" />
        <span className="text-sm">Send PDF</span>
      </button>
      <button
        onClick={() => { onAction('schedule', lead); onClose(); }}
        className="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-gray-300 hover:bg-navy-700 hover:text-white transition-all"
      >
        <Calendar className="w-4 h-4 text-gold-400" />
        <span className="text-sm">Schedule Viewing</span>
      </button>
      <hr className="my-2 border-white/5" />
      <button
        onClick={() => { onAction('view', lead); onClose(); }}
        className="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-gray-300 hover:bg-navy-700 hover:text-white transition-all"
      >
        <ExternalLink className="w-4 h-4" />
        <span className="text-sm">View Details</span>
      </button>
      <button
        onClick={() => { onAction('edit', lead); onClose(); }}
        className="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-gray-300 hover:bg-navy-700 hover:text-white transition-all"
      >
        <Edit className="w-4 h-4" />
        <span className="text-sm">Edit Lead</span>
      </button>
    </div>
  );
};

// Lead card component
const LeadCard = ({ lead, index, onAction }) => {
  const [showMenu, setShowMenu] = useState(false);
  const hotnessScore = lead.lead_score || getHotnessScore(lead);

  const getTimeAgo = (timestamp) => {
    if (!timestamp) return 'Just Now';
    const now = new Date();
    const time = new Date(timestamp);
    const diff = Math.floor((now - time) / 1000 / 60);

    if (diff < 1) return 'Just Now';
    if (diff < 60) return `${diff}m ago`;
    if (diff < 1440) return `${Math.floor(diff / 60)}h ago`;
    return `${Math.floor(diff / 1440)}d ago`;
  };

  return (
    <Draggable draggableId={lead.id.toString()} index={index}>
      {(provided, snapshot) => (
        <div
          ref={provided.innerRef}
          {...provided.draggableProps}
          {...provided.dragHandleProps}
          className={`lead-card group relative ${snapshot.isDragging ? 'lead-card-dragging shadow-gold' : ''}`}
        >
          {/* Header */}
          <div className="flex items-start gap-3">
            {/* Avatar */}
            <div className="lead-avatar flex-shrink-0">
              {lead.name?.charAt(0)?.toUpperCase() || '?'}
            </div>

            {/* Info */}
            <div className="flex-1 min-w-0">
              <div className="flex items-center justify-between">
                <h4 className="lead-name truncate">{lead.name || `Lead #${lead.id}`}</h4>
                <div className="relative">
                  <button
                    onClick={(e) => { e.stopPropagation(); setShowMenu(!showMenu); }}
                    className={`p-1.5 rounded-lg transition-all ${showMenu ? 'bg-navy-600' : 'opacity-0 group-hover:opacity-100 hover:bg-navy-600'}`}
                  >
                    <MoreVertical className="w-4 h-4 text-gray-400" />
                  </button>
                  {showMenu && (
                    <LeadActionMenu
                      lead={lead}
                      onClose={() => setShowMenu(false)}
                      onAction={onAction}
                    />
                  )}
                </div>
              </div>

              <p className="lead-property truncate">
                {lead.property_type || 'Property'} {lead.transaction_type === 'rent' ? 'Rental' : ''}
                {lead.preferred_location && ` • ${lead.preferred_location}`}
              </p>

              <p className="lead-budget">
                ${(lead.budget_min || 0).toLocaleString()} - ${(lead.budget_max || 0).toLocaleString()}
              </p>
            </div>
          </div>

          {/* Contact Info */}
          {(lead.phone || lead.phone_number || lead.email) && (
            <div className="flex items-center gap-3 mt-3 text-xs text-gray-500">
              {(lead.phone || lead.phone_number) && (
                <span className="flex items-center gap-1">
                  <Phone className="w-3 h-3" />
                  {lead.phone || lead.phone_number}
                </span>
              )}
            </div>
          )}

          {/* Footer */}
          <div className="flex items-center justify-between mt-3 pt-3 border-t border-white/5">
            <HotnessIndicator score={hotnessScore} />
            <span className="lead-time">{getTimeAgo(lead.created_at)}</span>
          </div>
        </div>
      )}
    </Draggable>
  );
};

// Kanban column component
const KanbanColumn = ({ column, leads, onLeadAction }) => {
  return (
    <div className="pipeline-column">
      {/* Column Header */}
      <div className="pipeline-header">
        <div className="pipeline-title">
          <span className={`w-2.5 h-2.5 rounded-full ${column.color}`} />
          <span>{column.title}</span>
        </div>
        <span className="pipeline-count">{leads.length}</span>
      </div>

      {/* Droppable Area */}
      <Droppable droppableId={column.id}>
        {(provided, snapshot) => (
          <div
            ref={provided.innerRef}
            {...provided.droppableProps}
            className={`min-h-[400px] max-h-[600px] overflow-y-auto space-y-3 p-1 rounded-xl transition-colors ${snapshot.isDraggingOver ? 'bg-gold-500/5 ring-2 ring-gold-500/20' : ''
              }`}
          >
            {leads.map((lead, index) => (
              <LeadCard
                key={lead.id}
                lead={lead}
                index={index}
                onAction={onLeadAction}
              />
            ))}
            {provided.placeholder}

            {leads.length === 0 && !snapshot.isDraggingOver && (
              <div className="text-center text-gray-500 text-sm py-12 border-2 border-dashed border-white/10 rounded-xl">
                Drop leads here
              </div>
            )}
          </div>
        )}
      </Droppable>
    </div>
  );
};

// Main KanbanBoard component
export default function KanbanBoard({ tenantId, token }) {
  const [leads, setLeads] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedLead, setSelectedLead] = useState(null);

  // Load leads
  useEffect(() => {
    loadLeads();
  }, [tenantId]);

  const loadLeads = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_BASE_URL}/api/v1/tenants/${tenantId}/leads`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        setLeads(Array.isArray(data) ? data : (data.leads || []));
      }
    } catch (error) {
      console.error('Failed to load leads:', error);
      // Sample data for demo
      setLeads([
        { id: 1, name: 'Sarah Jenkins', property_type: 'Villa', preferred_location: 'Palm Jumeirah', budget_min: 2000000, budget_max: 5000000, status: 'new', lead_score: 85, created_at: new Date() },
        { id: 2, name: 'Michael Chen', property_type: 'Penthouse', preferred_location: 'Downtown', budget_min: 3000000, budget_max: 3500000, status: 'qualified', lead_score: 72, created_at: new Date(Date.now() - 3600000) },
        { id: 3, name: 'Emma Davis', property_type: 'Penthouse', preferred_location: 'Downtown', budget_min: 2000000, budget_max: 2500000, status: 'viewing_scheduled', lead_score: 68, phone: '+971501234567', created_at: new Date(Date.now() - 86400000) },
        { id: 4, name: 'Alex Jonten', property_type: 'Villa', preferred_location: 'Palm Jumeirah', budget_min: 3000000, budget_max: 3500000, status: 'new', lead_score: 45, created_at: new Date() },
        { id: 5, name: 'James Wilson', property_type: 'Apartment', preferred_location: 'Marina', budget_min: 1500000, budget_max: 2000000, status: 'closed_won', lead_score: 92, created_at: new Date(Date.now() - 172800000) },
      ]);
    } finally {
      setLoading(false);
    }
  };

  // Handle drag end
  const onDragEnd = useCallback(async (result) => {
    const { source, destination, draggableId } = result;

    // Dropped outside or no change
    if (!destination) return;
    if (source.droppableId === destination.droppableId && source.index === destination.index) return;

    const leadId = parseInt(draggableId);
    const newStatus = destination.droppableId;

    // Optimistically update UI
    setLeads(prevLeads =>
      prevLeads.map(lead =>
        lead.id === leadId ? { ...lead, status: newStatus } : lead
      )
    );

    // Play sound for won deals
    if (newStatus === 'closed_won') {
      try {
        const audio = new Audio('/sounds/cha-ching.mp3');
        audio.volume = 0.5;
        audio.play().catch(() => { });
      } catch (e) { }

      // Show notification
      if (window.showNotification) {
        const lead = leads.find(l => l.id === leadId);
        window.showNotification({
          type: 'deal_closed',
          title: '💰 Deal Closed!',
          message: `${lead?.name || 'Lead'} moved to Closed Won`,
        });
      }
    }

    // Update on server
    try {
      await fetch(`${API_BASE_URL}/api/v1/leads/${leadId}/status`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ status: newStatus })
      });
    } catch (error) {
      console.error('Failed to update lead status:', error);
      // Revert on error
      loadLeads();
    }
  }, [leads, token]);

  // Handle lead actions
  const handleLeadAction = useCallback((action, lead) => {
    switch (action) {
      case 'whatsapp':
        if (lead.phone || lead.phone_number) {
          window.open(`https://wa.me/${(lead.phone || lead.phone_number).replace(/\D/g, '')}`, '_blank');
        } else {
          alert('No phone number available');
        }
        break;
      case 'call':
        if (lead.phone || lead.phone_number) {
          window.open(`tel:${lead.phone || lead.phone_number}`, '_blank');
        }
        break;
      case 'pdf':
        // TODO: Implement PDF sending
        alert(`Sending PDF to ${lead.name}...`);
        break;
      case 'schedule':
        // TODO: Implement scheduling modal
        alert(`Opening scheduler for ${lead.name}...`);
        break;
      case 'view':
        setSelectedLead(lead);
        break;
      case 'edit':
        setSelectedLead(lead);
        break;
      default:
        console.log(`Action ${action} for lead:`, lead);
    }
  }, []);

  // Group leads by status
  const getLeadsByStatus = (status) => {
    return leads.filter(lead => {
      if (status === 'new') return lead.status === 'new' || !lead.status;
      if (status === 'qualified') return lead.status === 'qualified' || lead.status === 'contacted';
      return lead.status === status;
    });
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="spinner" />
      </div>
    );
  }

  return (
    <div className="p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-2xl font-bold text-white">CRM Pipeline</h2>
          <p className="text-gray-400 text-sm mt-1">Drag & drop leads to update their status</p>
        </div>
        <div className="text-sm text-gray-400">
          {leads.length} total leads
        </div>
      </div>

      {/* Kanban Board */}
      <DragDropContext onDragEnd={onDragEnd}>
        <div className="flex gap-5 overflow-x-auto pb-4">
          {COLUMNS.map(column => (
            <KanbanColumn
              key={column.id}
              column={column}
              leads={getLeadsByStatus(column.id)}
              onLeadAction={handleLeadAction}
            />
          ))}
        </div>
      </DragDropContext>

      {/* Lead Detail Modal */}
      {selectedLead && (
        <div className="modal-overlay" onClick={() => setSelectedLead(null)}>
          <div className="modal-content max-w-2xl" onClick={e => e.stopPropagation()}>
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center gap-4">
                <div className="lead-avatar w-14 h-14 text-lg">
                  {selectedLead.name?.charAt(0)?.toUpperCase() || '?'}
                </div>
                <div>
                  <h3 className="text-xl font-bold text-white">{selectedLead.name}</h3>
                  <p className="text-gray-400">{selectedLead.email || 'No email'}</p>
                </div>
              </div>
              <button onClick={() => setSelectedLead(null)} className="text-gray-400 hover:text-white">
                <X className="w-6 h-6" />
              </button>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="bg-navy-800/50 rounded-xl p-4">
                <p className="text-xs text-gray-400 mb-1">Property Interest</p>
                <p className="text-white">{selectedLead.property_type || 'Not specified'}</p>
              </div>
              <div className="bg-navy-800/50 rounded-xl p-4">
                <p className="text-xs text-gray-400 mb-1">Location</p>
                <p className="text-white">{selectedLead.preferred_location || 'Not specified'}</p>
              </div>
              <div className="bg-navy-800/50 rounded-xl p-4">
                <p className="text-xs text-gray-400 mb-1">Budget</p>
                <p className="text-gold-400 font-medium">
                  ${(selectedLead.budget_min || 0).toLocaleString()} - ${(selectedLead.budget_max || 0).toLocaleString()}
                </p>
              </div>
              <div className="bg-navy-800/50 rounded-xl p-4">
                <p className="text-xs text-gray-400 mb-1">Lead Score</p>
                <HotnessIndicator score={selectedLead.lead_score || getHotnessScore(selectedLead)} />
              </div>
            </div>

            <div className="flex gap-3 mt-6">
              <button
                onClick={() => handleLeadAction('whatsapp', selectedLead)}
                className="flex-1 btn-outline flex items-center justify-center gap-2"
              >
                <MessageSquare className="w-4 h-4" />
                WhatsApp
              </button>
              <button
                onClick={() => handleLeadAction('call', selectedLead)}
                className="flex-1 btn-outline flex items-center justify-center gap-2"
              >
                <Phone className="w-4 h-4" />
                Call
              </button>
              <button
                onClick={() => handleLeadAction('schedule', selectedLead)}
                className="flex-1 btn-gold flex items-center justify-center gap-2"
              >
                <Calendar className="w-4 h-4" />
                Schedule
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
