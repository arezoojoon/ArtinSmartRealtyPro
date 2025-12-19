import { useState } from 'react'
import { Layout } from '../components/Layout'
import { 
  BookOpen, 
  Plus, 
  Edit, 
  Trash2, 
  ExternalLink,
  BarChart2,
  Globe,
  Search
} from 'lucide-react'

const Catalogs = () => {
  const [catalogs, setCatalogs] = useState([
    {
      id: 1,
      title_en: 'Smart LED Display Panels',
      title_fa: 'پنل‌های نمایشگر LED هوشمند',
      title_ar: 'لوحات عرض LED الذكية',
      title_ru: 'Умные LED-панели',
      url: 'https://example.com/led-displays',
      pdf_url: 'https://example.com/catalogs/led-displays.pdf',
      keywords: 'led, display, screen, exhibition, booth, digital signage',
      clicks: 145,
      enabled: true
    },
    {
      id: 2,
      title_en: 'Interactive Kiosk Systems',
      title_fa: 'سیستم‌های کیوسک تعاملی',
      title_ar: 'أنظمة الكشك التفاعلية',
      title_ru: 'Интерактивные киоск-системы',
      url: 'https://example.com/kiosk-systems',
      pdf_url: 'https://example.com/catalogs/kiosks.pdf',
      keywords: 'kiosk, interactive, touchscreen, self-service, booth',
      clicks: 98,
      enabled: true
    },
    {
      id: 3,
      title_en: 'Exhibition Booth Furniture',
      title_fa: 'مبلمان غرفه نمایشگاهی',
      title_ar: 'أثاث أكشاك المعارض',
      title_ru: 'Мебель для выставочных стендов',
      url: 'https://example.com/booth-furniture',
      pdf_url: 'https://example.com/catalogs/furniture.pdf',
      keywords: 'furniture, booth, exhibition, display, stand, modular',
      clicks: 67,
      enabled: false
    }
  ])

  const [searchQuery, setSearchQuery] = useState('')

  const filteredCatalogs = catalogs.filter(catalog =>
    catalog.title_en.toLowerCase().includes(searchQuery.toLowerCase()) ||
    catalog.keywords.toLowerCase().includes(searchQuery.toLowerCase())
  )

  const totalClicks = catalogs.reduce((sum, c) => sum + c.clicks, 0)
  const activeCatalogs = catalogs.filter(c => c.enabled).length

  return (
    <Layout>
      <div className="space-y-6 animate-fade-in">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-white mb-2 flex items-center gap-3">
              <BookOpen className="w-8 h-8 text-gold-500" />
              Catalog Management
            </h1>
            <p className="text-gray-400">
              Manage exhibition catalogs shared with visitors via bots
            </p>
          </div>
          <button className="px-6 py-3 btn-gold rounded-xl flex items-center gap-2">
            <Plus className="w-5 h-5" />
            Add Catalog
          </button>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="glass-card glass-card-hover rounded-2xl p-6">
            <div className="flex items-start justify-between mb-4">
              <p className="text-sm font-medium text-white/50 uppercase tracking-wider">
                Total Catalogs
              </p>
              <div className="w-12 h-12 rounded-xl flex items-center justify-center bg-blue-500/20">
                <BookOpen className="w-6 h-6 text-blue-500" />
              </div>
            </div>
            <h3 className="text-3xl font-bold text-white">{catalogs.length}</h3>
            <p className="text-sm text-green-400 mt-2">{activeCatalogs} active</p>
          </div>

          <div className="glass-card glass-card-hover rounded-2xl p-6">
            <div className="flex items-start justify-between mb-4">
              <p className="text-sm font-medium text-white/50 uppercase tracking-wider">
                Total Clicks
              </p>
              <div className="w-12 h-12 rounded-xl flex items-center justify-center bg-gold-500/20">
                <BarChart2 className="w-6 h-6 text-gold-500" />
              </div>
            </div>
            <h3 className="text-3xl font-bold text-white">{totalClicks}</h3>
            <p className="text-sm text-white/40 mt-2">All time clicks</p>
          </div>

          <div className="glass-card glass-card-hover rounded-2xl p-6">
            <div className="flex items-start justify-between mb-4">
              <p className="text-sm font-medium text-white/50 uppercase tracking-wider">
                Languages
              </p>
              <div className="w-12 h-12 rounded-xl flex items-center justify-center bg-purple-500/20">
                <Globe className="w-6 h-6 text-purple-500" />
              </div>
            </div>
            <h3 className="text-3xl font-bold text-white">4</h3>
            <p className="text-sm text-white/40 mt-2">EN, FA, AR, RU</p>
          </div>
        </div>

        {/* Search */}
        <div className="glass-card rounded-2xl p-4">
          <div className="relative">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400 w-5 h-5" />
            <input
              type="text"
              placeholder="Search catalogs by title or keywords..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-12 pr-4 py-3 bg-navy-800/50 border border-white/10 rounded-xl text-white placeholder-gray-500 focus:outline-none focus:border-gold-500/50 transition-colors"
            />
          </div>
        </div>

        {/* Catalogs Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {filteredCatalogs.map((catalog) => (
            <div key={catalog.id} className="glass-card glass-card-hover rounded-2xl p-6">
              <div className="flex items-start justify-between mb-4">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <h3 className="text-xl font-bold text-white">{catalog.title_en}</h3>
                    <span className={`px-3 py-1 rounded-full text-xs font-bold ${
                      catalog.enabled 
                        ? 'bg-green-500/15 text-green-400 border border-green-500/30' 
                        : 'bg-gray-500/15 text-gray-400 border border-gray-500/30'
                    }`}>
                      {catalog.enabled ? 'Active' : 'Disabled'}
                    </span>
                  </div>
                  <p className="text-sm text-gray-400">
                    <span className="text-gold-500 font-medium">Keywords:</span> {catalog.keywords}
                  </p>
                </div>
                <div className="flex gap-2">
                  <button className="p-2 hover:bg-white/10 rounded-lg transition-colors">
                    <Edit className="w-4 h-4 text-gray-400" />
                  </button>
                  <button className="p-2 hover:bg-red-500/20 rounded-lg transition-colors">
                    <Trash2 className="w-4 h-4 text-red-400" />
                  </button>
                </div>
              </div>

              {/* Multi-language titles */}
              <div className="space-y-2 mb-4 p-4 bg-white/5 rounded-xl border border-white/10">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-bold text-gray-500 w-8">FA:</span>
                  <span className="text-sm text-white">{catalog.title_fa}</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-xs font-bold text-gray-500 w-8">AR:</span>
                  <span className="text-sm text-white">{catalog.title_ar}</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-xs font-bold text-gray-500 w-8">RU:</span>
                  <span className="text-sm text-white">{catalog.title_ru}</span>
                </div>
              </div>

              {/* URL & Stats */}
              <div className="flex items-center justify-between gap-4">
                <div className="flex items-center gap-3 flex-1 min-w-0">
                  <a
                    href={catalog.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-2 text-sm text-gold-500 hover:text-gold-400 transition-colors min-w-0"
                  >
                    <ExternalLink className="w-4 h-4 flex-shrink-0" />
                    <span className="truncate">View Online</span>
                  </a>
                  {catalog.pdf_url && (
                    <a
                      href={catalog.pdf_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center gap-2 px-3 py-1 text-xs bg-red-500/20 text-red-400 border border-red-500/30 rounded-lg hover:bg-red-500/30 transition-colors flex-shrink-0"
                    >
                      📄 PDF
                    </a>
                  )}
                </div>
                <div className="flex items-center gap-2 text-sm flex-shrink-0">
                  <BarChart2 className="w-4 h-4 text-gray-400" />
                  <span className="text-white font-bold">{catalog.clicks}</span>
                  <span className="text-gray-500">clicks</span>
                </div>
              </div>
            </div>
          ))}
        </div>

        {filteredCatalogs.length === 0 && (
          <div className="glass-card rounded-2xl p-12 text-center">
            <BookOpen className="w-16 h-16 text-gray-500 mx-auto mb-4" />
            <p className="text-gray-400">No catalogs found</p>
          </div>
        )}
      </div>
    </Layout>
  )
}

export default Catalogs
