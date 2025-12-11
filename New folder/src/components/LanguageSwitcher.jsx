import { useLanguage } from '../context/LanguageContext'
import { Globe } from 'lucide-react'

const LanguageSwitcher = () => {
  const { language, setLanguage } = useLanguage()

  const languages = [
    { code: 'en', name: 'English', flag: '🇬🇧' },
    { code: 'fa', name: 'فارسی', flag: '🇮🇷' },
    { code: 'ar', name: 'العربية', flag: '🇦🇪' }
  ]

  return (
    <div className="relative group">
      <button className="flex items-center gap-2 px-4 py-2 bg-white/5 hover:bg-white/10 rounded-xl transition-all border border-white/10">
        <Globe className="w-5 h-5 text-white/70" />
        <span className="text-white/90 font-medium">
          {languages.find(l => l.code === language)?.flag}
        </span>
      </button>

      {/* Dropdown */}
      <div className="absolute top-full mt-2 right-0 w-48 bg-navy-800 border border-white/10 rounded-xl shadow-2xl opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all z-50">
        {languages.map((lang) => (
          <button
            key={lang.code}
            onClick={() => setLanguage(lang.code)}
            className={`w-full flex items-center gap-3 px-4 py-3 hover:bg-white/10 transition-all first:rounded-t-xl last:rounded-b-xl ${
              language === lang.code ? 'bg-gold-500/20 text-gold-400' : 'text-white/70'
            }`}
          >
            <span className="text-xl">{lang.flag}</span>
            <span className="font-medium">{lang.name}</span>
            {language === lang.code && (
              <span className="ml-auto text-gold-400">✓</span>
            )}
          </button>
        ))}
      </div>
    </div>
  )
}

export default LanguageSwitcher
