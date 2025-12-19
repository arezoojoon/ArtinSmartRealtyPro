import { useState, useEffect } from 'react'
import { Layout } from '../components/Layout'
import FloatingHotLeads from '../components/FloatingHotLeads'
import AgentLeaderboard from '../components/AgentLeaderboard'
import LiveIndicator from '../components/LiveIndicator'
import { api } from '../context/AuthContext'
import { useLeadNotifications } from '../hooks/useLeadNotifications'
import { toast } from '../utils/toast'
import { 
  Users, 
  TrendingUp, 
  DollarSign,
  ArrowUp,
  ArrowDown,
  Phone,
  Mail,
  Calendar,
  MapPin,
  Clock
} from 'lucide-react'

const Dashboard = () => {
  // Enable notifications
  useLeadNotifications()
  
  const [stats, setStats] = useState(null)
  const [leads, setLeads] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchDashboardData()
  }, [])

  const fetchDashboardData = async () => {
    try {
      const [statsRes, leadsRes] = await Promise.all([
        api.get('/api/analytics/stats'),
        api.get('/api/leads?limit=20')
      ])
      
      setStats(statsRes.data)
      setLeads(leadsRes.data.leads || [])
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error)
      toast.error('Failed to load dashboard data')
    } finally {
      setLoading(false)
    }
  }

  // WebSocket event handlers
  const handleNewLead = (data) => {
    console.log('🆕 New lead via WebSocket:', data)
    fetchDashboardData() // Refresh data
  }

  const handleLeadUpdate = (data) => {
    console.log('🔄 Lead updated via WebSocket:', data)
    // Optionally refresh specific lead
  }

  const handleHotLead = (data) => {
    console.log('🔥 Hot lead via WebSocket:', data)
    // Show notification or update UI
  }

  if (loading) {
    return (
      <Layout>
        <div className="flex items-center justify-center h-96">
          <div className="spinner"></div>
        </div>
      </Layout>
    )
  }

  // KPI Data
  const kpis = [
    {
      title: 'Total Leads',
      value: stats?.total_leads || 0,
      change: '+12.5%',
      trend: 'up',
      icon: Users,
      color: 'gold'
    },
    {
      title: 'Active Deals',
      value: stats?.viewing_scheduled || 0,
      change: '+8.3%',
      trend: 'up',
      icon: Users,
      color: 'green'
    },
    {
      title: 'Conversion Rate',
      value: `${(stats?.conversion_rate || 0).toFixed(1)}%`,
      change: '+3.2%',
      trend: 'up',
      icon: TrendingUp,
      color: 'blue'
    },
    {
      title: 'Avg Deal Value',
      value: `$${((stats?.avg_deal_value || 0) / 1000).toFixed(0)}K`,
      change: '+18.7%',
      trend: 'up',
      icon: DollarSign,
      color: 'purple'
    }
  ]

  // Pipeline columns
  const pipeline = {
    new: leads.filter(l => l.status === 'new'),
    qualified: leads.filter(l => l.status === 'qualified'),
    viewing_scheduled: leads.filter(l => l.status === 'viewing_scheduled'),
    closed_won: leads.filter(l => l.status === 'closed_won')
  }

  return (
    <Layout>
      {/* Live Indicator with WebSocket */}
      <LiveIndicator
        onNewLead={handleNewLead}
        onLeadUpdate={handleLeadUpdate}
        onHotLead={handleHotLead}
      />

      <div className="space-y-8 animate-fade-in">
        {/* Page Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-white mb-2">
              Dashboard Overview
            </h1>
            <p className="text-gray-400">
              Welcome back! Here's what's happening with your leads today.
            </p>
          </div>
          <div className="flex items-center gap-2 glass-card px-4 py-2 rounded-xl">
            <Clock className="w-4 h-4 text-gold-500" />
            <span className="text-sm text-white/70">
              {new Date().toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' })}
            </span>
          </div>
        </div>

        {/* KPI Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {kpis.map((kpi, index) => (
            <KPICard key={index} {...kpi} />
          ))}
        </div>

        {/* Agent Leaderboard */}
        <AgentLeaderboard />

        {/* Pipeline Section */}
        <div>
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-2xl font-bold text-white">Lead Pipeline</h2>
            <div className="flex gap-2 glass-card rounded-xl p-1">
              <button className="px-4 py-2 bg-gold-500/15 text-gold-500 rounded-lg text-sm font-medium">
                Kanban
              </button>
              <button className="px-4 py-2 text-white/50 hover:bg-white/5 rounded-lg text-sm font-medium transition-colors">
                List
              </button>
              <button className="px-4 py-2 text-white/50 hover:bg-white/5 rounded-lg text-sm font-medium transition-colors">
                Calendar
              </button>
            </div>
          </div>

          {/* Kanban Board */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <PipelineColumn 
              title="New Leads" 
              badge="red" 
              count={pipeline.new.length}
              leads={pipeline.new}
            />
            <PipelineColumn 
              title="Qualified" 
              badge="yellow" 
              count={pipeline.qualified.length}
              leads={pipeline.qualified}
            />
            <PipelineColumn 
              title="Viewing Scheduled" 
              badge="green" 
              count={pipeline.viewing_scheduled.length}
              leads={pipeline.viewing_scheduled}
            />
            <PipelineColumn 
              title="Closed" 
              badge="blue" 
              count={pipeline.closed_won.length}
              leads={pipeline.closed_won}
            />
          </div>
        </div>
      </div>
      
      {/* Floating Hot Leads Panel */}
      <FloatingHotLeads />
    </Layout>
  )
}

