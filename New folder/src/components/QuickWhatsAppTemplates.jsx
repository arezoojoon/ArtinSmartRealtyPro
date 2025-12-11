import { useState } from 'react'
import { MessageCircle, Send, Clock, Zap } from 'lucide-react'

const QuickWhatsAppTemplates = ({ lead, onSend }) => {
  const [selectedTemplate, setSelectedTemplate] = useState(null)
  const [sending, setSending] = useState(false)

  const templates = [
    {
      id: 'welcome',
      icon: '👋',
      title: 'Welcome Message',
      preview: `سلام ${lead.full_name || 'عزیز'}! 🎉\n\nاز بازدید شما در نمایشگاه ممنونیم. چطوری می‌تونم کمکتون کنم؟`,
      text: (name) => `سلام ${name || 'عزیز'}! 🎉\n\nاز بازدید شما در نمایشگاه ممنونیم. چطوری می‌تونم کمکتون کنم؟`
    },
    {
      id: 'catalog',
      icon: '📚',
      title: 'Send Catalog',
      preview: `${lead.full_name || 'سلام'}،\n\nکاتالوگ کامل محصولات ${lead.product_interest || ''} رو براتون ارسال کردم.\n\nلطفاً بررسی کنید و اگر سوالی دارید، در خدمتم! 🙌`,
      text: (name, product) => `${name || 'سلام'},\n\nکاتالوگ کامل محصولات ${product || 'ما'} رو براتون ارسال کردم.\n\nلطفاً بررسی کنید و اگر سوالی دارید، در خدمتم! 🙌`
    },
    {
      id: 'discount',
      icon: '🎁',
      title: 'Exhibition Discount',
      preview: `${lead.full_name || 'عزیز'}! 🔥\n\nتخفیف ویژه نمایشگاه: 20% تخفیف فقط تا پایان هفته!\n\nبرای ثبت سفارش همین الان تماس بگیرید: 021-1234567`,
      text: (name) => `${name || 'عزیز'}! 🔥\n\nتخفیف ویژه نمایشگاه: 20% تخفیف فقط تا پایان هفته!\n\nبرای ثبت سفارش همین الان تماس بگیرید: 021-1234567`
    },
    {
      id: 'followup',
      icon: '📞',
      title: 'Follow-up Call',
      preview: `سلام ${lead.full_name || 'آقا/خانم'}،\n\nامیدوارم از بازدید نمایشگاه لذت برده باشید.\n\nفردا ساعت 3 بعدازظهر تماس می‌گیرم برای بررسی نیازهاتون. مناسبه؟`,
      text: (name) => `سلام ${name || 'آقا/خانم'},\n\nامیدوارم از بازدید نمایشگاه لذت برده باشید.\n\nفردا ساعت 3 بعدازظهر تماس می‌گیرم برای بررسی نیازهاتون. مناسبه?`
    },
    {
      id: 'urgent',
      icon: '⚡',
      title: 'Urgent Response',
      preview: `${lead.full_name}! ⏰\n\nفقط 3 عدد از این محصول باقی مونده!\n\nاگر می‌خواید رزرو کنید، همین الان بهم پیام بدید.`,
      text: (name) => `${name}! ⏰\n\nفقط 3 عدد از این محصول باقی مونده!\n\nاگر می‌خواید رزرو کنید، همین الان بهم پیام بدید.`
    },
    {
      id: 'demo',
      icon: '🎬',
      title: 'Demo Request',
      preview: `${lead.full_name}،\n\nیه دمو اختصاصی 30 دقیقه‌ای برای شما آماده کردیم.\n\nچه زمانی براتون راحته؟\n• فردا صبح 10\n• فردا بعدازظهر 3\n• پس‌فردا صبح 11`,
      text: (name) => `${name},\n\nیه دمو اختصاصی 30 دقیقه‌ای برای شما آماده کردیم.\n\nچه زمانی براتون راحته?\n• فردا صبح 10\n• فردا بعدازظهر 3\n• پس‌فردا صبح 11`
    }
  ]

  const handleSendTemplate = async (template) => {
    if (!lead.phone && !lead.whatsapp_number) {
      alert('No phone number available for this lead')
      return
    }

    setSending(true)
    setSelectedTemplate(template.id)

    try {
      const message = template.text(lead.full_name, lead.product_interest)
      const phone = lead.whatsapp_number || lead.phone
      
      // Open WhatsApp Web with pre-filled message
      const whatsappUrl = `https://wa.me/${phone.replace(/[^0-9]/g, '')}?text=${encodeURIComponent(message)}`
      window.open(whatsappUrl, '_blank')

      // Track action in backend
      if (onSend) {
        await onSend(template.id, message)
      }

      setTimeout(() => {
        setSending(false)
        setSelectedTemplate(null)
      }, 1000)

    } catch (error) {
      console.error('Failed to send WhatsApp message:', error)
      setSending(false)
      setSelectedTemplate(null)
    }
  }

  return (
    <div className="mt-4 bg-gradient-to-br from-green-50 to-emerald-50 dark:from-green-900/20 dark:to-emerald-900/20 rounded-xl p-6 border border-green-200 dark:border-green-800">
      {/* Header */}
      <div className="flex items-center gap-3 mb-4">
        <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-green-500 to-emerald-500 flex items-center justify-center">
          <MessageCircle className="w-5 h-5 text-white" />
        </div>
        <div>
          <h3 className="font-bold text-gray-900 dark:text-white">
            💬 Quick WhatsApp Messages
          </h3>
          <p className="text-xs text-gray-500 dark:text-gray-400">
            Send pre-written templates instantly
          </p>
        </div>
      </div>

      {/* Templates Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        {templates.map((template) => (
          <button
            key={template.id}
            onClick={() => handleSendTemplate(template)}
            disabled={sending && selectedTemplate === template.id}
            className="group relative bg-white dark:bg-gray-800 rounded-lg p-4 border-2 border-green-200 dark:border-green-800 hover:border-green-400 dark:hover:border-green-600 transition-all hover:shadow-lg disabled:opacity-50 disabled:cursor-not-allowed text-left"
          >
            {/* Icon & Title */}
            <div className="flex items-start justify-between mb-2">
              <div className="flex items-center gap-2">
                <span className="text-2xl">{template.icon}</span>
                <span className="font-semibold text-gray-900 dark:text-white text-sm">
                  {template.title}
                </span>
              </div>
              {sending && selectedTemplate === template.id ? (
                <div className="w-5 h-5 border-2 border-green-500/30 border-t-green-500 rounded-full animate-spin"></div>
              ) : (
                <Send className="w-4 h-4 text-green-600 dark:text-green-400 opacity-0 group-hover:opacity-100 transition-opacity" />
              )}
            </div>

            {/* Preview */}
            <p className="text-xs text-gray-600 dark:text-gray-400 line-clamp-3 leading-relaxed">
              {template.preview}
            </p>

            {/* Hover Effect */}
            <div className="absolute inset-0 bg-gradient-to-r from-green-500/5 to-emerald-500/5 rounded-lg opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none"></div>
          </button>
        ))}
      </div>

      {/* Info */}
      <div className="mt-4 flex items-center gap-2 text-xs text-gray-500 dark:text-gray-400">
        <Zap className="w-4 h-4" />
        <span>Click to open WhatsApp with pre-filled message</span>
      </div>
    </div>
  )
}

export default QuickWhatsAppTemplates
