/**
 * Impersonation Warning Bar
 * Sticky top bar shown when Super Admin is viewing a tenant's dashboard
 */

import React from 'react';
import { AlertTriangle } from 'lucide-react';

const ImpersonationBar = ({ tenantName, onExit }) => {
  return (
    <div className="fixed top-0 left-0 right-0 z-50 glass-card border-b-2 border-gold-500 bg-yellow-500/20 backdrop-blur-xl p-3 shadow-lg">
      <div className="flex items-center justify-between max-w-screen-2xl mx-auto px-6">
        <div className="flex items-center gap-3 text-gold-500 font-semibold">
          <AlertTriangle size={20} className="animate-pulse" />
          <span>⚠️ You are viewing <span className="text-white font-bold">{tenantName}</span>'s dashboard</span>
        </div>
        <button 
          onClick={onExit} 
          className="btn-gold text-sm py-2 px-4 hover:scale-105 transition-transform"
        >
          Exit to Super Admin
        </button>
      </div>
    </div>
  );
};

export default ImpersonationBar;
