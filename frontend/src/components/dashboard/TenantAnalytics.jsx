import { useState, useEffect } from 'react';
import { getSalesFunnel, getAgentPerformance, exportLeads } from '../../api/client';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell, FunnelChart, Funnel, LabelList } from 'recharts';
import { TrendingDown, Download, Trophy, Clock, Target } from 'lucide-react';

/**
 * Sales Funnel & Analytics - Impress the Buyer
 * Shows conversion rates, agent leaderboard, and export functionality
 */

const COLORS = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444'];

export default function TenantAnalytics() {
  const [funnelData, setFunnelData] = useState([]);
  const [agentStats, setAgentStats] = useState([]);
  const [period, setPeriod] = useState('30d');
  const [loading, setLoading] = useState(true);
  const [exporting, setExporting] = useState(false);
  
  useEffect(() => {
    loadAnalytics();
  }, [period]);
  
  const loadAnalytics = async () => {
    try {
      const [funnelRes, agentRes] = await Promise.all([
        getSalesFunnel(period),
        getAgentPerformance(period)
      ]);
      
      setFunnelData(funnelRes.data.funnel);
      setAgentStats(agentRes.data.agents);
    } catch (error) {
      console.error('Failed to load analytics:', error);
    } finally {
      setLoading(false);
    }
  };
  
  const handleExport = async () => {
    setExporting(true);
    try {
      const response = await exportLeads({ period });
      
      // Create download link
      const blob = new Blob([response.data], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `leads_export_${new Date().toISOString().split('T')[0]}.xlsx`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
      
      // Show success notification
      alert('✅ Leads exported successfully!');
    } catch (error) {
      console.error('Failed to export leads:', error);
      alert('❌ Export failed. Please try again.');
    } finally {
      setExporting(false);
    }
  };
  
  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }
  
  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white">📊 Analytics Dashboard</h2>
          <p className="text-gray-600 dark:text-gray-400">Sales performance and conversion metrics</p>
        </div>
        
        <div className="flex gap-3">
          {/* Period Selector */}
          <select
            value={period}
            onChange={(e) => setPeriod(e.target.value)}
            className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 outline-none"
          >
            <option value="7d">Last 7 Days</option>
            <option value="30d">Last 30 Days</option>
            <option value="90d">Last 90 Days</option>
            <option value="365d">Last Year</option>
          </select>
          
          {/* Export Button */}
          <button
            onClick={handleExport}
            disabled={exporting}
            className={`flex items-center gap-2 px-6 py-2 rounded-lg transition-colors ${
              exporting
                ? 'bg-gray-400 cursor-not-allowed'
                : 'bg-gradient-to-r from-green-600 to-green-700 hover:from-green-700 hover:to-green-800'
            } text-white shadow-lg`}
          >
            <Download className="w-5 h-5" />
            {exporting ? 'Exporting...' : 'Export to Excel'}
          </button>
        </div>
      </div>
      
      {/* Sales Funnel */}
      <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow">
        <div className="flex items-center gap-2 mb-6">
          <TrendingDown className="w-6 h-6 text-blue-600" />
          <h3 className="text-xl font-semibold text-gray-900 dark:text-white">Sales Funnel</h3>
        </div>
        
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Funnel Chart */}
          <div>
            <ResponsiveContainer width="100%" height={400}>
              <FunnelChart>
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1F2937',
                    border: 'none',
                    borderRadius: '8px',
                    color: '#fff'
                  }}
                />
                <Funnel
                  dataKey="value"
                  data={funnelData}
                  isAnimationActive
                >
                  <LabelList position="right" fill="#fff" stroke="none" dataKey="name" />
                  {funnelData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Funnel>
              </FunnelChart>
            </ResponsiveContainer>
          </div>
          
          {/* Funnel Stats */}
          <div className="space-y-4">
            {funnelData.map((stage, index) => {
              const percentage = funnelData[0] ? (stage.value / funnelData[0].value * 100).toFixed(1) : 0;
              const dropoff = index > 0 ? ((funnelData[index - 1].value - stage.value) / funnelData[index - 1].value * 100).toFixed(1) : 0;
              
              return (
                <div key={stage.name} className="bg-gray-50 dark:bg-gray-900 rounded-lg p-4">
                  <div className="flex justify-between items-start mb-2">
                    <div>
                      <h4 className="font-semibold text-gray-900 dark:text-white">{stage.name}</h4>
                      <p className="text-sm text-gray-600 dark:text-gray-400">{stage.description}</p>
                    </div>
                    <span className="text-2xl font-bold" style={{ color: COLORS[index % COLORS.length] }}>
                      {stage.value}
                    </span>
                  </div>
                  
                  <div className="flex justify-between items-center text-sm">
                    <span className="text-gray-600 dark:text-gray-400">
                      {percentage}% of total
                    </span>
                    {index > 0 && (
                      <span className="text-red-600 dark:text-red-400">
                        -{dropoff}% drop-off
                      </span>
                    )}
                  </div>
                  
                  {/* Progress Bar */}
                  <div className="mt-2 w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                    <div
                      className="h-2 rounded-full transition-all"
                      style={{
                        width: `${percentage}%`,
                        backgroundColor: COLORS[index % COLORS.length]
                      }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
      
      {/* Agent Leaderboard */}
      <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow">
        <div className="flex items-center gap-2 mb-6">
          <Trophy className="w-6 h-6 text-yellow-600" />
          <h3 className="text-xl font-semibold text-gray-900 dark:text-white">Agent Leaderboard</h3>
        </div>
        
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50 dark:bg-gray-900">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Rank
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Agent
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Closed Deals
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Total Value
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Avg Response Time
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Conversion Rate
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
              {agentStats.map((agent, index) => (
                <tr key={agent.id} className="hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      {index === 0 && <Trophy className="w-5 h-5 text-yellow-500 mr-2" />}
                      {index === 1 && <Trophy className="w-5 h-5 text-gray-400 mr-2" />}
                      {index === 2 && <Trophy className="w-5 h-5 text-orange-600 mr-2" />}
                      <span className="font-semibold text-gray-900 dark:text-white">#{index + 1}</span>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center text-white font-bold mr-3">
                        {agent.name.charAt(0)}
                      </div>
                      <div>
                        <div className="font-medium text-gray-900 dark:text-white">{agent.name}</div>
                        <div className="text-sm text-gray-600 dark:text-gray-400">{agent.email}</div>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center gap-2">
                      <Target className="w-4 h-4 text-green-600" />
                      <span className="text-2xl font-bold text-green-600">{agent.closed_deals}</span>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className="text-gray-900 dark:text-white font-semibold">
                      ${agent.total_value?.toLocaleString() || 0}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center gap-2">
                      <Clock className="w-4 h-4 text-blue-600" />
                      <span className="text-gray-900 dark:text-white">{agent.avg_response_time || '0m'}</span>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center gap-2">
                      <div className="flex-1">
                        <div className="text-sm font-semibold text-gray-900 dark:text-white mb-1">
                          {agent.conversion_rate || 0}%
                        </div>
                        <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                          <div
                            className="bg-gradient-to-r from-green-500 to-green-600 h-2 rounded-full"
                            style={{ width: `${agent.conversion_rate || 0}%` }}
                          />
                        </div>
                      </div>
                    </div>
                  </td>
                </tr>
              ))}
              
              {agentStats.length === 0 && (
                <tr>
                  <td colSpan="6" className="px-6 py-12 text-center text-gray-400">
                    No agent data available for this period
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
