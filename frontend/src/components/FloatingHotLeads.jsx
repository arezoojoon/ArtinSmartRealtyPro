/**
 * Floating Hot Leads Sidebar
 * Real-time display of burning and hot leads
 */

import React, { useState, useEffect } from 'react';
import { X, Flame, Phone, Mail, DollarSign, TrendingUp } from 'lucide-react';

const API_BASE_URL = import.meta.env.VITE_API_URL || '';

const getAuthHeaders = () => {
  const token = localStorage.getItem('token');
  return token ? { 'Authorization': `Bearer ${token}` } : {};
};

const FloatingHotLeads = () => {
  const [hotLeads, setHotLeads] = useState([]);
  const [isMinimized, setIsMinimized] = useState(false);
  const [isVisible, setIsVisible] = useState(true);

  useEffect(() => {
    fetchHotLeads();
    // Refresh every 30 seconds
    const interval = setInterval(fetchHotLeads, 30000);
    return () => clearInterval(interval);
  }, []);

  const fetchHotLeads = async () => {
    try {
      const tenantId = localStorage.getItem('tenantId') || '1';
      const response = await fetch(`${API_BASE_URL}/api/tenants/${tenantId}/leads?limit=100`, {
        headers: getAuthHeaders(),
      });
      
      if (!response.ok) {
        console.error('Failed to fetch leads:', response.statusText);
        return;
      }
      
      const data = await response.json();
      const leads = Array.isArray(data) ? data : (data.leads || []);
      
      // Filter for burning and hot leads
      const hot = leads.filter(lead => 
        lead?.temperature === 'burning' || lead?.temperature === 'hot'
      ).slice(0, 5); // Top 5 hot leads
      
      setHotLeads(hot);
    } catch (error) {
      console.error('Failed to fetch hot leads:', error);
      // Don't crash on error, just log it
    }
  };

  if (!isVisible) return null;

  if (isMinimized) {
    return (
      <div className="fixed bottom-6 right-6 z-50">
        <button
          onClick={() => setIsMinimized(false)}
          className="glass-card rounded-full p-4 shadow-gold hover:shadow-2xl transition-all group"
        >
          <div className="relative">
            <Flame size={28} className="text-red-500 animate-pulse" />
            {hotLeads.length > 0 && (
              <span className="absolute -top-2 -right-2 bg-red-500 text-white text-xs font-bold rounded-full w-6 h-6 flex items-center justify-center animate-bounce">
                {hotLeads.length}
              </span>
            )}
          </div>
        </button>
      </div>
    );
  }

  return (
    <div className="fixed bottom-6 right-6 w-80 z-50 glass-card rounded-2xl shadow-2xl border border-red-500/30">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-white/10">
        <div className="flex items-center gap-2">
          <Flame size={20} className="text-red-500 animate-pulse" />
          <h3 className="text-white font-bold">🔥 Hot Leads</h3>
          <span className="bg-red-500 text-white text-xs font-bold rounded-full px-2 py-0.5">
            {hotLeads.length}
          </span>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => setIsMinimized(true)}
            className="text-white/60 hover:text-white transition-colors"
          >
            −
          </button>
          <button
            onClick={() => setIsVisible(false)}
            className="text-white/60 hover:text-white transition-colors"
          >
            <X size={18} />
          </button>
        </div>
      </div>

      {/* Hot Leads List */}
      <div className="max-h-[400px] overflow-y-auto p-3 space-y-3">
        {hotLeads.length === 0 ? (
          <div className="text-center py-8">
            <Flame size={48} className="text-white/20 mx-auto mb-3" />
            <p className="text-white/40 text-sm">No hot leads at the moment</p>
            <p className="text-white/30 text-xs mt-1">Keep nurturing your leads!</p>
          </div>
        ) : (
          hotLeads.map(lead => (
            <div
              key={lead.id}
              className="bg-navy-800/50 rounded-xl p-3 border border-white/10 hover:border-red-500/30 transition-all cursor-pointer group"
            >
              {/* Name & Temperature */}
              <div className="flex items-start justify-between mb-2">
                <h4 className="text-white font-semibold text-sm group-hover:text-gold-500 transition-colors">
                  {lead?.name || lead?.full_name || 'Anonymous'}
                </h4>
                <span className={`${
                  lead.temperature === 'burning' 
                    ? 'bg-red-500/20 text-red-400 border-red-500/30' 
                    : 'bg-orange-500/20 text-orange-400 border-orange-500/30'
                } px-2 py-0.5 rounded-md text-xs font-bold border`}>
                  {lead.temperature === 'burning' ? '🔥' : '🌶️'}
                </span>
              </div>

              {/* Contact Info */}
              <div className="space-y-1.5 text-xs text-white/70 mb-2">
                {lead.phone && (
                  <div className="flex items-center gap-2">
                    <Phone size={12} className="text-gold-500" />
                    <span>{lead.phone}</span>
                  </div>
                )}
                {lead.email && (
                  <div className="flex items-center gap-2">
                    <Mail size={12} className="text-gold-500" />
                    <span className="truncate">{lead.email}</span>
                  </div>
                )}
                {(lead?.budget_min || lead?.budget_max) && (
                  <div className="flex items-center gap-2">
                    <DollarSign size={12} className="text-gold-500" />
                    <span className="text-gold-400 font-semibold">
                      {lead.budget_min ? `${(Number(lead.budget_min)/1000000).toFixed(1)}M` : ''} 
                      {lead.budget_min && lead.budget_max ? ' - ' : ''}
                      {lead.budget_max ? `${(Number(lead.budget_max)/1000000).toFixed(1)}M` : ''}
                    </span>
                  </div>
                )}
              </div>

              {/* Lead Score */}
              <div className="flex items-center justify-between pt-2 border-t border-white/10">
                <div className="flex items-center gap-1.5">
                  <TrendingUp size={12} className="text-green-400" />
                  <span className="text-white/60 text-xs">
                    Score: <strong className="text-green-400">{lead.lead_score || 0}</strong>
                  </span>
                </div>
                <button className="text-xs font-semibold text-gold-500 hover:text-gold-400 transition-colors">
                  Contact →
                </button>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Footer */}
      <div className="p-3 border-t border-white/10">
        <button
          onClick={fetchHotLeads}
          className="w-full py-2 rounded-lg bg-red-500/10 text-red-400 text-sm font-semibold hover:bg-red-500/20 transition-colors"
        >
          🔄 Refresh Hot Leads
        </button>
      </div>
    </div>
  );
};

export default FloatingHotLeads;
