import { useState, useEffect } from 'react'
import { X, Save, User, Phone, Mail, MapPin, DollarSign, MessageSquare, AlertCircle } from 'lucide-react'
import AISalesCoach from './AISalesCoach'
import QuickWhatsAppTemplates from './QuickWhatsAppTemplates'

const LeadModal = ({ isOpen, onClose, onSave, lead = null, mode = 'create' }) => {
  const [formData, setFormData] = useState({
    full_name: '',
    phone: '',
    email: '',
    telegram_username: '',
    product_interest: '',
    budget_min: '',
    budget_max: '',
    company_name: '',
    job_title: '',
    status: 'new',
    priority: 'medium',
    notes: ''
  })

  const [errors, setErrors] = useState({})
  const [isSubmitting, setIsSubmitting] = useState(false)

  useEffect(() => {
    if (lead && mode === 'edit') {
      setFormData({
        full_name: lead.full_name || '',
        phone: lead.phone || '',
        email: lead.email || '',
        telegram_username: lead.telegram_username || '',
        product_interest: lead.product_interest || '',
        budget_min: lead.budget_min || '',
        budget_max: lead.budget_max || '',
        company_name: lead.company_name || '',
        job_title: lead.job_title || '',
        status: lead.status || 'new',
        priority: lead.priority || 'medium',
        notes: lead.notes || ''
      })
    } else {
      // Reset form for create mode
      setFormData({
        full_name: '',
        phone: '',
        email: '',
        telegram_username: '',
        product_interest: '',
        budget_min: '',
        budget_max: '',
        company_name: '',
        job_title: '',
        status: 'new',
        priority: 'medium',
        notes: ''
      })
    }
    setErrors({})
  }, [lead, mode, isOpen])

  const validate = () => {
    const newErrors = {}

    if (!formData.full_name.trim()) {
      newErrors.full_name = 'Name is required'
    }

    if (!formData.phone && !formData.email && !formData.telegram_username) {
      newErrors.contact = 'At least one contact method is required (Phone, Email, or Telegram)'
    }

    // Phone validation - international format
    if (formData.phone) {
      // Remove spaces, dashes, parentheses
      const cleanPhone = formData.phone.replace(/[\s\-\(\)]/g, '')
      
      // Must start with + and have 10-15 digits
      const phoneRegex = /^\+?[1-9]\d{9,14}$/
      
      if (!phoneRegex.test(cleanPhone)) {
        newErrors.phone = 'Invalid phone number. Use international format: +971501234567'
      }
      
      // Check for obviously invalid patterns
      if (/[a-zA-Z]/.test(cleanPhone)) {
        newErrors.phone = 'Phone number cannot contain letters'
      }
    }

    if (formData.email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      newErrors.email = 'Invalid email format'
    }

    if (formData.budget_min && formData.budget_max && 
        parseFloat(formData.budget_min) > parseFloat(formData.budget_max)) {
      newErrors.budget = 'Minimum budget cannot exceed maximum budget'
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = async (e) => {
    e.preventDefault()

    if (!validate()) return

    setIsSubmitting(true)

    try {
      await onSave(formData, lead?.id)
      onClose()
    } catch (error) {
      setErrors({ submit: error.message || 'Failed to save lead' })
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleChange = (e) => {
    const { name, value } = e.target
    setFormData(prev => ({
      ...prev,
      [name]: value
    }))
    // Clear error for this field
    if (errors[name]) {
      setErrors(prev => {
        const newErrors = { ...prev }
        delete newErrors[name]
        return newErrors
      })
    }
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50 p-0 sm:p-4 animate-fade-in">
      <div className="glass-card rounded-none sm:rounded-2xl max-w-3xl w-full h-full sm:h-auto sm:max-h-[90vh] overflow-hidden shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between p-4 sm:p-6 border-b border-white/10">
          <h2 className="text-xl sm:text-2xl font-bold text-white flex items-center gap-2 sm:gap-3">
            <User className="w-5 h-5 sm:w-6 sm:h-6 text-gold-500" />
            <span className="hidden sm:inline">{mode === 'edit' ? '✏️ Edit Visitor Info' : '➕ Add New Visitor'}</span>
            <span className="sm:hidden">{mode === 'edit' ? 'Edit' : 'Add'}</span>
          </h2>
          <button
            onClick={onClose}
            className="p-2 hover:bg-white/10 rounded-lg transition-colors touch-manipulation"
            aria-label="Close"
          >
            <X className="w-5 h-5 text-white/60" />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-4 sm:p-6 overflow-y-auto h-[calc(100vh-140px)] sm:h-auto sm:max-h-[calc(90vh-140px)]">
          {/* Error Alert */}
          {(errors.contact || errors.submit) && (
            <div className="mb-6 p-4 bg-red-500/10 border border-red-500/30 rounded-xl flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
              <div>
                <p className="text-sm font-semibold text-red-400">Error</p>
                <p className="text-sm text-red-300/80">{errors.contact || errors.submit}</p>
              </div>
            </div>
          )}

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Full Name */}
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-white/70 mb-2">
                Full Name <span className="text-red-400">*</span>
              </label>
              <input
                type="text"
                name="full_name"
                value={formData.full_name}
                onChange={handleChange}
                className={`w-full px-4 py-3 bg-white/5 border ${
                  errors.full_name ? 'border-red-500/50' : 'border-white/10'
                } rounded-xl text-white placeholder-white/30 focus:outline-none focus:border-gold-500/40 focus:ring-4 focus:ring-gold-500/10 transition-all`}
                placeholder="John Doe"
              />
              {errors.full_name && (
                <p className="mt-1 text-sm text-red-400">{errors.full_name}</p>
              )}
            </div>

            {/* Phone */}
            <div>
              <label className="block text-sm font-medium text-white/70 mb-2">
                Phone Number
              </label>
              <div className="relative">
                <Phone className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-white/40" />
                <input
                  type="tel"
                  name="phone"
                  value={formData.phone}
                  onChange={handleChange}
                  className={`w-full pl-12 pr-4 py-3 bg-white/5 border ${
                    errors.phone ? 'border-red-500/50' : 'border-white/10'
                  } rounded-xl text-white placeholder-white/30 focus:outline-none focus:border-gold-500/40 focus:ring-4 focus:ring-gold-500/10 transition-all`}
                  placeholder="+971501234567 (international format)"
                />
              </div>
              {errors.phone && (
                <p className="mt-1 text-sm text-red-400">{errors.phone}</p>
              )}
            </div>

            {/* Email */}
            <div>
              <label className="block text-sm font-medium text-white/70 mb-2">
                Email
              </label>
              <div className="relative">
                <Mail className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-white/40" />
                <input
                  type="email"
                  name="email"
                  value={formData.email}
                  onChange={handleChange}
                  className={`w-full pl-12 pr-4 py-3 bg-white/5 border ${
                    errors.email ? 'border-red-500/50' : 'border-white/10'
                  } rounded-xl text-white placeholder-white/30 focus:outline-none focus:border-gold-500/40 focus:ring-4 focus:ring-gold-500/10 transition-all`}
                  placeholder="john@example.com"
                />
              </div>
              {errors.email && (
                <p className="mt-1 text-sm text-red-400">{errors.email}</p>
              )}
            </div>

            {/* Telegram */}
            <div>
              <label className="block text-sm font-medium text-white/70 mb-2">
                Telegram Username
              </label>
              <input
                type="text"
                name="telegram_username"
                value={formData.telegram_username}
                onChange={handleChange}
                className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white placeholder-white/30 focus:outline-none focus:border-gold-500/40 focus:ring-4 focus:ring-gold-500/10 transition-all"
                placeholder="@johndoe"
              />
            </div>

            {/* Product Interest */}
            <div>
              <label className="block text-sm font-medium text-white/70 mb-2">
                🎯 Product/Service Interest
              </label>
              <select
                name="product_interest"
                value={formData.product_interest}
                onChange={handleChange}
                className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white focus:outline-none focus:border-gold-500/40 focus:ring-4 focus:ring-gold-500/10 transition-all"
              >
                <option value="">Select Product Category</option>
                <option value="furniture">🛋️ Furniture</option>
                <option value="electronics">📱 Electronics</option>
                <option value="software">💻 Software/SaaS</option>
                <option value="machinery">⚙️ Machinery/Equipment</option>
                <option value="services">👥 Professional Services</option>
                <option value="consulting">📊 Consulting</option>
                <option value="other">✨ Other</option>
              </select>
            </div>

            {/* Budget Min */}
            <div>
              <label className="block text-sm font-medium text-white/70 mb-2">
                💵 Estimated Order Value (Min)
              </label>
              <div className="relative">
                <DollarSign className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-white/40" />
                <input
                  type="number"
                  name="budget_min"
                  value={formData.budget_min}
                  onChange={handleChange}
                  className="w-full pl-12 pr-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white placeholder-white/30 focus:outline-none focus:border-gold-500/40 focus:ring-4 focus:ring-gold-500/10 transition-all"
                  placeholder="10000"
                  min="0"
                />
              </div>
            </div>

            {/* Budget Max */}
            <div>
              <label className="block text-sm font-medium text-white/70 mb-2">
                💰 Estimated Order Value (Max)
              </label>
              <div className="relative">
                <DollarSign className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-white/40" />
                <input
                  type="number"
                  name="budget_max"
                  value={formData.budget_max}
                  onChange={handleChange}
                  className="w-full pl-12 pr-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white placeholder-white/30 focus:outline-none focus:border-gold-500/40 focus:ring-4 focus:ring-gold-500/10 transition-all"
                  placeholder="500000"
                  min="0"
                />
              </div>
              {errors.budget && (
                <p className="mt-1 text-sm text-red-400">{errors.budget}</p>
              )}
            </div>

            {/* Company Name */}
            <div>
              <label className="block text-sm font-medium text-white/70 mb-2">
                🏢 Company Name
              </label>
              <div className="relative">
                <MapPin className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-white/40" />
                <input
                  type="text"
                  name="company_name"
                  value={formData.company_name}
                  onChange={handleChange}
                  className="w-full pl-12 pr-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white placeholder-white/30 focus:outline-none focus:border-gold-500/40 focus:ring-4 focus:ring-gold-500/10 transition-all"
                  placeholder="ABC Corporation"
                />
              </div>
            </div>

            {/* Job Title */}
            <div>
              <label className="block text-sm font-medium text-white/70 mb-2">
                💼 Job Title / Position
              </label>
              <input
                type="text"
                name="job_title"
                value={formData.job_title}
                onChange={handleChange}
                className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white placeholder-white/30 focus:outline-none focus:border-gold-500/40 focus:ring-4 focus:ring-gold-500/10 transition-all"
                placeholder="CEO, Marketing Manager, Buyer..."
              />
            </div>

            {/* Status */}
            <div>
              <label className="block text-sm font-medium text-white/70 mb-2">
                📊 Visitor Status
              </label>
              <select
                name="status"
                value={formData.status}
                onChange={handleChange}
                className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white focus:outline-none focus:border-gold-500/40 focus:ring-4 focus:ring-gold-500/10 transition-all"
              >
                <option value="new">🆕 Just Scanned</option>
                <option value="qualified">✨ Interested</option>
                <option value="viewing_scheduled">📞 Follow-up Scheduled</option>
                <option value="negotiation">💬 In Discussion</option>
                <option value="closed_won">🎉 Converted to Customer</option>
                <option value="closed_lost">❌ Not Interested</option>
              </select>
            </div>

            {/* Priority */}
            <div>
              <label className="block text-sm font-medium text-white/70 mb-2">
                🔥 Priority Level
              </label>
              <select
                name="priority"
                value={formData.priority}
                onChange={handleChange}
                className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white focus:outline-none focus:border-gold-500/40 focus:ring-4 focus:ring-gold-500/10 transition-all"
              >
                <option value="low">Low</option>
                <option value="medium">Medium</option>
                <option value="high">High</option>
                <option value="urgent">Urgent</option>
              </select>
            </div>

            {/* Notes */}
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-white/70 mb-2">
                Notes
              </label>
              <div className="relative">
                <MessageSquare className="absolute left-4 top-4 w-4 h-4 text-white/40" />
                <textarea
                  name="notes"
                  value={formData.notes}
                  onChange={handleChange}
                  rows="4"
                  className="w-full pl-12 pr-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white placeholder-white/30 focus:outline-none focus:border-gold-500/40 focus:ring-4 focus:ring-gold-500/10 transition-all resize-none"
                  placeholder="Additional notes about this lead..."
                />
              </div>
            </div>
          </div>

          {/* AI Sales Coach - Only show in edit mode */}
          {mode === 'edit' && lead?.id && (
            <>
              <AISalesCoach leadId={lead.id} leadData={lead} />
              <QuickWhatsAppTemplates lead={lead} />
            </>
          )}

          {/* Footer Buttons */}
          <div className="flex items-center gap-4 mt-8 pt-6 border-t border-white/10">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-6 py-3 bg-white/5 hover:bg-white/10 border border-white/10 rounded-xl text-white font-medium transition-all"
              disabled={isSubmitting}
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="flex-1 btn-gold flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isSubmitting ? (
                <>
                  <div className="spinner w-5 h-5 border-2"></div>
                  <span>Saving...</span>
                </>
              ) : (
                <>
                  <Save className="w-5 h-5" />
                  <span>{mode === 'edit' ? 'Update Lead' : 'Create Lead'}</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default LeadModal
