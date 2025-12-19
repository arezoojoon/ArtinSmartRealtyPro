import { createContext, useContext, useState, useEffect } from 'react'
import { translations, getTranslation } from '../i18n/translations'

const LanguageContext = createContext()

export const useLanguage = () => {
  const context = useContext(LanguageContext)
  if (!context) {
    throw new Error('useLanguage must be used within LanguageProvider')
  }
  return context
}

export const LanguageProvider = ({ children }) => {
  const [language, setLanguage] = useState(() => {
    // Load from localStorage or default to English
    return localStorage.getItem('language') || 'en'
  })

  useEffect(() => {
    // Save to localStorage
    localStorage.setItem('language', language)
    
    // Set HTML dir and lang attributes
    const isRTL = ['fa', 'ar'].includes(language)
    document.documentElement.dir = isRTL ? 'rtl' : 'ltr'
    document.documentElement.lang = language
    
    // Add RTL class to body for CSS targeting
    if (isRTL) {
      document.body.classList.add('rtl')
    } else {
      document.body.classList.remove('rtl')
    }
  }, [language])

  const t = (key) => getTranslation(language, key)
  
  const isRTL = ['fa', 'ar'].includes(language)

  const value = {
    language,
    setLanguage,
    t,
    isRTL,
    translations: translations[language] || translations.en
  }

  return (
    <LanguageContext.Provider value={value}>
      {children}
    </LanguageContext.Provider>
  )
}