// KPI Card Component
const KPICard = ({ title, value, change, trend, icon: Icon, color }) => {
  const colorClasses = {
    gold: 'bg-gold-500/20 text-gold-500',
    green: 'bg-green-500/20 text-green-500',
    blue: 'bg-blue-500/20 text-blue-500',
    purple: 'bg-purple-500/20 text-purple-500'
  }

  return (
    <div className="glass-card glass-card-hover rounded-2xl p-6 relative overflow-hidden group">
      {/* Background gradient */}
      <div className="absolute inset-0 bg-gradient-to-br from-gold-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity"></div>
      
      <div className="relative">
        <div className="flex items-start justify-between mb-4">
          <p className="text-sm font-medium text-white/50 uppercase tracking-wider">
            {title}
          </p>
          <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${colorClasses[color]}`}>
            <Icon className="w-6 h-6" />
          </div>
        </div>

        <div className="mb-3">
          <h3 className="text-3xl font-bold text-white">{value}</h3>
        </div>

        <div className={`flex items-center gap-2 text-sm ${trend === 'up' ? 'text-green-400' : 'text-red-400'}`}>
          {trend === 'up' ? (
            <ArrowUp className="w-4 h-4" />
          ) : (
            <ArrowDown className="w-4 h-4" />
          )}
          <span className="font-semibold">{change}</span>
          <span className="text-white/40">from last month</span>
        </div>
      </div>
    </div>
  )
}

// Pipeline Column Component
const PipelineColumn = ({ title, badge, count, leads }) => {
  const badgeClasses = {
    red: 'badge-red',
    yellow: 'badge-yellow',
    green: 'badge-green',
    blue: 'badge-blue'
  }

  return (
    <div className="glass-card rounded-2xl p-6 min-h-[600px] flex flex-col">
      {/* Column Header */}
      <div className="flex items-center justify-between mb-6 pb-4 border-b border-white/5">
        <div className="flex items-center gap-3">
          <h3 className="font-semibold text-white">{title}</h3>
          <span className={badgeClasses[badge]}>{count}</span>
        </div>
        <span className="text-sm text-white/40">{count} leads</span>
      </div>

      {/* Lead Cards */}
      <div className="space-y-4 flex-1 overflow-y-auto">
        {leads.length > 0 ? (
          leads.map((lead) => <LeadCard key={lead.id} lead={lead} />)
        ) : (
          <div className="flex items-center justify-center h-40 text-white/30 text-sm">
            No leads in this stage
          </div>
        )}
      </div>
    </div>
  )
}

// Lead Card Component
const LeadCard = ({ lead }) => {
  const priorityColors = {
    low: 'bg-green-500',
    medium: 'bg-yellow-500',
    high: 'bg-red-500',
    urgent: 'bg-purple-500'
  }

  return (
    <div className="bg-white/5 border border-white/10 rounded-xl p-4 hover:bg-white/10 hover:border-gold-500/30 transition-all cursor-pointer group">
      <div className="flex items-start justify-between mb-3">
        <div>
          <h4 className="font-semibold text-white group-hover:text-gold-500 transition-colors">
            {lead.full_name}
          </h4>
          <p className="text-sm text-white/50">{lead.property_type || 'Property Interest'}</p>
        </div>
        <div className={`w-2 h-2 rounded-full ${priorityColors[lead.priority]} shadow-lg`}></div>
      </div>

      <div className="space-y-2 text-xs text-white/60">
        {lead.phone && (
          <div className="flex items-center gap-2">
            <Phone className="w-3 h-3 text-gold-500" />
            <span>{lead.phone}</span>
          </div>
        )}
        {lead.email && (
          <div className="flex items-center gap-2">
            <Mail className="w-3 h-3 text-gold-500" />
            <span>{lead.email}</span>
          </div>
        )}
        {lead.first_contact_at && (
          <div className="flex items-center gap-2">
            <Calendar className="w-3 h-3 text-gold-500" />
            <span>{new Date(lead.first_contact_at).toLocaleDateString()}</span>
          </div>
        )}
      </div>

      {lead.budget_max && (
        <div className="mt-3 pt-3 border-t border-white/5">
          <p className="text-sm font-bold text-gold-500">
            Budget: ${(lead.budget_max / 1000).toFixed(0)}K
          </p>
        </div>
      )}
    </div>
  )
}

// Floating Hot Leads Panel
const FloatingPanel = () => {
  return <FloatingHotLeads />
}

export default Dashboard
