import { useState, useEffect } from 'react'
import { Layout } from '../components/Layout'
import { api } from '../context/AuthContext'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
  Filler
} from 'chart.js'
import { Line, Bar, Pie, Doughnut } from 'react-chartjs-2'
import { TrendingUp, Users, Target, DollarSign, Calendar, Download } from 'lucide-react'

// Register ChartJS components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
  Filler
)

const Analytics = () => {
  const [stats, setStats] = useState(null)
  const [leads, setLeads] = useState([])
  const [loading, setLoading] = useState(true)
  const [timeRange, setTimeRange] = useState('7days')

  useEffect(() => {
    fetchAnalyticsData()
  }, [timeRange])

  const fetchAnalyticsData = async () => {
    try {
      const [statsRes, leadsRes] = await Promise.all([
        api.get('/api/analytics/stats'),
        api.get('/api/leads?limit=1000')
      ])
      
      setStats(statsRes.data)
      setLeads(leadsRes.data.leads || [])
    } catch (error) {
      console.error('Failed to fetch analytics:', error)
    } finally {
      setLoading(false)
    }
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

  // Status Distribution Data
  const statusData = {
    labels: ['New', 'Qualified', 'Viewing', 'Negotiation', 'Won', 'Lost'],
    datasets: [
      {
        data: [
          stats?.new_leads || 0,
          stats?.qualified_leads || 0,
          stats?.viewing_scheduled || 0,
          leads.filter(l => l.status === 'negotiation').length,
          stats?.closed_won || 0,
          stats?.closed_lost || 0,
        ],
        backgroundColor: [
          'rgba(239, 68, 68, 0.8)',    // Red
          'rgba(234, 179, 8, 0.8)',     // Yellow
          'rgba(34, 197, 94, 0.8)',     // Green
          'rgba(59, 130, 246, 0.8)',    // Blue
          'rgba(168, 85, 247, 0.8)',    // Purple
          'rgba(107, 114, 128, 0.8)',   // Gray
        ],
        borderColor: [
          'rgb(239, 68, 68)',
          'rgb(234, 179, 8)',
          'rgb(34, 197, 94)',
          'rgb(59, 130, 246)',
          'rgb(168, 85, 247)',
          'rgb(107, 114, 128)',
        ],
        borderWidth: 2,
      },
    ],
  }

  // Lead Trend Data (Last 7 days)
  const getTrendData = () => {
    const last7Days = []
    const today = new Date()
    
    for (let i = 6; i >= 0; i--) {
      const date = new Date(today)
      date.setDate(date.getDate() - i)
      last7Days.push(date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }))
    }

    const leadsByDay = last7Days.map((day, index) => {
      const date = new Date()
      date.setDate(date.getDate() - (6 - index))
      return leads.filter(lead => {
        const leadDate = new Date(lead.created_at)
        return leadDate.toDateString() === date.toDateString()
      }).length
    })

    return {
      labels: last7Days,
      datasets: [
        {
          label: 'New Leads',
          data: leadsByDay,
          borderColor: 'rgb(212, 175, 55)',
          backgroundColor: 'rgba(212, 175, 55, 0.1)',
          fill: true,
          tension: 0.4,
        },
      ],
    }
  }

  // Property Type Distribution
  const propertyTypeData = () => {
    const types = {}
    leads.forEach(lead => {
      if (lead.property_type) {
        types[lead.property_type] = (types[lead.property_type] || 0) + 1
      }
    })

    return {
      labels: Object.keys(types),
      datasets: [
        {
          data: Object.values(types),
          backgroundColor: [
            'rgba(212, 175, 55, 0.8)',
            'rgba(34, 197, 94, 0.8)',
            'rgba(59, 130, 246, 0.8)',
            'rgba(168, 85, 247, 0.8)',
            'rgba(239, 68, 68, 0.8)',
            'rgba(234, 179, 8, 0.8)',
          ],
          borderWidth: 2,
          borderColor: '#0f1729',
        },
      ],
    }
  }

  // Budget Range Distribution
  const budgetRangeData = () => {
    const ranges = {
      '0-250K': 0,
      '250K-500K': 0,
      '500K-1M': 0,
      '1M-2M': 0,
      '2M+': 0,
    }

    leads.forEach(lead => {
      if (lead.budget_max) {
        const budget = lead.budget_max
        if (budget < 250000) ranges['0-250K']++
        else if (budget < 500000) ranges['250K-500K']++
        else if (budget < 1000000) ranges['500K-1M']++
        else if (budget < 2000000) ranges['1M-2M']++
        else ranges['2M+']++
      }
    })

    return {
      labels: Object.keys(ranges),
      datasets: [
        {
          label: 'Leads by Budget',
          data: Object.values(ranges),
          backgroundColor: 'rgba(212, 175, 55, 0.8)',
          borderColor: 'rgb(212, 175, 55)',
          borderWidth: 1,
        },
      ],
    }
  }

  // Chart options
  const lineChartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: true,
        labels: {
          color: 'rgba(255, 255, 255, 0.7)',
          font: {
            size: 12,
          },
        },
      },
      tooltip: {
        backgroundColor: 'rgba(15, 23, 41, 0.9)',
        titleColor: '#D4AF37',
        bodyColor: 'rgba(255, 255, 255, 0.8)',
        borderColor: 'rgba(212, 175, 55, 0.3)',
        borderWidth: 1,
        padding: 12,
        displayColors: false,
      },
    },
    scales: {
      y: {
        beginAtZero: true,
        grid: {
          color: 'rgba(255, 255, 255, 0.05)',
        },
        ticks: {
          color: 'rgba(255, 255, 255, 0.5)',
        },
      },
      x: {
        grid: {
          color: 'rgba(255, 255, 255, 0.05)',
        },
        ticks: {
          color: 'rgba(255, 255, 255, 0.5)',
        },
      },
    },
  }

  const pieChartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'bottom',
        labels: {
          color: 'rgba(255, 255, 255, 0.7)',
          font: {
            size: 12,
          },
          padding: 15,
        },
      },
      tooltip: {
        backgroundColor: 'rgba(15, 23, 41, 0.9)',
        titleColor: '#D4AF37',
        bodyColor: 'rgba(255, 255, 255, 0.8)',
        borderColor: 'rgba(212, 175, 55, 0.3)',
        borderWidth: 1,
        padding: 12,
      },
    },
  }

  // Summary Stats
  const summaryStats = [
    {
      title: 'Total Leads',
      value: stats?.total_leads || 0,
      icon: Users,
      color: 'gold',
      trend: '+12.5%'
    },
    {
      title: 'Conversion Rate',
      value: `${(stats?.conversion_rate || 0).toFixed(1)}%`,
      icon: Target,
      color: 'green',
      trend: '+3.2%'
    },
    {
      title: 'Avg Deal Value',
      value: `$${((stats?.avg_deal_value || 0) / 1000).toFixed(0)}K`,
      icon: DollarSign,
      color: 'blue',
      trend: '+8.7%'
    },
    {
      title: 'Active This Week',
      value: leads.filter(l => {
        const weekAgo = new Date()
        weekAgo.setDate(weekAgo.getDate() - 7)
        return new Date(l.created_at) > weekAgo
      }).length,
      icon: TrendingUp,
      color: 'purple',
      trend: '+15.3%'
    },
  ]

  return (
    <Layout>
      <div className="space-y-6 animate-fade-in">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-white mb-2">Analytics Dashboard</h1>
            <p className="text-white/50">Performance insights and trends</p>
          </div>
          <div className="flex gap-3">
            <select
              value={timeRange}
              onChange={(e) => setTimeRange(e.target.value)}
              className="px-4 py-2 bg-white/5 border border-white/10 rounded-xl text-white focus:outline-none focus:border-gold-500/40"
            >
              <option value="7days">Last 7 Days</option>
              <option value="30days">Last 30 Days</option>
              <option value="90days">Last 90 Days</option>
            </select>
            <button className="px-4 py-2 bg-white/5 hover:bg-white/10 border border-white/10 rounded-xl text-white transition-all flex items-center gap-2">
              <Download className="w-4 h-4" />
              Export
            </button>
          </div>
        </div>

        {/* Summary Stats */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {summaryStats.map((stat, index) => (
            <div key={index} className="glass-card glass-card-hover rounded-2xl p-6">
              <div className="flex items-start justify-between mb-4">
                <p className="text-sm font-medium text-white/50 uppercase tracking-wider">
                  {stat.title}
                </p>
                <div className={`w-12 h-12 rounded-xl flex items-center justify-center bg-${stat.color}-500/20`}>
                  <stat.icon className={`w-6 h-6 text-${stat.color}-500`} />
                </div>
              </div>
              <div className="mb-2">
                <h3 className="text-3xl font-bold text-white">{stat.value}</h3>
              </div>
              <div className="flex items-center gap-2 text-sm text-green-400">
                <TrendingUp className="w-4 h-4" />
                <span className="font-semibold">{stat.trend}</span>
                <span className="text-white/40">vs last period</span>
              </div>
            </div>
          ))}
        </div>

        {/* Charts Row 1 */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Lead Trend Chart */}
          <div className="glass-card rounded-2xl p-6">
            <h3 className="text-xl font-bold text-white mb-6 flex items-center gap-2">
              <Calendar className="w-5 h-5 text-gold-500" />
              Lead Generation Trend
            </h3>
            <div className="h-80">
              <Line data={getTrendData()} options={lineChartOptions} />
            </div>
          </div>

          {/* Status Distribution */}
          <div className="glass-card rounded-2xl p-6">
            <h3 className="text-xl font-bold text-white mb-6 flex items-center gap-2">
              <Target className="w-5 h-5 text-gold-500" />
              Pipeline Distribution
            </h3>
            <div className="h-80">
              <Doughnut data={statusData} options={pieChartOptions} />
            </div>
          </div>
        </div>

        {/* Charts Row 2 */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Budget Range */}
          <div className="glass-card rounded-2xl p-6">
            <h3 className="text-xl font-bold text-white mb-6 flex items-center gap-2">
              <DollarSign className="w-5 h-5 text-gold-500" />
              Budget Distribution
            </h3>
            <div className="h-80">
              <Bar data={budgetRangeData()} options={lineChartOptions} />
            </div>
          </div>

          {/* Property Type */}
          <div className="glass-card rounded-2xl p-6">
            <h3 className="text-xl font-bold text-white mb-6 flex items-center gap-2">
              <Users className="w-5 h-5 text-gold-500" />
              Property Type Interest
            </h3>
            <div className="h-80">
              <Pie data={propertyTypeData()} options={pieChartOptions} />
            </div>
          </div>
        </div>

        {/* Top Performers */}
        <div className="glass-card rounded-2xl p-6">
          <h3 className="text-xl font-bold text-white mb-6">Top Locations</h3>
          <div className="space-y-4">
            {Object.entries(
              leads.reduce((acc, lead) => {
                if (lead.preferred_location) {
                  acc[lead.preferred_location] = (acc[lead.preferred_location] || 0) + 1
                }
                return acc
              }, {})
            )
              .sort(([, a], [, b]) => b - a)
              .slice(0, 5)
              .map(([location, count], index) => (
                <div key={index} className="flex items-center gap-4">
                  <div className="w-8 h-8 rounded-lg bg-gold-500/20 flex items-center justify-center text-gold-500 font-bold text-sm">
                    {index + 1}
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-white font-medium">{location}</span>
                      <span className="text-white/50 text-sm">{count} leads</span>
                    </div>
                    <div className="h-2 bg-white/5 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-gradient-gold"
                        style={{ width: `${(count / leads.length) * 100}%` }}
                      />
                    </div>
                  </div>
                </div>
              ))}
          </div>
        </div>
      </div>
    </Layout>
  )
}

export default Analytics
