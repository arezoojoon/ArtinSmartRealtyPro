import { useState, useEffect } from 'react'
import { Layout } from '../components/Layout'
import { api } from '../context/AuthContext'
import { toast } from 'react-toastify'
import { 
  Settings as SettingsIcon, 
  Building2, 
  Phone, 
  Mail, 
  MapPin, 
  Link as LinkIcon,
  MessageCircle,
  Globe,
  Save,
  CheckCircle,
  Key,
  Lock
} from 'lucide-react'

const Settings = () => {
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)
  const [loading, setLoading] = useState(true)

  const [settings, setSettings] = useState({
    companyName: 'Artin Smart Exhibition Services',
    companyLogo: null,
    contactPerson: 'John Doe',
    phone: '+971 50 123 4567',
    email: 'info@artinsmartagent.com',
    boothLocation: 'Hall 3, Stand B-45',
    bookingUrl: 'https://expo.artinsmartagent.com/book',
    telegramEnabled: true,
    telegramBotToken: '',
    whatsappEnabled: true,
    whatsappApiToken: '',
    enabledLanguages: ['en', 'fa', 'ar', 'ru'],
    defaultLanguage: 'en'
  })

  const [botConfig, setBotConfig] = useState({
    telegram_configured: false,
    whatsapp_configured: false,
    telegram_bot_token_preview: null,
    whatsapp_api_token_preview: null
  })

  // Fetch bot config on mount
  useEffect(() => {
    fetchBotConfig()
  }, [])

  const fetchBotConfig = async () => {
    try {
      const response = await api.get('/api/settings/bot-config')
      
      setBotConfig({
        telegram_configured: response.data.telegram_configured,
        whatsapp_configured: response.data.whatsapp_configured,
        telegram_bot_token_preview: response.data.telegram_bot_token,
        whatsapp_api_token_preview: response.data.whatsapp_api_token
      })
    } catch (error) {
      console.error('❌ Error fetching bot config:', error)
      toast.error('❌ خطا در دریافت تنظیمات Bot')
    } finally {
      setLoading(false)
    }
  }

  const handleChange = (field, value) => {
    setSettings(prev => ({ ...prev, [field]: value }))
  }

  const handleSave = async () => {
    setSaving(true)
    
    try {
      // Update bot config if tokens are provided
      const botUpdateData = {}
      if (settings.telegramBotToken) {
        botUpdateData.telegram_bot_token = settings.telegramBotToken
      }
      if (settings.whatsappApiToken) {
        botUpdateData.whatsapp_api_token = settings.whatsappApiToken
      }
      
      if (Object.keys(botUpdateData).length > 0) {
        await api.patch('/api/settings/bot-config', botUpdateData)
        toast.success('✅ تنظیمات Bot با موفقیت ذخیره شد')
        
        // Clear input fields and refresh config
        setSettings(prev => ({
          ...prev,
          telegramBotToken: '',
          whatsappApiToken: ''
        }))
        await fetchBotConfig()
      } else {
        toast.info('ℹ️ هیچ تغییری برای ذخیره وجود ندارد')
      }
      
      setSaved(true)
      setTimeout(() => setSaved(false), 3000)
    } catch (error) {
      console.error('❌ Error saving bot config:', error)
      toast.error(error.response?.data?.detail || '❌ خطا در ذخیره تنظیمات')
    } finally {
      setSaving(false)
    }
  }

  const toggleLanguage = (lang) => {
    setSettings(prev => ({
      ...prev,
      enabledLanguages: prev.enabledLanguages.includes(lang)
        ? prev.enabledLanguages.filter(l => l !== lang)
        : [...prev.enabledLanguages, lang]
    }))
  }

  if (loading) {
    return (
      <Layout>
        <div className="flex items-center justify-center h-64">
          <div className="text-white text-xl">⏳ در حال بارگذاری...</div>
        </div>
      </Layout>
    )
  }

  return (
    <Layout>
      <div className="space-y-6 animate-fade-in">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-white mb-2 flex items-center gap-3">
              <SettingsIcon className="w-8 h-8 text-gold-500" />
              Settings
            </h1>
            <p className="text-gray-400">Configure exhibition booth settings</p>
          </div>
          <button onClick={handleSave} disabled={saving || saved} className="px-6 py-3 btn-gold rounded-xl flex items-center gap-2">
            {saving ? 'Saving...' : saved ? <><CheckCircle className="w-5 h-5" />Saved!</> : <><Save className="w-5 h-5" />Save</>}
          </button>
        </div>

        {/* Exhibitor Info */}
        <div className="glass-card rounded-2xl p-6">
          <h3 className="text-xl font-bold text-white mb-6 flex items-center gap-2">
            <Building2 className="w-5 h-5 text-gold-500" />Exhibitor Information
          </h3>
          
          {/* Logo Upload Section */}
          <div className="mb-6 pb-6 border-b border-white/10">
            <label className="block text-sm font-medium text-white/70 mb-3">
              Company Logo
            </label>
            <div className="flex items-center gap-6">
              <div className="w-24 h-24 rounded-xl border-2 border-white/10 flex items-center justify-center bg-navy-800/50 overflow-hidden">
                {settings.companyLogo ? (
                  <img src={settings.companyLogo} alt="Logo" className="w-full h-full object-cover" />
                ) : (
                  <Building2 className="w-12 h-12 text-white/30" />
                )}
              </div>
              <div className="flex-1">
                <label className="px-6 py-3 bg-gold-500/10 hover:bg-gold-500/20 border border-gold-500/30 text-gold-500 rounded-xl cursor-pointer inline-flex items-center gap-2 transition-all">
                  <input
                    type="file"
                    accept="image/*"
                    className="hidden"
                    onChange={(e) => {
                      const file = e.target.files?.[0]
                      if (file) {
                        const reader = new FileReader()
                        reader.onloadend = () => {
                          handleChange('companyLogo', reader.result)
                        }
                        reader.readAsDataURL(file)
                      }
                    }}
                  />
                  📤 Upload Logo
                </label>
                <p className="text-xs text-white/50 mt-2">
                  Recommended: 512x512px, PNG or JPG, max 2MB
                </p>
              </div>
            </div>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div><label className="block text-sm font-medium text-white/70 mb-2">Company Name</label>
            <input type="text" value={settings.companyName} onChange={(e) => handleChange('companyName', e.target.value)} className="w-full px-4 py-3 bg-navy-800/50 border border-white/10 rounded-xl text-white focus:outline-none focus:border-gold-500/50"/></div>
            <div><label className="block text-sm font-medium text-white/70 mb-2">Contact Person</label>
            <input type="text" value={settings.contactPerson} onChange={(e) => handleChange('contactPerson', e.target.value)} className="w-full px-4 py-3 bg-navy-800/50 border border-white/10 rounded-xl text-white focus:outline-none focus:border-gold-500/50"/></div>
            <div><label className="block text-sm font-medium text-white/70 mb-2"><Phone className="w-4 h-4 inline mr-2"/>Phone</label>
            <input type="tel" value={settings.phone} onChange={(e) => handleChange('phone', e.target.value)} className="w-full px-4 py-3 bg-navy-800/50 border border-white/10 rounded-xl text-white focus:outline-none focus:border-gold-500/50"/></div>
            <div><label className="block text-sm font-medium text-white/70 mb-2"><Mail className="w-4 h-4 inline mr-2"/>Email</label>
            <input type="email" value={settings.email} onChange={(e) => handleChange('email', e.target.value)} className="w-full px-4 py-3 bg-navy-800/50 border border-white/10 rounded-xl text-white focus:outline-none focus:border-gold-500/50"/></div>
            <div><label className="block text-sm font-medium text-white/70 mb-2"><MapPin className="w-4 h-4 inline mr-2"/>Booth Location</label>
            <input type="text" value={settings.boothLocation} onChange={(e) => handleChange('boothLocation', e.target.value)} className="w-full px-4 py-3 bg-navy-800/50 border border-white/10 rounded-xl text-white focus:outline-none focus:border-gold-500/50"/></div>
            <div><label className="block text-sm font-medium text-white/70 mb-2"><LinkIcon className="w-4 h-4 inline mr-2"/>Booking URL</label>
            <input type="url" value={settings.bookingUrl} onChange={(e) => handleChange('bookingUrl', e.target.value)} className="w-full px-4 py-3 bg-navy-800/50 border border-white/10 rounded-xl text-white focus:outline-none focus:border-gold-500/50"/></div>
          </div>
        </div>

        {/* Bot Settings با Token Configuration */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Telegram Bot Config */}
          <div className="glass-card rounded-2xl p-6">
            <h3 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
              <MessageCircle className="w-5 h-5 text-blue-500"/>
              Telegram Bot
            </h3>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-white/70">وضعیت:</span>
                <span className={`px-3 py-1 rounded-lg text-sm font-semibold ${
                  botConfig.telegram_configured 
                    ? 'bg-green-500/30 text-green-200' 
                    : 'bg-red-500/30 text-red-200'
                }`}>
                  {botConfig.telegram_configured ? '✅ پیکربندی شده' : '❌ پیکربندی نشده'}
                </span>
              </div>
              
              {botConfig.telegram_configured && (
                <div className="bg-blue-500/10 border border-blue-500/30 rounded-xl p-3">
                  <div className="flex items-center gap-2 text-blue-300 text-sm">
                    <Key className="w-4 h-4" />
                    <span>Token فعلی: {botConfig.telegram_bot_token_preview}</span>
                  </div>
                </div>
              )}
              
              <div>
                <label className="block text-sm font-medium text-white/70 mb-2 flex items-center gap-2">
                  <Lock className="w-4 h-4" />
                  Bot Token جدید (اختیاری)
                </label>
                <input
                  type="password"
                  value={settings.telegramBotToken}
                  onChange={(e) => handleChange('telegramBotToken', e.target.value)}
                  placeholder="1234567890:ABCdefGHIjklMNOpqrsTUVwxyz"
                  className="w-full px-4 py-3 bg-navy-800/50 border border-white/10 rounded-xl text-white placeholder-white/30 focus:outline-none focus:border-blue-500/50"
                />
                <p className="text-xs text-white/50 mt-2">
                  💡 Token را از @BotFather در Telegram دریافت کنید
                </p>
              </div>
            </div>
          </div>

          {/* WhatsApp Bot Config */}
          <div className="glass-card rounded-2xl p-6">
            <h3 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
              <MessageCircle className="w-5 h-5 text-green-500"/>
              WhatsApp Bot
            </h3>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-white/70">وضعیت:</span>
                <span className={`px-3 py-1 rounded-lg text-sm font-semibold ${
                  botConfig.whatsapp_configured 
                    ? 'bg-green-500/30 text-green-200' 
                    : 'bg-red-500/30 text-red-200'
                }`}>
                  {botConfig.whatsapp_configured ? '✅ پیکربندی شده' : '❌ پیکربندی نشده'}
                </span>
              </div>
              
              {botConfig.whatsapp_configured && (
                <div className="bg-green-500/10 border border-green-500/30 rounded-xl p-3">
                  <div className="flex items-center gap-2 text-green-300 text-sm">
                    <Key className="w-4 h-4" />
                    <span>API Token فعلی: {botConfig.whatsapp_api_token_preview}</span>
                  </div>
                </div>
              )}
              
              <div>
                <label className="block text-sm font-medium text-white/70 mb-2 flex items-center gap-2">
                  <Lock className="w-4 h-4" />
                  API Token جدید (اختیاری)
                </label>
                <input
                  type="password"
                  value={settings.whatsappApiToken}
                  onChange={(e) => handleChange('whatsappApiToken', e.target.value)}
                  placeholder="EAAxxxxxxxxxxxxxxxxxx"
                  className="w-full px-4 py-3 bg-navy-800/50 border border-white/10 rounded-xl text-white placeholder-white/30 focus:outline-none focus:border-green-500/50"
                />
                <p className="text-xs text-white/50 mt-2">
                  💡 API Token را از WhatsApp Business Platform دریافت کنید
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Save Bot Tokens Button */}
        <div className="flex justify-center mt-6">
          <button
            onClick={handleSave}
            disabled={saving || (!settings.telegramBotToken && !settings.whatsappApiToken)}
            className={`px-8 py-4 rounded-xl font-bold text-lg transition-all flex items-center gap-3 ${
              saving || (!settings.telegramBotToken && !settings.whatsappApiToken)
                ? 'bg-gray-600 cursor-not-allowed opacity-50'
                : saved
                ? 'bg-green-600 hover:bg-green-700 shadow-lg shadow-green-500/50'
                : 'bg-gold-600 hover:bg-gold-700 shadow-lg shadow-gold-500/50'
            }`}
          >
            {saving ? (
              <>
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                در حال ذخیره...
              </>
            ) : saved ? (
              <>
                <CheckCircle className="w-6 h-6" />
                ✅ ذخیره شد!
              </>
            ) : (
              <>
                <Save className="w-6 h-6" />
                💾 ذخیره تنظیمات Bot
              </>
            )}
          </button>
        </div>

        {/* Languages */}
        <div className="glass-card rounded-2xl p-6">
          <h3 className="text-xl font-bold text-white mb-6 flex items-center gap-2">
            <Globe className="w-5 h-5 text-gold-500"/>Languages
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {[{code:'en',name:'English 🇬🇧'},{code:'fa',name:'فارسی 🇮🇷'},{code:'ar',name:'عربي 🇸🇦'},{code:'ru',name:'Русский 🇷🇺'}].map(lang => (
              <label key={lang.code} className="cursor-pointer">
                <input type="checkbox" checked={settings.enabledLanguages.includes(lang.code)} onChange={() => toggleLanguage(lang.code)} className="sr-only peer"/>
                <div className="px-4 py-3 bg-navy-800/50 border-2 border-white/10 rounded-xl peer-checked:border-gold-500 peer-checked:bg-gold-500/10 transition-all">
                  <span className="text-sm font-medium text-white">{lang.name}</span>
                </div>
              </label>
            ))}
          </div>
        </div>
      </div>
    </Layout>
  )
}

export default Settings
