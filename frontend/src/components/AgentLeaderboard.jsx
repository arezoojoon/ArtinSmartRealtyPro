/**
 * Agent Leaderboard Component
 * Shows top performing agents based on conversions and lead interactions
 */

import React, { useState, useEffect } from 'react';
import { Trophy, TrendingUp, Award, Star } from 'lucide-react';

const API_BASE_URL = import.meta.env.VITE_API_URL || '';

const getAuthHeaders = () => {
  const token = localStorage.getItem('token');
  return token ? { 'Authorization': `Bearer ${token}` } : {};
};

const AgentLeaderboard = () => {
  const [agents, setAgents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [period, setPeriod] = useState('month'); // 'week', 'month', 'year'

  useEffect(() => {
    fetchLeaderboard();
  }, [period]);

  const fetchLeaderboard = async () => {
    try {
      // For now, generate mock data
      // TODO: Connect to real API endpoint /api/agents/leaderboard?period={period}
      
      const mockAgents = [
        {
          id: 1,
          name: 'Current Agent',
          email: 'agent@artinrealty.com',
          avatar: null,
          total_leads: 145,
          converted_leads: 23,
          conversion_rate: 15.9,
          total_interactions: 532,
          revenue_generated: 4500000,
          rank: 1,
          trend: 'up'
        },
        // Can add more agents if multi-agent system
      ];

      setAgents(mockAgents);
    } catch (error) {
      console.error('Failed to fetch leaderboard:', error);
    } finally {
      setLoading(false);
    }
  };

  const getMedalEmoji = (rank) => {
    if (rank === 1) return '🥇';
    if (rank === 2) return '🥈';
    if (rank === 3) return '🥉';
    return `#${rank}`;
  };

  const getMedalColor = (rank) => {
    if (rank === 1) return 'text-yellow-400';
    if (rank === 2) return 'text-gray-300';
    if (rank === 3) return 'text-orange-400';
    return 'text-white/60';
  };

  if (loading) {
    return (
      <div className="glass-card rounded-2xl p-6">
        <div className="animate-pulse">
          <div className="h-6 bg-white/10 rounded w-1/3 mb-4"></div>
          <div className="space-y-3">
            {[1, 2, 3].map(i => (
              <div key={i} className="h-16 bg-white/5 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  // If single agent, show personal stats card
  if (agents.length === 1) {
    const agent = agents[0];
    
    return (
      <div className="glass-card rounded-2xl p-6 border border-gold-500/30">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 bg-gradient-to-br from-gold-500 to-gold-600 rounded-full flex items-center justify-center">
              <Trophy size={24} className="text-navy-900" />
            </div>
            <div>
              <h3 className="text-white font-bold text-lg">Your Performance</h3>
              <p className="text-white/60 text-sm">This {period}</p>
            </div>
          </div>
          
          {/* Period Selector */}
          <select
            value={period}
            onChange={(e) => setPeriod(e.target.value)}
            className="bg-navy-800/50 text-white px-3 py-2 rounded-lg border border-white/10 text-sm focus:border-gold-500 focus:outline-none"
          >
            <option value="week">This Week</option>
            <option value="month">This Month</option>
            <option value="year">This Year</option>
          </select>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-navy-800/50 rounded-xl p-4 border border-white/10">
            <p className="text-white/60 text-xs mb-1">Total Leads</p>
            <p className="text-2xl font-bold text-white">{agent.total_leads}</p>
          </div>
          
          <div className="bg-navy-800/50 rounded-xl p-4 border border-white/10">
            <p className="text-white/60 text-xs mb-1">Converted</p>
            <p className="text-2xl font-bold text-green-400">{agent.converted_leads}</p>
          </div>
          
          <div className="bg-navy-800/50 rounded-xl p-4 border border-white/10">
            <p className="text-white/60 text-xs mb-1">Conv. Rate</p>
            <div className="flex items-center gap-2">
              <p className="text-2xl font-bold text-gold-500">{agent.conversion_rate}%</p>
              {agent.trend === 'up' && (
                <TrendingUp size={16} className="text-green-400" />
              )}
            </div>
          </div>
          
          <div className="bg-navy-800/50 rounded-xl p-4 border border-white/10">
            <p className="text-white/60 text-xs mb-1">Revenue</p>
            <p className="text-2xl font-bold text-gold-500">
              ${(agent.revenue_generated / 1000000).toFixed(1)}M
            </p>
          </div>
        </div>

        {/* Achievement Badges */}
        <div className="mt-6 pt-6 border-t border-white/10">
          <p className="text-white/60 text-sm mb-3">Achievements</p>
          <div className="flex flex-wrap gap-2">
            {agent.conversion_rate > 10 && (
              <span className="badge-gold text-xs flex items-center gap-1">
                <Award size={14} /> High Converter
              </span>
            )}
            {agent.total_leads > 100 && (
              <span className="bg-blue-500/20 text-blue-400 border border-blue-500/30 px-3 py-1.5 rounded-full text-xs font-bold flex items-center gap-1">
                <Star size={14} /> Lead Champion
              </span>
            )}
            {agent.total_interactions > 500 && (
              <span className="bg-purple-500/20 text-purple-400 border border-purple-500/30 px-3 py-1.5 rounded-full text-xs font-bold flex items-center gap-1">
                💬 Super Engaged
              </span>
            )}
          </div>
        </div>
      </div>
    );
  }

  // Multi-agent leaderboard
  return (
    <div className="glass-card rounded-2xl p-6">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <Trophy size={24} className="text-gold-500" />
          <h3 className="text-white font-bold text-lg">Agent Leaderboard</h3>
        </div>
        
        {/* Period Selector */}
        <select
          value={period}
          onChange={(e) => setPeriod(e.target.value)}
          className="bg-navy-800/50 text-white px-3 py-2 rounded-lg border border-white/10 text-sm focus:border-gold-500 focus:outline-none"
        >
          <option value="week">This Week</option>
          <option value="month">This Month</option>
          <option value="year">This Year</option>
        </select>
      </div>

      {/* Leaderboard List */}
      <div className="space-y-3">
        {agents.map((agent, index) => (
          <div
            key={agent.id}
            className={`flex items-center gap-4 p-4 rounded-xl border transition-all hover:shadow-gold ${
              agent.rank === 1 
                ? 'bg-gradient-to-r from-gold-500/10 to-gold-600/5 border-gold-500/30' 
                : 'bg-navy-800/30 border-white/10'
            }`}
          >
            {/* Rank Badge */}
            <div className={`text-2xl font-bold ${getMedalColor(agent.rank)} min-w-[3rem] text-center`}>
              {getMedalEmoji(agent.rank)}
            </div>

            {/* Agent Info */}
            <div className="flex-1">
              <h4 className="text-white font-semibold">{agent.name}</h4>
              <p className="text-white/60 text-sm">{agent.email}</p>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-3 gap-4 text-center">
              <div>
                <p className="text-white/60 text-xs">Leads</p>
                <p className="text-white font-bold">{agent.total_leads}</p>
              </div>
              <div>
                <p className="text-white/60 text-xs">Conv.</p>
                <p className="text-green-400 font-bold">{agent.converted_leads}</p>
              </div>
              <div>
                <p className="text-white/60 text-xs">Rate</p>
                <p className="text-gold-500 font-bold">{agent.conversion_rate}%</p>
              </div>
            </div>

            {/* Trend Indicator */}
            {agent.trend === 'up' && (
              <TrendingUp size={20} className="text-green-400" />
            )}
          </div>
        ))}
      </div>

      {agents.length === 0 && (
        <div className="text-center py-12">
          <Trophy size={48} className="text-white/20 mx-auto mb-3" />
          <p className="text-white/40">No leaderboard data yet</p>
          <p className="text-white/30 text-sm mt-1">Start converting leads to appear here!</p>
        </div>
      )}
    </div>
  );
};

export default AgentLeaderboard;
