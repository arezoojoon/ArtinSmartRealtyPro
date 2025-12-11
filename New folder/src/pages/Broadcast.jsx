import { useState } from 'react'
import { Layout } from '../components/Layout'
import { 
  Send, 
  Users, 
  MessageSquare, 
  Globe,
  Clock,
  CheckCircle,
  AlertCircle
} from 'lucide-react'

const Broadcast = () => {
  const [message, setMessage] = useState('')
  const [language, setLanguage] = useState('all')
  const [channel, setChannel] = useState('all')
  const [sending, setSending] = useState(false)

  const [broadcasts, setBroadcasts] = useState([
    {
      id: 1,
      message: 'Special promotion: 20% off all properties this week!',
      language: 'en',
      channel: 'telegram',
      recipients: 145,
      status: 'sent',
      sent_at: '2025-11-25T14:30:00'
    },
    {
      id: 2,
      message: 'پیشنهاد ویژه: بازدید از غرفه ما و شرکت در قرعه‌کشی!',
      language: 'fa',
      channel: 'whatsapp',
      recipients: 89,
      status: 'sent',
      sent_at: '2025-11-25T14:32:00'
    },
    {
      id: 3,
      message: 'Visit our booth at Hall 3, Stand B-45 for exclusive deals!',
      language: 'all',
      channel: 'all',
      recipients: 312,
      status: 'scheduled',
      sent_at: '2025-11-26T10:00:00'
    }
  ])

  const handleSendBroadcast = async () => {
    if (!message.trim()) return

    setSending(true)
    // Simulate API call
    setTimeout(() => {
      const newBroadcast = {
        id: broadcasts.length + 1,
        message,
        language,
        channel,
        recipients: 250,
        status: 'sent',
        sent_at: new Date().toISOString()
      }
      setBroadcasts([newBroadcast, ...broadcasts])
      setMessage('')
      setSending(false)
    }, 2000)
  }

  const stats = {
    totalSent: broadcasts.filter(b => b.status === 'sent').length,
    totalRecipients: broadcasts.reduce((sum, b) => sum + b.recipients, 0),
    scheduled: broadcasts.filter(b => b.status === 'scheduled').length
  }

  return (
    <Layout>
      <div className="space-y-6 animate-fade-in">
        {/* Header */}
        <div>
          <h1 className="text-3xl font-bold text-white mb-2 flex items-center gap-3">
            <Send className="w-8 h-8 text-gold-500" />
            Broadcast Messaging
          </h1>
          <p className="text-gray-400">
            Send messages to all leads via Telegram and WhatsApp
          </p>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="glass-card glass-card-hover rounded-2xl p-6">
            <div className="flex items-start justify-between mb-4">
              <p className="text-sm font-medium text-white/50 uppercase tracking-wider">
                Messages Sent
              </p>
              <div className="w-12 h-12 rounded-xl flex items-center justify-center bg-green-500/20">
                <CheckCircle className="w-6 h-6 text-green-500" />
              </div>
            </div>
            <h3 className="text-3xl font-bold text-white">{stats.totalSent}</h3>
            <p className="text-sm text-white/40 mt-2">Successful broadcasts</p>
          </div>

          <div className="glass-card glass-card-hover rounded-2xl p-6">
            <div className="flex items-start justify-between mb-4">
              <p className="text-sm font-medium text-white/50 uppercase tracking-wider">
                Total Recipients
              </p>
              <div className="w-12 h-12 rounded-xl flex items-center justify-center bg-blue-500/20">
                <Users className="w-6 h-6 text-blue-500" />
              </div>
            </div>
            <h3 className="text-3xl font-bold text-white">{stats.totalRecipients}</h3>
            <p className="text-sm text-white/40 mt-2">Messages delivered</p>
          </div>

          <div className="glass-card glass-card-hover rounded-2xl p-6">
            <div className="flex items-start justify-between mb-4">
              <p className="text-sm font-medium text-white/50 uppercase tracking-wider">
                Scheduled
              </p>
              <div className="w-12 h-12 rounded-xl flex items-center justify-center bg-yellow-500/20">
                <Clock className="w-6 h-6 text-yellow-500" />
              </div>
            </div>
            <h3 className="text-3xl font-bold text-white">{stats.scheduled}</h3>
            <p className="text-sm text-white/40 mt-2">Pending broadcasts</p>
          </div>
        </div>

        {/* Compose Message */}
        <div className="glass-card rounded-2xl p-6">
          <h3 className="text-xl font-bold text-white mb-6 flex items-center gap-2">
            <MessageSquare className="w-5 h-5 text-gold-500" />
            Compose Broadcast
          </h3>

          <div className="space-y-4">
            {/* Message Input */}
            <div>
              <label className="block text-sm font-medium text-white/70 mb-2">
                Message
              </label>
              <textarea
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                placeholder="Type your broadcast message here..."
                rows={6}
                className="w-full px-4 py-3 bg-navy-800/50 border border-white/10 rounded-xl text-white placeholder-gray-500 focus:outline-none focus:border-gold-500/50 transition-colors resize-none"
              />
              <p className="text-xs text-gray-500 mt-2">
                {message.length} characters
              </p>
            </div>

            {/* Filters */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-white/70 mb-2">
                  <Globe className="w-4 h-4 inline mr-2" />
                  Language
                </label>
                <select
                  value={language}
                  onChange={(e) => setLanguage(e.target.value)}
                  className="w-full px-4 py-3 bg-navy-800/50 border border-white/10 rounded-xl text-white focus:outline-none focus:border-gold-500/50 transition-colors cursor-pointer"
                >
                  <option value="all">All Languages</option>
                  <option value="en">English</option>
                  <option value="fa">فارسی (Farsi)</option>
                  <option value="ar">العربية (Arabic)</option>
                  <option value="ru">Русский (Russian)</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-white/70 mb-2">
                  <Send className="w-4 h-4 inline mr-2" />
                  Channel
                </label>
                <select
                  value={channel}
                  onChange={(e) => setChannel(e.target.value)}
                  className="w-full px-4 py-3 bg-navy-800/50 border border-white/10 rounded-xl text-white focus:outline-none focus:border-gold-500/50 transition-colors cursor-pointer"
                >
                  <option value="all">All Channels</option>
                  <option value="telegram">Telegram Only</option>
                  <option value="whatsapp">WhatsApp Only</option>
                </select>
              </div>
            </div>

            {/* Send Button */}
            <div className="flex items-center justify-between pt-4 border-t border-white/10">
              <p className="text-sm text-gray-400">
                Estimated recipients: <span className="text-white font-bold">~250 leads</span>
              </p>
              <button
                onClick={handleSendBroadcast}
                disabled={!message.trim() || sending}
                className="px-6 py-3 btn-gold rounded-xl flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {sending ? (
                  <>
                    <div className="w-5 h-5 border-2 border-navy-900/30 border-t-navy-900 rounded-full animate-spin"></div>
                    Sending...
                  </>
                ) : (
                  <>
                    <Send className="w-5 h-5" />
                    Send Broadcast
                  </>
                )}
              </button>
            </div>
          </div>
        </div>

        {/* Broadcast History */}
        <div className="glass-card rounded-2xl overflow-hidden">
          <div className="p-6 border-b border-white/10">
            <h3 className="text-xl font-bold text-white flex items-center gap-2">
              <Clock className="w-5 h-5 text-gold-500" />
              Broadcast History
            </h3>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-white/5 border-b border-white/10">
                <tr>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-white/60 uppercase tracking-wider">
                    Message
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-white/60 uppercase tracking-wider">
                    Language
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-white/60 uppercase tracking-wider">
                    Channel
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-white/60 uppercase tracking-wider">
                    Recipients
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-white/60 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-white/60 uppercase tracking-wider">
                    Sent At
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {broadcasts.map((broadcast) => (
                  <tr key={broadcast.id} className="hover:bg-white/5 transition-colors">
                    <td className="px-6 py-4">
                      <p className="text-white text-sm max-w-md truncate">
                        {broadcast.message}
                      </p>
                    </td>
                    <td className="px-6 py-4">
                      <span className="px-3 py-1 rounded-full text-xs font-bold bg-blue-500/15 text-blue-400 border border-blue-500/30">
                        {broadcast.language === 'all' ? 'All' : broadcast.language.toUpperCase()}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <span className="px-3 py-1 rounded-full text-xs font-bold bg-purple-500/15 text-purple-400 border border-purple-500/30">
                        {broadcast.channel === 'all' ? 'Both' : broadcast.channel}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <p className="text-white font-bold">{broadcast.recipients}</p>
                    </td>
                    <td className="px-6 py-4">
                      <span className={`px-3 py-1 rounded-full text-xs font-bold border ${
                        broadcast.status === 'sent'
                          ? 'bg-green-500/15 text-green-400 border-green-500/30'
                          : 'bg-yellow-500/15 text-yellow-400 border-yellow-500/30'
                      }`}>
                        {broadcast.status === 'sent' ? (
                          <CheckCircle className="w-3 h-3 inline mr-1" />
                        ) : (
                          <Clock className="w-3 h-3 inline mr-1" />
                        )}
                        {broadcast.status}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <p className="text-white text-sm">
                        {new Date(broadcast.sent_at).toLocaleDateString()}
                      </p>
                      <p className="text-gray-400 text-xs">
                        {new Date(broadcast.sent_at).toLocaleTimeString()}
                      </p>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Warning Card */}
        <div className="glass-card rounded-2xl p-6 border-l-4 border-yellow-500">
          <div className="flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-yellow-500 flex-shrink-0 mt-0.5" />
            <div>
              <h4 className="text-white font-bold mb-2">Important Notice</h4>
              <p className="text-gray-300 text-sm">
                Please ensure your broadcast messages comply with local regulations and respect user preferences. 
                Users who have opted out will not receive broadcasts. Always provide value and avoid spam.
              </p>
            </div>
          </div>
        </div>
      </div>
    </Layout>
  )
}

export default Broadcast
