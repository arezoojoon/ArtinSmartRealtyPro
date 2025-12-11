import { useState, useEffect } from 'react'
import { Layout } from '../components/Layout'
import { api } from '../context/AuthContext'
import { 
  Trophy, 
  Ticket, 
  Gift, 
  Search, 
  Filter,
  Download,
  RefreshCw,
  Users,
  Award,
  Star,
  Copy,
  Check
} from 'lucide-react'

const Lottery = () => {
  const [leads, setLeads] = useState([])
  const [loading, setLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')
  const [filterStatus, setFilterStatus] = useState('all')
  const [copiedCode, setCopiedCode] = useState(null)

  useEffect(() => {
    fetchLeads()
  }, [])

  const fetchLeads = async () => {
    try {
      const response = await api.get('/api/leads?limit=1000')
      setLeads(response.data.leads || [])
    } catch (error) {
      console.error('Failed to fetch leads:', error)
    } finally {
      setLoading(false)
    }
  }

  // Generate lottery code (6-digit unique)
  const generateLotteryCode = () => {
    return Math.random().toString(36).substring(2, 8).toUpperCase()
  }

  const copyToClipboard = (code) => {
    navigator.clipboard.writeText(code)
    setCopiedCode(code)
    setTimeout(() => setCopiedCode(null), 2000)
  }

  // Filter leads
  const filteredLeads = leads.filter(lead => {
    const matchesSearch = 
      lead.full_name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      lead.phone?.includes(searchQuery) ||
      lead.email?.toLowerCase().includes(searchQuery.toLowerCase())
    
    const matchesStatus = filterStatus === 'all' || lead.status === filterStatus
    
    return matchesSearch && matchesStatus
  })

  // Stats
  const stats = {
    total: leads.length,
    withCode: leads.filter(l => l.lottery_code).length,
    eligible: leads.filter(l => l.status !== 'closed_lost').length,
    winners: 0 // This would come from a separate winners table
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

  return (
    <Layout>
      <div className="space-y-6 animate-fade-in">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-white mb-2 flex items-center gap-3">
              <Trophy className="w-8 h-8 text-gold-500" />
              Lottery System
            </h1>
            <p className="text-gray-400">
              Manage lottery codes and track eligible participants
            </p>
          </div>
          <div className="flex gap-3">
            <button className="px-4 py-2 bg-white/5 hover:bg-white/10 border border-white/10 rounded-xl text-white transition-all flex items-center gap-2">
              <Download className="w-4 h-4" />
              Export Winners
            </button>
            <button 
              onClick={fetchLeads}
              className="px-4 py-2 bg-white/5 hover:bg-white/10 border border-white/10 rounded-xl text-white transition-all flex items-center gap-2"
            >
              <RefreshCw className="w-4 h-4" />
              Refresh
            </button>
          </div>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <div className="glass-card glass-card-hover rounded-2xl p-6">
            <div className="flex items-start justify-between mb-4">
              <p className="text-sm font-medium text-white/50 uppercase tracking-wider">
                Total Participants
              </p>
              <div className="w-12 h-12 rounded-xl flex items-center justify-center bg-blue-500/20">
                <Users className="w-6 h-6 text-blue-500" />
              </div>
            </div>
            <h3 className="text-3xl font-bold text-white">{stats.total}</h3>
            <p className="text-sm text-white/40 mt-2">All registered leads</p>
          </div>

          <div className="glass-card glass-card-hover rounded-2xl p-6">
            <div className="flex items-start justify-between mb-4">
              <p className="text-sm font-medium text-white/50 uppercase tracking-wider">
                Codes Generated
              </p>
              <div className="w-12 h-12 rounded-xl flex items-center justify-center bg-gold-500/20">
                <Ticket className="w-6 h-6 text-gold-500" />
              </div>
            </div>
            <h3 className="text-3xl font-bold text-white">{stats.withCode}</h3>
            <p className="text-sm text-white/40 mt-2">
              {((stats.withCode / stats.total) * 100).toFixed(0)}% coverage
            </p>
          </div>

          <div className="glass-card glass-card-hover rounded-2xl p-6">
            <div className="flex items-start justify-between mb-4">
              <p className="text-sm font-medium text-white/50 uppercase tracking-wider">
                Eligible Entries
              </p>
              <div className="w-12 h-12 rounded-xl flex items-center justify-center bg-green-500/20">
                <Gift className="w-6 h-6 text-green-500" />
              </div>
            </div>
            <h3 className="text-3xl font-bold text-white">{stats.eligible}</h3>
            <p className="text-sm text-white/40 mt-2">Active participants</p>
          </div>

          <div className="glass-card glass-card-hover rounded-2xl p-6">
            <div className="flex items-start justify-between mb-4">
              <p className="text-sm font-medium text-white/50 uppercase tracking-wider">
                Winners Drawn
              </p>
              <div className="w-12 h-12 rounded-xl flex items-center justify-center bg-purple-500/20">
                <Award className="w-6 h-6 text-purple-500" />
              </div>
            </div>
            <h3 className="text-3xl font-bold text-white">{stats.winners}</h3>
            <p className="text-sm text-white/40 mt-2">Prize recipients</p>
          </div>
        </div>

        {/* Filters & Search */}
        <div className="glass-card rounded-2xl p-6">
          <div className="flex flex-col md:flex-row gap-4">
            <div className="flex-1 relative">
              <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400 w-5 h-5" />
              <input
                type="text"
                placeholder="Search by name, phone, or email..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-12 pr-4 py-3 bg-navy-800/50 border border-white/10 rounded-xl text-white placeholder-gray-500 focus:outline-none focus:border-gold-500/50 transition-colors"
              />
            </div>
            <div className="flex gap-3">
              <div className="relative">
                <Filter className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 w-5 h-5" />
                <select
                  value={filterStatus}
                  onChange={(e) => setFilterStatus(e.target.value)}
                  className="pl-10 pr-8 py-3 bg-navy-800/50 border border-white/10 rounded-xl text-white focus:outline-none focus:border-gold-500/50 transition-colors appearance-none cursor-pointer"
                >
                  <option value="all">All Status</option>
                  <option value="new">New</option>
                  <option value="qualified">Qualified</option>
                  <option value="viewing_scheduled">Viewing Scheduled</option>
                  <option value="closed_won">Closed Won</option>
                </select>
              </div>
            </div>
          </div>
        </div>

        {/* Lottery Codes Table */}
        <div className="glass-card rounded-2xl overflow-hidden">
          <div className="p-6 border-b border-white/10">
            <h3 className="text-xl font-bold text-white flex items-center gap-2">
              <Ticket className="w-5 h-5 text-gold-500" />
              Lottery Codes
            </h3>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-white/5 border-b border-white/10">
                <tr>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-white/60 uppercase tracking-wider">
                    Participant
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-white/60 uppercase tracking-wider">
                    Contact
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-white/60 uppercase tracking-wider">
                    Lottery Code
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-white/60 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-white/60 uppercase tracking-wider">
                    Registered
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {filteredLeads.length > 0 ? (
                  filteredLeads.map((lead) => {
                    const lotteryCode = lead.lottery_code || generateLotteryCode()
                    const isCopied = copiedCode === lotteryCode
                    
                    return (
                      <tr key={lead.id} className="hover:bg-white/5 transition-colors">
                        <td className="px-6 py-4">
                          <div className="flex items-center gap-3">
                            <div className="w-10 h-10 rounded-full flex items-center justify-center text-navy-900 font-bold text-sm" style={{background: 'linear-gradient(135deg, #E5C365 0%, #B8962E 100%)'}}>
                              {lead.full_name?.charAt(0) || '?'}
                            </div>
                            <div>
                              <p className="font-semibold text-white">{lead.full_name}</p>
                              <p className="text-sm text-gray-400">{lead.source || 'Website'}</p>
                            </div>
                          </div>
                        </td>
                        <td className="px-6 py-4">
                          <p className="text-white text-sm">{lead.phone || 'N/A'}</p>
                          <p className="text-gray-400 text-xs">{lead.email || 'No email'}</p>
                        </td>
                        <td className="px-6 py-4">
                          <div className="flex items-center gap-2">
                            <code className="px-3 py-2 bg-gold-500/10 border border-gold-500/30 rounded-lg text-gold-500 font-mono text-sm font-bold">
                              {lotteryCode}
                            </code>
                            <button
                              onClick={() => copyToClipboard(lotteryCode)}
                              className="p-2 hover:bg-white/10 rounded-lg transition-colors"
                              title="Copy code"
                            >
                              {isCopied ? (
                                <Check className="w-4 h-4 text-green-400" />
                              ) : (
                                <Copy className="w-4 h-4 text-gray-400" />
                              )}
                            </button>
                          </div>
                        </td>
                        <td className="px-6 py-4">
                          <span className={`
                            px-3 py-1 rounded-full text-xs font-bold border
                            ${lead.status === 'new' ? 'bg-red-500/15 text-red-400 border-red-500/30' : ''}
                            ${lead.status === 'qualified' ? 'bg-yellow-500/15 text-yellow-400 border-yellow-500/30' : ''}
                            ${lead.status === 'viewing_scheduled' ? 'bg-green-500/15 text-green-400 border-green-500/30' : ''}
                            ${lead.status === 'closed_won' ? 'bg-blue-500/15 text-blue-400 border-blue-500/30' : ''}
                          `}>
                            {lead.status?.replace('_', ' ')}
                          </span>
                        </td>
                        <td className="px-6 py-4">
                          <p className="text-white text-sm">
                            {new Date(lead.created_at).toLocaleDateString()}
                          </p>
                          <p className="text-gray-400 text-xs">
                            {new Date(lead.created_at).toLocaleTimeString()}
                          </p>
                        </td>
                      </tr>
                    )
                  })
                ) : (
                  <tr>
                    <td colSpan="5" className="px-6 py-12 text-center">
                      <div className="flex flex-col items-center gap-3">
                        <Ticket className="w-12 h-12 text-gray-500" />
                        <p className="text-gray-400">No participants found</p>
                      </div>
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Winner Selection Section */}
        <div className="glass-card rounded-2xl p-6">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h3 className="text-xl font-bold text-white flex items-center gap-2">
                <Star className="w-5 h-5 text-gold-500" />
                Draw Winners
              </h3>
              <p className="text-sm text-gray-400 mt-1">
                Randomly select winners from eligible participants
              </p>
            </div>
            <button className="px-6 py-3 btn-gold rounded-xl flex items-center gap-2">
              <Trophy className="w-5 h-5" />
              Draw Random Winner
            </button>
          </div>

          {/* Winners List Placeholder */}
          <div className="bg-white/5 rounded-xl p-8 text-center border border-dashed border-white/20">
            <Trophy className="w-16 h-16 text-gold-500/50 mx-auto mb-4" />
            <p className="text-white/50">No winners drawn yet</p>
            <p className="text-white/30 text-sm mt-2">
              Click "Draw Random Winner" to select a lucky participant
            </p>
          </div>
        </div>
      </div>
    </Layout>
  )
}

export default Lottery
